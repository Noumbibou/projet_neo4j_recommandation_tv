# recommendations/models.py (Version adaptée pour vos datasets)
"""
Models Neo4j adaptés pour vos datasets CSV existants
"""

from datetime import datetime
from tv_recommender.neo4j_db import neo4j_db


class Neo4jBaseModel:
    """Classe de base pour tous les models Neo4j"""
    
    @staticmethod
    def _format_result(record):
        """Formater un résultat Neo4j en dictionnaire Python"""
        if not record:
            return None
        return dict(record)


class User(Neo4jBaseModel):
    """
    Model User pour Neo4j
    Correspondance: user_id, name, age, gender, occupation, join_date, email
    """
    
    @staticmethod
    def create(user_id, name, email, age=None, gender=None, occupation=None, join_date=None):
        """Créer un utilisateur dans Neo4j"""
        query = """
        CREATE (u:User {
            user_id: $user_id,
            name: $name,
            email: $email,
            age: $age,
            gender: $gender,
            occupation: $occupation,
            join_date: $join_date
        })
        RETURN u.user_id as user_id, u.name as name, u.email as email
        """
        result = neo4j_db.query(query, {
            'user_id': user_id,
            'name': name,
            'email': email,
            'age': age,
            'gender': gender,
            'occupation': occupation,
            'join_date': join_date or datetime.now().isoformat()
        })
        return result[0] if result else None
    
    @staticmethod
    def get(user_id):
        """Récupérer un utilisateur par user_id"""
        query = """
        MATCH (u:User {user_id: $user_id})
        RETURN u.user_id as user_id, u.name as name, u.email as email,
               u.age as age, u.gender as gender, u.occupation as occupation,
               u.join_date as join_date
        """
        result = neo4j_db.query(query, {'user_id': user_id})
        return result[0] if result else None
    
    @staticmethod
    def get_by_name(name):
        """Récupérer un utilisateur par name (pour compatibilité Django)"""
        query = """
        MATCH (u:User {name: $name})
        RETURN u.user_id as user_id, u.name as name, u.email as email,
               u.age as age, u.gender as gender, u.occupation as occupation
        """
        result = neo4j_db.query(query, {'name': name})
        return result[0] if result else None
    
    @staticmethod
    def update(user_id, **kwargs):
        """Mettre à jour un utilisateur"""
        set_clauses = []
        params = {'user_id': user_id}
        
        for key, value in kwargs.items():
            if value is not None and key in ['name', 'email', 'age', 'gender', 'occupation']:
                set_clauses.append(f'u.{key} = ${key}')
                params[key] = value
        
        if not set_clauses:
            return None
        
        query = f"""
        MATCH (u:User {{user_id: $user_id}})
        SET {', '.join(set_clauses)}
        RETURN u.user_id as user_id, u.name as name, u.email as email
        """
        result = neo4j_db.query(query, params)
        return result[0] if result else None
    
    @staticmethod
    def delete(user_id):
        """Supprimer un utilisateur et toutes ses relations"""
        query = """
        MATCH (u:User {user_id: $user_id})
        DETACH DELETE u
        RETURN COUNT(u) as deleted
        """
        result = neo4j_db.query(query, {'user_id': user_id})
        return result[0]['deleted'] > 0 if result else False
    
    @staticmethod
    def exists(user_id):
        """Vérifier si un utilisateur existe"""
        query = """
        MATCH (u:User {user_id: $user_id})
        RETURN COUNT(u) > 0 as exists
        """
        result = neo4j_db.query(query, {'user_id': user_id})
        return result[0]['exists'] if result else False


