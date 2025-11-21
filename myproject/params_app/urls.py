from django.urls import path
from params_app import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login, name='login'),  # Add trailing slash here
    path('dashboard/', views.dashboard, name='dashboard'),  # Add trailing slash here
    path('signup/', views.signup, name='signup'),  # Add trailing slash here
    path('contact/', views.contact_view, name='contact'),  # Add trailing slash here
    path('about/', views.about, name='about'),  # Add trailing slash here
    path('userin/', views.userin, name='userin'),  # Add trailing slash here
    path('users/', views.user_list, name='users'),
    path('billings/', views.billings, name='billings'),
    path('locations/', views.locations, name='locations'),
    path('parkings/', views.parkings, name='parkings'),
    path('settings/', views.settings, name='settings'),
    path('slots/', views.slots, name='slots'),
    path('ticket/', views.ticket, name='ticket'),
    path('destination/', views.destination, name='destination'),
    path('generate-qr/', views.generate_qr_code, name='generate_qr_code'),  # for qr code
    path('generate-ticket/', views.generate_ticket, name='generate_ticket'),
    path('logout/', views.logout, name='logout'),  # Use your custom logout view
    
]
