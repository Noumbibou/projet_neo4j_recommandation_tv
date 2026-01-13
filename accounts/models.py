"""
Modèle étendu pour stocker les informations supplémentaires dans Django
"""

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """
    Profil utilisateur étendu (optionnel)
    Stocke les infos supplémentaires dans Django
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=20, null=True, blank=True)
    occupation = models.CharField(max_length=100, null=True, blank=True)
    bio = models.TextField(blank=True)
    
    def __str__(self):
        return f"Profil de {self.user.username}"


# Signal pour créer le profil automatiquement
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Créer un profil utilisateur automatiquement"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Sauvegarder le profil utilisateur"""
    if hasattr(instance, 'profile'):
        instance.profile.save()