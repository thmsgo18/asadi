import os, json
import re

from django.contrib import messages
from django.contrib.messages.context_processors import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from datetime import date

from .models import Quiz, QuestionQuiz, ReponseUtilisateur, ProgressionQuiz
from scenario.models import Scenario
from prompts.models import Prompt
from utilisateurs.models import Utilisateur
from src.api import reponseAssistant, generate_quiz_title, PleiadeLLM

from django.urls import reverse
from django.http import JsonResponse, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from src.api import PleiadeLLM, reponseAssistant
from decouple import config
from django.utils.text import Truncator
from django.contrib import messages

"""
Module de vues pour l'application quiz.

Ce module contient les vues pour la gestion des quiz, notamment
la création, le lancement, la participation et la suppression des quiz.
"""

def quiz(request):
    """
    Vue principale pour l'accès à l'application quiz.
    
    Vérifie si l'utilisateur est authentifié et le redirige vers
    la page appropriée.
    
    Args:
        request: La requête HTTP.
        
    Returns:
        HttpResponse: La page de prompt ou redirection vers la page de connexion.
    """
    if request.user.is_authenticated:
        return render(request, "prompt.html")
    else:
        messages.error(request, "Veuillez vous connectez pour accéder au site !!!")
        return redirect('connexion')


@login_required
def creer_quiz(request):
    """
    Gère la création d'un nouveau quiz.
    
    Cette vue traite les différentes étapes de création d'un quiz :
    - Définition du thème
    - Génération des questions
    - Validation et enregistrement du quiz
    
    Args:
        request: La requête HTTP.
        
    Returns:
        HttpResponse: La page de création de quiz avec le contexte approprié.
    """
    if request.method == "POST":
        action = request.POST.get("action")
        theme = request.session.get("theme_quiz")
        
        # Traitement de l'action
        
        if not theme:
            theme = request.POST.get("reponse")
            request.session["theme_quiz"] = theme

        if action == "regenerer":
            # régénérer des questions sur le même thème
            # Régénération des questions
            questions = generer_questions(theme)
            request.session["questions_quiz"] = questions

        elif action == "valider":
            try:
                # Validation du quiz en cours
                utilisateur = request.user
                
                # Générer un titre créatif pour le quiz
                quiz_title = generate_quiz_title(theme)

                
                prompt = Prompt.objects.create(title=f"Thème du quiz : {theme}", user=utilisateur)
                quiz = Quiz.objects.create(titre=quiz_title, utilisateur=utilisateur, prompt=prompt)


                questions = request.session.get("questions_quiz", [])
                for q in questions:
                    QuestionQuiz.objects.create(
                        quiz=quiz,
                        questionQuiz=q["question"],
                        bonneReponse=q["bonneReponse"]
                    )

                # Nettoyage session
                del request.session["questions_quiz"]
                del request.session["theme_quiz"]
                request.session.modified = True  # Forcer la sauvegarde des modifications de session

                # Quiz créé avec succès
                # Construire l'URL directement
                redirect_url = f"/quiz/{quiz.id}/lancer/"

                return redirect(redirect_url)
            except Exception as e:

                messages.error(request, f"Erreur lors de la création du quiz: {e}")

        else:
            # Première soumission : générer des questions
            questions = generer_questions(theme)
            request.session["questions_quiz"] = questions

    questions = request.session.get("questions_quiz")
    theme = request.session.get("theme_quiz")

    return render(request, "creer_quiz.html", {
        "questions": questions,
        "theme": theme
    })


