from django.contrib.auth.decorators import login_required, user_passes_test
from django.forms import inlineformset_factory
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods

from prompts.models import Prompt
from quiz.models import Quiz
from scenario.models import Scenario, QuestionReponse, ScenarioLance, ReponseUtilisateur
from scenario.forms import ScenarioForm, QuestionReponseForm
from django.conf import settings
from src.api import PleiadeLLM, reponseAssistant
from decouple import config

"""
Module de vues pour l'application scenario.

Ce module contient les vues pour la gestion des scénarios pédagogiques,
notamment la création, la modification, le lancement et la participation
aux scénarios.
"""

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

@login_required
def scenario_redirect(request):
    """
    Redirige vers le premier scénario disponible ou la page principale des scénarios.
    
    Args:
        request: La requête HTTP.
        
    Returns:
        HttpResponse: Redirection vers le premier scénario ou la page principale.
    """
    scenarios = Scenario.objects.all()
    if scenarios.exists():
        first_scenario = scenarios.first()
        return redirect('voir_scenario', pk=first_scenario.pk)
    else:
        return redirect('scenario')


@login_required
def scenario(request):
    """
    Vue principale pour la gestion des scénarios.
    
    Cette vue permet de rechercher, filtrer et créer des scénarios.
    Elle gère également le processus de création de scénario en plusieurs étapes.
    
    Args:
        request: La requête HTTP.
        
    Returns:
        HttpResponse: La page des scénarios avec le contexte approprié.
    """
    query = request.GET.get('q', '')
    filter_scenario = request.GET.get('filter_scenario', '')

    scenarios = Scenario.objects.all()

    if query:
        scenarios = scenarios.filter(titre__icontains=query)

    if filter_scenario:
        scenarios = scenarios.filter(id=filter_scenario)

    contexte = None
    titre = None

    if request.method == "POST":
        action = request.POST.get('action')

        if action == 'valider':
            titre = request.session.get('titre_scenario')
            contexte = request.session.get('contexte_scenario')

            if not titre or not contexte:
                return redirect('scenario')

            nouveau_scenario = Scenario.objects.create(titre=titre, contexte=contexte)
            del request.session['titre_scenario']
            del request.session['contexte_scenario']

            return redirect('voir_scenario', pk=nouveau_scenario.pk)


        elif action == 'regenerer':
            titre = request.session.get('titre_scenario')

            if titre:
                llm = PleiadeLLM(api_key=config("API_KEY"))
                prompt = f"Génère un court contexte (5 lignes maximum) pour un scénario intitulé : {titre}. Sois direct et précis."
                contexte = llm.complete(prompt).text.strip()
                request.session['contexte_scenario'] = contexte

                return render(request, "scenario.html", {
                    "form": ScenarioForm(initial={'titre': titre}),
                    "scenarios": scenarios,
                    "titre_genere": titre,
                    "contexte_genere": contexte,
                })

        else:
            form = ScenarioForm(request.POST)
            if form.is_valid():
                contexte_utilisateur = form.cleaned_data['contexte_utilisateur']

                llm = PleiadeLLM(api_key=config("API_KEY"))
                prompt = f"En te basant sur ce contexte : '{contexte_utilisateur}', génère un titre pertinent pour un scénario et un contexte détaillé (5 lignes maximum). Format de réponse : 'Titre: [titre généré]\nContexte: [contexte généré]'. Sois direct et précis."
                reponse = llm.complete(prompt).text.strip()
                
                # Extraire le titre et le contexte de la réponse
                try:
                    titre_partie = reponse.split('\nContexte:')[0]
                    contexte_partie = reponse.split('\nContexte:')[1]
                    
                    titre = titre_partie.replace('Titre:', '').strip()
                    contexte = contexte_partie.strip()
                except:
                    # Fallback si le format n'est pas respecté
                    titre = "Scénario généré"
                    contexte = reponse

                request.session['titre_scenario'] = titre
                request.session['contexte_scenario'] = contexte

                return render(request, "scenario.html", {
                    "form": ScenarioForm(),
                    "scenarios": scenarios,
                    "titre_genere": titre,
                    "contexte_genere": contexte,
                })

    # Si ce n’est pas POST, juste un GET classique : on renvoie la page vide avec les scénarios
    return render(request, "scenario.html", {
        "form": ScenarioForm(),
        "scenarios": scenarios,
    })


    
