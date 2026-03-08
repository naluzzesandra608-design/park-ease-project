from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import date, timedelta
from decimal import Decimal

from .models import (Vehicle, ParkingReceipt, TyreServiceTransaction,
                     TyrePrice, BatteryTransaction, BatteryPrice, UserProfile)
from .forms import (VehicleRegistrationForm, SignOutForm, TyreServiceForm,
                    TyrePriceForm, BatteryTransactionForm, BatteryPriceForm,
                    CreateUserForm, LoginForm)


# ─── Auth Views ────────────────────────────────────────────────────────────────

def landing(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm()
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password']
            )
            if user:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
    return render(request, 'core/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


# ─── Dashboard ─────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    today = date.today()
    active_vehicles = Vehicle.objects.filter(is_active=True).count()

    # Today's revenue
    parking_revenue = ParkingReceipt.objects.filter(
        signed_out_at__date=today
    ).aggregate(total=Sum('amount_paid'))['total'] or 0

    tyre_revenue = TyreServiceTransaction.objects.filter(
        transaction_date__date=today
    ).aggregate(total=Sum('amount'))['total'] or 0

    battery_revenue = BatteryTransaction.objects.filter(
        transaction_date__date=today
    ).aggregate(total=Sum('amount'))['total'] or 0

    total_revenue = parking_revenue + tyre_revenue + battery_revenue

    recent_vehicles = Vehicle.objects.filter(is_active=True).order_by('-arrival_time')[:5]
    recent_signouts = ParkingReceipt.objects.filter(
        signed_out_at__isnull=False
    ).order_by('-signed_out_at')[:5]

    context = {
        'active_vehicles': active_vehicles,
        'parking_revenue': parking_revenue,
        'tyre_revenue': tyre_revenue,
        'battery_revenue': battery_revenue,
        'total_revenue': total_revenue,
        'recent_vehicles': recent_vehicles,
        'recent_signouts': recent_signouts,
    }
    return render(request, 'core/dashboard.html', context)


# ─── Parking Views ─────────────────────────────────────────────────────────────

@login_required
def register_vehicle(request):
    role = getattr(getattr(request.user, 'profile', None), 'role', 'admin')
    if role not in ['attendant', 'admin']:
        messages.error(request, 'You do not have permission to register vehicles.')
        return redirect('dashboard')

    form = VehicleRegistrationForm()
    if request.method == 'POST':
        form = VehicleRegistrationForm(request.POST)
        if form.is_valid():
            vehicle = form.save(commit=False)
            vehicle.registered_by = request.user
            vehicle.save()
            # Create receipt
            receipt = ParkingReceipt.objects.create(vehicle=vehicle)
            messages.success(request, f'Vehicle registered! Receipt: {receipt.receipt_number}')
            return redirect('view_receipt', pk=receipt.pk)

    return render(request, 'core/register_vehicle.html', {'form': form})


@login_required
def active_vehicles(request):
    vehicles = Vehicle.objects.filter(is_active=True).order_by('-arrival_time')
    return render(request, 'core/active_vehicles.html', {'vehicles': vehicles})


@login_required
def signout_vehicle(request):
    query = request.GET.get('q', '')
    vehicle = None
    receipt = None
    if query:
        # Try by receipt number
        try:
            receipt = ParkingReceipt.objects.get(receipt_number__iexact=query, signed_out_at__isnull=True)
            vehicle = receipt.vehicle
        except ParkingReceipt.DoesNotExist:
            # Try by plate
            try:
                vehicle = Vehicle.objects.get(number_plate__iexact=query, is_active=True)
                receipt = vehicle.receipt
            except (Vehicle.DoesNotExist, ParkingReceipt.DoesNotExist):
                messages.error(request, f'No active vehicle found for: {query}')

    return render(request, 'core/signout_vehicle.html', {
        'vehicle': vehicle,
        'receipt': receipt,
        'query': query,
    })


@login_required
def process_signout(request, pk):
    receipt = get_object_or_404(ParkingReceipt, pk=pk, signed_out_at__isnull=True)
    vehicle = receipt.vehicle
    form = SignOutForm(instance=receipt)

    if request.method == 'POST':
        form = SignOutForm(request.POST, instance=receipt)
        if form.is_valid():
            signout = form.save(commit=False)
            signout.signed_out_at = timezone.now()
            signout.signed_out_by = request.user
            signout.amount_paid = vehicle.parking_fee
            signout.save()
            vehicle.departure_time = timezone.now()
            vehicle.is_active = False
            vehicle.save()
            messages.success(request, f'Vehicle signed out. Fee: UGX {vehicle.parking_fee:,}')
            return redirect('view_receipt', pk=receipt.pk)

    return render(request, 'core/process_signout.html', {
        'form': form,
        'vehicle': vehicle,
        'receipt': receipt,
    })


@login_required
def view_receipt(request, pk):
    receipt = get_object_or_404(ParkingReceipt, pk=pk)
    return render(request, 'core/receipt.html', {'receipt': receipt, 'vehicle': receipt.vehicle})


# ─── Tyre Views ────────────────────────────────────────────────────────────────

@login_required
def tyre_dashboard(request):
    today = date.today()
    transactions = TyreServiceTransaction.objects.order_by('-transaction_date')[:20]
    today_revenue = TyreServiceTransaction.objects.filter(
        transaction_date__date=today
    ).aggregate(total=Sum('amount'))['total'] or 0
    return render(request, 'core/tyre_dashboard.html', {
        'transactions': transactions,
        'today_revenue': today_revenue,
    })


@login_required
def tyre_service(request):
    role = getattr(getattr(request.user, 'profile', None), 'role', 'admin')
    if role not in ['tyre_manager', 'admin']:
        messages.error(request, 'You do not have permission to record tyre services.')
        return redirect('tyre_dashboard')

    prices = TyrePrice.objects.all()
    form = TyreServiceForm()
    if request.method == 'POST':
        form = TyreServiceForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.served_by = request.user
            transaction.save()
            messages.success(request, f'Tyre service recorded! Receipt: {transaction.receipt_number}')
            return redirect('tyre_dashboard')

    return render(request, 'core/tyre_service.html', {'form': form, 'prices': prices})


@login_required
def tyre_prices(request):
    role = getattr(getattr(request.user, 'profile', None), 'role', 'admin')
    if role not in ['tyre_manager', 'admin']:
        messages.error(request, 'Only Tyre Manager or Admin can manage prices.')
        return redirect('tyre_dashboard')

    prices = TyrePrice.objects.all()
    form = TyrePriceForm()
    if request.method == 'POST':
        form = TyrePriceForm(request.POST)
        if form.is_valid():
            price = form.save(commit=False)
            price.set_by = request.user
            price.save()
            messages.success(request, 'Tyre price added.')
            return redirect('tyre_prices')

    return render(request, 'core/tyre_prices.html', {'form': form, 'prices': prices})


# ─── Battery Views ─────────────────────────────────────────────────────────────

@login_required
def battery_dashboard(request):
    today = date.today()
    transactions = BatteryTransaction.objects.order_by('-transaction_date')[:20]
    today_revenue = BatteryTransaction.objects.filter(
        transaction_date__date=today
    ).aggregate(total=Sum('amount'))['total'] or 0
    return render(request, 'core/battery_dashboard.html', {
        'transactions': transactions,
        'today_revenue': today_revenue,
    })


@login_required
def battery_transaction(request):
    role = getattr(getattr(request.user, 'profile', None), 'role', 'admin')
    if role not in ['battery_manager', 'admin']:
        messages.error(request, 'You do not have permission to record battery transactions.')
        return redirect('battery_dashboard')

    prices = BatteryPrice.objects.all()
    form = BatteryTransactionForm()
    if request.method == 'POST':
        form = BatteryTransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.served_by = request.user
            transaction.save()
            messages.success(request, f'Battery transaction recorded! Receipt: {transaction.receipt_number}')
            return redirect('battery_dashboard')

    return render(request, 'core/battery_transaction.html', {'form': form, 'prices': prices})


@login_required
def battery_prices(request):
    role = getattr(getattr(request.user, 'profile', None), 'role', 'admin')
    if role not in ['battery_manager', 'admin']:
        messages.error(request, 'Only Battery Manager or Admin can manage prices.')
        return redirect('battery_dashboard')

    prices = BatteryPrice.objects.all()
    form = BatteryPriceForm()
    if request.method == 'POST':
        form = BatteryPriceForm(request.POST)
        if form.is_valid():
            price = form.save(commit=False)
            price.set_by = request.user
            price.save()
            messages.success(request, 'Battery price added.')
            return redirect('battery_prices')

    return render(request, 'core/battery_prices.html', {'form': form, 'prices': prices})


# ─── Reports ───────────────────────────────────────────────────────────────────

@login_required
def reports(request):
    role = getattr(getattr(request.user, 'profile', None), 'role', 'admin')
    if role != 'admin':
        messages.error(request, 'Only Admin can view reports.')
        return redirect('dashboard')
    return render(request, 'core/reports.html')


@login_required
def daily_report(request):
    role = getattr(getattr(request.user, 'profile', None), 'role', 'admin')
    if role != 'admin':
        messages.error(request, 'Only Admin can view reports.')
        return redirect('dashboard')

    report_date_str = request.GET.get('date', date.today().isoformat())
    try:
        report_date = date.fromisoformat(report_date_str)
    except ValueError:
        report_date = date.today()

    # Signed-out vehicles
    signouts = ParkingReceipt.objects.filter(
        signed_out_at__date=report_date
    ).select_related('vehicle')

    parking_revenue = signouts.aggregate(total=Sum('amount_paid'))['total'] or 0

    # Tyre
    tyre_transactions = TyreServiceTransaction.objects.filter(transaction_date__date=report_date)
    tyre_revenue = tyre_transactions.aggregate(total=Sum('amount'))['total'] or 0

    # Battery
    battery_transactions = BatteryTransaction.objects.filter(transaction_date__date=report_date)
    battery_revenue = battery_transactions.aggregate(total=Sum('amount'))['total'] or 0

    total_revenue = parking_revenue + tyre_revenue + battery_revenue

    # Vehicle type breakdown
    vehicle_breakdown = {}
    for so in signouts:
        vtype = so.vehicle.get_vehicle_type_display()
        if vtype not in vehicle_breakdown:
            vehicle_breakdown[vtype] = {'count': 0, 'revenue': 0}
        vehicle_breakdown[vtype]['count'] += 1
        vehicle_breakdown[vtype]['revenue'] += float(so.amount_paid)

    context = {
        'report_date': report_date,
        'signouts': signouts,
        'parking_revenue': parking_revenue,
        'tyre_revenue': tyre_revenue,
        'battery_revenue': battery_revenue,
        'total_revenue': total_revenue,
        'tyre_transactions': tyre_transactions,
        'battery_transactions': battery_transactions,
        'vehicle_breakdown': vehicle_breakdown,
    }
    return render(request, 'core/daily_report.html', context)


# ─── User Management ───────────────────────────────────────────────────────────

@login_required
def manage_users(request):
    role = getattr(getattr(request.user, 'profile', None), 'role', 'admin')
    if role != 'admin':
        messages.error(request, 'Only Admin can manage users.')
        return redirect('dashboard')
    users = User.objects.all().select_related('profile')
    return render(request, 'core/manage_users.html', {'users': users})


@login_required
def create_user(request):
    role = getattr(getattr(request.user, 'profile', None), 'role', 'admin')
    if role != 'admin':
        messages.error(request, 'Only Admin can create users.')
        return redirect('dashboard')

    form = CreateUserForm()
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            user = User.objects.create_user(
                username=d['username'],
                first_name=d['first_name'],
                last_name=d['last_name'],
                email=d.get('email', ''),
                password=d['password'],
            )
            UserProfile.objects.create(user=user, role=d['role'], phone=d.get('phone', ''))
            messages.success(request, f'User {user.username} created successfully.')
            return redirect('manage_users')

    return render(request, 'core/create_user.html', {'form': form})


@login_required
def delete_user(request, pk):
    role = getattr(getattr(request.user, 'profile', None), 'role', 'admin')
    if role != 'admin':
        messages.error(request, 'Only Admin can delete users.')
        return redirect('manage_users')
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('manage_users')
    user.delete()
    messages.success(request, 'User deleted.')
    return redirect('manage_users')


# ─── API ───────────────────────────────────────────────────────────────────────

@login_required
def api_vehicle_lookup(request, plate):
    try:
        vehicle = Vehicle.objects.get(number_plate__iexact=plate, is_active=True)
        receipt = vehicle.receipt
        return JsonResponse({
            'found': True,
            'driver_name': vehicle.driver_name,
            'vehicle_type': vehicle.get_vehicle_type_display(),
            'number_plate': vehicle.number_plate,
            'arrival_time': vehicle.arrival_time.strftime('%d/%m/%Y %H:%M'),
            'receipt_number': receipt.receipt_number,
            'parking_fee': vehicle.parking_fee,
            'receipt_pk': receipt.pk,
        })
    except (Vehicle.DoesNotExist, ParkingReceipt.DoesNotExist):
        return JsonResponse({'found': False})
