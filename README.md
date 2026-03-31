# DjangoTest
Application pour tester l'utilisation de Django

## Installation de Django

avec la commande suivante

``` powershell
python.exe -m pip install Django
```

## Création du site

### Structure Mentale

``` powershell
python.exe -m pip install Django
cd .\mysite\
python.exe manage.py startapp todo
```

Django crée `manage.py` automatiquement pour piloter les tâches d’administration du projet. Les modèles sont des classes Python dérivées de `django.db.models.Model`, et l’URLconf mappe des chemins vers des vues Python.

### Modèle Django

