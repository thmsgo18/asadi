from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

"""
Module de modèles pour l'application utilisateurs.

Ce module définit les modèles de données pour la gestion des utilisateurs
dans l'application ASADI, avec un système d'authentification personnalisé.
"""


class CustomUserManager(BaseUserManager):
    """
    Gestionnaire personnalisé pour le modèle Utilisateur.
    
    Cette classe étend BaseUserManager pour fournir des méthodes de création
    d'utilisateurs et de superutilisateurs avec validation personnalisée.
    """
    def create_user(self, email, password=None, **extra_fields):
        """
        Crée et sauvegarde un utilisateur avec l'email et le mot de passe donnés.
        
        Args:
            email (str): Adresse email de l'utilisateur (obligatoire).
            password (str, optional): Mot de passe de l'utilisateur. Defaults to None.
            **extra_fields: Champs supplémentaires pour l'utilisateur.
            
        Returns:
            Utilisateur: L'instance d'utilisateur créée.
            
        Raises:
            ValueError: Si l'email ou le mot de passe n'est pas fourni.
        """
        if not email:
            raise ValueError("L'adresse email est obligatoire")

        if not password:
            raise ValueError("Le mot de passe est obligatoire")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Crée et sauvegarde un superutilisateur avec l'email et le mot de passe donnés.
        
        Args:
            email (str): Adresse email du superutilisateur.
            password (str, optional): Mot de passe du superutilisateur. Defaults to None.
            **extra_fields: Champs supplémentaires pour le superutilisateur.
            
        Returns:
            Utilisateur: L'instance de superutilisateur créée.
            
        Raises:
            ValueError: Si le mot de passe n'est pas fourni ou si is_staff ou is_superuser n'est pas True.
        """
        if not password:
            raise ValueError("Le mot de passe est obligatoire pour le superutilisateur")

        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)


        if extra_fields.get('is_staff') is not True:
            raise ValueError("Le superutilisateur doit avoir is_staff=True.")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Le superutilisateur doit avoir is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


# Create your models here.
class Utilisateur(AbstractBaseUser, PermissionsMixin):
    """
    Modèle d'utilisateur personnalisé pour l'application ASADI.
    
    Étend AbstractBaseUser et PermissionsMixin pour fournir un modèle
    d'utilisateur avec authentification par email et rôles personnalisés.
    
    Attributes:
        username (CharField): Nom d'utilisateur (max 255 caractères).
        nom (CharField): Nom de famille de l'utilisateur (max 100 caractères).
        prenom (CharField): Prénom de l'utilisateur (max 100 caractères).
        email (EmailField): Adresse email unique de l'utilisateur.
        date_inscription (DateTimeField): Date et heure d'inscription.
        is_active (BooleanField): Indique si l'utilisateur est actif.
        is_staff (BooleanField): Indique si l'utilisateur est membre du personnel.
        role (CharField): Rôle de l'utilisateur (max 100 caractères).
        niveau (IntegerField): Niveau de l'utilisateur.
    """
    username = models.CharField('nom utilisateur', max_length=255)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    date_inscription = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    role = models.CharField(max_length=100, null=True, blank=True)
    niveau = models.IntegerField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'nom', 'prenom', 'role', 'niveau']

    objects = CustomUserManager()

    def __str__(self):
        """
        Retourne une représentation sous forme de chaîne de l'utilisateur.
        
        Returns:
            str: L'adresse email de l'utilisateur.
        """
        return self.email

    def set_role(self, nouveau_role):
        """
        Définit un nouveau rôle pour l'utilisateur et sauvegarde les modifications.
        
        Args:
            nouveau_role (str): Le nouveau rôle à attribuer à l'utilisateur.
        """
        self.role = nouveau_role
        self.save()

    def set_niveau(self, nouveau_niveau):
        """
        Définit un nouveau niveau pour l'utilisateur et sauvegarde les modifications.
        
        Args:
            nouveau_niveau (int): Le nouveau niveau à attribuer à l'utilisateur.
        """
        self.niveau = nouveau_niveau
        self.save()


    @property
    def historique_prompts(self):
        """
        Récupère l'historique des prompts de l'utilisateur.
        
        Returns:
            QuerySet: Ensemble des prompts associés à l'utilisateur.
        """
        return self.historique.all()

    @property
    def listeQuiz(self):
        """
        Récupère la liste des quiz de l'utilisateur.
        
        Returns:
            QuerySet: Ensemble des quiz associés à l'utilisateur.
        """
        return self.listeQuiz.all()

    @property
    def listeScenario(self):
        """
        Récupère la liste des scénarios disponibles pour l'utilisateur.
        
        Returns:
            QuerySet: Ensemble des scénarios associés à l'utilisateur.
        """
        return self.scenarioDispo.all()