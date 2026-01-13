# test_neo4j.py

import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tv_recommender.settings')
django.setup()

from tv_recommender.neo4j_db import neo4j_db

def test_connection():
    """
    Test de connexion à Neo4j
    """
    try:
        query = "RETURN 'Connexion réussie!' as message, datetime() as time"
        result = neo4j_db.query(query)
        
        if result:
            print("✅ Connexion à Neo4j réussie!")
            print(f"Message: {result[0]['message']}")
            print(f"Heure: {result[0]['time']}")
        
        # Test de création de nœud
        create_query = """
        CREATE (s:Serie {
            title: 'Test Serie',
            genre: 'Drama'
        })
        RETURN s
        """
        neo4j_db.execute_write(create_query)
        print("✅ Création de nœud test réussie!")
        
        # Nettoyage
        delete_query = "MATCH (s:Serie {title: 'Test Serie'}) DELETE s"
        neo4j_db.execute_write(delete_query)
        print("✅ Nettoyage réussi!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        neo4j_db.close()

if __name__ == "__main__":
    test_connection()