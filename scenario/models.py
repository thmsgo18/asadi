from django.utils import timezone

from django.db import models
from utilisateurs.models import Utilisateur

"""
Module de modèles pour l'application scenario.

Ce module définit les modèles de données pour la gestion des scénarios,
questions-réponses et réponses des utilisateurs dans l'application ASADI.
"""


class Scenario(models.Model):
    """
    Modèle représentant un scénario pédagogique.
    
    Un scénario est un ensemble de questions-réponses avec un contexte
    qui peut être lancé par des utilisateurs.
    
    Attributes:
        titre (CharField): Titre du scénario (max 100 caractères).
        contexte (TextField): Description du contexte du scénario.
        date_lancement (DateTimeField): Date et heure de création du scénario.
    """
    titre = models.CharField(max_length=100)
    contexte = models.TextField()
    date_lancement = models.DateTimeField(default=timezone.now)

    def __str__(self):
        """
        Retourne une représentation sous forme de chaîne du scénario.
        
        Returns:
            str: Le titre du scénario.
        """
        return self.titre


class QuestionReponse(models.Model):
    """
    Modèle représentant une paire question-réponse dans un scénario.
    
    Attributes:
        scenario (ForeignKey): Le scénario auquel cette question-réponse appartient.
        question (TextField): Le texte de la question.
        reponse (TextField): La réponse attendue à la question.
    """
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, related_name="questions_reponses")
    question = models.TextField()
    reponse = models.TextField()

    def __str__(self):
        """
        Retourne une représentation sous forme de chaîne de la question-réponse.
        
        Returns:
            str: Le début de la question suivi de points de suspension.
        """
        return f"Q: {self.question[:30]}..."


class ScenarioLance(models.Model):
    """
    Modèle représentant une instance de scénario lancée par un utilisateur.
    
    Attributes:
        scenario (ForeignKey): Le scénario lancé.
        utilisateur (ForeignKey): L'utilisateur qui a lancé le scénario.
        date_lancement (DateTimeField): Date et heure de lancement du scénario.
        termine (BooleanField): Indique si le scénario a été terminé par l'utilisateur.
        commentaire (TextField): Commentaire optionnel sur le scénario lancé.
    """
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE)
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='scenarioDispo')
    date_lancement = models.DateTimeField(auto_now_add=True)
    termine = models.BooleanField(default=False)
    commentaire = models.TextField(blank=True, null=True)


    def __str__(self):
        """
        Retourne une représentation sous forme de chaîne du scénario lancé.
        
        Returns:
            str: Une chaîne contenant le nom de l'utilisateur et le titre du scénario.
        """
        return f"{self.utilisateur.nom} - {self.scenario.titre}"


class ReponseUtilisateur(models.Model):
    """
    Modèle représentant une réponse d'un utilisateur à une question d'un scénario.
    
    Attributes:
        scenario_lance (ForeignKey): L'instance du scénario lancé par l'utilisateur.
        question_reponse (ForeignKey): La question-réponse à laquelle l'utilisateur répond.
        reponse (TextField): La réponse fournie par l'utilisateur.
        feedback_llm (TextField): Feedback optionnel généré par le modèle de langage.
    """
    scenario_lance = models.ForeignKey(ScenarioLance, on_delete=models.CASCADE, related_name="reponses_utilisateur")
    question_reponse = models.ForeignKey(QuestionReponse, on_delete=models.CASCADE)
    reponse = models.TextField()
    feedback_llm = models.TextField(blank=True, null=True)  

    def __str__(self):
        """
        Retourne une représentation sous forme de chaîne de la réponse utilisateur.
        
        Returns:
            str: Une chaîne contenant le nom de l'utilisateur et le début de la question.
        """
        return f"{self.scenario_lance.utilisateur.nom} - {self.question_reponse.question[:30]}..."

