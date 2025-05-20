from django.db import models

from prompts.models import Prompt
from utilisateurs.models import Utilisateur
from django.conf import settings

"""
Module de modèles pour l'application quiz.

Ce module définit les modèles de données pour la gestion des quiz,
questions, réponses et progression des utilisateurs.
"""

# Create your models here.

class Quiz(models.Model):
    """
    Modèle représentant un quiz.
    
    Un quiz est un ensemble de questions créé par un utilisateur,
    associé à un prompt et pouvant être répondu par d'autres utilisateurs.
    
    Attributes:
        titre (CharField): Titre du quiz (max 100 caractères).
        date_creation (DateTimeField): Date et heure de création du quiz.
        utilisateur (ForeignKey): L'utilisateur qui a créé le quiz.
        prompt (OneToOneField): Le prompt associé au quiz.
        debutQuiz (BooleanField): Indique si le quiz a été démarré.
        feedback_global (TextField): Commentaire global sur le quiz.
    """
    titre = models.CharField(max_length=100)
    date_creation = models.DateTimeField(auto_now_add=True)
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE,related_name='listeQuiz')
    prompt = models.OneToOneField(Prompt, on_delete=models.CASCADE)
    debutQuiz = models.BooleanField(default=False)
    feedback_global = models.TextField(null=True, blank=True)

    def __str__(self):
        """
        Retourne une représentation sous forme de chaîne du quiz.
        
        Returns:
            str: Le titre du quiz.
        """
        return self.titre





class QuestionQuiz(models.Model):
    """
    Modèle représentant une question de quiz.
    
    Attributes:
        quiz (ForeignKey): Le quiz auquel cette question appartient.
        questionQuiz (TextField): Le texte de la question.
        bonneReponse (TextField): La réponse correcte à la question.
    """
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    questionQuiz = models.TextField()
    bonneReponse = models.TextField()
    def __str__(self):
        """
        Retourne une représentation sous forme de chaîne de la question.
        
        Returns:
            str: Le texte de la question.
        """
        return self.questionQuiz



class ReponseUtilisateur(models.Model):
    """
    Modèle représentant une réponse d'un utilisateur à une question de quiz.
    
    Attributes:
        questionQuiz (ForeignKey): La question à laquelle l'utilisateur a répondu.
        utilisateur (ForeignKey): L'utilisateur qui a répondu à la question.
        reponseUtilisateur (TextField): La réponse fournie par l'utilisateur.
        est_correcte (BooleanField): Indique si la réponse est correcte.
    """
    questionQuiz = models.ForeignKey(QuestionQuiz, on_delete=models.CASCADE)
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    reponseUtilisateur = models.TextField()
    est_correcte = models.BooleanField(default=False)

    def __str__(self):
        """
        Retourne une représentation sous forme de chaîne de la réponse utilisateur.
        
        Returns:
            str: Une chaîne contenant le nom de l'utilisateur et le début de la question.
        """
        return f"{self.utilisateur.nom} → {self.questionQuiz.questionQuiz[:30]}"
    

class ProgressionQuiz(models.Model):
    """
    Modèle représentant la progression d'un utilisateur dans un quiz.
    
    Attributes:
        utilisateur (ForeignKey): L'utilisateur dont on suit la progression.
        quiz (ForeignKey): Le quiz concerné.
        index_courant (IntegerField): L'index de la question actuelle dans le quiz.
        termine (BooleanField): Indique si l'utilisateur a terminé le quiz.
    """
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    quiz = models.ForeignKey('Quiz', on_delete=models.CASCADE)
    index_courant = models.IntegerField(default=0)
    termine = models.BooleanField(default=False)

    class Meta:
        """
        Méta-options pour le modèle ProgressionQuiz.
        
        Attributes:
            unique_together: Garantit qu'il n'y a qu'un seul enregistrement par paire utilisateur/quiz.
        """
        unique_together = ('utilisateur', 'quiz')  # Un seul enregistrement par utilisateur/quiz