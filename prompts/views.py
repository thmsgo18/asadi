import os
import re
from urllib.parse import urlencode
from io import BytesIO
from PIL import Image, ImageFont, ImageDraw
import markdown

from django.http import HttpResponse
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.safestring import mark_safe
from django.db.models import Max, F
from django.db.models.functions import Coalesce
from django.conf import settings
from datetime import date
from django.contrib import messages

from quiz.models import Quiz
from scenario.models import Scenario, ScenarioLance
from utilisateurs.models import Utilisateur
from workspace.models import Workspace
from .models import Prompt, Question, Reponse
from sentence_transformers import CrossEncoder
from rank_bm25 import BM25Okapi
from src.outils import preprocess
from src.api import generate_prompt_title, reponseAssistant

"""
Module de vues pour l'application prompts.

Module principal pour la gestion des prompts (conversations), la recherche de documents,
et diverses fonctionnalités liées aux utilisateurs comme la génération d'avatars et le changement de mot de passe.

Ce module contient les vues pour la gestion des prompts (conversations),
la recherche de documents, et diverses fonctionnalités liées aux utilisateurs
comme la génération d'avatars et le changement de mot de passe.
"""

# ─── Initialisation ChromaDB + Embeddings ─────────────────────────────────────────────────
"""
Initialisation de ChromaDB et des embeddings pour la recherche vectorielle.

Ce bloc configure le client ChromaDB, la fonction d'embedding et la collection
qui seront utilisés pour la recherche sémantique de documents.
"""
import chromadb
from chromadb.utils import embedding_functions

# 1) Client persistant (PersistentClient gère la persistence sans persist())
chroma_client = chromadb.PersistentClient(path=str(settings.CHROMA_DB_DIR))

# 2) EmbeddingFunction conforme à l'interface ChromaDB
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-mpnet-base-v2"
)



# 3) Création / récupération de la collection
collection = chroma_client.get_or_create_collection(
    name="asadi_collection",
    embedding_function=embedding_fn
)


# Partie pour gérer le retriever et le reranker
"""
Initialisation du modèle de reranking.

Ce modèle est utilisé pour réordonner les résultats de recherche en fonction
de leur pertinence par rapport à la requête de l'utilisateur.
"""
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")











# ────────────────────────────────────────────────────────────────────────────

def linkify_documents(text: str) -> str:
    """
    Convertit les références aux documents en liens cliquables et formate le texte en HTML.
    
    Cette fonction recherche les références aux documents dans le texte (format [[nom_fichier.ext]]),
    les convertit en liens HTML cliquables, puis applique un formatage Markdown au texte.
    
    Args:
        text (str): Le texte contenant potentiellement des références à des documents.
        
    Returns:
        str: Le texte formaté en HTML avec des liens cliquables vers les documents.
    """
    # S'assurer que text est une chaîne
    if text is None:
        text = ""
    else:
        text = str(text)
    media_root = str(settings.MEDIA_ROOT)
    media_url  = settings.MEDIA_URL.rstrip('/')
    exts   = ('.pdf', '.xlsx', '.docx')
    lookup = {}
    for root, _, fnames in os.walk(media_root):
        for fname in fnames:
            if fname.lower().endswith(exts):
                full = os.path.join(root, fname)
                rel  = os.path.relpath(full, media_root).replace(os.sep, '/')
                lookup[fname] = rel

    def normalize(s):
        return re.sub(r'[^0-9a-z]', '',
                      s.lower().replace(' ', '').replace('_', ''))

    def repl(match):
        raw = match.group(1)
        rel = lookup.get(raw)
        if rel is None:
            raw_norm = normalize(raw)
            for k, v in lookup.items():
                if normalize(k) == raw_norm:
                    rel = v
                    raw = k
                    break
        if rel is None:
            return raw
        url = f"{media_url}/{rel}"
        return f'<a href="{url}" target="_blank">{raw}</a>'
    
    # Étape 1: Pré-traitement du texte
    # Remplacer les liens de documents
    text = re.sub(r'\[\[([^\]]+\.(?:pdf|xlsx|docx))\]\]', repl, text)
    
    # S'assurer que les listes numérotées sont correctement formatées
    # Ajouter un espace après chaque numéro si nécessaire
    text = re.sub(r'^(\d+)\.(\S)', r'\1. \2', text, flags=re.MULTILINE)
    
    # Étape 2: Convertir le texte Markdown en HTML
    html = markdown.markdown(text, extensions=['extra', 'nl2br', 'sane_lists'])
    
    # Étape 3: Post-traitement du HTML
    # Corriger certains problèmes courants de mise en forme
    html = re.sub(r'<li>\s*<p>(.*?)</p>\s*</li>', r'<li>\1</li>', html)
    
    # Étape 4: Retourner le HTML sécurisé
    return mark_safe(html)