class Series(Neo4jBaseModel):
    """
    Model Series pour Neo4j
    Correspondance: series_id, title, original_title, year, is_adult
    """
    
    @staticmethod
    def create(series_id, title, original_title, year, is_adult=False):
        """Créer une série"""
        query = """
        CREATE (s:Series {
            series_id: $series_id,
            title: $title,
            original_title: $original_title,
            year: $year,
            is_adult: $is_adult
        })
        RETURN s.series_id as series_id, s.title as title, 
               s.original_title as original_title, s.year as year
        """
        result = neo4j_db.query(query, {
            'series_id': series_id,
            'title': title,
            'original_title': original_title,
            'year': year,
            'is_adult': is_adult
        })
        return result[0] if result else None
    
    @staticmethod
    def get(series_id):
        """Récupérer une série par series_id"""
        query = """
        MATCH (s:Series {series_id: $series_id})
        OPTIONAL MATCH (s)-[:HAS_GENRE]->(g:Genre)
        OPTIONAL MATCH (s)-[:HAS_ACTOR]->(a:Actor)
        RETURN s.series_id as series_id,
               s.title as title,
               s.original_title as original_title,
               s.year as year,
               s.is_adult as is_adult,
               COLLECT(DISTINCT g.name) as genres,
               COLLECT(DISTINCT {
                   actor_id: a.actor_id,
                   name: a.name
               }) as actors
        """
        result = neo4j_db.query(query, {'series_id': series_id})
        return result[0] if result else None
    
    @staticmethod
    def get_by_title(title):
        """Récupérer une série par titre"""
        query = """
        MATCH (s:Series)
        WHERE s.title = $title OR s.original_title = $title
        OPTIONAL MATCH (s)-[:HAS_GENRE]->(g:Genre)
        OPTIONAL MATCH (s)-[:HAS_ACTOR]->(a:Actor)
        RETURN s.series_id as series_id,
               s.title as title,
               s.original_title as original_title,
               s.year as year,
               COLLECT(DISTINCT g.name) as genres,
               COLLECT(DISTINCT {
                   actor_id: a.actor_id,
                   name: a.name
               }) as actors
        """
        result = neo4j_db.query(query, {'title': title})
        return result[0] if result else None
    
    @staticmethod
    def get_all(limit=None):
        """Récupérer toutes les séries"""
        query = """
        MATCH (s:Series)
        WHERE s.is_adult = false
        OPTIONAL MATCH (s)-[:HAS_GENRE]->(g:Genre)
        RETURN s.series_id as series_id,
               s.title as title,
               s.original_title as original_title,
               s.year as year,
               COLLECT(DISTINCT g.name) as genres
        ORDER BY s.title
        """
        if limit:
            query += f" LIMIT {limit}"
        return neo4j_db.query(query)
    
    @staticmethod
    def search(keyword, limit=20):
        """Rechercher des séries par mot-clé"""
        query = """
        MATCH (s:Series)
        WHERE toLower(s.title) CONTAINS toLower($keyword) 
           OR toLower(s.original_title) CONTAINS toLower($keyword)
        AND s.is_adult = false
        OPTIONAL MATCH (s)-[:HAS_GENRE]->(g:Genre)
        RETURN s.series_id as series_id,
               s.title as title,
               s.original_title as original_title,
               s.year as year,
               COLLECT(DISTINCT g.name) as genres
        ORDER BY s.title
        LIMIT $limit
        """
        return neo4j_db.query(query, {'keyword': keyword, 'limit': limit})
    
    @staticmethod
    def update(series_id, **kwargs):
        """Mettre à jour une série"""
        set_clauses = []
        params = {'series_id': series_id}
        
        for key, value in kwargs.items():
            if value is not None and key in ['title', 'original_title', 'year', 'is_adult']:
                set_clauses.append(f's.{key} = ${key}')
                params[key] = value
        
        if not set_clauses:
            return None
        
        query = f"""
        MATCH (s:Series {{series_id: $series_id}})
        SET {', '.join(set_clauses)}
        RETURN s.series_id as series_id, s.title as title
        """
        result = neo4j_db.query(query, params)
        return result[0] if result else None
    
    @staticmethod
    def delete(series_id):
        """Supprimer une série"""
        query = """
        MATCH (s:Series {series_id: $series_id})
        DETACH DELETE s
        RETURN COUNT(s) as deleted
        """
        result = neo4j_db.query(query, {'series_id': series_id})
        return result[0]['deleted'] > 0 if result else False