@login_required
@user_passes_test(est_admin)
def valider_scenario(request):
    """
    Valide et enregistre un nouveau scénario.
    
    Cette vue est réservée aux administrateurs et finalise la création
    d'un scénario en l'enregistrant dans la base de données.
    
    Args:
        request: La requête HTTP.
        
    Returns:
        HttpResponse: Redirection vers la page des scénarios.
    """
    titre = request.session.get('titre_scenario')
    contexte = request.session.get('contexte_scenario')

    if not titre or not contexte:
        return redirect('scenario')

    # Enregistrer le scénario
    scenario = Scenario.objects.create(titre=titre, contexte=contexte)

    # Nettoyer la session
    del request.session['titre_scenario']
    del request.session['contexte_scenario']

    return redirect('voir_scenario', pk=scenario.pk)

    

@login_required
def voir_scenario(request, pk):
    """
    Affiche les détails d'un scénario spécifique.
    
    Args:
        request: La requête HTTP.
        pk (int): L'identifiant du scénario à afficher.
        
    Returns:
        HttpResponse: La page de détail du scénario avec le contexte approprié.
    """
    scenarios = Scenario.objects.all()
    scenario = get_object_or_404(Scenario, pk=pk)
    questions_reponses = scenario.questions_reponses.all()
    query = request.GET.get('q', '')
    filter_scenario = request.GET.get('filter_scenario', '')

    if query:
        scenarios = scenarios.filter(titre__icontains=query)

    if filter_scenario:
        scenarios = scenarios.filter(id=filter_scenario)

    return render(request, 'voir_scenario.html', {
        'scenario': scenario,
        'scenarios': scenarios,
        'questions_reponses': questions_reponses,
        "query": query,
        "filter_scenario": filter_scenario,
    })


@login_required
@user_passes_test(est_admin)
def supprimer_scenario(request, scenario_id):
    """
    Supprime un scénario spécifique.
    
    Cette vue est réservée aux administrateurs.
    
    Args:
        request: La requête HTTP.
        scenario_id (int): L'identifiant du scénario à supprimer.
        
    Returns:
        HttpResponse: Redirection vers la page des scénarios.
    """
    scenario = Scenario.objects.filter(id=scenario_id).first()
    if not scenario:
        return redirect('scenario')
    scenario.delete()
    return redirect('scenario')



@login_required
@user_passes_test(est_admin)
def supprimer_question(request, question_id):
    """
    Supprime une question d'un scénario.
    
    Cette vue est réservée aux administrateurs.
    
    Args:
        request: La requête HTTP.
        question_id (int): L'identifiant de la question à supprimer.
        
    Returns:
        HttpResponse: Redirection vers la page de modification du scénario parent.
    """
    question = get_object_or_404(QuestionReponse, id=question_id)
    scenario_id = question.scenario.id
    question.delete()
    return redirect('voir_scenario', pk=scenario_id)



