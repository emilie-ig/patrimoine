DROP TABLE IF EXISTS OBJET_DOMAINE, IMAGE_OBJET, IMAGE, OBJET_PATRIMONIAL,
                     DOMAINE, LIEU, AUTEUR, SOURCE CASCADE;

-- ------------------------------------------------------------
-- 1. SOURCE : traçabilité
-- ------------------------------------------------------------
CREATE TABLE SOURCE (
    source_id SERIAL PRIMARY KEY,
    nom VARCHAR(50) NOT NULL UNIQUE,
    format VARCHAR(4), -- xlsx, csv
    url TEXT,
    date_telechargement DATE
);

-- ------------------------------------------------------------
-- 2. AUTEUR : créateurs d'objets et photographes
-- Les noms d'origine ont plusieurs formats
-- (« DERAIN André », « Despax J-B. (peintre) », « Fabioux, Martine »)
-- On stocke ici le nom normalisé ; le texte d'origine reste dans
-- OBJET_PATRIMONIAL.auteur_source et IMAGE.photographe_source
-- ------------------------------------------------------------
CREATE TABLE AUTEUR (
    id_auteur SERIAL PRIMARY KEY,
    nom TEXT NOT NULL,
    annee_naissance INTEGER,
    annee_deces INTEGER,
    anonyme BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (nom, annee_naissance, annee_deces)
);

-- ------------------------------------------------------------
-- 3. LIEU : communes, commun à Joconde et Palissy
--    code_insee : fourni par Palissy (COG_Insee)
-- ------------------------------------------------------------
CREATE TABLE LIEU (
    id_lieu SERIAL PRIMARY KEY,
    commune TEXT NOT NULL,
    departement TEXT,
    region TEXT,
    code_insee VARCHAR(5),
    UNIQUE (commune, departement)
);

-- ------------------------------------------------------------
-- 4. DOMAINE : vocabulaire des domaines
--    Joconde : « peinture », « dessin »... ; Palissy : « orfèvrerie et autres
--    objets en métal »... Les deux vocabulaires sont différents
-- ------------------------------------------------------------
CREATE TABLE DOMAINE (
    id_domaine SERIAL PRIMARY KEY,
    libelle TEXT NOT NULL UNIQUE
);

-- ------------------------------------------------------------
-- 5. OBJET_PATRIMONIAL : objets de Joconde et de Palissy
-- ------------------------------------------------------------
CREATE TABLE OBJET_PATRIMONIAL (
    id_objet SERIAL PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES SOURCE(source_id),
    reference_source TEXT NOT NULL, -- référence d'origine
    titre TEXT,
    denomination TEXT,
    id_auteur INTEGER REFERENCES AUTEUR(id_auteur),
    auteur_source TEXT,                    -- texte d'origine
    id_lieu INTEGER REFERENCES LIEU(id_lieu),
    lieu_conservation TEXT, -- musée (Joconde) ou édifice (Palissy)
    materiaux_source TEXT, -- texte d'origine
    date_source TEXT, -- texte d'origine (année, siècle, période)
    annee_debut INTEGER, -- calculée à partir de date_source
    annee_fin INTEGER,
    UNIQUE (source_id, reference_source),
    CHECK (annee_debut IS NULL OR annee_fin IS NULL OR annee_debut <= annee_fin)
);

-- Un objet peut relever de plusieurs domaines
CREATE TABLE OBJET_DOMAINE (
    id_objet INTEGER NOT NULL REFERENCES OBJET_PATRIMONIAL(id_objet) ON DELETE CASCADE,
    id_domaine INTEGER NOT NULL REFERENCES DOMAINE(id_domaine),
    PRIMARY KEY (id_objet, id_domaine)
);

-- ------------------------------------------------------------
-- 6. IMAGE : photographies de Mémoire
-- ------------------------------------------------------------
CREATE TABLE IMAGE (
    id_image SERIAL PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES SOURCE(source_id),
    reference_source TEXT NOT NULL, -- Reference_de_la_notice
    id_photographe INTEGER REFERENCES AUTEUR(id_auteur),
    photographe_source TEXT, -- Auteur_de_la_photographie, texte d'origine
    categorie_phototype TEXT,
    lien_image TEXT,
    UNIQUE (source_id, reference_source)
);

-- ------------------------------------------------------------
-- 7. IMAGE_OBJET : une photo peut illustrer plusieurs notices
--    (« PM19001325;IA19000152 ») et une notice peut avoir plusieurs photos.
--    On ne garde que les références Palissy (PM...) présentes dans OBJET_PATRIMONIAL
--    Les références Mérimée (IA...) n'ont pas de table ici
-- ------------------------------------------------------------
CREATE TABLE IMAGE_OBJET (
    id_image INTEGER NOT NULL REFERENCES IMAGE(id_image) ON DELETE CASCADE,
    id_objet INTEGER NOT NULL REFERENCES OBJET_PATRIMONIAL(id_objet) ON DELETE CASCADE,
    PRIMARY KEY (id_image, id_objet)
);

-- ------------------------------------------------------------
-- Index sur les clés étrangères
-- ------------------------------------------------------------
CREATE INDEX idx_objet_source      ON OBJET_PATRIMONIAL(source_id);
CREATE INDEX idx_objet_auteur      ON OBJET_PATRIMONIAL(id_auteur);
CREATE INDEX idx_objet_lieu        ON OBJET_PATRIMONIAL(id_lieu);
CREATE INDEX idx_image_photographe ON IMAGE(id_photographe);
CREATE INDEX idx_image_objet_objet ON IMAGE_OBJET(id_objet);