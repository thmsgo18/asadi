from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.prompt, name='prompt'),

    path("logout/", LogoutView.as_view(next_page="connexion"), name="logout"),

    path("changer-mot-de-passe/", views.changer_mot_de_passe, name="changer_mot_de_passe"),

    path("avatar/<str:username>.png/", views.avatar_png, name='avatar_png'),
]