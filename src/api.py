from typing import Any
from pydantic import Field
from decouple import config
import time, requests
from llama_index.core.llms import (
    CustomLLM,
    CompletionResponse,
    CompletionResponseGen,
    LLMMetadata,
)
from llama_index.core.llms.callbacks import llm_completion_callback
from requests.exceptions import RequestException

"""
Module d'interface avec l'API Pleiade LLM.

Ce module permet de créer un type PleiadeLLM compatible avec LlamaIndex et fournit
des fonctions pour effectuer des requêtes au modèle de langage Pleiade.
"""

class PleiadeLLM(CustomLLM):
    """
    Classe d'interface avec l'API Pleiade compatible avec LlamaIndex.
    
    Cette classe permet d'utiliser le modèle de langage Pleiade avec l'écosystème LlamaIndex
    en implémentant les méthodes requises par l'interface CustomLLM.
    
    Attributes:
        api_key (str): Clé d'API pour l'authentification avec le service Pleiade.
        model_name (str): Nom du modèle à utiliser (par défaut "llama3.3:latest").
        url (str): URL de l'endpoint API Pleiade.
        context_window (int): Taille de la fenêtre de contexte en tokens.
        num_output (int): Nombre maximum de tokens en sortie.
    """
    api_key: str = Field(...)
    model_name: str = "llama3.3:latest"
    url: str = "https://pleiade.mi.parisdescartes.fr/api/chat/completions"
    context_window: int = 4096
    num_output: int = 512

    @property
    def metadata(self) -> LLMMetadata:
        """
        Fournit les métadonnées du modèle LLM.
        
        Returns:
            LLMMetadata: Objet contenant les métadonnées du modèle (taille de fenêtre, capacités, etc.).
        """
        return LLMMetadata(
            context_window=self.context_window,
            num_output=self.num_output,
            model_name=self.model_name,
            is_chat_model=True,
        )

    @llm_completion_callback()
    def complete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        """
        Envoie une requête de complétion au modèle Pleiade et retourne la réponse.
        
        Args:
            prompt (str): Le texte d'entrée à compléter par le modèle.
            **kwargs (Any): Arguments supplémentaires pour la requête.
            
        Returns:
            CompletionResponse: Réponse formatée contenant le texte généré.
            
        Raises:
            Exception: Si la requête échoue ou si le statut de réponse n'est pas 200.
        """
        headers = {
            "Authorization": f"Bearer sk-{self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": "Tu es un assistant intelligent qui répond à des questions administratives uniquement à partir des informations fournies. Tu fournis aussi la source de tes réponses, et tu précises quand tu ne peux pas répondre."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }

        start = time.time()
        try:
            response = requests.post(self.url, headers=headers, json=data, timeout=60)
        except RequestException as e:
            print(f"Erreur requête LLM : {e}")
            raise Exception(f"Erreur requête LLM : {e}")
        end = time.time()

        print(f"⏱ Temps de réponse : {end - start:.2f} secondes")

        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            return CompletionResponse(text=content)
        else:
            raise Exception(f"Erreur {response.status_code} : {response.text}")

    @llm_completion_callback()
    def stream_complete(self, prompt: str, **kwargs: Any) -> CompletionResponseGen:
        """
        Méthode de streaming de complétion (non implémentée pour Pleiade).
        
        Args:
            prompt (str): Le texte d'entrée à compléter par le modèle.
            **kwargs (Any): Arguments supplémentaires pour la requête.
            
        Returns:
            CompletionResponseGen: Générateur de réponse pour le streaming.
            
        Raises:
            NotImplementedError: Cette fonctionnalité n'est pas supportée par l'API Pleiade.
        """
        raise NotImplementedError("Le modèle Pleiade ne supporte pas le streaming.")


