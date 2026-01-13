"""
Configuration de l'app accounts pour charger les signals
"""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    
    def ready(self):
        """Importer les signals au démarrage de l'application"""
        import accounts.signals
