"""
Commande pour vider complètement Neo4j
Usage: python manage.py clear_neo4j --confirm
"""

from django.core.management.base import BaseCommand

from tv_recommender.neo4j_db import neo4j_db


class Command(BaseCommand):
    help = 'Vider complètement la base Neo4j (ATTENTION: supprime toutes les données)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirmer la suppression de toutes les données',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(self.style.WARNING(
                'ATTENTION: Cette commande va supprimer TOUTES les données Neo4j'
            ))
            self.stdout.write('Pour confirmer, utilisez: python manage.py clear_neo4j --confirm')
            return

        try:
            self.stdout.write('Suppression de toutes les données Neo4j...')
            neo4j_db.query("MATCH (n) DETACH DELETE n")
            self.stdout.write(self.style.SUCCESS('✓ Base Neo4j vidée'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Erreur: {e}'))
