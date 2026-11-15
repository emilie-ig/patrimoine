DROP TABLE IF EXISTS IMAGE_OBJET, IMAGE, OBJET_PATRIMONIAL,
                    LIEU, AUTEUR, SOURCE CASCADE;

-- ------------------------------------------------------------
-- SOURCE : traçabilité
-- ------------------------------------------------------------
CREATE TABLE SOURCE (
    id_source SERIAL PRIMARY KEY,
    nom VARCHAR(50) NOT NULL UNIQUE,
    format VARCHAR(4), -- xlsx, csv
    url TEXT,
    date_telechargement DATE
);

-- ------------------------------------------------------------
-- AUTEUR : créateurs d'objets et photographes
-- Les noms d'origine ont plusieurs formats
-- (« DERAIN André », « Despax J-B. (peintre) », « Fabioux, Martine »)
-- On stocke ici le nom normalisé, le texte d'origine reste dans
-- OBJET_PATRIMONIAL.auteur_source et IMAGE.photographe_source
-- ------------------------------------------------------------
CREATE TABLE AUTEUR (
    id_auteur SERIAL PRIMARY KEY,
    nom TEXT NOT NULL,
    annee_naissance INTEGER,
    annee_deces INTEGER,
    anonyme BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE NULLS NOT DISTINCT (nom, annee_naissance, annee_deces)
);

-- ------------------------------------------------------------
-- LIEU : communes, commun à Joconde et Palissy
--    code_insee : fourni par Palissy (COG_Insee)
-- ------------------------------------------------------------
CREATE TABLE LIEU (
    id_lieu SERIAL PRIMARY KEY,
    commune TEXT NOT NULL,
    departement TEXT,
    region TEXT,
    code_insee VARCHAR(5),
    UNIQUE NULLS NOT DISTINCT (commune, departement)
);

-- ------------------------------------------------------------
-- OBJET_PATRIMONIAL : objets de Joconde et de Palissy
-- ------------------------------------------------------------
CREATE TABLE OBJET_PATRIMONIAL (
    id_objet SERIAL PRIMARY KEY,
    id_source INTEGER NOT NULL REFERENCES SOURCE(id_source),
    reference_source TEXT NOT NULL, -- référence d'origine
    titre TEXT,
    description TEXT,
    domaine TEXT,
    denomination TEXT,
    id_auteur INTEGER REFERENCES AUTEUR(id_auteur),
    auteur_source TEXT,                    -- texte d'origine
    id_lieu INTEGER REFERENCES LIEU(id_lieu),
    lieu_conservation TEXT, -- musée (Joconde) ou édifice (Palissy)
    materiaux_source TEXT, -- texte d'origine
    date_source TEXT, -- texte d'origine (année, siècle, période)
    annee_debut INTEGER, -- calculée à partir de date_source
    annee_fin INTEGER,
    UNIQUE (id_source, reference_source),
    CHECK (annee_debut IS NULL OR annee_fin IS NULL OR annee_debut <= annee_fin)
);

-- ------------------------------------------------------------
-- IMAGE : photographies de Mémoire
-- ------------------------------------------------------------
CREATE TABLE IMAGE (
    id_image SERIAL PRIMARY KEY,
    id_source INTEGER NOT NULL REFERENCES SOURCE(id_source),
    reference_source TEXT NOT NULL, -- Reference_de_la_notice
    id_photographe INTEGER REFERENCES AUTEUR(id_auteur),
    photographe_source TEXT, -- Auteur_de_la_photographie, texte d'origine
    categorie_phototype TEXT,
    lien_image TEXT,
    UNIQUE (id_source, reference_source)
);

-- ------------------------------------------------------------
-- IMAGE_OBJET : une photo peut illustrer plusieurs notices
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
CREATE INDEX idx_objet_source ON OBJET_PATRIMONIAL(id_source);
CREATE INDEX idx_objet_auteur ON OBJET_PATRIMONIAL(id_auteur);
CREATE INDEX idx_objet_lieu ON OBJET_PATRIMONIAL(id_lieu);
CREATE INDEX idx_image_photographe ON IMAGE(id_photographe);
CREATE INDEX idx_image_objet_objet ON IMAGE_OBJET(id_objet);