def generer_questions(theme):
    """
    Génère des questions pour un quiz sur un thème donné.
    
    Utilise le modèle de langage pour générer un ensemble de questions
    et réponses sur le thème spécifié.
    
    Args:
        theme (str): Le thème du quiz pour lequel générer des questions.
        
    Returns:
        list: Liste de dictionnaires contenant les questions et réponses générées.
    """
    try:
        llm = PleiadeLLM(api_key=config("API_KEY"))
        prompt_llm = f"""
Génère 5 questions de type réponse courte sur le thème : {theme}.
Pour chaque question, donne une bonne réponse claire et concise.
Retourne uniquement le tableau JSON suivant, sans rien ajouter autour :

[
  {{
    "question": "...",
    "bonneReponse": "..."
  }},
  ...
]
"""
        reponse = llm.complete(prompt_llm).text
        match = re.search(r"\[.*?\]", reponse, re.DOTALL)
        if match:
            questions = json.loads(match.group(0))
            return questions
        else:
            return []
    except Exception as e:
        print("Erreur génération questions :", e)
        return []




@login_required
def detail_quiz(request, quiz_id):
    """
    Affiche les détails d'un quiz spécifique.
    
    Args:
        request: La requête HTTP.
        quiz_id (int): L'identifiant du quiz à afficher.
        
    Returns:
        HttpResponse: La page de détail du quiz avec le contexte approprié.
    """  # ← bien mettre quiz_id ici !
    quiz = get_object_or_404(Quiz, id=quiz_id, utilisateur=request.user)
    questions = QuestionQuiz.objects.filter(quiz=quiz)
    return render(request, "detail_quiz.html", {
        "quiz": quiz,
        "questions": questions
    })




@login_required
def supprimer_quiz(request, quiz_id):
    """
    Supprime un quiz spécifique.
    
    Vérifie que l'utilisateur est le propriétaire du quiz
    avant de procéder à sa suppression.
    
    Args:
        request: La requête HTTP.
        quiz_id (int): L'identifiant du quiz à supprimer.
        
    Returns:
        HttpResponse: Redirection vers la page de prompt.
    """
    quiz = Quiz.objects.filter(id=quiz_id, utilisateur=request.user).first()
    if quiz:
        # supprimer d'abord le prompt lié
        if quiz.prompt:
            quiz.prompt.delete()
        # puis supprimer le quiz
        quiz.delete()
    return redirect("prompt")


