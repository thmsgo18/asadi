from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

"""
Module de modèles pour l'application prompts.

Ce module définit les modèles de données pour la gestion des prompts,
questions et réponses dans l'application ASADI.
"""

class Prompt(models.Model):
    """
    Modèle représentant un prompt (conversation).
    
    Un prompt est une conversation entre un utilisateur et le système,
    composée de questions et de réponses.
    
    Attributes:
        user (ForeignKey): L'utilisateur propriétaire du prompt.
        title (CharField): Titre du prompt (max 255 caractères).
        date_creation (DateTimeField): Date et heure de création du prompt.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='prompts')
    title = models.CharField(max_length=255, default="Nouveau prompt")
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


    @property
    def questions_Dans_Prompt(self):
        """
        Récupère toutes les questions associées à ce prompt.
        
        Returns:
            list: Liste des textes des questions associées au prompt.
        """
        return [question.questionPrompt for question in self.questions.all()]

    @property
    def reponses_Dans_Prompt(self):
        """
        Récupère toutes les réponses associées à ce prompt.
        
        Returns:
            list: Liste des textes des réponses associées au prompt.
        """
        return [response.text for response in self.responses.all()]


class Question(models.Model):
    """
    Modèle représentant une question posée dans un prompt.
    
    Attributes:
        prompt (ForeignKey): Le prompt auquel cette question est associée.
        questionPrompt (TextField): Le texte de la question.
        reponse (OneToOneField): La réponse associée à cette question, si elle existe.
        date_creation (DateTimeField): Date et heure de création de la question.
    """
    prompt = models.ForeignKey(Prompt, on_delete=models.CASCADE, related_name='questions')
    questionPrompt = models.TextField()
    reponse = models.OneToOneField('Reponse', null=True, blank=True, on_delete=models.SET_NULL, related_name='question_associee')
    date_creation = models.DateTimeField(auto_now_add=True)

    @property
    def reponse_Prompt(self):
        """
        Récupère la réponse associée à cette question.
        
        Returns:
            str: Le texte de la réponse ou "(pas encore de réponse)" si aucune réponse n'existe.
        """
        try:
            return self.reponse.rep
        except AttributeError: #changer le nom de l'exception en
            return "(pas encore de réponse)"


class Reponse(models.Model):
    """
    Modèle représentant une réponse à une question.
    
    Attributes:
        rep (TextField): Le texte de la réponse.
    """
    rep = models.TextField()

    def __str__(self):
        return f"{self.question_associee.questionPrompt} - {self.rep}"