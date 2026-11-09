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