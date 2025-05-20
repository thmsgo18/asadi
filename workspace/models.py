from django.db import models
import os
from django.conf import settings

"""
Module de modèles pour l'application workspace.

Ce module définit les modèles de données pour la gestion des espaces de travail
dans l'application ASADI.
"""

class Workspace(models.Model):
    """
    Modèle représentant un espace de travail.
    
    Un espace de travail permet d'organiser et de regrouper des documents
    dans un dossier spécifique du système de fichiers.
    
    Attributes:
        name (CharField): Nom unique de l'espace de travail (max 100 caractères).
        contenue (CharField): Description du contenu de l'espace de travail (max 120 caractères).
        document (ManyToManyField): Relation plusieurs-à-plusieurs avec les documents associés.
        date_creation (DateTimeField): Date et heure de création de l'espace de travail.
    """
    name = models.CharField(max_length=100, unique=True)
    contenue = models.CharField(max_length=120)
    document = models.ManyToManyField('documents.Document', blank=True, related_name='workspaces')
    date_creation = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """
        Sauvegarde l'instance d'espace de travail et crée le dossier correspondant.
        
        Cette méthode étend la méthode save() standard pour gérer la création et
        le renommage des dossiers associés à l'espace de travail dans le système de fichiers.
        
        Args:
            *args: Arguments variables passés à la méthode save() parente.
            **kwargs: Arguments nommés variables passés à la méthode save() parente.
        """
        if self.pk:
            old_instance = Workspace.objects.get(pk=self.pk)
            if old_instance.name != self.name:
                old_path = os.path.join(settings.MEDIA_ROOT, 'documents', old_instance.name)
                new_path = os.path.join(settings.MEDIA_ROOT, 'documents', self.name)
                if os.path.exists(old_path):
                    os.rename(old_path, new_path)

        super().save(*args, **kwargs)
        workspace_path = os.path.join(settings.MEDIA_ROOT, 'documents', self.name)
        os.makedirs(workspace_path, exist_ok=True)

    def __str__(self):
        """
        Retourne une représentation sous forme de chaîne de l'espace de travail.
        
        Returns:
            str: Le nom de l'espace de travail.
        """
        return self.name