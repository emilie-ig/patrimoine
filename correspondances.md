# Plan de correspondance

| Table | Colonne | Joconde | Palissy | Transformation |
|---|---|---|---|---|
| OBJET_PATRIMONIAL | id_source | (fixe) | (fixe) | Valeur de la table SOURCE |
| OBJET_PATRIMONIAL | reference_source | `reference` | `Reference` | Aucune, texte d'origine |
| OBJET_PATRIMONIAL | titre | `titre` | `Titre_editorial` | Nettoyer les espaces |
| OBJET_PATRIMONIAL | description | `description` | `Description` | Nettoyer les espaces |
| OBJET_PATRIMONIAL | denomination | `denominatio`| `Denomination` | Nettoyer les espaces |
| OBJET_PATRIMONIAL | auteur_source | `auteur` | `Auteur_de_l_oeuvre_ou_createur_de_l_objet` | Texte d'origine |
| OBJET_PATRIMONIAL | id_auteur | via AUTEUR | via AUTEUR | Voir AUTEUR |
| OBJET_PATRIMONIAL | id_lieu | via LIEU | via LIEU | Voir LIEU |
| OBJET_PATRIMONIAL | lieu_conservation | `nom_officie` | `Nom_de_l_edifice` | Nettoyer les espaces |
| OBJET_PATRIMONIAL | domaine | `domaine` | `Domaine` | Lire la liste (`['x']` et `["x"]`), joindre par « ; » |
| OBJET_PATRIMONIAL | materiaux_source | `materiaux_t` | `Materiaux` | Texte d'origine |
| OBJET_PATRIMONIAL | date_source | `periode_de__1`| `Annee_de_creation`, sinon `Siecle_de_creation` | Texte d'origine |
| OBJET_PATRIMONIAL | annee_debut, annee_fin | déduites de date_source | déduites de date_source | Année : début = fin. Siècle : 17e = 1601 à 1700 |
| LIEU | commune | `ville` | `Commune_forme_index` | Clé de rapprochement : sans accents, sans majuscules, sans tirets |
| LIEU | departement | `departement` | `Departement_en_lettres` | Même clé de rapprochement |
| LIEU | region | `region` | `Region` | Nettoyer |
| LIEU | code_insee | aucune | `COG_Insee` (ou `Code_INSEE_commune_actuelle` ?) | Lire en texte (zéro initial) ; pour Joconde, retrouver via commune + département |
| AUTEUR | nom | `auteur` | `Auteur_de_l_oeuvre_ou_createur_de_l_objet` | Séparer nom, prénom, dates, rôle selon le format |
| AUTEUR | annee_naissance, annee_deces | dates entre parenthèses | à voir | Extraire « (1829-1905) » |
| AUTEUR | anonyme | « anonyme » | à voir | Vrai si la valeur est « anonyme » |

## Images

| Table | Colonne | Mémoire | Transformation |
|---|---|---|---|
| IMAGE | reference_source | `Reference_de_la_notice` | Aucune |
| IMAGE | photographe_source | `Auteur_de_la_photographie` | Texte d'origine |
| IMAGE | id_photographe | `Auteur_de_la_photographie` | Via AUTEUR |
| IMAGE | categorie_phototype | `Categorie_du_phototype` | Aucune |
| IMAGE | lien_image | `Lien_vers_l_image` | Aucune |
| IMAGE_OBJET | (liaison) | `References_Palissy_Merimee_lien_notice_en_cours` | Séparer sur « ; », garder les « PM », rattacher à Palissy `Reference` |