def reponseAssistant(results, query, history_messages=None):
    """
    Génère une réponse de l'assistant basée sur les résultats de recherche et la requête.
    
    Utilise l'API Pleiade pour générer une réponse contextuelle basée sur les résultats
    fournis et l'historique de conversation optionnel.
    
    Args:
        results (str): Résultats de recherche ou contexte à utiliser pour la réponse.
        query (str): Question ou requête de l'utilisateur.
        history_messages (list, optional): Historique des messages précédents. Defaults to None.
        
    Returns:
        str: Réponse générée par le modèle ou None en cas d'erreur.
    """
    url = "https://pleiade.mi.parisdescartes.fr/api/chat/completions"
    headers = {
        "Authorization": f"Bearer sk-{config('API_KEY')}",
        "Content-Type": "application/json"
    }

    system_prompt = """
    Tu es un assistant administratif et juridique qui répond **uniquement** à partir des extraits fournis. Ne complète rien avec tes connaissances.

    Structure impérative de ta réponse :

    1. 🧾 **Extrait(s) utile(s)** : Cite littéralement l'extrait du ou des documents. Indique systématiquement le nom du fichier source entre crochets, dans ce format : [[NomDuFichier.pdf]]

    2. ✅ **Réponse finale** : Donne une réponse claire, synthétique et conforme aux extraits.

    3. ❓ **Si l'information ne figure pas** dans les extraits : réponds uniquement "Je n’ai pas suffisamment d’informations dans les sources." sans ajouter d’explication ou d’invention.

    Ne commente jamais la source en langage naturel. Ne fais aucune inférence non justifiée. Ne cite jamais de texte qui n’est pas dans les extraits.
    """

  

    # On construit la liste des messages
    messages = [
        {"role": "system", "content": system_prompt},
    ]
    if history_messages:
        messages += history_messages

    # Enfin, le nouveau prompt utilisateur, avec le contexte RAG
    messages.append({
        "role": "user",
        "content": f"context :{results}, question : {query} ?"
    })

    print(messages)

    payload = {
        "model": "llama3.3:latest",
        "messages": messages,
        "temperature": 0.3
    }

    start_time = time.time()
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
    except RequestException as e:
        print(f"Erreur requête LLM : {e}")
        return None
    end_time = time.time()

    if response.status_code != 200:
        print(f"Erreur {response.status_code} : {response.text}")
        return None

    try:
        reponse_ia = response.json()["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        print("Erreur : Structure de réponse inattendue")
        return None

    print(f"Temps de réponse : {end_time - start_time:.2f} s")
    print(results)
    return reponse_ia






def resumeDocument(document):
    url = "https://pleiade.mi.parisdescartes.fr/api/chat/completions"
    headers = {
        "Authorization": f"Bearer sk-{config('API_KEY')}",
        "Content-Type": "application/json"
    }

    system_prompt = """
    Tu es un assistant expert en analyse de documents administratifs.

Ta mission est de lire un document administratif complet et d’en produire un **résumé clair, structuré et synthétique** qui pourra servir de chunk de résumé dans un système RAG (Retrieval-Augmented Generation).

Ce résumé doit :
- Être **compréhensible par une personne non spécialiste**
- Résumer en **un seul paragraphe (80 à 150 mots)** les **objectifs du document, les bénéficiaires concernés, les conditions ou critères mentionnés, les démarches à suivre et les éventuelles dates clés**
- Être **fidèle au contenu du document**, sans interprétation ni ajout
- Être **utile pour répondre à des requêtes générales** telles que : « À quoi sert ce document ? », « Qui est concerné ? », « Quelles sont les étapes de la procédure ? »
- Ne pas commencer par « Ce document explique… » ou « Le présent document… » → formule directe, factuelle
- Éviter les abréviations, sigles ou formulations trop techniques si une paraphrase claire est possible

Ne cite pas les annexes sauf si elles contiennent des informations essentielles à la compréhension du document.

Rédige un paragraphe unique, informatif, fluide et compact, prêt à être intégré dans une base de données vectorielle.

    """
  

    # On construit la liste des messages
    messages = [
        {"role": "system", "content": system_prompt},
    ]
 
    messages.append({
        "role": "user",
        "content": f"Document  : {document}"
    })

    payload = {
        "model": "llama3.3:latest",
        "messages": messages,
        "temperature": 0.3
    }

    start_time = time.time()
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
    except RequestException as e:
        print(f"Erreur requête LLM : {e}")
        return None
    end_time = time.time()

    if response.status_code != 200:
        print(f"Erreur {response.status_code} : {response.text}")
        return None

    try:
        reponse_ia = response.json()["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        print("Erreur : Structure de réponse inattendue")
        return None

    print(f"Temps de réponse : {end_time - start_time:.2f} s")
    return reponse_ia






def generate_prompt_title(first_question: str) -> str:
    """
    Génère un titre court pour une conversation basé sur la première question.
    
    Appelle le LLM Pleiade pour produire un titre concis et pertinent à partir
    de la première question d'une conversation.
    
    Args:
        first_question (str): La première question posée par l'utilisateur.
        
    Returns:
        str: Un titre court généré pour la conversation ou "Nouveau prompt" en cas d'échec.
    """
    url = "https://pleiade.mi.parisdescartes.fr/api/chat/completions"
    headers = {
        "Authorization": f"Bearer sk-{config('API_KEY')}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "llama3.3:latest",
        "messages": [
            {"role": "system","content": ("Tu es un assistant qui génère un titre court et pertinent pour " "une question administrative.")},
            {"role": "user","content": f"Propose-moi un titre bref pour cette question: «{first_question}»" "— et **sans** guillemets autour du titre."}
        ],
        "temperature": 0.3,
        # Possibilité de limiter le nombre de tokens pour rester sur un titre
        "max_tokens": 20
    }
    start = time.time()
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=60)
    except RequestException as e:
        print(f"Erreur requête LLM : {e}")
        return "Nouveau prompt"
    elapsed = time.time() - start

    if resp.status_code == 200:
        try:
            title = resp.json()["choices"][0]["message"]["content"].strip()
            return title
        except (KeyError, IndexError):
            pass
    # fallback en cas d'erreur
    return "Nouveau prompt"


def generate_quiz_title(theme: str) -> str:
    """
    Génère un titre attrayant pour un quiz basé sur son thème.
    
    Appelle le LLM Pleiade pour créer un titre accrocheur et original
    pour un quiz éducatif sur le thème spécifié.
    
    Args:
        theme (str): Le thème du quiz pour lequel générer un titre.
        
    Returns:
        str: Un titre accrocheur pour le quiz ou "Quiz sur {theme}" en cas d'échec.
    """
    url = "https://pleiade.mi.parisdescartes.fr/api/chat/completions"
    headers = {
        "Authorization": f"Bearer sk-{config('API_KEY')}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "llama3.3:latest",
        "messages": [
            {"role": "system","content": "Tu es un assistant qui génère des titres créatifs et engageants pour des quiz éducatifs."},
            {"role": "user","content": f"Crée un titre accrocheur et original pour un quiz sur le thème: '{theme}'. " 
                                    "Le titre doit être court (maximum 6 mots), captivant et donner envie de participer. " 
                                    "Ne mets pas de guillemets autour du titre et n'utilise pas l'expression 'Quiz sur...'"}
        ],
        "temperature": 0.7,  # Plus de créativité pour les titres de quiz
        "max_tokens": 15
    }
    start = time.time()
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=60)
    except RequestException as e:
        print(f"Erreur requête LLM : {e}")
        return f"Quiz sur {theme}"
    elapsed = time.time() - start

    if resp.status_code == 200:
        try:
            title = resp.json()["choices"][0]["message"]["content"].strip()
            # S'assurer que le titre n'est pas trop long
            if len(title) > 50:
                title = title[:47] + "..."
            return title
        except (KeyError, IndexError):
            pass
    # fallback en cas d'erreur
    return f"Quiz sur {theme}"