@login_required
@user_passes_test(est_admin)
def ajouter_question(request, scenario_id):
    """
    Ajoute une nouvelle question à un scénario existant.
    
    Cette vue est réservée aux administrateurs et gère le formulaire
    d'ajout de question, y compris la génération de questions par l'IA.
    
    Args:
        request: La requête HTTP.
        scenario_id (int): L'identifiant du scénario auquel ajouter la question.
        
    Returns:
        HttpResponse: La page d'ajout de question ou redirection.
    """

    scenario = get_object_or_404(Scenario, id=scenario_id)
    scenarios = Scenario.objects.all()
    query = request.GET.get('q', '')
    filter_scenario = request.GET.get('filter_scenario', '')

    if query:
        scenarios = scenarios.filter(titre__icontains=query)

    if filter_scenario:
        scenarios = scenarios.filter(id=filter_scenario)

     # --- POST ---
    if request.method == "POST":
        action = request.POST.get("action")

        # ⬇️  NOUVEAU  ➜ génération IA
        if action == "generate_ai":
            llm = PleiadeLLM(api_key=config("API_KEY"))

            prompt = f"""
Tu es un formateur RH.
Contexte du scénario : « {scenario.contexte} ».

Crée UNE question fermée (une phrase) et sa réponse attendue (un ou deux mots /
une très courte expression).  Formate ta sortie exactement ainsi :
QUESTION: <texte de la question>
REPONSE: <texte de la réponse>
"""
            raw = llm.complete(prompt).text.strip()

            # Parsing ultra-simple
            try:
                question_txt = raw.split("QUESTION:", 1)[1].split("REPONSE:", 1)[0].strip()
                reponse_txt = raw.split("REPONSE:", 1)[1].strip()
            except Exception:
                # si le LLM répond mal, on laisse l'utilisateur gérer
                question_txt, reponse_txt = "", ""

            # On pré-remplit le formulaire et on reste sur la page
            form = QuestionReponseForm(initial={
                "question": question_txt,
                "reponse":  reponse_txt
            })
            return render(request, "ajouter_question.html", {
                "form":      form,
                "scenario":  scenario,
                "scenarios": scenarios,
                "query":     request.GET.get('q', ''),
                "filter_scenario": request.GET.get('filter_scenario', ''),
                "ai_gen": True,   # pour un petit message éventuel
            })

        # ⬇️  branches existantes conservées
        form = QuestionReponseForm(request.POST)
        if form.is_valid():
            qr = form.save(commit=False)
            qr.scenario = scenario
            qr.save()

            if action == "add_finish":
                return redirect('voir_scenario', pk=scenario.id)
            return redirect('ajouter_question', scenario_id=scenario.id)

    # --- GET ---
    form = QuestionReponseForm()
    return render(request, "ajouter_question.html", {
        "form": form,
        "scenario": scenario,
        "scenarios": scenarios,
        "query": request.GET.get('q', ''),
        "filter_scenario": request.GET.get('filter_scenario', ''),
    })

@login_required
@user_passes_test(est_admin)
def modifier_question(request, question_id):
    """
    Modifie une question existante d'un scénario.
    
    Cette vue est réservée aux administrateurs et gère le formulaire
    de modification de question, y compris la génération de réponses par l'IA.
    
    Args:
        request: La requête HTTP.
        question_id (int): L'identifiant de la question à modifier.
        
    Returns:
        HttpResponse: La page de modification de question ou redirection.
    """
    question  = get_object_or_404(QuestionReponse, id=question_id)
    scenario  = question.scenario
    scenarios = Scenario.objects.all()

    query           = request.GET.get('q', '')
    filter_scenario = request.GET.get('filter_scenario', '')

    if query:
        scenarios = scenarios.filter(titre__icontains=query)
    if filter_scenario:
        scenarios = scenarios.filter(id=filter_scenario)

    # ───────── POST ─────────
    if request.method == "POST":
        action = request.POST.get("action")

        # --- NOUVEAU : génération IA --------------------------------------
        if action == "generate_ai":
            llm = PleiadeLLM(api_key=config("API_KEY"))

            prompt = f"""
Tu es formateur RH.
Contexte du scénario : « {scenario.contexte} ».

Voici la question actuelle :
QUESTION: {question.question}
REPONSE:  {question.reponse}

Propose une version améliorée de la question ET de la réponse,
toujours au même format :
QUESTION: ...
REPONSE: ...
et ne site pas de source.
"""
            raw = llm.complete(prompt).text.strip()

            try:
                q_txt = raw.split("QUESTION:", 1)[1].split("REPONSE:", 1)[0].strip()
                r_txt = raw.split("REPONSE:", 1)[1].strip()
            except Exception:
                q_txt, r_txt = question.question, question.reponse  # fallback

            form = QuestionReponseForm(initial={"question": q_txt,
                                                "reponse":  r_txt},
                                       instance=question)
            return render(request, "modifier_question.html", {
                "form":      form,
                "scenario":  scenario,
                "question":  question,
                "position":  list(scenario.questions_reponses.all()).index(question)+1,
                "scenarios": scenarios,
                "query":     query,
                "filter_scenario": filter_scenario,
                "ai_gen": True,
            })
        # ------------------------------------------------------------------

        # action par défaut : enregistrer
        form = QuestionReponseForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            return redirect('voir_scenario', pk=scenario.id)

    # ───────── GET ─────────
    form = QuestionReponseForm(instance=question)
    position = list(scenario.questions_reponses.all()).index(question) + 1

    return render(request, "modifier_question.html", {
        "form": form,
        "scenario": scenario,
        "question": question,
        "position": position,
        "scenarios": scenarios,
        "query": query,
        "filter_scenario": filter_scenario,
    })

