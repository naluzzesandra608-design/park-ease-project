from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.landing, name='landing'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Parking
    path('parking/register/', views.register_vehicle, name='register_vehicle'),
    path('parking/signout/', views.signout_vehicle, name='signout_vehicle'),
    path('parking/signout/<int:pk>/', views.process_signout, name='process_signout'),
    path('parking/receipt/<int:pk>/', views.view_receipt, name='view_receipt'),
    path('parking/active/', views.active_vehicles, name='active_vehicles'),

    # Tyre
    path('tyre/', views.tyre_dashboard, name='tyre_dashboard'),
    path('tyre/service/', views.tyre_service, name='tyre_service'),
    path('tyre/prices/', views.tyre_prices, name='tyre_prices'),

    # Battery
    path('battery/', views.battery_dashboard, name='battery_dashboard'),
    path('battery/transaction/', views.battery_transaction, name='battery_transaction'),
    path('battery/prices/', views.battery_prices, name='battery_prices'),

    # Reports
    path('reports/', views.reports, name='reports'),
    path('reports/daily/', views.daily_report, name='daily_report'),

    # Admin/Users
    path('users/', views.manage_users, name='manage_users'),
    path('users/create/', views.create_user, name='create_user'),
    path('users/delete/<int:pk>/', views.delete_user, name='delete_user'),

    # API
    path('api/vehicle/<str:plate>/', views.api_vehicle_lookup, name='api_vehicle_lookup'),
]
