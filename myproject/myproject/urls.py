from django.contrib import admin
from django.urls import path, include
from params_app import views as app_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("params_app.urls")),
]

# Custom error handlers
handler404 = "params_app.views.error_404"
handler500 = "params_app.views.error_500"
