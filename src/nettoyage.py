"""Fonctions de nettoyage réutilisées par tous les scripts de chargement"""

import re
import unicodedata
import pandas as pd

def propre(v):
    """Nettoie une valeur texte : enlève les espaces en trop

    Renvoie None si la valeur est vide ou manquante
    Exemple : "  Saint-Dié   " -> "Saint-Dié"
    """
    if v is None or pd.isna(v):
        return None
    v = " ".join(str(v).split()) # supprime les espaces au début, à la fin et en double
    return v or None # une chaîne vide devient None

def cle(texte):
    """Fabrique une clé de rapprochement : même clé = même nom écrit autrement

    On enlève les accents, les majuscules et la ponctuation.
    Exemple : "Saint-Dié-des-Vosges" et "SAINT DIE DES VOSGES"
              donnent la même clé "saint die des vosges"
    La clé sert à comparer deux textes. Elle n'est jamais stockée comme valeur finale
    """
    texte = propre(texte)
    if texte is None:
        return None
    texte = unicodedata.normalize("NFKD", texte) # sépare les lettres de leurs accents
    texte = "".join(c for c in texte if not unicodedata.combining(c)) # retire les accents
    texte = texte.lower().replace("œ", "oe").replace("æ", "ae") # ligatures
    texte = re.sub(r"[^a-z0-9]+", " ", texte) # tout ce qui n'est pas lettre ou chiffre -> espace
    return texte.strip() or None

MOTIF_INSEE = re.compile(r"\d{5}|2[AB]\d{3}")   # 5 chiffres, ou code corse (2A / 2B + 3 chiffres)

def code_insee_brut(v):
    """Remet un code INSEE en forme"""
    v = propre(v)
    if v is None:
        return None
    if v.endswith(".0"):
        v = v[:-2]
    return v.zfill(5) if v.isdigit() and len(v) < 5 else v


def code_insee(v):
    """Renvoie le code INSEE s'il est valide, sinon None."""
    v = code_insee_brut(v)
    return v if v and MOTIF_INSEE.fullmatch(v) else None