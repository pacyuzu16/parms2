from django.urls import path
from params_app import views

urlpatterns = [
    # -- Public --
    path("",          views.home,         name="home"),
    path("contact/",  views.contact_view, name="contact"),
    path("about/",    views.about,        name="about"),

    # -- Auth --
    path("login/",          views.login,          name="login"),
    path("signup/",         views.signup,          name="signup"),
    path("logout/",         views.logout,          name="logout"),
    path("google-welcome/", views.google_welcome,  name="google_welcome"),

    # -- Admin dashboard (SPA) --
    path("dashboard/",        views.dashboard,       name="dashboard"),
    path("update-settings/",  views.update_settings, name="update_settings"),

    # -- Regular user --
    path("userin/",        views.userin,        name="userin"),
    path("profile/",       views.profile,       name="profile"),
    path("notifications/", views.notifications, name="notifications"),
    path("billings/",      views.billings,      name="billings"),
    path("locations/",     views.locations,     name="locations"),
    path("parkings/",      views.parkings,      name="parkings"),
    path("settings/",      views.settings,      name="settings"),
    path("slots/",         views.slots,         name="slots"),
    path("book/",          views.book_space,    name="book_space"),
    path("ticket/",        views.ticket,        name="ticket"),
    path("exit/",          views.exit_parking,  name="exit_parking"),
    path("destination/",   views.destination,   name="destination"),
    path("map/",           views.map_view,      name="map"),

    # -- JSON / REST APIs --
    path("api/dashboard-data/",               views.dashboard_data,            name="dashboard_data"),
    path("api/lookup-plate/",                 views.api_lookup_plate,          name="api_lookup_plate"),
    path("api/recommendations/",              views.api_recommendations,        name="api_recommendations"),
    path("api/predictions/",                  views.api_predictions,            name="api_predictions"),
    path("api/predictions/<int:lot_id>/",     views.api_predictions,            name="api_predictions_lot"),
    path("api/detect-entry/",                 views.api_detect_entry,           name="api_detect_entry"),
    path("api/detect-exit/",                  views.api_detect_exit,            name="api_detect_exit"),
    path("api/notifications/data/",           views.api_user_notifications,     name="api_user_notifications"),
    path("api/notifications/<int:notif_id>/read/", views.api_mark_notification_read, name="api_mark_notification_read"),
    path("api/notifications/mark-all-read/",  views.api_mark_all_read,          name="api_mark_all_read"),
    path("api/lot/<int:lot_id>/",             views.api_lot_detail,             name="api_lot_detail"),
    path("api/map-data/",                     views.api_map_data,               name="api_map_data"),
    path("api/ml-insights/",                  views.api_ml_insights,            name="api_ml_insights"),
    path("api/detect-plate/",                 views.admin_detect_plate,         name="admin_detect_plate"),
    path("api/admin-lookup-plate/",           views.api_admin_lookup_plate,     name="api_admin_lookup_plate"),
    path("api/admin-close-session/",          views.api_admin_close_session,    name="api_admin_close_session"),

    # -- Chatbot --
    path("api/chatbot/message/",              views.chatbot_message,            name="chatbot_message"),
    path("api/chatbot/contact-submit/",       views.chatbot_contact_submit,     name="chatbot_contact_submit"),

    # -- Legacy redirects --
    path("users/",      views.user_list, name="users"),
    path("user-list/",  views.user_list, name="user_list"),

    # -- Utilities --
    path("generate-qr/",       views.generate_qr_code, name="generate_qr_code"),
    path("generate-ticket/",   views.generate_ticket,  name="generate_ticket"),

    # -- Admin CRUD --
    path("manage/contacts/",                          views.admin_contacts,           name="admin_contacts"),
    path("manage/contacts/<int:message_id>/",         views.admin_contact_detail,     name="admin_contact_detail"),
    path("manage/vehicles/",                          views.admin_vehicles,           name="admin_vehicles"),
    path("manage/vehicles/create/",                   views.admin_vehicle_create,     name="admin_vehicle_create"),
    path("manage/vehicles/<int:vehicle_id>/edit/",    views.admin_vehicle_edit,       name="admin_vehicle_edit"),
    path("manage/parking-lots/",                      views.admin_parking_lots,       name="admin_parking_lots"),
    path("manage/parking-lots/create/",               views.admin_parking_lot_create, name="admin_parking_lot_create"),
    path("manage/parking-lots/<int:lot_id>/edit/",    views.admin_parking_lot_edit,   name="admin_parking_lot_edit"),
    path("manage/tickets/",                           views.admin_tickets,            name="admin_tickets"),
    path("manage/tickets/<int:ticket_id>/edit/",      views.admin_ticket_edit,        name="admin_ticket_edit"),
    path("manage/users/",                             views.admin_users_management,   name="admin_users_management"),
    path("manage/users/<int:user_id>/edit/",          views.admin_user_edit,          name="admin_user_edit"),
    path("manage/reports/",                           views.admin_reports,            name="admin_reports"),
    path("manage/export/<str:report_type>/",          views.admin_export_csv,         name="admin_export_csv"),
]
