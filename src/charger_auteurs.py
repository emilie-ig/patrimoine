
"""Remplit la table AUTEUR
 
Principe :
1. On lit les champs « auteur » de Joconde et de Palissy (Grand Est)
2. Pour chaque valeur, on garde l'auteur principal (le premier cité) et on le nettoie
   avec premier_auteur() : voir les règles dans nettoyage.py
3. On regroupe les écritures d'une même personne grâce à la clé de rapprochement
   (sans accents ni majuscules).
4. On insère le résultat dans AUTEUR.
 
Lancement, depuis la racine du projet, avec le .venv activé :
    python src/charger_auteurs.py
"""
 
from pathlib import Path
 
import pandas as pd
from sqlalchemy import text
 
from connexion import creer_engine
from nettoyage import premier_auteur
 
# --------------------------------------------------
# Chemins des fichiers
# --------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
JOCONDE = ROOT / "data" / "raw" / "joconde.xlsx"
PALISSY_GE = ROOT / "data" / "interim" / "palissy_grand_est.csv"
RAPPORT = ROOT / "reports" / "auteurs_a_verifier.csv"
 
# --------------------------------------------------
# 1. Lecture des deux colonnes d'auteurs
# --------------------------------------------------
joconde = pd.read_excel(JOCONDE, usecols=["auteur"], dtype=str)
palissy = pd.read_csv(
    PALISSY_GE, sep="|", dtype=str,
    usecols=["Auteur_de_l_oeuvre_ou_createur_de_l_objet"],
)
 
sources = [
    ("Joconde", joconde["auteur"]),
    ("Palissy", palissy["Auteur_de_l_oeuvre_ou_createur_de_l_objet"]),
]
 
# --------------------------------------------------
# 2. Nettoyage et regroupement
# --------------------------------------------------
auteurs = {}        # clé de rapprochement -> informations sur l'auteur
a_verifier = []     # cas qu'on ne sait pas traiter automatiquement
 
for nom_source, colonne in sources:
    valeurs = colonne.dropna()
    print(f"--- {nom_source} : {len(valeurs)} objets avec un auteur renseigné, "
          f"dont {valeurs.str.contains(';').sum()} avec plusieurs auteurs (on garde le premier) ---")
 
    for texte in valeurs.unique(): # chaque texte distinct n'est traité qu'une fois
        a = premier_auteur(texte)
        if a is None:
            continue
 
        if a["cle"] not in auteurs:
            auteurs[a["cle"]] = a# première écriture rencontrée = celle qu'on conserve
        else:
            # même personne déjà vue : on complète ses dates si on les découvre ici
            for champ in ("naissance", "deces"):
                if auteurs[a["cle"]][champ] is None and a[champ] is not None:
                    auteurs[a["cle"]][champ] = a[champ]
 
        # une virgule restante signale souvent un format « Nom, Prénom » ou deux auteurs collés
        if "," in a["nom"]:
            a_verifier.append({"source": nom_source, "texte_origine": texte, "nom_retenu": a["nom"]})
 
df = pd.DataFrame(auteurs.values()).rename(
    columns={"naissance": "annee_naissance", "deces": "annee_deces"}
)
# entiers qui acceptent les valeurs vides (sinon pandas les transforme en décimaux)
for colonne in ["annee_naissance", "annee_deces"]:
    df[colonne] = pd.to_numeric(df[colonne]).astype("Int64")
 
print("\nAuteurs distincts :", len(df))
print("dont anonymes :", int(df["anonyme"].sum()))
print("avec année de naissance :", int(df["annee_naissance"].notna().sum()))
print("noms contenant encore une virgule (à vérifier) :", len(a_verifier))
 
RAPPORT.parent.mkdir(exist_ok=True)
pd.DataFrame(a_verifier).to_csv(RAPPORT, index=False)
 
# --------------------------------------------------
# 3. Insertion dans PostgreSQL
# --------------------------------------------------
engine = creer_engine()
 
# Garde-fou : on ne recharge pas une table déjà remplie
with engine.connect() as conn:
    deja = conn.execute(text("SELECT COUNT(*) FROM auteur")).scalar()
if deja > 0:
    raise SystemExit(f"AUTEUR contient déjà {deja} lignes. Pour recharger : TRUNCATE auteur RESTART IDENTITY CASCADE;")
 
df[["nom", "annee_naissance", "annee_deces", "anonyme"]].to_sql(
    "auteur", engine, if_exists="append", index=False
)
 
print(pd.read_sql(
    "SELECT COUNT(*) AS nb_auteurs, COUNT(annee_naissance) AS avec_naissance, "
    "SUM(anonyme::int) AS anonymes FROM auteur",
    engine,
))
 