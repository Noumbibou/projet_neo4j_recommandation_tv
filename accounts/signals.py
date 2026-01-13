"""
Signals Django pour synchroniser avec Neo4j
Utilise user_id comme identifiant unique
"""

from django.db.models.signals import post_save, pre_delete
from django.contrib.auth.models import User as DjangoUser
from django.dispatch import receiver
from recommendations.models import User as Neo4jUser
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=DjangoUser)
def sync_user_to_neo4j(sender, instance, created, **kwargs):
    """
    Synchroniser un utilisateur Django avec Neo4j
    user_id = Django User.id
    name = Django User.username
    """
    try:
        user_id = str(instance.id)  # Convertir en string pour Neo4j
        
        if created:
            # Nouvel utilisateur : créer dans Neo4j
            Neo4jUser.create(
                user_id=user_id,
                name=instance.username,
                email=instance.email,
                age=None,  # À remplir via un formulaire étendu si besoin
                gender=None,
                occupation=None,
                join_date=instance.date_joined.isoformat()
            )
            logger.info(f"Utilisateur Neo4j créé : {instance.username} (ID: {user_id})")
        else:
            # Utilisateur existant : mettre à jour
            if Neo4jUser.exists(user_id):
                Neo4jUser.update(
                    user_id=user_id,
                    name=instance.username,
                    email=instance.email
                )
                logger.info(f"Utilisateur Neo4j mis à jour : {instance.username}")
            else:
                # Si absent, créer
                Neo4jUser.create(
                    user_id=user_id,
                    name=instance.username,
                    email=instance.email,
                    join_date=instance.date_joined.isoformat()
                )
                logger.warning(f"Utilisateur Neo4j créé (manquant) : {instance.username}")
    
    except Exception as e:
        logger.error(f"Erreur sync Neo4j pour {instance.username}: {e}")


@receiver(pre_delete, sender=DjangoUser)
def delete_user_from_neo4j(sender, instance, **kwargs):
    """Supprimer un utilisateur de Neo4j"""
    try:
        user_id = str(instance.id)
        deleted = Neo4jUser.delete(user_id)
        
        if deleted:
            logger.info(f"Utilisateur Neo4j supprimé : {instance.username}")
        else:
            logger.warning(f"Utilisateur Neo4j introuvable : {instance.username}")
    
    except Exception as e:
        logger.error(f"Erreur suppression Neo4j pour {instance.username}: {e}")