def hybrid_retrieve(query, n_results=8, workspace=None):
    """
    Effectue une recherche hybride (vectorielle et par mots-clés) sur les documents indexés.
    
    Cette fonction combine une recherche vectorielle (sémantique) et une recherche par mots-clés (BM25)
    pour trouver les documents les plus pertinents par rapport à la requête. Les résultats sont
    ensuite réordonnés par un modèle de reranking pour améliorer la pertinence.
    
    Args:
        query (str): La requête de recherche de l'utilisateur.
        n_results (int, optional): Nombre de résultats à retourner. Defaults to 8.
        workspace (str, optional): Filtre par espace de travail. Defaults to None.
        
    Returns:
        list: Liste de tuples (document, métadonnées) des documents les plus pertinents.
    """
    # 🔄 Charger corpus et BM25 dynamiquement
    docs_raw = collection.get(include=["documents", "metadatas"])
    corpus = docs_raw["documents"]
    metadatas = docs_raw["metadatas"]

    bm25 = None
    if corpus:
        tokenized_corpus = [preprocess(doc) for doc in corpus]
        bm25 = BM25Okapi(tokenized_corpus)

    query_embedding = embedding_fn([query])

    # 🔍 Recherche vectorielle
    vector_results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
        where={"workspace": workspace} if workspace else None
    )

    vector_chunks = []
    if vector_results.get("documents"):
        for doc, meta in zip(vector_results["documents"][0], vector_results["metadatas"][0]):
            vector_chunks.append((doc, meta))

    # 🔍 Recherche mots-clés avec BM25
    keyword_matches = []
    if bm25:
        tokenized_query = preprocess(query)
        scores = bm25.get_scores(tokenized_query)
        top_bm25_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:n_results]
        keyword_matches = [(corpus[i], metadatas[i]) for i in top_bm25_indices if scores[i] > 0]

    # 🔗 Fusionner sans doublons
    combined_chunks = vector_chunks + keyword_matches
    combined_chunks = list({doc: meta for doc, meta in combined_chunks}.items())
    combined_chunks = combined_chunks[:50]

    # 🔁 Reranking
    rerank_inputs = [[query, doc] for doc, _ in combined_chunks]
    if rerank_inputs:
        rerank_scores = reranker.predict(rerank_inputs)
        sorted_combined = sorted(zip(rerank_scores, combined_chunks), reverse=True)
        top_chunks = [(doc, meta) for score, (doc, meta) in sorted_combined[:4]]
    else:
        top_chunks = []

    return top_chunks






def prompt(request):
    """
    Vue principale pour la gestion des prompts (conversations) avec l'assistant.
    
    Cette vue gère la création, l'affichage et l'interaction avec les prompts.
    Elle traite les questions des utilisateurs, recherche les documents pertinents,
    et génère des réponses à l'aide du modèle de langage.
    
    Args:
        request: La requête HTTP.
        
    Returns:
        HttpResponse: La page de prompt avec le contexte approprié.
    """
    user      = request.user
    scenarios = Scenario.objects.all()
    quiz      = Quiz.objects.filter(utilisateur=user)

    if not user.is_authenticated:
        messages.error(request, "Veuillez vous connecter pour accéder au site !")
        return redirect('connexion')

    prompts = (
        Prompt.objects
        .filter(user=user, quiz__isnull=True)
        .annotate(
            last_activity=Coalesce(
                Max('questions__date_creation'),
                F('date_creation')
            )
        )
        .order_by('-last_activity')
    )

    group_names = list(user.groups.values_list("name", flat=True))
    # Récupérer le workspace sélectionné (GET ou POST)
    workspace_selected = request.GET.get("workspace") or request.POST.get("workspace")

    # suppression via ?delete=
    if request.method == "POST" and request.GET.get("delete"):
        Prompt.objects.filter(id=request.GET["delete"], user=user).delete()
        return redirect('prompt')

    prompt_id      = request.GET.get("prompt_id") or request.POST.get("prompt_id")
    current_prompt = Prompt.objects.filter(id=prompt_id, user=user).first() if prompt_id else None

    # nouveau prompt
    if request.method == "POST" and request.GET.get("new") == "true":
        p = Prompt.objects.create(user=user, title="Nouveau prompt")
        return redirect(f"{request.path}?prompt_id={p.id}")

    # envoi d'une question
    if request.method == "POST" and request.POST.get("prompt"):
        user_input = request.POST["prompt"]
        if not current_prompt:
            current_prompt = Prompt.objects.create(user=user, title="Nouveau prompt")

        question = Question.objects.create(
            prompt=current_prompt,
            questionPrompt=user_input
        )
        # Niveau: premier prompt de l'utilisateur
        total_q = Question.objects.filter(prompt__user=user).count()
        if total_q == 1 and (user.niveau or 0) < settings.MAX_NIVEAU:
            user.niveau = (user.niveau or 0) + 1
            user.save()

        # ─── pipeline RAG + LLM ─────────────────────────────────────────
        query_embeddings = embedding_fn([user_input])  # liste de 1 seul élément


        # Filtrer les contextes par workspace si sélectionné
