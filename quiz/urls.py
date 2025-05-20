from django.urls import path
from . import views

urlpatterns = [
    path('', views.quiz, name='quiz'),
    path("creer_quiz/", views.creer_quiz, name="creer_quiz"),
    path("quiz/<int:quiz_id>/", views.detail_quiz, name="quiz_detail"),
    path("<int:quiz_id>/supprimer/", views.supprimer_quiz, name="supprimer_quiz"),
    path("<int:quiz_id>/lancer/", views.lancer_quiz, name="lancer_quiz"),
    path("quiz/<int:quiz_id>/suivant/", views.quiz_suivant, name="quiz_suivant"),
    path('quiz/annuler_creation/', views.annuler_creation_quiz, name='annuler_creation_quiz'),
    path('quiz/regenerer_quiz_plus_dur/', views.regenerer_quiz_plus_dur, name='regenerer_quiz_plus_dur'),
    path('quiz/preview_quiz_plus_dur/<int:quiz_id>/', views.preview_quiz_plus_dur, name='preview_quiz_plus_dur'),
    path('annuler_creation_quiz/<int:quiz_id>/', views.annuler_creation_quiz, name='annuler_creation_quiz'),
]