"""
Configuration Django pour le projet ASADI.

Ce module contient les paramètres de configuration Django pour le projet ASADI,
incluant les paramètres de base de données, les applications installées,
les middlewares, et d'autres configurations importantes.

Generated by 'django-admin startproject' using Django 5.1.7.

Attributes:
    BASE_DIR (Path): Chemin de base du projet.
    SECRET_KEY (str): Clé secrète utilisée pour le cryptage.
    DEBUG (bool): Mode de débogage (True en développement, False en production).
    ALLOWED_HOSTS (list): Liste des hôtes autorisés à servir l'application.
    INSTALLED_APPS (list): Liste des applications Django installées.
    MIDDLEWARE (list): Liste des middlewares utilisés par l'application.
    ROOT_URLCONF (str): Module contenant les configurations d'URL racine.
    TEMPLATES (list): Configuration des moteurs de templates.
    WSGI_APPLICATION (str): Point d'entrée WSGI pour l'application.
    DATABASES (dict): Configuration des bases de données.
    AUTH_PASSWORD_VALIDATORS (list): Validateurs de mot de passe.
    AUTH_USER_MODEL (str): Modèle utilisateur personnalisé.
    LANGUAGE_CODE (str): Code de langue par défaut.
    TIME_ZONE (str): Fuseau horaire par défaut.
    USE_I18N (bool): Activation de l'internationalisation.
    USE_TZ (bool): Activation de la gestion des fuseaux horaires.
    STATIC_URL (str): URL pour les fichiers statiques.
    MEDIA_URL (str): URL pour les fichiers média.
    MEDIA_ROOT (str): Chemin vers le répertoire des fichiers média.
    LOGIN_REDIRECT_URL (str): URL de redirection après connexion.
    LOGOUT_REDIRECT_URL (str): URL de redirection après déconnexion.

For more information on these settings, see:
https://docs.djangoproject.com/en/5.1/topics/settings/
https://docs.djangoproject.com/en/5.1/ref/settings/
"""
import os
from pathlib import Path
from decouple import config
from django.contrib.messages import constants as messages
import sys


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-gjf#y_v64^exh4*&4p*bdtsdy(xss+qkjbl6jnm^z6ak_=m0#3"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '[::1]',  # pour IPv6 en local
    'asadi.fr',  # nom de domaine de production
    'www.asadi.fr',
]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "prompts",
    "utilisateurs",
    "quiz",
    "scenario",
    "documents",
    "workspace",
]

LOGIN_URL = ''



MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "ASADI.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / 'ASADI/templates']
        ,
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "ASADI.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST"),
        "PORT": "5432",
    }
}

#Email configuration
EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST=config("EMAIL_HOST")
EMAIL_USE_TLS=True
EMAIL_PORT=config("EMAIL_PORT")
EMAIL_HOST_USER=config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD=config("EMAIL_HOST_PASSWORD")

#Choix du modele de l'utilisateur qu'on a créé
AUTH_USER_MODEL = 'utilisateurs.Utilisateur'

AUTHENTICATION_BACKENDS = ['utilisateurs.backends.EmailBackend']

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "fr-FR"

TIME_ZONE = "Europe/Paris"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "/static/"
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "ASADI/static"),
]
STATIC_ROOT = BASE_DIR / 'ASADI/staticfiles'
# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'



MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'error',
}

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CHROMA_DB_DIR = BASE_DIR / "chroma_db"

# Niveau maximum global
MAX_NIVEAU = 20

# Augmenter la limite de taille de fichier à 50 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50 MB