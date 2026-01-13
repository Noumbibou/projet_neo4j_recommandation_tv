"""
Commande Django pour initialiser Neo4j avec les contraintes et index
Usage: python manage.py init_neo4j
"""

from django.core.management.base import BaseCommand
from tv_recommender.neo4j_db import neo4j_db


class Command(BaseCommand):
    help = 'Initialiser Neo4j avec les contraintes et index nécessaires'
    
    def handle(self, *args, **options):
        self.stdout.write('Initialisation de Neo4j...')
        
        # Contraintes
        constraints = [
            "CREATE CONSTRAINT user_username_unique IF NOT EXISTS FOR (u:User) REQUIRE u.username IS UNIQUE",
            "CREATE CONSTRAINT user_email_unique IF NOT EXISTS FOR (u:User) REQUIRE u.email IS UNIQUE",
            "CREATE CONSTRAINT series_title_unique IF NOT EXISTS FOR (s:Series) REQUIRE s.title IS UNIQUE",
            "CREATE CONSTRAINT genre_name_unique IF NOT EXISTS FOR (g:Genre) REQUIRE g.name IS UNIQUE",
            "CREATE CONSTRAINT actor_name_unique IF NOT EXISTS FOR (a:Actor) REQUIRE a.name IS UNIQUE",
        ]
        
        # Index
        indexes = [
            "CREATE INDEX series_release_year IF NOT EXISTS FOR (s:Series) ON (s.release_year)",
            "CREATE INDEX rated_date IF NOT EXISTS FOR ()-[r:RATED]-() ON (r.date)",
            "CREATE INDEX rated_score IF NOT EXISTS FOR ()-[r:RATED]-() ON (r.score)",
        ]
        
        try:
            # Créer les contraintes
            self.stdout.write('Création des contraintes...')
            for constraint in constraints:
                neo4j_db.query(constraint)
                self.stdout.write(self.style.SUCCESS(f'✓ {constraint[:50]}...'))
            
            # Créer les index
            self.stdout.write('\nCréation des index...')
            for index in indexes:
                neo4j_db.query(index)
                self.stdout.write(self.style.SUCCESS(f'✓ {index[:50]}...'))
            
            self.stdout.write(self.style.SUCCESS('\n✓ Neo4j initialisé avec succès!'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Erreur: {e}'))