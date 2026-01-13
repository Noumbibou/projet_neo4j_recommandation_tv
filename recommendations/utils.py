"""
Utilitaires pour gérer les IDs Django <-> Neo4j
"""

def get_neo4j_user_id(django_user):
    """
    Obtenir l'user_id Neo4j à partir d'un utilisateur Django
    """
    return str(django_user.id)


def get_series_id_from_django(series_title):
    """
    Dans le cas où vous créez des séries via Django,
    générez un series_id unique
    """
    import uuid
    return str(uuid.uuid4())
