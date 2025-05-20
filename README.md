# ASADI

## À propos du projet
ASADI est une application Django utilisant un système RAG avec ChromaDB et un LLM. Elle permet aux utilisateurs de filtrer les contextes lors des requêtes au LLM à travers une fonctionnalité de sélection de workspace.

## Gestion de version
Ce projet est versionné simultanément avec :
- **SVN** : Système de versionnage principal
- **GitHub** : Système de versionnage secondaire

Cette double gestion de version permet de bénéficier des avantages des deux systèmes :
- SVN pour la compatibilité avec les processus existants
- GitHub pour la collaboration, les pull requests et l'intégration avec d'autres outils

## Installation et configuration

### Prérequis
- Python 3.8+
- Django
- Autres dépendances listées dans `requirements.txt`

### Installation
```bash
# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Configurer l'environnement
# Copier .env.example en .env et modifier selon vos besoins

# Lancer le serveur de développement
python manage.py runserver
```

## Structure du projet
- **ASADI/** : Application principale Django
- **documents/** : Gestion des documents
- **prompts/** : Gestion des prompts pour le LLM
- **scenario/** : Fonctionnalités liées aux scénarios
- **utilisateurs/** : Gestion des utilisateurs
- **workspace/** : Gestion des workspaces pour filtrer les contextes
