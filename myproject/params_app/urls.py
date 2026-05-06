from django.urls import path
from params_app import views

urlpatterns = [
    # ── Public ──────────────────────────────────────────────────────────────────
    path('',          views.home,         name='home'),
    path('contact/',  views.contact_view, name='contact'),
    path('about/',    views.about,        name='about'),

    # ── Auth ────────────────────────────────────────────────────────────────────
    path('login/',    views.login,   name='login'),
    path('signup/',   views.signup,  name='signup'),
    path('logout/',   views.logout,  name='logout'),

    # ── Admin dashboard (SPA) ───────────────────────────────────────────────────
    path('dashboard/',         views.dashboard,         name='dashboard'),
    path('update-settings/',   views.update_settings,   name='update_settings'),

    # ── Regular user ────────────────────────────────────────────────────────────
    path('userin/',      views.userin,      name='userin'),
    path('billings/',    views.billings,    name='billings'),
    path('locations/',   views.locations,   name='locations'),
    path('parkings/',    views.parkings,    name='parkings'),
    path('settings/',    views.settings,    name='settings'),
    path('slots/',       views.slots,       name='slots'),
    path('ticket/',      views.ticket,      name='ticket'),
    path('destination/', views.destination, name='destination'),

    # ── Legacy redirects (kept for backwards compat) ────────────────────────────
    path('users/',      views.user_list, name='users'),
    path('user-list/',  views.user_list, name='user_list'),

    # ── Utilities ───────────────────────────────────────────────────────────────
    path('generate-qr/',      views.generate_qr_code, name='generate_qr_code'),
    path('generate-ticket/',  views.generate_ticket,  name='generate_ticket'),
    path('api/dashboard-data/', views.dashboard_data, name='dashboard_data'),

    # ── Admin CRUD (all redirect back to dashboard?tab=X) ───────────────────────
    path('manage/contacts/',                          views.admin_contacts,           name='admin_contacts'),
    path('manage/contacts/<int:message_id>/',         views.admin_contact_detail,     name='admin_contact_detail'),
    path('manage/vehicles/',                          views.admin_vehicles,            name='admin_vehicles'),
    path('manage/vehicles/create/',                   views.admin_vehicle_create,      name='admin_vehicle_create'),
    path('manage/vehicles/<int:vehicle_id>/edit/',    views.admin_vehicle_edit,        name='admin_vehicle_edit'),
    path('manage/parking-lots/',                      views.admin_parking_lots,        name='admin_parking_lots'),
    path('manage/parking-lots/create/',               views.admin_parking_lot_create,  name='admin_parking_lot_create'),
    path('manage/parking-lots/<int:lot_id>/edit/',    views.admin_parking_lot_edit,    name='admin_parking_lot_edit'),
    path('manage/tickets/',                           views.admin_tickets,             name='admin_tickets'),
    path('manage/tickets/<int:ticket_id>/edit/',      views.admin_ticket_edit,         name='admin_ticket_edit'),
    path('manage/users/',                             views.admin_users_management,    name='admin_users_management'),
    path('manage/users/<int:user_id>/edit/',          views.admin_user_edit,           name='admin_user_edit'),
    path('manage/reports/',                           views.admin_reports,             name='admin_reports'),
]
