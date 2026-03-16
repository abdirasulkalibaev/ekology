# ekology/apps.py

from django.apps import AppConfig


class MainappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ekology'

    def ready(self):
        import ekology.signals  # signallarni ulash
