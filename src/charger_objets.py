"""Remplit la table OBJET_PATRIMONIAL avec les objets de Joconde et de Palissy (Grand Est).

Principe :
1. On lit les deux sources et on renomme leurs colonnes selon le plan de correspondance
   (docs/correspondances.md).
2. On relie chaque objet à son lieu (table LIEU) et à son auteur principal (table AUTEUR),
   avec les mêmes clés de rapprochement que pour le chargement de ces tables.
3. On transforme les dates en années de début et de fin (annees_depuis_texte).
4. On insère le tout, et on écrit dans reports/ ce qu'on n'a pas su traiter.

À lancer APRÈS charger_lieux.py et charger_auteurs.py, et après avoir rempli SOURCE :
    python src/charger_objets.py
"""

import ast
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from connexion import creer_engine
from nettoyage import propre, cle, premier_auteur, annees_depuis_texte

# --------------------------------------------------
# Chemins des fichiers
# --------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
JOCONDE = ROOT / "data" / "raw" / "joconde.xlsx"
PALISSY_GE = ROOT / "data" / "interim" / "palissy_grand_est.csv"
RAPPORT_DATES = ROOT / "reports" / "dates_non_comprises.csv"


# --------------------------------------------------
# Fonctions propres à ce script
# --------------------------------------------------
def liste_vers_texte(valeur):
    """Transforme "['sculpture', 'croyances - coutumes']" ou '["peinture"]' en "sculpture ; croyances - coutumes".

    Joconde écrit ses listes avec des apostrophes, Palissy avec des guillemets : les deux sont lues.
    Si la valeur n'est pas une liste, on la garde telle quelle.
    """
    valeur = propre(valeur)
    if valeur is None:
        return None
    if valeur.startswith("["):
        try:
            elements = ast.literal_eval(valeur)
            textes = [propre(e) for e in elements]
            return " ; ".join(t for t in textes if t) or None
        except (ValueError, SyntaxError):
            pass
    return valeur


def annees(date_source, date_secours):
    """Années de début et de fin. Si le texte principal n'est pas compris, on essaie le texte de secours."""
    debut, fin = annees_depuis_texte(date_source)
    if debut is None and date_secours is not None:
        debut, fin = annees_depuis_texte(date_secours)
    return debut, fin


# --------------------------------------------------
# 1. Connexion et vérifications
# --------------------------------------------------
engine = creer_engine()

COLONNES = [
    "id_source", "reference_source", "titre", "description", "denomination",
    "id_auteur", "auteur_source", "id_lieu", "lieu_conservation", "domaine",
    "materiaux_source", "date_source", "annee_debut", "annee_fin",
]

