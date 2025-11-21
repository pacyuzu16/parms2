from django.apps import AppConfig


class ParamsAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "params_app"
def ready(self):
    import params_app.signals