def detail_question(request, question_id):
    scenarios = Scenario.objects.all()
    question = get_object_or_404(QuestionReponse, id=question_id)
    scenario = question.scenario
    questions = list(scenario.questions_reponses.all())
    position = questions.index(question) + 1 if question in questions else question.id
    query = request.GET.get('q', '')
    filter_scenario = request.GET.get('filter_scenario', '')

    if query:
        scenarios = scenarios.filter(titre__icontains=query)

    if filter_scenario:
        scenarios = scenarios.filter(id=filter_scenario)
    return render(request, 'detail_question.html', {
        'question': question,
        'scenario': scenario,
        'position': position,
        'scenarios': scenarios,
        "query": query,
        "filter_scenario": filter_scenario,
    })

@login_required
@user_passes_test(est_admin)
def modifier_scenario(request, scenario_id):
    """
    Modifie un scénario existant.
    
    Cette vue est réservée aux administrateurs et gère le formulaire
    de modification de scénario, y compris la gestion des questions associées.
    
    Args:
        request: La requête HTTP.
        scenario_id (int): L'identifiant du scénario à modifier.
        
    Returns:
        HttpResponse: La page de modification du scénario ou redirection.
    """
    scenarios = Scenario.objects.all()
    scenario = get_object_or_404(Scenario, id=scenario_id)

    query = request.GET.get('q', '')
    filter_scenario = request.GET.get('filter_scenario', '')

    if query:
        scenarios = scenarios.filter(titre__icontains=query)

    if filter_scenario:
        scenarios = scenarios.filter(id=filter_scenario)

    if request.method == "POST":
        action = request.POST.get('action')
        
        if action == 'generer':
            form = ScenarioForm(request.POST)
            if form.is_valid():
                titre = form.cleaned_data['titre']
                llm = PleiadeLLM(api_key=config("API_KEY"))
                prompt = f"Génère un court contexte (5 lignes maximum) pour un scénario intitulé : {titre}. Sois direct et précis."
                contexte = llm.complete(prompt).text.strip()

                request.session['titre_modification'] = titre
                request.session['contexte_modification'] = contexte

                form = ScenarioForm(initial={'titre': titre})
                return render(request, 'modifier_scenario.html', {
                    'form': form,
                    'scenario': scenario,
                    'scenarios': scenarios,
                    'nouveau_titre': titre,
                    'nouveau_contexte': contexte,
                    "query": query,
                    "filter_scenario": filter_scenario,
                })


        if action == 'regenerer':
            titre = request.POST.get('titre')
            if titre:
                llm = PleiadeLLM(api_key=config("API_KEY"))
                prompt = f"Génère un court contexte (5 lignes maximum) pour un scénario intitulé : {titre}. Sois direct et précis."
                contexte = llm.complete(prompt).text.strip()

                request.session['titre_modification'] = titre
                request.session['contexte_modification'] = contexte

                form = ScenarioForm(initial={'titre': titre})
                return render(request, 'modifier_scenario.html', {
                    'form': form,
                    'scenario': scenario,
                    'scenarios': scenarios,
                    'nouveau_titre': titre,
                    'nouveau_contexte': contexte,
                    "query": query,
                    "filter_scenario": filter_scenario,
                })

        elif action == 'valider':
            titre = request.session.get('titre_modification')
            contexte = request.session.get('contexte_modification')

            if titre and contexte:
                scenario.titre = titre
                scenario.contexte = contexte
                scenario.save()
                del request.session['titre_modification']
                del request.session['contexte_modification']
                return redirect('voir_scenario', pk=scenario.id)
    
    # 👇 C'est ici qu'on arrive S'IL N'Y A PAS DE POST OU PAS D'ACTION VALIDE
    form = ScenarioForm(instance=scenario)

    return render(request, 'modifier_scenario.html', {
        'form': form,
        'scenario': scenario,
        'scenarios': scenarios,
        "query": query,
        "filter_scenario": filter_scenario,
    })


