"""
Management command to create initial data for ParkEase.
Run: python manage.py setup_parkease
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import UserProfile, TyrePrice, BatteryPrice


class Command(BaseCommand):
    help = 'Set up initial ParkEase data (admin user, sample prices)'

    def handle(self, *args, **options):
        self.stdout.write('Setting up ParkEase...')

        # Create superuser / admin
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                password='parkease123',
                first_name='System',
                last_name='Admin',
                email='admin@parkville.ug'
            )
            UserProfile.objects.create(user=admin, role='admin', phone='0712000000')
            self.stdout.write(self.style.SUCCESS('✅ Admin user created: admin / parkease123'))
        else:
            self.stdout.write('ℹ️  Admin user already exists.')

        # Create attendant
        if not User.objects.filter(username='attendant1').exists():
            att = User.objects.create_user(
                username='attendant1',
                password='attend123',
                first_name='John',
                last_name='Mukasa',
            )
            UserProfile.objects.create(user=att, role='attendant', phone='0701234567')
            self.stdout.write(self.style.SUCCESS('✅ Attendant created: attendant1 / attend123'))

        # Create tyre manager
        if not User.objects.filter(username='tyre_mgr').exists():
            tm = User.objects.create_user(
                username='tyre_mgr',
                password='tyre123',
                first_name='Peter',
                last_name='Ssebale',
            )
            UserProfile.objects.create(user=tm, role='tyre_manager', phone='0752345678')
            self.stdout.write(self.style.SUCCESS('✅ Tyre Manager created: tyre_mgr / tyre123'))

        # Create battery manager
        if not User.objects.filter(username='battery_mgr').exists():
            bm = User.objects.create_user(
                username='battery_mgr',
                password='battery123',
                first_name='Sarah',
                last_name='Nakato',
            )
            UserProfile.objects.create(user=bm, role='battery_manager', phone='0783456789')
            self.stdout.write(self.style.SUCCESS('✅ Battery Manager created: battery_mgr / battery123'))

        # Sample tyre prices
        if not TyrePrice.objects.exists():
            admin_user = User.objects.filter(username='admin').first()
            tyres = [
                ('165/70R13', 'Bridgestone', 95000),
                ('185/65R15', 'Michelin', 120000),
                ('195/65R15', 'Dunlop', 110000),
                ('205/55R16', 'Pirelli', 145000),
                ('245/70R16', 'Goodyear', 180000),
                ('7.00R16', 'Hankook', 250000),
            ]
            for size, brand, price in tyres:
                TyrePrice.objects.create(size=size, brand=brand, price=price, set_by=admin_user)
            self.stdout.write(self.style.SUCCESS('✅ Sample tyre prices added.'))

        # Sample battery prices
        if not BatteryPrice.objects.exists():
            admin_user = User.objects.filter(username='admin').first()
            batteries = [
                ('Exide', '45Ah', 'hire', 15000, 'per day'),
                ('Exide', '45Ah', 'sale', 280000, ''),
                ('Chloride', '60Ah', 'hire', 20000, 'per day'),
                ('Chloride', '60Ah', 'sale', 350000, ''),
                ('Raylite', '100Ah', 'hire', 30000, 'per day'),
                ('Raylite', '100Ah', 'sale', 550000, ''),
            ]
            for brand, cap, ttype, price, dur in batteries:
                BatteryPrice.objects.create(
                    brand=brand, capacity=cap, transaction_type=ttype,
                    price=price, hire_duration=dur, set_by=admin_user
                )
            self.stdout.write(self.style.SUCCESS('✅ Sample battery prices added.'))

        self.stdout.write(self.style.SUCCESS('\n🎉 ParkEase setup complete!'))
        self.stdout.write('\nLogin credentials:')
        self.stdout.write('  Admin:            admin / parkease123')
        self.stdout.write('  Parking Attendant: attendant1 / attend123')
        self.stdout.write('  Tyre Manager:     tyre_mgr / tyre123')
        self.stdout.write('  Battery Manager:  battery_mgr / battery123')
