# Proposition d'architecture

## 1. Principe de decoupage

`api_docs` doit etre une app transverse qui agrege les specifications OpenAPI publiees
par les apps metier. Chaque domaine garde sa logique metier, ses modeles, ses vues,
ses URLs et sa spec OpenAPI. L'app `api_docs` ne fait qu'offrir une porte d'entree
unique pour consulter la documentation.

Structure cible recommandee :

- `api_docs` : hub de documentation OpenAPI
- `accounts` : utilisateurs, profils, permissions applicatives, login/logout front
- `products` : catalogue
- `todo` : a garder comme zone de test ou de demo
- `orders` : commandes
- `fulfillment` : preparation au colisage, reservation, picking
- `shipping` : expeditions, transporteurs, tracking
- `billing` : factures, avoirs, pieces comptables

Je te conseille d'eviter une enorme app `documents` si elle doit porter plusieurs
cycles de vie metier. Les commandes, la logistique, l'expedition et la facturation
evoluent rarement au meme rythme. Si tu tiens a un regroupement visuel, `documents`
peut rester un dossier de code ou un package Python, mais pas forcement une seule
app Django.

## 2. Documentation OpenAPI

Chaque app metier expose :

- ses endpoints dans `api.py`
- ses routes dans `urls.py`
- sa spec via une route du type `/api/<domaine>/openapi.yaml`
- sa declaration de documentation dans `<app>/api_docs.py`

Ensuite `api_docs` centralise :

- `/api/docs`
- `/api/docs/<domaine>`

Ce modele permet d'ajouter un nouveau domaine sans toucher au rendu de la doc,
seulement en ajoutant l'app et en enregistrant sa spec.

## 3. Authentification front

Pour le front utilisateur, je recommande une authentification par session Django :

- creation d'une app `accounts`
- login/logout avec les vues Django ou des vues maison
- permissions basees sur groupes et permissions Django
- protections CSRF standard pour les formulaires et actions back-office

Pourquoi ce choix :

- parfait pour le back-office admin
- simple a faire vivre cote navigateur
- coherent avec l'admin Django et les templates serveur

Note pratique pour ce projet :

- la base locale utilise deja `django.contrib.auth.models.User`
- il vaut mieux garder ce modele pour l'instant afin d'eviter une migration risquee
- si un `AUTH_USER_MODEL` personnalise devient necessaire, il faudra le faire dans
  une phase dediee avec strategie de migration ou reinitialisation maitrisee

## 4. Securisation API Machine-to-Machine

Je recommande de separer l'auth navigateur de l'auth M2M.

Option cible :

- OAuth2 Client Credentials avec un fournisseur externe ou `django-oauth-toolkit`
- scopes par domaine : `products:read`, `orders:write`, `billing:read`, etc.
- journalisation des appels et rotation des secrets

Option de depart si tu veux aller plus vite :

- table `ApiClient`
- secret stocke sous forme hachee
- emission de tokens courts ou verification par cle API
- scopes par client

Je recommande quand meme de viser rapidement un modele standard OAuth2 si l'API doit
etre consommee par plusieurs systemes.

## 5. Acces front et admin pour les documents

Les futurs domaines `orders`, `fulfillment`, `shipping` et `billing` devraient chacun
fournir :

- des ecrans admin Django pour les operations internes
- des vues front ou API pour l'interface utilisateur
- des permissions explicites selon le role
- une spec OpenAPI propre au domaine

En pratique, chaque app peut suivre le meme squelette :

- `models.py`
- `admin.py`
- `views.py`
- `api.py`
- `urls.py`
- `forms.py`
- `services.py`
- `permissions.py`
- `api_docs.py`
