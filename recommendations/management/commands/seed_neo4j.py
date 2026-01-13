"""
Commande Django pour peupler Neo4j avec des données de test
Usage: python manage.py seed_neo4j
"""

from django.core.management.base import BaseCommand
from recommendations.models import Genre, Actor, Series


class Command(BaseCommand):
    help = 'Peupler Neo4j avec des données de test'
    
    def handle(self, *args, **options):
        self.stdout.write('Peuplement de Neo4j avec des données de test...\n')
        
        # Genres
        self.stdout.write('Création des genres...')
        genres = ['Drama', 'Comedy', 'Sci-Fi', 'Thriller', 'Crime', 'Fantasy', 'Horror', 'Action']
        for genre_name in genres:
            Genre.get_or_create(genre_name)
            self.stdout.write(self.style.SUCCESS(f'✓ Genre: {genre_name}'))
        
        # Acteurs
        self.stdout.write('\nCréation des acteurs...')
        actors = [
            'Bryan Cranston', 'Aaron Paul', 'Emilia Clarke', 'Kit Harington',
            'Pedro Pascal', 'Bella Ramsey', 'Millie Bobby Brown', 'Winona Ryder'
        ]
        for actor_name in actors:
            Actor.get_or_create(actor_name)
            self.stdout.write(self.style.SUCCESS(f'✓ Acteur: {actor_name}'))
        
        # Séries
        self.stdout.write('\nCréation des séries...')
        series_data = [
            {
                'title': 'Breaking Bad',
                'description': 'Un professeur de chimie atteint d\'un cancer se lance dans la production de méthamphétamine',
                'release_year': 2008,
                'genres': ['Drama', 'Crime', 'Thriller'],
                'actors': ['Bryan Cranston', 'Aaron Paul']
            },
            {
                'title': 'Game of Thrones',
                'description': 'Neuf familles nobles se disputent le contrôle des terres de Westeros',
                'release_year': 2011,
                'genres': ['Drama', 'Fantasy', 'Action'],
                'actors': ['Emilia Clarke', 'Kit Harington']
            },
            {
                'title': 'The Last of Us',
                'description': 'Un contrebandier et une jeune fille traversent une Amérique post-apocalyptique',
                'release_year': 2023,
                'genres': ['Drama', 'Sci-Fi', 'Horror'],
                'actors': ['Pedro Pascal', 'Bella Ramsey']
            },
            {
                'title': 'Stranger Things',
                'description': 'Dans les années 80, des événements étranges se produisent dans une petite ville américaine',
                'release_year': 2016,
                'genres': ['Sci-Fi', 'Horror', 'Drama'],
                'actors': ['Millie Bobby Brown', 'Winona Ryder']
            }
        ]
        
        for serie_data in series_data:
            # Créer la série
            serie = Series.create(
                serie_data['title'],
                serie_data['description'],
                serie_data['release_year']
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Série: {serie_data["title"]}'))
            
            # Ajouter les genres
            for genre in serie_data['genres']:
                Series.add_genre(serie_data['title'], genre)
            
            # Ajouter les acteurs
            for actor in serie_data['actors']:
                Series.add_actor(serie_data['title'], actor)
        
        self.stdout.write(self.style.SUCCESS('\n✓ Données de test créées avec succès!'))