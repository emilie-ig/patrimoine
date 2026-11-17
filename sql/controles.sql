-- ============================================================
-- Contrôles de qualité de la base patrimoine
-- Lancement, depuis la racine du projet :
--     psql -U postgres -d patrimoine -f sql/controles.sql
-- ============================================================

\echo
\echo '1. Objets par source (avec auteur, lieu et années)'
SELECT s.nom AS source,
       COUNT(*)            AS nb_objets,
       COUNT(o.id_auteur)  AS avec_auteur,
       COUNT(o.id_lieu)    AS avec_lieu,
       COUNT(o.annee_debut) AS avec_annees
FROM objet_patrimonial o
JOIN source s ON s.id_source = o.id_source
GROUP BY s.nom
ORDER BY s.nom;

\echo
\echo '2. Objets par département et par source'
SELECT l.departement, s.nom AS source, COUNT(*) AS nb_objets
FROM objet_patrimonial o
JOIN lieu l   ON l.id_lieu = o.id_lieu
JOIN source s ON s.id_source = o.id_source
GROUP BY l.departement, s.nom
ORDER BY l.departement, s.nom;

\echo
\echo '3. Objets par siècle (siècle du milieu de la période de création)'
SELECT s.nom AS source,
       ((o.annee_debut + o.annee_fin) / 2 - 1) / 100 + 1 AS siecle_approx,
       COUNT(*) AS nb_objets
FROM objet_patrimonial o
JOIN source s ON s.id_source = o.id_source
WHERE o.annee_debut IS NOT NULL AND o.annee_fin IS NOT NULL
GROUP BY s.nom, siecle_approx
ORDER BY s.nom, siecle_approx;

\echo
\echo '4. Les 15 auteurs les plus fréquents (hors anonymes)'
SELECT a.nom, COUNT(*) AS nb_objets
FROM objet_patrimonial o
JOIN auteur a ON a.id_auteur = o.id_auteur
WHERE NOT a.anonyme
GROUP BY a.nom
ORDER BY nb_objets DESC
LIMIT 15;

\echo
\echo '5. Part des objets anonymes, par source'
SELECT s.nom AS source,
       COUNT(*) FILTER (WHERE a.anonyme) AS objets_anonymes,
       COUNT(*)                          AS objets_avec_auteur
FROM objet_patrimonial o
JOIN auteur a ON a.id_auteur = o.id_auteur
JOIN source s ON s.id_source = o.id_source
GROUP BY s.nom
ORDER BY s.nom;

\echo
\echo '6. Années suspectes'
SELECT COUNT(*) FILTER (WHERE annee_fin - annee_debut > 300) AS intervalle_de_plus_de_300_ans,
       COUNT(*) FILTER (WHERE annee_debut > 2026)            AS annee_dans_le_futur
FROM objet_patrimonial;

\echo
\echo '7. Objets sans lieu'
SELECT id_objet, id_source, reference_source, titre
FROM objet_patrimonial
WHERE id_lieu IS NULL;

\echo
\echo '8. Cohérence : auteurs et lieux sans aucun objet (on attend 0 et 0)'
SELECT
  (SELECT COUNT(*) FROM auteur a
    WHERE NOT EXISTS (SELECT 1 FROM objet_patrimonial o WHERE o.id_auteur = a.id_auteur)) AS auteurs_sans_objet,
  (SELECT COUNT(*) FROM lieu l
    WHERE NOT EXISTS (SELECT 1 FROM objet_patrimonial o WHERE o.id_lieu = l.id_lieu))     AS lieux_sans_objet;

\echo
\echo '9. Les 20 domaines les plus fréquents, par source (vocabulaires différents)'
SELECT s.nom AS source, o.domaine, COUNT(*) AS nb_objets
FROM objet_patrimonial o
JOIN source s ON s.id_source = o.id_source
GROUP BY s.nom, o.domaine
ORDER BY nb_objets DESC
LIMIT 20;