def pimp(query):
    """
    Améliore une requête utilisateur pour obtenir de meilleurs résultats.
    
    Utilise l'API Pleiade pour reformuler et enrichir une requête utilisateur
    afin d'améliorer les résultats de recherche.
    
    Args:
        query (str): La requête utilisateur à améliorer.
        
    Returns:
        str: La requête améliorée ou la requête originale en cas d'échec.
    """
    url = "https://pleiade.mi.parisdescartes.fr/api/chat/completions"
    headers = {
        "Authorization": f"Bearer sk-{config('API_KEY')}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama3.3:latest",
        "messages": [
            {"role": "system", "content": "Tu es chargé de retourner un prompt plus adéquat à une recherche rag, sans pour autant dénaturer son sens pour que l'utilisateur ai sa réponse demandé. À titre d'exemple tu vas éliminer les fautes d'orthographes et de syntaxe. Retourne le prompt modifié uniquement et n'ajoute pas de contexte,juste le prompt. Précise dans quels documents tu as cherché tes informations "},
            {"role": "user", "content": f"question : {query} ?"}
        ],
        "temperature": 0.7
    }
    start_time = time.time()
    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
    except RequestException as e:
        print(f"Erreur requête LLM : {e}")
        return 
    end_time = time.time()

    if response.status_code == 200:
        try:
            # Extraire la réponse de l'IA
            reponse_ia = response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            print("Erreur : Structure de réponse inattendue")
    else:
        print(f"Erreur {response.status_code} : {response.text}")
        return 
    
    print(f"Temps de réponse : {end_time - start_time:.2f} secondes")
    return reponse_ia
