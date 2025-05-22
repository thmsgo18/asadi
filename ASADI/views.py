from django.contrib.auth import get_user_model
from django.contrib.messages.context_processors import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import Group
from django.template.defaulttags import csrf_token
from django.views.decorators.csrf import csrf_protect
from datetime import timedelta
from django.utils import timezone
from django.utils.timezone import now
from django.db.models import Q
from django.db.models import Avg, Max
from django.conf import settings
from django.core.mail import send_mail

from scenario.models import Scenario
from utilisateurs.models import Utilisateur

"""
Module de vues principales pour le projet ASADI.

Ce module contient les vues générales du projet ASADI, notamment
les vues de gestion des utilisateurs, les pages statiques et les
gestionnaires d'erreurs personnalisés.
"""

def page_not_found_view(request, exception):
    """
    Gestionnaire pour les erreurs 404 (page non trouvée).
    
    Args:
        request: La requête HTTP ayant généré l'erreur.
        exception: L'exception ayant causé l'erreur 404.
        
    Returns:
        HttpResponse: La page d'erreur 404 personnalisée avec le statut 404.
    """
    return render(request, '404.html', status=404)

def no_permission(request):
    """
    Gestionnaire pour les erreurs 403 (accès refusé).
    
    Args:
        request: La requête HTTP ayant généré l'erreur.
        
    Returns:
        HttpResponse: La page d'erreur 403 personnalisée avec le statut 403.
    """
    return render(request, '403.html', status=403)

def est_admin(user):
    """
    Vérifie si un utilisateur est membre du groupe 'administrateurs'.
    
    Cette fonction est utilisée comme prédicat pour le décorateur user_passes_test
    afin de restreindre l'accès aux vues administratives.
    
    Args:
        user: L'utilisateur à vérifier.
        
    Returns:
        bool: True si l'utilisateur est un administrateur, False sinon.
    """
    return user.groups.filter(name='administrateurs').exists()


@csrf_protect
@user_passes_test(est_admin, login_url='no_permission')
def liste_utilisateurs(request):
    """
    Affiche la liste des utilisateurs avec options de filtrage et statistiques.
    
    Cette vue est réservée aux administrateurs et permet de visualiser, filtrer
    et rechercher les utilisateurs, ainsi que d'afficher diverses statistiques.
    
    Args:
        request: La requête HTTP.
        
    Returns:
        HttpResponse: La page de liste des utilisateurs ou redirection vers la page de connexion.
    """
    if request.user.is_authenticated:
        Utilisateur = get_user_model()
        admin_group = Group.objects.get(name='administrateurs')

        query = request.GET.get('q', '').strip()
        filter_role = request.GET.get('filter_role', '').strip()

        utilisateurs = Utilisateur.objects.all()

        if query:
            utilisateurs = utilisateurs.filter(
                Q(prenom__icontains=query) |
                Q(nom__icontains=query) |
                Q(username__icontains=query))

        if filter_role == 'admin':
            utilisateurs = utilisateurs.filter(groups=admin_group)
        elif filter_role == 'user':
            utilisateurs = utilisateurs.exclude(groups=admin_group)

        admin_ids = set(utilisateurs.filter(groups=admin_group).values_list('id', flat=True))
        for u in utilisateurs:
            u.is_admin = (u.id in admin_ids)

            # STATISTIQUES
        total_users = Utilisateur.objects.count()
        total_admins = Utilisateur.objects.filter(groups=admin_group).count()

        # Tri des utilisateurs par ordre alphabétique (nom puis prénom)
        utilisateurs = utilisateurs.order_by('nom', 'prenom')

        # calcul de la moyenne des niveaux
        moyenne_niveau_brut = utilisateurs.aggregate(avg=Avg('niveau'))['avg'] or 0
        # Formatage avec un seul chiffre après la virgule
        moyenne_niveau = round(moyenne_niveau_brut, 1)
       
        
        today = now().date()
        lundi = today - timedelta(days=today.weekday())
        #calcul nb connexion aujourd'hui et 7 dernier jours
        connexions_today = Utilisateur.objects.filter(last_login__date=today).count()
        connexions_week = Utilisateur.objects.filter(last_login__date__gte=lundi).count()
         #calcul nb inscrit sur les 7 derniers jours
        nb_inscrit_semaine= Utilisateur.objects.filter(date_inscription=lundi).count()
        dernier = Utilisateur.objects.exclude(last_login__isnull=True).order_by('-last_login').first()
        
        # Calcul du niveau maximum atteint par un utilisateur
        niveau_max = Utilisateur.objects.aggregate(max=Max('niveau'))['max'] or 0
        utilisateur_niveau_max = Utilisateur.objects.filter(niveau=niveau_max).first() if niveau_max > 0 else None

        return render(request, "liste_utilisateurs.html", {
            'utilisateurs': utilisateurs,
            'admin_group': admin_group,
            'query': query,
            'filter_role': filter_role,

            'total_users': total_users,
            'total_admins': total_admins,
            'connexions_today': connexions_today,
            'connexions_week': connexions_week,
            'dernier': dernier,
            'moyenne_niveau': moyenne_niveau, 
            'nb_inscrit_semaine': nb_inscrit_semaine,
            'niveau_max': niveau_max,
            'utilisateur_niveau_max': utilisateur_niveau_max,
        })
    else:
        messages.error(request, "Veuillez vous connectez pour accéder au site !!!")
        return redirect('connexion')


