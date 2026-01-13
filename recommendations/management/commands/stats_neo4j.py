"""
Commande pour afficher les statistiques Neo4j
Usage: python manage.py stats_neo4j
"""

from django.core.management.base import BaseCommand

from tv_recommender.neo4j_db import neo4j_db


class Command(BaseCommand):
    help = 'Afficher les statistiques de la base Neo4j'

    def handle(self, *args, **options):
        self.stdout.write('='*60)
        self.stdout.write('STATISTIQUES NEO4J')
        self.stdout.write('='*60)

        try:
            # Nombre de nœuds par type
            stats_query = """
            MATCH (n)
            RETURN labels(n)[0] as type, COUNT(n) as count
            ORDER BY count DESC
            """
            stats = neo4j_db.query(stats_query)

            self.stdout.write('\nNombre de nœuds par type:')
            total_nodes = 0
            for stat in stats:
                self.stdout.write(f"  {stat['type']:15} : {stat['count']:>6}")
                total_nodes += stat['count']
            self.stdout.write(f"  {'TOTAL':15} : {total_nodes:>6}")

            # Nombre de relations par type
            rel_query = """
            MATCH ()-[r]->()
            RETURN type(r) as type, COUNT(r) as count
            ORDER BY count DESC
            """
            relations = neo4j_db.query(rel_query)

            self.stdout.write('\nNombre de relations par type:')
            total_rels = 0
            for rel in relations:
                self.stdout.write(f"  {rel['type']:15} : {rel['count']:>6}")
                total_rels += rel['count']
            self.stdout.write(f"  {'TOTAL':15} : {total_rels:>6}")

            # Séries les plus notées
            top_series_query = """
            MATCH (u:User)-[r:RATED]->(s:Series)
            WITH s, r, coalesce(r['rating'], r['score']) AS rating_value
            WHERE rating_value IS NOT NULL
            RETURN s.title as title,
                   COUNT(r) as ratings_count,
                   AVG(toFloat(rating_value)) as avg_rating
            ORDER BY ratings_count DESC
            LIMIT 10
            """
            top_series = neo4j_db.query(top_series_query)

            if top_series:
                self.stdout.write('\nTop 10 séries les plus notées:')
                for i, serie in enumerate(top_series, 1):
                    self.stdout.write(
                        f"  {i:2}. {serie['title'][:40]:40} - "
                        f"{serie['ratings_count']:3} notes, "
                        f"moy: {serie['avg_rating']:.1f}/5"
                    )

            self.stdout.write('\n' + '='*60)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Erreur: {e}'))
