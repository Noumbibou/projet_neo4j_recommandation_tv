"""
Commande pour initialiser les contraintes Neo4j adaptées aux nouveaux champs
Usage: python manage.py init_neo4j_constraints
"""

from django.core.management.base import BaseCommand

from tv_recommender.neo4j_db import neo4j_db


class Command(BaseCommand):
    help = 'Initialiser les contraintes et index Neo4j'

    def handle(self, *args, **options):
        self.stdout.write('Initialisation des contraintes Neo4j...')

        # Contraintes d'unicité
        constraints = [
            "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE",
            "CREATE CONSTRAINT series_id_unique IF NOT EXISTS FOR (s:Series) REQUIRE s.series_id IS UNIQUE",
            "CREATE CONSTRAINT actor_id_unique IF NOT EXISTS FOR (a:Actor) REQUIRE a.actor_id IS UNIQUE",
            "CREATE CONSTRAINT genre_name_unique IF NOT EXISTS FOR (g:Genre) REQUIRE g.name IS UNIQUE",
        ]

        # Index pour performances
        indexes = [
            "CREATE INDEX user_name IF NOT EXISTS FOR (u:User) ON (u.name)",
            "CREATE INDEX user_email IF NOT EXISTS FOR (u:User) ON (u.email)",
            "CREATE INDEX series_title IF NOT EXISTS FOR (s:Series) ON (s.title)",
            "CREATE INDEX series_year IF NOT EXISTS FOR (s:Series) ON (s.year)",
            "CREATE INDEX actor_name IF NOT EXISTS FOR (a:Actor) ON (a.name)",
            "CREATE INDEX rating_timestamp IF NOT EXISTS FOR ()-[r:RATED]-() ON (r.timestamp)",
            "CREATE INDEX rating_value IF NOT EXISTS FOR ()-[r:RATED]-() ON (r.rating)",
        ]

        try:
            # Créer les contraintes
            self.stdout.write('\nCréation des contraintes...')
            for constraint in constraints:
                neo4j_db.query(constraint)
                self.stdout.write(self.style.SUCCESS(f'✓ {constraint[:60]}...'))

            # Créer les index
            self.stdout.write('\nCréation des index...')
            for index in indexes:
                neo4j_db.query(index)
                self.stdout.write(self.style.SUCCESS(f'✓ {index[:60]}...'))

            self.stdout.write(self.style.SUCCESS('\n✓ Initialisation terminée!'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Erreur: {e}'))
