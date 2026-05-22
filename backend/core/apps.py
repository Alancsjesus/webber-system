from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        import core.signals
        from core.audit_signals import connect_signals
        connect_signals()
        from core.notification_signals import conectar_signals
        conectar_signals()