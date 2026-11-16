"""Remplit la table LIEU

Principe :
1. Palissy (Grand Est) sert de référence : il a le département, la région et le code INSEE
2. On cherche chaque commune de Joconde dans cette référence, avec une clé de rapprochement
   (commune + département, sans accents ni majuscules)
3. On insère dans LIEU la référence Palissy, puis les communes de Joconde absentes de Palissy

Lancement, depuis la racine du projet, avec le .venv activé :
    python src/charger_lieux.py

on filtre le grand est avec le notebook 02 car Joconde est limité à cette région
"""

from getpass import getpass
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

from nettoyage import propre, cle, code_insee

# --------------------------------------------------
# Chemins des fichiers (calculés à partir de l'emplacement de ce script)
# --------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
PALISSY_GE = ROOT / "data" / "interim" / "palissy_grand_est.csv"
JOCONDE = ROOT / "data" / "raw" / "joconde.xlsx"
RAPPORT = ROOT / "reports" / "lieux_non_rapproches.csv"

if not PALISSY_GE.exists():
    raise SystemExit(f"Fichier introuvable : {PALISSY_GE}\nLance d'abord le filtrage Grand Est (notebook 02).")

# --------------------------------------------------
# 1. Référence : les communes de Palissy Grand Est
# --------------------------------------------------
# dtype=str : on lit tout en texte, pour ne pas perdre les zéros des codes INSEE
pal = pd.read_csv(PALISSY_GE, sep="|", dtype=str)

ref = pd.DataFrame({
    "commune": pal["Commune_forme_index"].map(propre),
    "departement": pal["Departement_en_lettres"].map(propre),
    "region": pal["Region"].map(propre),
    # on garde le code INSEE actuel s'il existe, sinon l'ancien (COG_Insee)
    "insee": pal["Code_INSEE_commune_actuelle"].map(code_insee)
                .fillna(pal["COG_Insee"].map(code_insee)),
}).dropna(subset=["commune"])

# clés de rapprochement : permettent de comparer deux écritures du même nom
ref["k_commune"] = ref["commune"].map(cle)
ref["k_dep"] = ref["departement"].map(cle)

# une seule ligne par commune (Palissy en a des milliers : une par objet)
ref = ref.drop_duplicates(["k_commune", "k_dep"])
print("Lieux Palissy Grand Est :", len(ref))

# --------------------------------------------------
# 2. Les communes de Joconde, rapprochées de la référence
# --------------------------------------------------
joconde = pd.read_excel(JOCONDE, usecols=["ville", "departement", "region"], dtype=str)

jo = joconde.drop_duplicates().rename(columns={"ville": "commune"})
for colonne in ["commune", "departement", "region"]:
    jo[colonne] = jo[colonne].map(propre)
jo["k_commune"] = jo["commune"].map(cle)
jo["k_dep"] = jo["departement"].map(cle)

# how="left" : on garde toutes les communes de Joconde, avec le code INSEE si on le trouve
jo = jo.merge(ref[["k_commune", "k_dep", "insee"]], on=["k_commune", "k_dep"], how="left")

non_rapprochees = jo[jo["insee"].isna()][["commune", "departement"]]
print("Communes Joconde :", len(jo), "| avec code INSEE trouvé :", jo["insee"].notna().sum())
print(non_rapprochees.head(20))

# on garde la liste complète pour le rapport de qualité
RAPPORT.parent.mkdir(exist_ok=True)
non_rapprochees.to_csv(RAPPORT, index=False)

# --------------------------------------------------
# 3. Assemblage et insertion dans PostgreSQL
# --------------------------------------------------
colonnes = ["commune", "departement", "region", "insee", "k_commune", "k_dep"]

# Palissy d'abord : keep="first" garde sa version (avec code INSEE) quand une commune est dans les deux
lieux = (pd.concat([ref[colonnes], jo[colonnes]])
         .drop_duplicates(["k_commune", "k_dep"], keep="first")
         .rename(columns={"insee": "code_insee"}))

engine = create_engine(URL.create(
    "postgresql+psycopg2",
    username="postgres",
    password=getpass("Mot de passe PostgreSQL : "),   # jamais écrit dans le fichier
    host="localhost",
    port=5432,
    database="patrimoine",
))

# Garde-fou : on ne recharge pas une table déjà remplie (la contrainte UNIQUE refuserait de toute façon)
with engine.connect() as conn:
    deja = conn.execute(text("SELECT COUNT(*) FROM lieu")).scalar()
if deja > 0:
    raise SystemExit(f"LIEU contient déjà {deja} lignes. Pour recharger : TRUNCATE lieu RESTART IDENTITY CASCADE;")

lieux[["commune", "departement", "region", "code_insee"]].to_sql(
    "lieu", engine, if_exists="append", index=False
)

print(pd.read_sql("SELECT COUNT(*) AS nb_lieux, COUNT(code_insee) AS avec_code_insee FROM lieu", engine))