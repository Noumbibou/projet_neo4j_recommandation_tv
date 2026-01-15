# recommendations/management/commands/import_csv_data.py
"""
Commande Django pour importer les données CSV vers Neo4j
Usage: python manage.py import_csv_data --actors actors.csv --series series.csv ...
"""

from django.core.management.base import BaseCommand
from recommendations.models import User, Series, Genre, Actor, Rating
from tv_recommender.neo4j_db import neo4j_db
import csv
import os


class Command(BaseCommand):
    help = 'Importer les données CSV vers Neo4j'
    
    def add_arguments(self, parser):
        parser.add_argument('--actors', type=str, help='Chemin vers actors.csv')
        parser.add_argument('--series', type=str, help='Chemin vers series.csv')
        parser.add_argument('--genres', type=str, help='Chemin vers genres.csv')
        parser.add_argument('--series-genres', type=str, help='Chemin vers series_genres.csv')
        parser.add_argument('--series-actors', type=str, help='Chemin vers series_actors.csv')
        parser.add_argument('--users', type=str, help='Chemin vers users.csv')
        parser.add_argument('--ratings', type=str, help='Chemin vers ratings.csv')
        parser.add_argument('--limit', type=int, default=None, help='Limiter le nombre de lignes importées')
    
    def handle(self, *args, **options):
        self.stdout.write('='*60)
        self.stdout.write('IMPORT DES DONNÉES CSV VERS NEO4J')
        self.stdout.write('='*60)
        
        # Import des genres
        if options['genres']:
            self.import_genres(options['genres'])
        
        # Import des acteurs
        if options['actors']:
            self.import_actors(options['actors'], options['limit'])
        
        # Import des séries
        if options['series']:
            self.import_series(options['series'], options['limit'])
        
        # Import des relations series-genres
        if options['series_genres']:
            self.import_series_genres(options['series_genres'])
        
        # Import des relations series-acteurs
        if options['series_actors']:
            self.import_series_actors(options['series_actors'])
        
        # Import des utilisateurs
        if options['users']:
            self.import_users(options['users'], options['limit'])

        # Import des notations (relations RATED)
        if options['ratings']:
            self.import_ratings(options['ratings'], options['limit'])
        
        self.stdout.write(self.style.SUCCESS('\n✓ Import terminé!'))
    
    def import_genres(self, filepath):
        """Importer les genres depuis genres.csv"""
        self.stdout.write(f'\n--- Import des genres depuis {filepath} ---')
        
        if not os.path.exists(filepath):
            self.stdout.write(self.style.ERROR(f'✗ Fichier introuvable: {filepath}'))
            return
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                count = 0
                
                for row in reader:
                    genre_id = row.get('genre_id')
                    name = row.get('name')
                    
                    if genre_id and name:
                        Genre.create(genre_id, name)
                        count += 1
                        if count % 10 == 0:
                            self.stdout.write(f'  {count} genres importés...')
            
            self.stdout.write(self.style.SUCCESS(f'✓ {count} genres importés'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Erreur: {e}'))
    
    def import_actors(self, filepath, limit=None):
        """Importer les acteurs depuis actors.csv"""
        self.stdout.write(f'\n--- Import des acteurs depuis {filepath} ---')
        
        if not os.path.exists(filepath):
            self.stdout.write(self.style.ERROR(f'✗ Fichier introuvable: {filepath}'))
            return
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                count = 0
                
                for row in reader:
                    if limit and count >= limit:
                        break
                    
                    actor_id = row.get('actor_id')
                    name = row.get('name')
                    birth_year = row.get('birth_year')
                    death_year = row.get('death_year')
                    professions = row.get('professions')
                    known_for_titles = row.get('known_for_titles')
                    
                    if actor_id and name:
                        try:
                            Actor.create(
                                actor_id=actor_id,
                                name=name,
                                birth_year=int(birth_year) if birth_year and birth_year != '\\N' else None,
                                death_year=int(death_year) if death_year and death_year != '\\N' else None,
                                professions=professions,
                                known_for_titles=known_for_titles
                            )
                            count += 1
                            if count % 100 == 0:
                                self.stdout.write(f'  {count} acteurs importés...')
                        except Exception as actor_error:
                            # Si l'acteur existe déjà, continuer
                            if "already exists" in str(actor_error):
                                self.stdout.write(f'  Acteur "{name}" (ID: {actor_id}) déjà existent, skip...')
                                continue
                            else:
                                raise actor_error
            
            self.stdout.write(self.style.SUCCESS(f'✓ {count} acteurs importés'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Erreur: {e}'))
    
    def import_series(self, filepath, limit=None):
        """Importer les séries depuis series.csv"""
        self.stdout.write(f'\n--- Import des séries depuis {filepath} ---')
        
        if not os.path.exists(filepath):
            self.stdout.write(self.style.ERROR(f'✗ Fichier introuvable: {filepath}'))
            return
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                count = 0
                
                for row in reader:
                    if limit and count >= limit:
                        break
                    
                    series_id = row.get('series_id')
                    title = row.get('title')
                    original_title = row.get('original_title')
                    year = row.get('year')
                    is_adult = row.get('is_adult', '0')
                    
                    if series_id and title:
                        try:
                            Series.create(
                                series_id=series_id,
                                title=title,
                                original_title=original_title or title,
                                year=int(year) if year and year != '\\N' else None,
                                is_adult=(is_adult == '1')
                            )
                            count += 1
                            if count % 100 == 0:
                                self.stdout.write(f'  {count} séries importées...')
                        except Exception as series_error:
                            # Si la série existe déjà, continuer
                            if "already exists" in str(series_error):
                                self.stdout.write(f'  Série "{title}" (ID: {series_id}) déjà existente, skip...')
                                continue
                            else:
                                raise series_error
            
            self.stdout.write(self.style.SUCCESS(f'✓ {count} séries importées'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Erreur: {e}'))
    
    def import_series_genres(self, filepath):
        """Importer les relations series-genres depuis series_genres.csv"""
        self.stdout.write(f'\n--- Import des relations series-genres depuis {filepath} ---')
        
        if not os.path.exists(filepath):
            self.stdout.write(self.style.ERROR(f'✗ Fichier introuvable: {filepath}'))
            return
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                count = 0
                
                for row in reader:
                    series_id = row.get('series_id')
                    genre_name = row.get('genre_name')
                    
                    if series_id and genre_name:
                        Genre.link_to_series(series_id, genre_name)
                        count += 1
                        if count % 100 == 0:
                            self.stdout.write(f'  {count} relations créées...')
            
            self.stdout.write(self.style.SUCCESS(f'✓ {count} relations series-genres créées'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Erreur: {e}'))
    
    def import_series_actors(self, filepath):
        """Importer les relations series-acteurs depuis series_actors.csv"""
        self.stdout.write(f'\n--- Import des relations series-acteurs depuis {filepath} ---')
        
        if not os.path.exists(filepath):
            self.stdout.write(self.style.ERROR(f'✗ Fichier introuvable: {filepath}'))
            return
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                count = 0
                
                for row in reader:
                    series_id = row.get('series_id')
                    actor_id = row.get('actor_id')
                    
                    if series_id and actor_id:
                        Actor.link_to_series(series_id, actor_id)
                        count += 1
                        if count % 100 == 0:
                            self.stdout.write(f'  {count} relations créées...')
            
            self.stdout.write(self.style.SUCCESS(f'✓ {count} relations series-acteurs créées'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Erreur: {e}'))
    
    def import_users(self, filepath, limit=None):
        """Importer les utilisateurs depuis users.csv"""
        self.stdout.write(f'\n--- Import des utilisateurs depuis {filepath} ---')
        
        if not os.path.exists(filepath):
            self.stdout.write(self.style.ERROR(f'✗ Fichier introuvable: {filepath}'))
            return
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                count = 0
                
                for row in reader:
                    if limit and count >= limit:
                        break
                    
                    user_id = row.get('user_id')
                    name = row.get('name')
                    email = row.get('email')
                    age = row.get('age')
                    gender = row.get('gender')
                    occupation = row.get('occupation')
                    join_date = row.get('join_date')
                    
                    if user_id and name and email:
                        User.create(
                            user_id=user_id,
                            name=name,
                            email=email,
                            age=int(age) if age and age != '\\N' else None,
                            gender=gender,
                            occupation=occupation,
                            join_date=join_date
                        )
                        count += 1
                        if count % 100 == 0:
                            self.stdout.write(f'  {count} utilisateurs importés...')
            
            self.stdout.write(self.style.SUCCESS(f'✓ {count} utilisateurs importés'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Erreur: {e}'))

    def import_ratings(self, filepath, limit=None):
        """Importer les notations depuis ratings.csv (création de relations RATED)"""
        self.stdout.write(f'\n--- Import des notations depuis {filepath} ---')

        if not os.path.exists(filepath):
            self.stdout.write(self.style.ERROR(f'✗ Fichier introuvable: {filepath}'))
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                count = 0

                for row in reader:
                    if limit and count >= limit:
                        break

                    user_id = row.get('user_id')
                    series_id = row.get('series_id')
                    rating = row.get('rating')
                    date = row.get('date')
                    timestamp = row.get('timestamp')

                    if not (user_id and series_id and rating):
                        continue

                    try:
                        rating_value = float(rating)
                    except (TypeError, ValueError):
                        continue

                    timestamp_value = None
                    if timestamp not in (None, '', '\\N'):
                        try:
                            timestamp_value = int(timestamp)
                        except (TypeError, ValueError):
                            timestamp_value = None

                    Rating.create(
                        user_id=user_id,
                        series_id=series_id,
                        rating=rating_value,
                        date=date if date not in (None, '', '\\N') else None,
                        timestamp=timestamp_value,
                    )

                    count += 1
                    if count % 500 == 0:
                        self.stdout.write(f'  {count} notations importées...')

            self.stdout.write(self.style.SUCCESS(f'✓ {count} notations importées'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Erreur: {e}'))