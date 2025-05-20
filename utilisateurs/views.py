from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from utilisateurs.models import Utilisateur
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordResetView

"""
Module de vues pour l'application utilisateurs.

Ce module contient les vues pour la gestion des utilisateurs, notamment
l'authentification, l'inscription et la réinitialisation de mot de passe.
"""

# Create your views here.

def no_permission(request, exception):
    """
    Gestionnaire pour les erreurs 403 (accès refusé).
    
    Args:
        request: La requête HTTP ayant généré l'erreur.
        exception: L'exception ayant causé l'erreur 403.
        
    Returns:
        HttpResponse: La page d'erreur 403 personnalisée avec le statut 403.
    """
    return render(request, '403.html', status=403)

def connexion(request):
    """
    Gère l'authentification des utilisateurs.
    
    Cette vue traite le formulaire de connexion, authentifie l'utilisateur
    et le redirige vers la page appropriée en fonction de son rôle.
    
    Args:
        request: La requête HTTP.
        
    Returns:
        HttpResponse: La page de connexion ou redirection vers la page appropriée.
    """
    #recuperation des infos de connexion
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        #verification de l'authentification et du profil
        utilisateur = authenticate(request, email=email,password=password)
        if utilisateur is not None: #si l'utilisateur existe bien avec les bonnes caractéristiques
            login(request, utilisateur)

            # Vérifie si l'utilisateur appartient au groupe 'administrateurs'
            if utilisateur.groups.filter(name="administrateurs").exists():
                return redirect("menu")  # nom de l'URL vers la vue menu
            else:
                return redirect("prompt")  # nom de l'URL vers la vue prompt
        else:
            messages.error(request, "Identifiants incorrects. Veuillez vérifier votre adresse e-mail et votre mot de passe.")
            return redirect("connexion")
    return render(request, "connexion.html")


def inscription(request):
    """
    Gère l'inscription des nouveaux utilisateurs.
    
    Cette vue traite le formulaire d'inscription, vérifie les données soumises,
    crée un nouvel utilisateur si les données sont valides et le redirige vers
    la page de connexion.
    
    Args:
        request: La requête HTTP.
        
    Returns:
        HttpResponse: La page d'inscription ou redirection vers la page de connexion.
    """
    if request.method == "POST": #type de formulaire
        #recuperation des infos de l'utilisateur
        username = request.POST.get("username")
        nom = request.POST.get("nom")
        prenom = request.POST.get("prenom")
        email = request.POST.get("email")
        password = request.POST.get("password")
        password2 = request.POST.get("password2")

        if Utilisateur.objects.filter(username=username):
            messages.error(request, "Nom d'utilisateur déjà pris !!!")
            return redirect(inscription)

        if Utilisateur.objects.filter(email=email):
            messages.error(request, "Compte déjà créer !!! ")
            return redirect(connexion)

        if password != password2:
            messages.error(request, "Les mots de passe ne concordent pas. Veuillez réessayez !!!")
            return redirect(inscription)

        #Creation de l'utilisateur dans la bdd
        utilisateur = Utilisateur.objects.create_user(email, password, username=username, nom=nom, prenom=prenom, role="utilisateur", niveau=1)

        #sauvegarde de l'utilisateur dans la bdd
        utilisateur.save()
        messages.success(request, "Votre compte à été créé avec succès !!!")
        return redirect(connexion)

    return render(request, "inscription.html")


class ResetPasswordView(SuccessMessageMixin, PasswordResetView):
    """
    Vue pour la réinitialisation de mot de passe.
    
    Cette classe étend PasswordResetView pour fournir une interface
    de réinitialisation de mot de passe avec des messages de succès.
    
    Attributes:
        template_name (str): Nom du template pour la page de réinitialisation.
        email_template_name (str): Nom du template pour l'email de réinitialisation.
        subject_template_name (str): Nom du template pour le sujet de l'email.
        success_message (str): Message affiché en cas de succès.
        success_url (str): URL de redirection après succès.
    """
    template_name = "reset_password.html"
    email_template_name = "reset_password_email.txt"
    subject_template_name = "reset_password_subject.txt"
    success_message = "Les instructions pour réinitialiser votre mot de passe viennent de vous être envoyer !!! N'hésitez pas à jetez un coup d'oeil aux spams !!!"
    success_url = reverse_lazy("connexion")

