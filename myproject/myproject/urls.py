from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from params_app import views as app_views

urlpatterns = [
    path("admin/",    admin.site.urls),
    path("accounts/", include("allauth.urls")),   # Google OAuth endpoints
    path("",          include("params_app.urls")),
] + static(settings.MEDIA_URL, document_root=getattr(settings, 'MEDIA_ROOT', ''))

# Custom error handlers
handler404 = "params_app.views.error_404"
handler500 = "params_app.views.error_500"
