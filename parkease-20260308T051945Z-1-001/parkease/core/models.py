from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'System Admin'),
        ('attendant', 'Parking Attendant'),
        ('tyre_manager', 'Tyre Section Manager'),
        ('battery_manager', 'Battery Section Manager'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='attendant')
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"


class Vehicle(models.Model):
    VEHICLE_TYPES = [
        ('truck', 'Truck'),
        ('personal_car', 'Personal Car'),
        ('taxi', 'Taxi'),
        ('coaster', 'Coaster'),
        ('boda_boda', 'Boda-boda'),
    ]

    # Driver Info
    driver_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    nin_number = models.CharField(max_length=30, blank=True)

    # Vehicle Info
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES)
    number_plate = models.CharField(max_length=10)
    vehicle_model = models.CharField(max_length=100)
    vehicle_color = models.CharField(max_length=50)

    # Timing
    arrival_time = models.DateTimeField(default=timezone.now)
    departure_time = models.DateTimeField(null=True, blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    registered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='registered_vehicles')

    def __str__(self):
        return f"{self.number_plate} - {self.driver_name}"

    @property
    def duration_hours(self):
        end = self.departure_time or timezone.now()
        delta = end - self.arrival_time
        return delta.total_seconds() / 3600

    @property
    def parking_rate_type(self):
        """Determine if arrival was day, night, or short stay"""
        hour = self.arrival_time.hour
        duration = self.duration_hours
        if duration < 3:
            return 'short'
        elif 6 <= hour <= 18:
            return 'day'
        else:
            return 'night'

    @property
    def parking_fee(self):
        rate_type = self.parking_rate_type
        rates = {
            'truck':        {'day': 5000, 'night': 10000, 'short': 2000},
            'personal_car': {'day': 3000, 'night': 2000,  'short': 2000},
            'taxi':         {'day': 3000, 'night': 2000,  'short': 2000},
            'coaster':      {'day': 4000, 'night': 2000,  'short': 3000},
            'boda_boda':    {'day': 2000, 'night': 2000,  'short': 1000},
        }
        vtype = self.vehicle_type
        if vtype in rates and rate_type in rates[vtype]:
            return rates[vtype][rate_type]
        return 0


class ParkingReceipt(models.Model):
    vehicle = models.OneToOneField(Vehicle, on_delete=models.CASCADE, related_name='receipt')
    receipt_number = models.CharField(max_length=20, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Sign-out info
    receiver_name = models.CharField(max_length=100, blank=True)
    receiver_phone = models.CharField(max_length=20, blank=True)
    receiver_gender = models.CharField(max_length=10, blank=True)
    receiver_nin = models.CharField(max_length=30, blank=True)
    signed_out_at = models.DateTimeField(null=True, blank=True)
    signed_out_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Receipt #{self.receipt_number}"

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = f"PKE-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
        super().save(*args, **kwargs)


class TyrePrice(models.Model):
    size = models.CharField(max_length=50)
    brand = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    set_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.brand} {self.size} - UGX {self.price}"


class TyreServiceTransaction(models.Model):
    SERVICE_TYPES = [
        ('pressure', 'Pressure Check'),
        ('puncture', 'Puncture Fixing'),
        ('valve', 'Valve Replacement'),
        ('new_tyre', 'New Tyre Sale'),
    ]
    vehicle_plate = models.CharField(max_length=10)
    driver_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPES)
    tyre_size = models.CharField(max_length=50, blank=True)
    tyre_brand = models.CharField(max_length=100, blank=True)
    quantity = models.IntegerField(default=1)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_date = models.DateTimeField(default=timezone.now)
    served_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    receipt_number = models.CharField(max_length=20, unique=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Tyre - {self.vehicle_plate} - {self.receipt_number}"

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = f"TYR-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
        super().save(*args, **kwargs)


class BatteryPrice(models.Model):
    TRANSACTION_TYPES = [
        ('hire', 'Hire'),
        ('sale', 'Sale'),
    ]
    brand = models.CharField(max_length=100)
    capacity = models.CharField(max_length=50)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    hire_duration = models.CharField(max_length=50, blank=True, help_text="e.g., per day, per week")
    set_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.brand} {self.capacity} ({self.transaction_type}) - UGX {self.price}"


class BatteryTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('hire', 'Hire'),
        ('sale', 'Sale'),
        ('return', 'Return'),
    ]
    customer_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    vehicle_plate = models.CharField(max_length=10, blank=True)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    battery_brand = models.CharField(max_length=100)
    battery_capacity = models.CharField(max_length=50)
    quantity = models.IntegerField(default=1)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    hire_start = models.DateField(null=True, blank=True)
    hire_end = models.DateField(null=True, blank=True)
    transaction_date = models.DateTimeField(default=timezone.now)
    served_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    receipt_number = models.CharField(max_length=20, unique=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Battery - {self.customer_name} - {self.receipt_number}"

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = f"BAT-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
        super().save(*args, **kwargs)