@csrf_protect
@user_passes_test(est_admin, login_url='no_permission')
def modifier_utilisateur(request, user_id):
    """
    Affiche et traite le formulaire de modification d'un utilisateur.
    
    En méthode POST, met à jour les informations de l'utilisateur et redirige vers
    la liste des utilisateurs. Cette vue est réservée aux administrateurs.
    
    Args:
        request: La requête HTTP.
        user_id (int): L'identifiant de l'utilisateur à modifier.
        
    Returns:
        HttpResponse: Redirection vers la liste des utilisateurs.
    """
    Utilisateur = get_user_model()
    utilisateur = get_object_or_404(Utilisateur, id=user_id)

    if request.method == "POST":
        # Récupération des valeurs envoyées
        username = request.POST.get("username", "").strip()
        prenom = request.POST.get("prenom", "").strip()
        nom  = request.POST.get("nom", "").strip()
        email = request.POST.get("email", "").strip()
        niveau = request.POST.get("niveau", "").strip()

        # Mise à jour
        utilisateur.username = username
        utilisateur.prenom = prenom 
        utilisateur.nom = nom
        utilisateur.email = email
        utilisateur.niveau = niveau
        utilisateur.save()

        return redirect('liste_utilisateurs')

    # En cas de GET direct (rare ici, puisque on ouvre la modal via JS),
    # on redirige simplement vers la liste
    return redirect('liste_utilisateurs')

@csrf_protect
@user_passes_test(est_admin, login_url='no_permission')
def supprimer_utilisateur(request):
    """
    Supprime un utilisateur spécifié par son ID.
    
    Cette vue est réservée aux administrateurs et ne fonctionne qu'en méthode POST.
    Elle empêche la suppression d'autres administrateurs.
    
    Args:
        request: La requête HTTP contenant l'ID de l'utilisateur à supprimer.
        
    Returns:
        JsonResponse: Réponse JSON indiquant le succès ou l'échec de l'opération.
    """
    if request.method == "POST":
        Utilisateur = get_user_model()
        user_id = request.POST.get("user_id")
        try:
            utilisateur = Utilisateur.objects.get(id=user_id)
            if utilisateur.groups.filter(name="administrateurs").exists():
                return JsonResponse({"success": False, "error": "Impossible de supprimer un administrateur."})
            utilisateur.delete()
            return JsonResponse({"success": True})
        except Utilisateur.DoesNotExist:
            return JsonResponse({"success": False, "error": "Utilisateur introuvable."})
    return JsonResponse({"success": False, "error": "Requête non autorisée."})



@user_passes_test(est_admin, login_url='no_permission')
def menu(request):
    """
    Affiche le menu principal pour les administrateurs.
    
    Cette vue est réservée aux administrateurs authentifiés.
    
    Args:
        request: La requête HTTP.
        
    Returns:
        HttpResponse: La page de menu ou redirection vers la page de connexion.
    """
    if request.user.is_authenticated:
        return render(request, "menu.html")
    else:
        messages.error(request, "Veuillez vous connectez pour accéder au site !!!")
        return redirect('connexion')




def mentions_legales(request):
    """
    Affiche la page des mentions légales.
    
    Args:
        request: La requête HTTP.
        
    Returns:
        HttpResponse: La page des mentions légales.
    """
    return render(request, 'mentions_legales.html')


def cgu(request):
    """
    Affiche la page des Conditions Générales d'Utilisation.
    
    Args:
        request: La requête HTTP.
        
    Returns:
        HttpResponse: La page des CGU.
    """
    return render(request, 'cgu.html')


def politique_confidentialite(request):
    """
    Affiche la page de la politique de confidentialité.
    
    Args:
        request: La requête HTTP.
        
    Returns:
        HttpResponse: La page de la politique de confidentialité.
    """
    return render(request, 'politique_confidentialite.html')

def contact(request):
    """
    Affiche la page de contact.
    
    Args:
        request: La requête HTTP.
        
    Returns:
        HttpResponse: La page de contact.
    """
    return render(request,'contact.html')