class Genre(Neo4jBaseModel):
    """
    Model Genre pour Neo4j
    Correspondance: genre_id, name
    """
    
    @staticmethod
    def create(genre_id, name):
        """Créer un genre"""
        query = """
        CREATE (g:Genre {
            genre_id: $genre_id,
            name: $name
        })
        RETURN g.genre_id as genre_id, g.name as name
        """
        result = neo4j_db.query(query, {
            'genre_id': genre_id,
            'name': name
        })
        return result[0] if result else None
    
    @staticmethod
    def get_or_create(name):
        """Récupérer ou créer un genre (par nom uniquement)"""
        query = """
        MERGE (g:Genre {name: $name})
        RETURN g.name as name
        """
        result = neo4j_db.query(query, {'name': name})
        return result[0] if result else None
    
    @staticmethod
    def get_all():
        """Récupérer tous les genres"""
        query = """
        MATCH (g:Genre)
        RETURN g.genre_id as genre_id, g.name as name
        ORDER BY g.name
        """
        return neo4j_db.query(query)
    
    @staticmethod
    def link_to_series(series_id, genre_name):
        """Lier un genre à une série"""
        query = """
        MATCH (s:Series {series_id: $series_id})
        MERGE (g:Genre {name: $genre_name})
        MERGE (s)-[:HAS_GENRE]->(g)
        RETURN s.series_id as series_id, g.name as genre_name
        """
        result = neo4j_db.query(query, {
            'series_id': series_id,
            'genre_name': genre_name
        })
        return result[0] if result else None


class Actor(Neo4jBaseModel):
    """
    Model Actor pour Neo4j
    Correspondance: actor_id, name, birth_year, death_year, professions, known_for_titles
    """
    
    @staticmethod
    def create(actor_id, name, birth_year=None, death_year=None, professions=None, known_for_titles=None):
        """Créer un acteur"""
        query = """
        CREATE (a:Actor {
            actor_id: $actor_id,
            name: $name,
            birth_year: $birth_year,
            death_year: $death_year,
            professions: $professions,
            known_for_titles: $known_for_titles
        })
        RETURN a.actor_id as actor_id, a.name as name
        """
        result = neo4j_db.query(query, {
            'actor_id': actor_id,
            'name': name,
            'birth_year': birth_year,
            'death_year': death_year,
            'professions': professions,
            'known_for_titles': known_for_titles
        })
        return result[0] if result else None
    
    @staticmethod
    def get(actor_id):
        """Récupérer un acteur"""
        query = """
        MATCH (a:Actor {actor_id: $actor_id})
        RETURN a.actor_id as actor_id,
               a.name as name,
               a.birth_year as birth_year,
               a.death_year as death_year,
               a.professions as professions,
               a.known_for_titles as known_for_titles
        """
        result = neo4j_db.query(query, {'actor_id': actor_id})
        return result[0] if result else None
    
    @staticmethod
    def get_all(limit=100):
        """Récupérer tous les acteurs"""
        query = """
        MATCH (a:Actor)
        RETURN a.actor_id as actor_id, a.name as name
        ORDER BY a.name
        LIMIT $limit
        """
        return neo4j_db.query(query, {'limit': limit})
    
    @staticmethod
    def link_to_series(series_id, actor_id):
        """Lier un acteur à une série"""
        query = """
        MATCH (s:Series {series_id: $series_id})
        MATCH (a:Actor {actor_id: $actor_id})
        MERGE (s)-[:HAS_ACTOR]->(a)
        RETURN s.series_id as series_id, a.actor_id as actor_id
        """
        result = neo4j_db.query(query, {
            'series_id': series_id,
            'actor_id': actor_id
        })
        return result[0] if result else None
    
    @staticmethod
    def get_series(actor_id):
        """Récupérer toutes les séries d'un acteur"""
        query = """
        MATCH (a:Actor {actor_id: $actor_id})<-[:HAS_ACTOR]-(s:Series)
        WHERE s.is_adult = false
        RETURN s.series_id as series_id,
               s.title as title,
               s.year as year
        ORDER BY s.year DESC
        """
        return neo4j_db.query(query, {'actor_id': actor_id})