with engine.connect() as conn:
    colonnes_table = {r[0] for r in conn.execute(text(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'objet_patrimonial'"))}
    manquantes = [c for c in COLONNES if c not in colonnes_table]
    if manquantes:
        raise SystemExit(f"Colonnes absentes de la table objet_patrimonial : {manquantes}\n"
                         "Pour 'domaine' : ALTER TABLE objet_patrimonial ADD COLUMN IF NOT EXISTS domaine TEXT;")

    deja = conn.execute(text("SELECT COUNT(*) FROM objet_patrimonial")).scalar()
    if deja > 0:
        raise SystemExit(f"OBJET_PATRIMONIAL contient déjà {deja} lignes. "
                         "Pour recharger : TRUNCATE objet_patrimonial RESTART IDENTITY CASCADE;")

    sources = {nom: i for nom, i in conn.execute(text("SELECT nom, id_source FROM source"))}
    lieux = {(cle(c), cle(d)): i for i, c, d in conn.execute(text("SELECT id_lieu, commune, departement FROM lieu"))}
    auteurs = {cle(n): i for i, n in conn.execute(text("SELECT id_auteur, nom FROM auteur"))}


def trouver_source(debut_nom):
    trouvees = [i for nom, i in sources.items() if nom.lower().startswith(debut_nom.lower())]
    if len(trouvees) != 1:
        raise SystemExit(f"Source '{debut_nom}' introuvable (ou ambiguë) dans la table SOURCE : {list(sources)}")
    return trouvees[0]


id_joconde = trouver_source("Joconde")
id_palissy = trouver_source("Palissy")
print(f"Lieux en base : {len(lieux)} | auteurs en base : {len(auteurs)}")

# --------------------------------------------------
# 2. Joconde : renommage des colonnes selon le plan de correspondance
# --------------------------------------------------
jo = pd.read_excel(JOCONDE, dtype=str)
objets_jo = pd.DataFrame({
    "id_source": id_joconde,
    "reference_source": jo["reference"].map(propre),
    "titre": jo["titre"].map(propre),
    "description": jo["description"].map(propre),
    "denomination": jo["denominatio"].map(propre),
    "auteur_source": jo["auteur"].map(propre),
    "commune": jo["ville"],                      # colonnes temporaires pour retrouver le lieu
    "departement": jo["departement"],
    "lieu_conservation": jo["nom_officie"].map(propre),
    "domaine": jo["domaine"].map(liste_vers_texte),
    "materiaux_source": jo["materiaux_t"].map(propre),
    "date_source": jo["periode_de__1"].map(propre),
    "date_secours": None,                        # Joconde n'a pas de seconde colonne de date
})

# --------------------------------------------------
# 3. Palissy Grand Est
# --------------------------------------------------
pal = pd.read_csv(PALISSY_GE, sep="|", dtype=str, usecols=[
    "Reference", "Titre_editorial", "Description", "Denomination",
    "Auteur_de_l_oeuvre_ou_createur_de_l_objet", "Commune_forme_index",
    "Departement_en_lettres", "Nom_de_l_edifice", "Domaine", "Materiaux",
    "Annee_de_creation", "Siecle_de_creation",
])
annee = pal["Annee_de_creation"].map(propre)
siecle = pal["Siecle_de_creation"].map(propre)

objets_pal = pd.DataFrame({
    "id_source": id_palissy,
    "reference_source": pal["Reference"].map(propre),
    "titre": pal["Titre_editorial"].map(propre),
    "description": pal["Description"].map(propre),
    "denomination": pal["Denomination"].map(propre),
    "auteur_source": pal["Auteur_de_l_oeuvre_ou_createur_de_l_objet"].map(propre),
    "commune": pal["Commune_forme_index"],
    "departement": pal["Departement_en_lettres"],
    "lieu_conservation": pal["Nom_de_l_edifice"].map(propre),
    "domaine": pal["Domaine"].map(liste_vers_texte),
    "materiaux_source": pal["Materiaux"].map(propre),
    "date_source": annee.fillna(siecle),         # l'année si elle existe, sinon le siècle
    "date_secours": siecle,                      # si l'année n'est pas comprise (« après 1834 »), on se rabat sur le siècle
})

objets = pd.concat([objets_jo, objets_pal], ignore_index=True)

# --------------------------------------------------
# 4. Liens vers LIEU et AUTEUR
# --------------------------------------------------
objets["id_lieu"] = [lieux.get((cle(c), cle(d))) for c, d in zip(objets["commune"], objets["departement"])]


def id_auteur_de(texte):
    a = premier_auteur(texte)
    return auteurs.get(a["cle"]) if a else None


objets["id_auteur"] = objets["auteur_source"].map(id_auteur_de)

# --------------------------------------------------
# 5. Dates : texte -> années de début et de fin
# --------------------------------------------------
intervalles = pd.DataFrame(
    [annees(d, s) for d, s in zip(objets["date_source"], objets["date_secours"])],
    index=objets.index, columns=["annee_debut", "annee_fin"],
)
objets[["annee_debut", "annee_fin"]] = intervalles

# entiers qui acceptent les valeurs vides
for colonne in ["id_lieu", "id_auteur", "annee_debut", "annee_fin"]:
    objets[colonne] = pd.to_numeric(objets[colonne]).astype("Int64")

# --------------------------------------------------
# 6. Chiffres pour le rapport de qualité
# --------------------------------------------------
print("\nObjets à charger :", len(objets))
print(objets.groupby("id_source").size().to_string())
print("sans lieu retrouvé :", int(objets["id_lieu"].isna().sum()))
print("auteur source renseigné mais sans auteur en base :",
      int((objets["auteur_source"].notna() & objets["id_auteur"].isna()).sum()))

avec_date = objets["date_source"].notna()
non_comprises = objets[avec_date & objets["annee_debut"].isna()]
print("avec un texte de date :", int(avec_date.sum()),
      "| dont dates non comprises :", len(non_comprises))

RAPPORT_DATES.parent.mkdir(exist_ok=True)
(non_comprises["date_source"].value_counts()
    .rename_axis("texte_de_date").reset_index(name="nb_objets")
    .to_csv(RAPPORT_DATES, index=False))

# --------------------------------------------------
# 7. Insertion dans PostgreSQL
# --------------------------------------------------
objets[COLONNES].to_sql("objet_patrimonial", engine, if_exists="append", index=False, chunksize=5000)

print(pd.read_sql(
    "SELECT id_source, COUNT(*) AS nb_objets, COUNT(id_auteur) AS avec_auteur, "
    "COUNT(id_lieu) AS avec_lieu, COUNT(annee_debut) AS avec_annees "
    "FROM objet_patrimonial GROUP BY id_source ORDER BY id_source",
    engine,
))