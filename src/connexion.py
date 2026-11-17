
"""Connexion à la base PostgreSQL du projet, partagée par tous les scripts de chargement"""
 
from getpass import getpass
 
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
 
 
def creer_engine():
    """Demande le mot de passe au clavier et ouvre la connexion"""
    return create_engine(URL.create(
        "postgresql+psycopg2",
        username="postgres",
        password=getpass("Mot de passe PostgreSQL : "),
        host="localhost",
        port=5432,
        database="patrimoine",
    ))
 