class Rating(Neo4jBaseModel):
    """
    Model pour gérer les notations (relation RATED)
    Correspondance: user_id, series_id, series_title, rating, date, timestamp
    """
    
    @staticmethod
    def create(user_id, series_id, rating, date=None, timestamp=None):
        """Créer ou mettre à jour une notation"""
        if date is None:
            date = datetime.now().isoformat()
        if timestamp is None:
            timestamp = int(datetime.now().timestamp())
        
        query = """
        MATCH (u:User {user_id: $user_id})
        MATCH (s:Series {series_id: $series_id})
        MERGE (u)-[r:RATED]->(s)
        SET r.rating = $rating,
            r.series_title = s.title,
            r.date = datetime($date),
            r.timestamp = $timestamp
        RETURN u.user_id as user_id,
               s.series_id as series_id,
               s.title as series_title,
               r.rating as rating,
               r.date as date,
               r.timestamp as timestamp
        """
        result = neo4j_db.query(query, {
            'user_id': user_id,
            'series_id': series_id,
            'rating': rating,
            'date': date,
            'timestamp': timestamp
        })
        return result[0] if result else None
    
    @staticmethod
    def get(user_id, series_id):
        """Récupérer la notation d'un utilisateur pour une série"""
        query = """
        MATCH (u:User {user_id: $user_id})-[r:RATED]->(s:Series {series_id: $series_id})
        RETURN u.user_id as user_id,
               s.series_id as series_id,
               s.title as series_title,
               r.rating as rating,
               r.date as date,
               r.timestamp as timestamp
        """
        result = neo4j_db.query(query, {
            'user_id': user_id,
            'series_id': series_id
        })
        return result[0] if result else None
    
    @staticmethod
    def get_user_ratings(user_id):
        """Récupérer toutes les notations d'un utilisateur"""
        query = """
        MATCH (u:User {user_id: $user_id})-[r:RATED]->(s:Series)
        OPTIONAL MATCH (s)-[:HAS_GENRE]->(g:Genre)
        RETURN s.series_id as series_id,
               s.title as series_title,
               s.year as year,
               r.rating as rating,
               r.date as date,
               r.timestamp as timestamp,
               COLLECT(DISTINCT g.name) as genres
        ORDER BY r.timestamp DESC
        """
        return neo4j_db.query(query, {'user_id': user_id})
    
    @staticmethod
    def get_series_ratings(series_id):
        """Récupérer toutes les notations d'une série"""
        query = """
        MATCH (u:User)-[r:RATED]->(s:Series {series_id: $series_id})
        RETURN u.user_id as user_id,
               u.name as username,
               r.rating as rating,
               r.date as date,
               r.timestamp as timestamp
        ORDER BY r.timestamp DESC
        """
        return neo4j_db.query(query, {'series_id': series_id})
    
    @staticmethod
    def get_average_rating(series_id):
        """Récupérer la note moyenne d'une série"""
        query = """
        MATCH (u:User)-[r:RATED]->(s:Series {series_id: $series_id})
        RETURN s.series_id as series_id,
               s.title as series_title,
               AVG(r.rating) as average_rating,
               COUNT(r) as total_ratings
        """
        result = neo4j_db.query(query, {'series_id': series_id})
        return result[0] if result else None
    
    @staticmethod
    def delete(user_id, series_id):
        """Supprimer une notation"""
        query = """
        MATCH (u:User {user_id: $user_id})-[r:RATED]->(s:Series {series_id: $series_id})
        DELETE r
        RETURN COUNT(r) as deleted
        """
        result = neo4j_db.query(query, {
            'user_id': user_id,
            'series_id': series_id
        })
        return result[0]['deleted'] > 0 if result else False
    
    @staticmethod
    def get_user_statistics(user_id):
        """Statistiques de visionnage d'un utilisateur"""
        query = """
        MATCH (u:User {user_id: $user_id})-[r:RATED]->(s:Series)-[:HAS_GENRE]->(g:Genre)
        WITH u, COUNT(DISTINCT s) as series_count, 
             AVG(r.rating) as avg_rating,
             COLLECT(DISTINCT g.name) as all_genres
        RETURN u.user_id as user_id,
               u.name as username,
               series_count,
               ROUND(avg_rating * 10) / 10.0 as avg_rating,
               all_genres as genres
        """
        result = neo4j_db.query(query, {'user_id': user_id})
        return result[0] if result else None


