# tv_recommender/neo4j_db.py

from neo4j import GraphDatabase
from django.conf import settings

class Neo4jConnection:
    """
    Classe pour gérer la connexion à Neo4j
    """
    _instance = None
    _driver = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Neo4jConnection, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                settings.NEO4J_BOLT_URL,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
    
    def close(self):
        if self._driver:
            self._driver.close()
            self._driver = None
    
    def query(self, query, parameters=None, db=None):
        """
        Exécute une requête Cypher
        """
        assert self._driver is not None, "Driver non initialisé"
        
        with self._driver.session(database=db) as session:
            result = session.run(query, parameters)
            return [record.data() for record in result]
    
    def execute_write(self, query, parameters=None):
        """
        Exécute une requête d'écriture
        """
        with self._driver.session() as session:
            result = session.write_transaction(
                lambda tx: tx.run(query, parameters)
            )
            return result

# Instance globale
neo4j_db = Neo4jConnection()