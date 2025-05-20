from django.urls import path
from . import views

urlpatterns = [
    path('', views.scenario, name='scenario'),
    path('scenario/<int:pk>/', views.voir_scenario, name='voir_scenario'),
    path('delete/<int:scenario_id>/', views.supprimer_scenario, name='supprimer_scenario'),
    path('question/delete/<int:question_id>/', views.supprimer_question, name='supprimer_question'),
    path('scenario/<int:scenario_id>/ajouter-question/', views.ajouter_question, name='ajouter_question'),
    path('question/modifier/<int:question_id>/', views.modifier_question, name='modifier_question'),
    path('question/<int:question_id>/', views.detail_question, name='detail_question'),
    path('scenario/<int:scenario_id>/modifier-scenario/', views.modifier_scenario, name='modifier_scenario'),
    path('scenario/', views.scenario_redirect, name='scenario_redirect'),
    path('scenario/<int:scenario_id>/lancer/', views.lancer_scenario, name='lancer_scenario'),
    path('scenario/<int:scenario_id>/rediriger/', views.redirection_scenario_utilisateur, name='rediriger_scenario'),
    path('scenario/valider/', views.valider_scenario, name='valider_scenario'),







]
