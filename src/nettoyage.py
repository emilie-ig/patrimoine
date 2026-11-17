"""Fonctions de nettoyage réutilisées par tous les scripts de chargement"""

import re
import unicodedata
import pandas as pd

MOTIF_INSEE = re.compile(r"\d{5}|2[AB]\d{3}")   # 5 chiffres, ou code corse (2A / 2B + 3 chiffres)
MOTIF_PARENTHESES = re.compile(r"\(([^)]*)\)")
MOTIF_DATES = re.compile(r"\s*(\d{3,4})?\s*-\s*(\d{3,4})?\s*")
NOMS_ANONYMES = {"anonyme", "auteur inconnu", "inconnu"}
MOTIF_NOM_VIRGULE_PRENOM = re.compile(r"([^,\s][^,]*[^,\s]), ([A-ZÀ-ÖØ-Þ][^,:]*)")

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

def premier_auteur(texte):
    """Analyse le champ « auteur » et renvoie l'auteur principal (le premier cité).

    Renvoie un dictionnaire {nom, cle, naissance, deces, anonyme}, ou None si le champ est vide.
    Exemples :
        "Dubois Paul (1829-1905)"                -> nom "Dubois Paul", naissance 1829, deces 1905
        "Wilbaut, Nicolas (peintre)"             -> nom "Wilbaut Nicolas"
        "ROY Pierre Marcel;DELATRE (imprimeur)"  -> nom "ROY Pierre Marcel"
        "auteur inconnu"                         -> nom "anonyme", anonyme True
    """
    texte = propre(texte)
    if texte is None:
        return None

    # plusieurs auteurs séparés par « ; » : on garde le premier qui n'est pas vide
    parties = [p for p in (propre(p) for p in texte.split(";")) if p]
    if not parties:
        return None
    premier = parties[0]

    # dates éventuelles entre parenthèses
    naissance = deces = None
    for contenu in MOTIF_PARENTHESES.findall(premier):
        m = MOTIF_DATES.fullmatch(contenu)
        if m:
            naissance = int(m.group(1)) if m.group(1) else None
            deces = int(m.group(2)) if m.group(2) else None

    # le nom, c'est le texte sans ses parenthèses (rôles, « attribué », dates...)
    nom = propre(MOTIF_PARENTHESES.sub(" ", premier))
    if nom is None:
        return None

    # format « Nom, Prénom » (frequent dans Palissy) -> « Nom Prénom » comme dans Joconde
    m = MOTIF_NOM_VIRGULE_PRENOM.fullmatch(nom)
    if m:
        nom = f"{m.group(1)} {m.group(2)}"

    k = cle(nom)
    if k is None:
        return None
    if k in NOMS_ANONYMES:
        return {"nom": "anonyme", "cle": "anonyme", "naissance": None, "deces": None, "anonyme": True}
    return {"nom": nom, "cle": k, "naissance": naissance, "deces": deces, "anonyme": False}


def _un_intervalle(morceau):
    """Transforme une expression de date en (année_début, année_fin) ou None si on ne la comprend pas
 
    Exemples :
        "1713" -> (1713, 1713)
        "17e siècle" -> (1601, 1700)
        "1er quart 20e siècle" -> (1901, 1925)
        "2e moitié 19e siècle" -> (1851, 1900)
    """
    morceau = morceau.strip().lower()
 
    # une année seule : "1713"
    m = re.fullmatch(r"(\d{3,4})", morceau)
    if m:
        a = int(m.group(1))
        return a, a
 
    # un siècle éventuellement précisé par un quart ou une moitié
    m = re.fullmatch(
        r"(?:(\d)\s*(?:er|re|ère|e|ème)\s+(quart|moitié|moitie)\s+)?"
        r"(\d{1,2})\s*(?:er|re|ère|e|ème)?\s*si[èe]cle",
        morceau,
    )
    if not m:
        return None
    rang, precision, siecle = m.group(1), m.group(2), int(m.group(3))
    base = (siecle - 1) * 100            # 17e siècle : base 1600, donc de 1601 à 1700
    if precision is None:
        return base + 1, base + 100
    rang = int(rang)
    if precision == "quart" and 1 <= rang <= 4:
        return base + (rang - 1) * 25 + 1, base + rang * 25
    if precision.startswith("moiti") and 1 <= rang <= 2:
        return base + (rang - 1) * 50 + 1, base + rang * 50
    return None
 
 
def annees_depuis_texte(texte):
    """Renvoie (année_début, année_fin) pour un texte de date, ou (None, None)
 
    Plusieurs valeurs séparées par « ; » : on prend du plus petit début au plus grand fin.
    Si une valeur n'est pas comprise, on renonce : ces cas sont comptés dans le rapport.
    """
    texte = propre(texte)
    if texte is None:
        return None, None
    intervalles = []
    for morceau in texte.split(";"):
        resultat = _un_intervalle(morceau)
        if resultat is None:
            return None, None
        intervalles.append(resultat)
    return min(d for d, _ in intervalles), max(f for _, f in intervalles)