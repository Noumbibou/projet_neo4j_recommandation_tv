"""
Synchroniser tous les utilisateurs Django vers Neo4j
Usage: python manage.py sync_django_to_neo4j
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User as DjangoUser
from recommendations.models import User as Neo4jUser


class Command(BaseCommand):
    help = 'Synchroniser tous les utilisateurs Django vers Neo4j'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forcer la mise à jour même si l\'utilisateur existe',
        )
    
    def handle(self, *args, **options):
        force = options['force']
        users = DjangoUser.objects.all()
        total = users.count()
        
        self.stdout.write(f'Synchronisation de {total} utilisateur(s)...\n')
        
        created = 0
        updated = 0
        errors = 0
        
        for user in users:
            try:
                user_id = str(user.id)
                exists = Neo4jUser.exists(user_id)
                
                if exists and not force:
                    self.stdout.write(f'⊙ {user.username} existe déjà (skip)')
                elif exists and force:
                    Neo4jUser.update(
                        user_id=user_id,
                        name=user.username,
                        email=user.email
                    )
                    updated += 1
                    self.stdout.write(self.style.WARNING(f'↻ {user.username} mis à jour'))
                else:
                    Neo4jUser.create(
                        user_id=user_id,
                        name=user.username,
                        email=user.email,
                        join_date=user.date_joined.isoformat()
                    )
                    created += 1
                    self.stdout.write(self.style.SUCCESS(f'✓ {user.username} créé'))
            
            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(f'✗ {user.username}: {e}'))
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS(f'Créés: {created}'))
        self.stdout.write(self.style.WARNING(f'Mis à jour: {updated}'))
        self.stdout.write(self.style.ERROR(f'Erreurs: {errors}'))
        self.stdout.write('='*50)