@login_required
def lancer_quiz(request, quiz_id):
    """
    Gère la participation à un quiz.
    
    Cette vue permet à un utilisateur de répondre aux questions d'un quiz,
    enregistre ses réponses et gère sa progression.
    
    Args:
        request: La requête HTTP.
        quiz_id (int): L'identifiant du quiz à lancer.
        
    Returns:
        HttpResponse: La page du quiz avec la question actuelle ou le résultat final.
    """
    user = request.user
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all()
    total = questions.count()
    quizz = Quiz.objects.filter(utilisateur=user)
    scenarios = Scenario.objects.all()
    prompts = Prompt.objects.filter(quiz__isnull=True, user=user).order_by('-date_creation')

    progression, created = ProgressionQuiz.objects.get_or_create(utilisateur=user, quiz=quiz)

    if request.GET.get('restart') == '1':
        ReponseUtilisateur.objects.filter(utilisateur=user, questionQuiz__quiz=quiz).delete()
        progression.index_courant = 0
        progression.termine = False
        progression.save()
        return redirect("lancer_quiz", quiz_id=quiz.id)

    if progression.termine:
        reponses = ReponseUtilisateur.objects.filter(utilisateur=user, questionQuiz__quiz=quiz)
        score = reponses.filter(est_correcte=True).count()

        if not quiz.feedback_global or quiz.feedback_global.strip() == "":
            questions_reponses = []
            for i, r in enumerate(reponses, start=1):
                statut = "✅" if r.est_correcte else "❌"
                questions_reponses.append(
                    f"Question N°{i} : {r.questionQuiz.questionQuiz}\n"
                    f"Ta réponse : {r.reponseUtilisateur} {statut}\n"
                    f"Bonne réponse : {r.questionQuiz.bonneReponse}\n"
                )

            questions_reponses_str = "\n".join(questions_reponses)

            prompt_global = f"""
Voici les réponses d’un utilisateur à un quiz sur le thème "{quiz.titre}".

Pour **chaque question**, affiche le numéro, l’intitulé, la réponse de l’utilisateur, indique si elle est correcte ou non, et rappelle la bonne réponse.

Utilise ce format :

---
Question N°X : [texte de la question]  
Ta réponse : [réponse utilisateur] ✅ / ❌  
Bonne réponse : [bonne réponse]
---

À la fin, rédige un petit message global (2-3 phrases) pour l’encourager et lui donner des conseils de révision si nécessaire.

Voici les réponses :

{questions_reponses_str}
"""
            feedback_global = reponseAssistant([], prompt_global)
            quiz.feedback_global = feedback_global
            quiz.save()
        else:
            feedback_global = quiz.feedback_global

        return render(request, "lancer_quiz.html", {
            "quiz_termine": True,
            "quiz_actuel": quiz,
            "score": score,
            "total": total,
            "feedback_global": feedback_global,
            "quiz": quizz,
            "scenarios": scenarios,
            "prompts": prompts,
        })

    index = progression.index_courant

    if index >= total:
        progression.termine = True
        progression.save()
        return redirect("lancer_quiz", quiz_id=quiz.id)

    feedback = None
    afficher_feedback = False
    derniere_reponse = None
    question = questions[index]

    if request.method == "POST":
        reponse = request.POST.get("reponse")

        prompt_feedback = f"""
Voici une question et la réponse attendue.
Question : {question.questionQuiz}
Bonne réponse : {question.bonneReponse}
Réponse de l'utilisateur : {reponse}

Compare la réponse attendue et la réponse de l'utilisateur.
Si la réponse est correcte, commence par "Bonne réponse :" et explique pourquoi.
Sinon, commence par "Mauvaise réponse :" et explique l’erreur, puis donne la bonne réponse clairement.
Utilise un ton bienveillant et adresse-toi directement à l’utilisateur.
"""
        feedback = reponseAssistant([], prompt_feedback)
        afficher_feedback = True

        est_correcte = feedback.strip().lower().startswith("bonne réponse")
        derniere_reponse = ReponseUtilisateur.objects.create(
            utilisateur=user,
            questionQuiz=question,
            reponseUtilisateur=reponse,
            est_correcte=est_correcte
        )

        # ⚡ On n'avance pas ici. On reste sur la même question pour afficher le feedback.

    return render(request, "lancer_quiz.html", {
        "quiz_actuel": quiz,
        "question": question,
        "numero": index + 1,
        "total": total,
        "feedback": feedback,
        "afficher_feedback": afficher_feedback,
        "derniere_reponse": derniere_reponse,
        "quiz": quizz,
        "scenarios": scenarios,
        "prompts": prompts,
    })



@login_required
def quiz_suivant(request, quiz_id):
    """
    Passe à la question suivante d'un quiz.
    
    Met à jour l'index de progression de l'utilisateur dans le quiz.
    
    Args:
        request: La requête HTTP.
        quiz_id (int): L'identifiant du quiz.
        
    Returns:
        HttpResponse: Redirection vers la page du quiz.
    """
    quiz = get_object_or_404(Quiz, id=quiz_id)
    user = request.user
    progression = ProgressionQuiz.objects.get(utilisateur=user, quiz=quiz)

    progression.index_courant += 1
    progression.save()

    return redirect("lancer_quiz", quiz_id=quiz.id)




@login_required
def annuler_creation_quiz(request, quiz_id=None):
    """
    Annule la création d'un quiz en cours.
    
    Nettoie les données de session liées à la création du quiz
    et supprime le quiz s'il a déjà été créé en base de données.
    
    Args:
        request: La requête HTTP.
        quiz_id (int, optional): L'identifiant du quiz à supprimer. Defaults to None.
        
    Returns:
        HttpResponse: Redirection vers la page de prompt.
    """
    # Nettoyer les variables en session (toujours utile)
    request.session.pop("theme_quiz", None)
    request.session.pop("questions_quiz", None)

    # Si un quiz_id est fourni, c’est un quiz déjà créé (ex: quiz plus dur)
    if quiz_id:
        quiz = Quiz.objects.filter(id=quiz_id, utilisateur=request.user).first()
        if quiz:
            if quiz.prompt:
                quiz.prompt.delete()
            quiz.delete()

    return redirect("prompt")