def lancer_scenario(request, scenario_id):
    """
    Lance ou reprend un scénario pour l'utilisateur courant.
    
    Cette vue gère la participation à un scénario, notamment :
    - La remise à zéro de la session si l'admin a supprimé des questions
    - La suppression des réponses orphelines si des questions ont été retirées
    - La gestion du flag restart pour réinitialiser le scénario
    - L'enregistrement des réponses de l'utilisateur
    - La génération de feedback par l'IA
    
    Args:
        request: La requête HTTP.
        scenario_id (int): L'identifiant du scénario à lancer.
        
    Returns:
        HttpResponse: La page du scénario avec la question actuelle ou le résultat final.
    """
    user = request.user
    scenario = get_object_or_404(Scenario, id=scenario_id)
    questions = scenario.questions_reponses.all().order_by('id')
    total_questions = questions.count()

    # ────────────────────────────────────────────────────────────────────────
    # Récupération / création de la session utilisateur
    # ────────────────────────────────────────────────────────────────────────
    scenario_lance, _ = ScenarioLance.objects.get_or_create(
        scenario=scenario,
        utilisateur=user
    )

    # ────────────────────────────────────────────────────────────────────────
    # PATCH 1 : structure du scénario modifiée par l'admin
    # ────────────────────────────────────────────────────────────────────────
    if total_questions == 0:
        # plus aucune question : reset complet
        scenario_lance.reponses_utilisateur.all().delete()
        scenario_lance.termine = False
        scenario_lance.commentaire = None
        scenario_lance.save()
    else:
        # on supprime les réponses qui pointent vers des questions supprimées
        ids_valides = set(questions.values_list('id', flat=True))
        orphelines = scenario_lance.reponses_utilisateur.exclude(
            question_reponse_id__in=ids_valides
        )
        if orphelines.exists():
            orphelines.delete()
            scenario_lance.termine = False
            scenario_lance.commentaire = None
            scenario_lance.save()

    # ────────────────────────────────────────────────────────────────────────
    # RESET manuel demandé (?restart=true)
    # ────────────────────────────────────────────────────────────────────────
    if request.method == "POST" and "restart" in request.GET:
        scenario_lance.reponses_utilisateur.all().delete()
        scenario_lance.termine = False
        scenario_lance.commentaire = None
        scenario_lance.save()
        return redirect('lancer_scenario', scenario_id=scenario_id)

    # ────────────────────────────────────────────────────────────────────────
    # Construction de la progression
    # ────────────────────────────────────────────────────────────────────────
    reponses_existantes = scenario_lance.reponses_utilisateur.all().order_by(
        'question_reponse__id'
    )
    questions_repondues_ids = reponses_existantes.values_list(
        'question_reponse__id', flat=True
    )
    prochaine_question = questions.exclude(id__in=questions_repondues_ids).first()

    # marquer terminé si tout est répondu et pas encore tagué
    if not prochaine_question and not scenario_lance.termine and total_questions > 0:
        scenario_lance.termine = True
        scenario_lance.save()

    # ────────────────────────────────────────────────────────────────────────
    # POST : enregistrement d’une réponse utilisateur
    # ────────────────────────────────────────────────────────────────────────
    if request.method == 'POST' and "restart" not in request.GET:
        user_reponse = request.POST.get('user_reponse')
        question_id  = request.POST.get('question_id')

        if user_reponse and question_id:
            question_obj = get_object_or_404(QuestionReponse, id=question_id)

            reponse_utilisateur = ReponseUtilisateur.objects.create(
                scenario_lance=scenario_lance,
                question_reponse=question_obj,
                reponse=user_reponse
            )

            prompt_feedback = f"""
Tu es un professeur bienveillant.
Voici une question : \"{question_obj.question}\"
Voici la bonne réponse attendue : \"{question_obj.reponse}\"
Voici la réponse de l'utilisateur : \"{user_reponse}\"
Donne un feedback constructif, encourageant, clair, en maximum 2 phrases.
"""
            feedback_question = reponseAssistant([], prompt_feedback)
            reponse_utilisateur.feedback_llm = feedback_question
            reponse_utilisateur.save()

            # recyclage des variables après ajout
            reponses_existantes = scenario_lance.reponses_utilisateur.all().order_by(
                'question_reponse__id'
            )
            questions_repondues_ids = reponses_existantes.values_list(
                'question_reponse__id', flat=True
            )
            prochaine_question = questions.exclude(
                id__in=questions_repondues_ids
            ).first()

            if not prochaine_question:
                scenario_lance.termine = True
                scenario_lance.save()

    # ────────────────────────────────────────────────────────────────────────
    # Construction du contexte d’affichage
    # ────────────────────────────────────────────────────────────────────────
    context = {
        'scenario': scenario,
        'reponses_existantes': reponses_existantes,
        'total_questions': total_questions,
        'quiz': Quiz.objects.filter(utilisateur=user),
        'prompts': Prompt.objects.filter(
            quiz__isnull=True,
            user=user
        ).order_by('-date_creation'),
        'scenarios': Scenario.objects.all(),
    }

    # ────────────────────────────────────────────────────────────────────────
    # Quand la session est terminée : score + feedback global
    # ────────────────────────────────────────────────────────────────────────
    if scenario_lance.termine or total_questions == 0:
        bonnes_reponses = sum(
            1 for r in reponses_existantes
            if r.reponse.strip().lower() == r.question_reponse.reponse.strip().lower()
        )

        score = f"{bonnes_reponses}/{total_questions}" if total_questions > 0 else "–"

        if total_questions > 0 and not scenario_lance.commentaire:
            # ─── avant l'appel à reponseAssistant ─────────────────────────────
            liste_reponses = "\n".join(
                f"{'✅' if r.reponse.strip().lower() == r.question_reponse.reponse.strip().lower() else '❌'} {r.reponse}"
                for r in reponses_existantes
            )

            prompt_feedback_global = f"""
            Tu es un professeur bienveillant.

            Le scénario s'intitule : \"{scenario.titre}\".
            Voici les réponses de l'utilisateur :
            {liste_reponses}

            Ton rôle est de toujours encourager l'utilisateur, quel que soit son résultat.
            Donne un commentaire global très positif en 3 phrases maximum,
            en mettant en avant ses efforts, sa persévérance et ses points forts.
            N'utilise jamais de critiques, même légères.
            """
            feedback_global = reponseAssistant([], prompt_feedback_global)
            scenario_lance.commentaire = feedback_global
            scenario_lance.save()
        else:
            feedback_global = scenario_lance.commentaire

        context.update({
            'prochaine_question': None,
            'score': score,
            'commentaire': feedback_global,
        })

        # si plus aucune question, on ne montre que le contexte
        if total_questions == 0:
            context['score'] = None
            context['commentaire'] = None
    else:
        context['prochaine_question'] = prochaine_question

    return render(request, 'lancer_scenario.html', context)

@login_required
def redirection_scenario_utilisateur(request, scenario_id):
    """
    Redirige l'utilisateur vers la page appropriée d'un scénario.
    
    Cette vue détermine si l'utilisateur doit être redirigé vers la page
    de détail du scénario ou vers la page de lancement du scénario.
    
    Args:
        request: La requête HTTP.
        scenario_id (int): L'identifiant du scénario.
        
    Returns:
        HttpResponse: Redirection vers la page appropriée.
    """
    scenario = get_object_or_404(Scenario, id=scenario_id)
    ScenarioLance.objects.get_or_create(
        scenario=scenario,
        utilisateur=request.user
    )
    # --> on ne touche plus aux réponses ici
    return redirect('lancer_scenario', scenario_id=scenario.id)
