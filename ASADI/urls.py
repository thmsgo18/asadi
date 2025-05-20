"""
Configuration des URLs pour le projet ASADI.

Ce module définit les routes URL principales du projet ASADI et inclut
les configurations d'URL des différentes applications du projet.

La liste `urlpatterns` associe les URLs aux vues correspondantes.

Attributes:
    handler403 (str): Gestionnaire pour les erreurs 403 (accès refusé).
    handler404 (function): Gestionnaire pour les erreurs 404 (page non trouvée).
    urlpatterns (list): Liste des modèles d'URL pour le routage des requêtes.

Examples:
    Function views:
        from my_app import views
        path('', views.home, name='home')
    
    Class-based views:
        from other_app.views import Home
        path('', Home.as_view(), name='home')
    
    Including another URLconf:
        from django.urls import include, path
        path('blog/', include('blog.urls'))

For more information, see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
"""
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path, include
from .views import *
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin

handler403 = 'utilisateurs.views.no_permission'
handler404 = page_not_found_view
urlpatterns = [
    path('no-permission/', no_permission, name='no_permission'),

    path('', include('utilisateurs.urls')),

    path('quiz/', include('quiz.urls')),

    path('scenario/', include('scenario.urls')),


    path('documents/', include('documents.urls')),

    path('prompts/', include('prompts.urls')),

    path("menu/", menu, name="menu"),

    path("cgu/", cgu, name="cgu"),
    path("mentions_legales/", mentions_legales, name="mentions_legales"),
    path("contact/", contact, name="contact"),

    path("liste_utilisateurs/", liste_utilisateurs, name="liste_utilisateurs"),
    path('supprimer_utilisateur/', supprimer_utilisateur, name='supprimer_utilisateur'),
    path("modifier_utilisateur/<int:user_id>/", modifier_utilisateur, name="modifier_utilisateur",),

    path("admin/", admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    # Sert /static/ **avant** tout autre traitement de vues
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)