def regenerer_quiz_plus_dur(request):
    if request.method in ["POST", "GET"]:
        if request.method == "POST":
            theme = request.POST.get("theme", "").strip()
            ancien_quiz_id = request.POST.get("quiz_id")  # 🛑 récupérer ID de l'ancien quiz
        else:
            theme = request.GET.get("theme", "").strip()
            ancien_quiz_id = request.GET.get("quiz_id")

        utilisateur = request.user
        redirect_preview = request.GET.get('redirect_preview')

        # 🔥 D'abord on supprime l'ancien quiz !
        if ancien_quiz_id:
            ancien_quiz = Quiz.objects.filter(id=ancien_quiz_id, utilisateur=utilisateur).first()
            if ancien_quiz:
                if ancien_quiz.prompt:
                    ancien_quiz.prompt.delete()
                ancien_quiz.delete()

        # Maintenant seulement on recrée le nouveau quiz
        titre_prompt = Truncator(f"Quiz difficile : {theme}").chars(100)
        titre_quiz = Truncator(f"Quiz difficile sur {theme}").chars(100)

        prompt = Prompt.objects.create(title=titre_prompt, user=utilisateur)
        quiz = Quiz.objects.create(titre=titre_quiz, utilisateur=utilisateur, prompt=prompt)

        try:
            llm = PleiadeLLM(api_key=config("API_KEY"))
            prompt_llm = f"""Génère 5 questions **plus difficiles** de type réponse courte sur le thème : {theme}.
            Format uniquement en JSON :
            [
              {{
                "question": "...",
                "bonneReponse": "..."
              }},
              ...
            ]"""

            reponse = llm.complete(prompt_llm).text
            match = re.search(r"\[.*?\]", reponse, re.DOTALL)
            if not match:
                raise ValueError("Pas de JSON détecté dans la réponse.")

            questions = json.loads(match.group(0))

            for q in questions:
                question = q.get("question", "")
                bonne_reponse = q.get("bonneReponse", "")
                QuestionQuiz.objects.create(
                    quiz=quiz,
                    questionQuiz=question,
                    bonneReponse=bonne_reponse
                )

            if redirect_preview:
                return redirect('preview_quiz_plus_dur', quiz.id)
            else:
                return redirect('lancer_quiz', quiz.id)

        except Exception as e:
            print("Erreur génération quiz plus difficile :", e)
            quiz.delete()
            prompt.delete()
            return redirect('prompt')
    
    else:
        return HttpResponseNotAllowed(["POST", "GET"])


@login_required
def preview_quiz_plus_dur(request, quiz_id):
    """
    Affiche un aperçu du quiz régénéré avec des questions plus difficiles.
    
    Args:
        request: La requête HTTP.
        quiz_id (int): L'identifiant du quiz original.
        
    Returns:
        HttpResponse: La page d'aperçu du quiz régénéré.
    """
    quiz = get_object_or_404(Quiz, id=quiz_id, utilisateur=request.user)
    questions = QuestionQuiz.objects.filter(quiz=quiz)

    if request.method == "POST":
        action = request.POST.get('action')
        if action == "lancer":
            return redirect('lancer_quiz', quiz.id)
        elif action == "regenerer":
            theme = quiz.titre.replace("Quiz difficile sur ", "").strip()
            return redirect(f"{reverse('regenerer_quiz_plus_dur')}?theme={theme}&quiz_id={quiz.id}&redirect_preview=1")

    return render(request, 'preview_quiz_plus_dur.html', {
        'quiz': quiz,
        'questions': questions,
    })
