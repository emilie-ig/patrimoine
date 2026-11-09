# Intégration et harmonisation de données patrimoniales

Prendre des inventaires de collections de formats et structures différents, les nettoyer, les harmoniser et les charger dans une base PostgreSQL commune.
--- 

**Objectif**

Les institutions patrimoniales décrivent leur collections avec des formats et des saisies différents. Ce projet simule la mise en commun de ces inventaires:
- diagnostiquer la qualité de chaque source ;
- définir un modèle de données commun (objets, images, institutions, lieux) ;
- transformer et normaliser les données, en gardant la trace de chaque transformation ;
- contrôler la qualité avec des règles de validation ;
- charger le résultat dans PostgreSQL et documenter la procédur

**Provenances des données**

Trois fichiers de données sont utilisés et sont libres de droits : 
- La base [*Joconde de Troyes*](https://www.data.gouv.fr/datasets/collections-des-musees-de-france-base-joconde-de-troyes-champagne-metropole?utm_source=chatgpt.com) qui décrit les oeuvres de musées de France (XLSX)
- La base [*Photographies: Fonds de la guerre 14-18*](https://www.data.gouv.fr/datasets/photographies-fonds-de-la-guerre-14-18-2?utm_source=chatgpt.com) qui contient des photographies concernant la première guerre mondiales (JSON)
- La base [*Muséofile*](https://www.data.gouv.fr/datasets/musees-de-france-base-museofile?utm_source=chatgpt.com) qui répertorie les Musées de France (CSV)

