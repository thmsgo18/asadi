from django.db import models
from workspace.models import Workspace

"""
Module de modèles pour l'application documents.

Ce module définit les modèles de données pour la gestion des documents
dans l'application ASADI, permettant leur organisation dans des espaces de travail.
"""

def get_upload_path(instance, filename):
    """
    Détermine le chemin d'upload pour un document.
    
    Cette fonction génère un chemin d'upload basé sur l'espace de travail
    auquel le document est associé, si disponible.
    
    Args:
        instance (Document): L'instance du document en cours d'upload.
        filename (str): Le nom du fichier original.
        
    Returns:
        str: Le chemin où le fichier doit être sauvegardé.
    """
    workspace = instance.workspaces.first()
    if workspace:
        return f'documents/{workspace.name}/{filename}'
    return f'documents/{filename}'

class Document(models.Model):
    """
    Modèle représentant un document dans l'application.
    
    Un document peut être associé à un ou plusieurs espaces de travail
    et contient un fichier physique avec des métadonnées.
    
    Attributes:
        nom (CharField): Nom du document (max 255 caractères).
        fichier (FileField): Fichier physique associé au document.
        type (CharField): Type du document (max 50 caractères).
        date_ajout (DateTimeField): Date et heure d'ajout du document.
    """
    nom = models.CharField(max_length=255)
    fichier = models.FileField(upload_to=get_upload_path, null=True, blank=True, max_length=255)
    type = models.CharField(max_length=50)
    date_ajout = models.DateTimeField(auto_now_add=True)

    @property
    def workspaces(self):
        """
        Récupère tous les espaces de travail disponibles.
        
        Returns:
            list: Liste de tous les espaces de travail existants.
        """
        return [workspace for workspace in Workspace.objects.all()]

    def __str__(self):
        """
        Retourne une représentation sous forme de chaîne du document.
        
        Returns:
            str: Le nom du document ou le nom du fichier si le nom n'est pas défini.
        """
        return self.nom or self.fichier.name