class Recommendation(Neo4jBaseModel):
    """Model pour générer des recommandations"""
    
    @staticmethod
    def by_genre(user_id, limit=10):
        """Recommandations basées sur les genres préférés"""
        query = """
        MATCH (u:User {user_id: $user_id})-[r:RATED]->(s:Series)-[:HAS_GENRE]->(g:Genre)
        WHERE r.rating >= 4
        WITH u, g, COUNT(*) as genre_weight
        ORDER BY genre_weight DESC
        MATCH (rec:Series)-[:HAS_GENRE]->(g)
        WHERE NOT (u)-[:RATED]->(rec) AND rec.is_adult = false
        WITH rec, COLLECT(DISTINCT g.name) as genres, SUM(genre_weight) as relevance
        RETURN rec.series_id as series_id,
               rec.title as title,
               rec.original_title as original_title,
               rec.year as year,
               genres,
               relevance as score
        ORDER BY relevance DESC
        LIMIT $limit
        """
        return neo4j_db.query(query, {'user_id': user_id, 'limit': limit})
    
    @staticmethod
    def collaborative(user_id, limit=10):
        """Recommandations par filtrage collaboratif"""
        query = """
        MATCH (u:User {user_id: $user_id})-[r1:RATED]->(s:Series)<-[r2:RATED]-(other:User)
        WHERE r1.rating >= 4 AND r2.rating >= 4 AND u <> other
        WITH u, other, COUNT(s) as common_series
        ORDER BY common_series DESC
        LIMIT 5
        MATCH (other)-[r:RATED]->(rec:Series)
        WHERE NOT (u)-[:RATED]->(rec) AND r.rating >= 4 AND rec.is_adult = false
        WITH rec, COUNT(DISTINCT other) as recommended_by, AVG(r.rating) as avg_rating
        OPTIONAL MATCH (rec)-[:HAS_GENRE]->(g:Genre)
        RETURN rec.series_id as series_id,
               rec.title as title,
               rec.year as year,
               COLLECT(DISTINCT g.name) as genres,
               recommended_by,
               ROUND(avg_rating * 10) / 10.0 as avg_rating
        ORDER BY recommended_by DESC, avg_rating DESC
        LIMIT $limit
        """
        return neo4j_db.query(query, {'user_id': user_id, 'limit': limit})
    
    @staticmethod
    def by_actors(user_id, limit=10):
        """Recommandations basées sur les acteurs préférés"""
        query = """
        MATCH (u:User {user_id: $user_id})-[r:RATED]->(s:Series)-[:HAS_ACTOR]->(a:Actor)
        WHERE r.rating >= 4
        WITH u, COLLECT(DISTINCT a) as favorite_actors
        UNWIND favorite_actors as actor
        MATCH (actor)<-[:HAS_ACTOR]-(rec:Series)
        WHERE NOT (u)-[:RATED]->(rec) AND rec.is_adult = false
        WITH rec, COLLECT(DISTINCT actor.name) as shared_actors, COUNT(actor) as actor_matches
        OPTIONAL MATCH (rec)-[:HAS_GENRE]->(g:Genre)
        RETURN rec.series_id as series_id,
               rec.title as title,
               rec.year as year,
               shared_actors,
               COLLECT(DISTINCT g.name) as genres,
               actor_matches as score
        ORDER BY actor_matches DESC
        LIMIT $limit
        """
        return neo4j_db.query(query, {'user_id': user_id, 'limit': limit})
    
    @staticmethod
    def hybrid(user_id, limit=10):
        """Recommandations hybrides"""
        query = """
        // Score basé sur les genres
        MATCH (u:User {user_id: $user_id})-[r:RATED]->(s:Series)-[:HAS_GENRE]->(g:Genre)
        WHERE r.rating >= 4
        WITH u, g, COUNT(*) as genre_weight
        MATCH (rec:Series)-[:HAS_GENRE]->(g)
        WHERE NOT (u)-[:RATED]->(rec) AND rec.is_adult = false
        WITH u, rec, SUM(genre_weight) as genre_score
        
        // Score collaboratif
        OPTIONAL MATCH (u)-[r1:RATED]->(s:Series)<-[r2:RATED]-(other:User)
        WHERE r1.rating >= 4 AND r2.rating >= 4
        WITH u, rec, genre_score, other
        OPTIONAL MATCH (other)-[r:RATED]->(rec)
        WHERE r.rating >= 4
        WITH rec, genre_score, COUNT(DISTINCT other) as collab_score
        
        // Informations complémentaires
        OPTIONAL MATCH (rec)-[:HAS_GENRE]->(g:Genre)
        OPTIONAL MATCH (rec)-[:HAS_ACTOR]->(a:Actor)
        
        RETURN rec.series_id as series_id,
               rec.title as title,
               rec.year as year,
               COLLECT(DISTINCT g.name) as genres,
               COLLECT(DISTINCT a.name)[0..5] as actors,
               (genre_score * 2 + collab_score * 3) as total_score
        ORDER BY total_score DESC
        LIMIT $limit
        """
        return neo4j_db.query(query, {'user_id': user_id, 'limit': limit})