# TEEEEEEEEST
        results = hybrid_retrieve(user_input, n_results=8, workspace=workspace_selected)



        # Si aucun document chargé, on ne fait pas appel au LLM
        if not results or not results[0][0]:
            raw_answer = "Aucun document chargé, je ne peux pas répondre."
        else:
            # Prépare l'historique
            history_messages = []
            for q in current_prompt.questions.order_by('date_creation'):
                history_messages.append({"role":"user",      "content":q.questionPrompt})
                if q.reponse:
                    history_messages.append({"role":"assistant", "content":q.reponse.rep})
            raw_answer = reponseAssistant(results, user_input, history_messages)
            if raw_answer is None:
                raw_answer = "Je n'ai pas pu obtenir de réponse du LLM. Veuillez réessayer plus tard."
        linked_answer = linkify_documents(raw_answer)
        # ────────────────────────────────────────────────────────────────

        llm_reponse      = Reponse.objects.create(rep=linked_answer)
        question.reponse = llm_reponse
        question.save()
        # Générer un titre dès la première question si le titre est par défaut
        if current_prompt.title == "Nouveau prompt":
            current_prompt.title = generate_prompt_title(user_input)
            current_prompt.save()
        # Conserver le filtre workspace dans l'URL après POST
        return redirect(f"{request.path}?prompt_id={current_prompt.id}{'&workspace='+workspace_selected if workspace_selected else ''}")

    questions  = current_prompt.questions.order_by('id') if current_prompt else None
    workspaces = Workspace.objects.all()

    # Calculer la largeur de la barre de progression (en %)
    progress_width = min(100, user.niveau * 100 // 20)

    return render(request, 'prompt.html', {
        'questions':         questions,
        'user':              user,
        'current_prompt':    current_prompt,
        'today':             date.today(),
        'prompts':           prompts,
        'group_names':       group_names,
        'scenarios':         scenarios,
        'quiz':              quiz,
        'workspaces':        workspaces,
        'selected_workspace': workspace_selected,
        'progress_width':    progress_width,
    })

@login_required
def changer_mot_de_passe(request):
    """
    Gère le changement de mot de passe d'un utilisateur.
    
    Cette vue affiche et traite le formulaire de changement de mot de passe.
    Elle vérifie que l'ancien mot de passe est correct et que le nouveau
    mot de passe respecte les critères de sécurité.
    
    Args:
        request: La requête HTTP.
        
    Returns:
        HttpResponse: La page de changement de mot de passe ou redirection.
    """
    if request.method == "POST":
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            return redirect('/prompts/?open=profil&msg=success')
        err = next(iter(form.errors.values()))[0] if form.errors else "Erreur ❌"
        return redirect(f"/prompts/?{urlencode({'open':'profil','msg':err})}")
    return redirect('/prompts/')






def avatar_png(request, username):
    """
    Génère un avatar PNG pour un utilisateur basé sur son nom d'utilisateur.
    
    Cette vue crée une image d'avatar avec les initiales de l'utilisateur
    sur un fond coloré déterminé par le nom d'utilisateur.
    
    Args:
        request: La requête HTTP.
        username (str): Le nom d'utilisateur pour lequel générer l'avatar.
        
    Returns:
        HttpResponse: L'image PNG de l'avatar avec le type MIME approprié.
    """
    user = get_object_or_404(Utilisateur, username=username)
    name = f"{user.prenom} {user.nom}".strip() or user.username
    initials = "".join(p[0] for p in name.split()[:2]).upper()

    size, bg, fg = 100, (84,213,208), (230,239,255)
    img = Image.new("RGB", (size,size), bg)
    draw = ImageDraw.Draw(img)
    draw.ellipse((0,0,size-1,size-1), fill=bg)
    try:
        font = ImageFont.truetype("/Library/Fonts/Arial.ttf", int(size*0.4))
    except OSError:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0,0), initials, font=font)
    w,h = bbox[2]-bbox[0], bbox[3]-bbox[1]
    x,y = (size-w)/2-bbox[0], (size-h)/2-bbox[1]
    draw.text((x,y), initials, font=font, fill=fg)

    buf = BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)
    return HttpResponse(buf, content_type="image/png")
