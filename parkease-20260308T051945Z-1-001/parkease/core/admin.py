from django.contrib import admin
from .models import (Vehicle, ParkingReceipt, TyrePrice, TyreServiceTransaction,
                     BatteryPrice, BatteryTransaction, UserProfile)

admin.site.register(Vehicle)
admin.site.register(ParkingReceipt)
admin.site.register(TyrePrice)
admin.site.register(TyreServiceTransaction)
admin.site.register(BatteryPrice)
admin.site.register(BatteryTransaction)
admin.site.register(UserProfile)
admin.site.site_header = 'ParkEase Admin'
admin.site.site_title = 'ParkEase'
