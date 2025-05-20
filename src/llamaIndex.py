from src.outils import lister_fichiers, convert_langchain_to_llama
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false" # pour éviter les forks pouvant provoquer des conflits
from extractions import get_text_from_any_pdf, est_pdf_scanne
from chargeFichier import pdfScanneLoad

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Document, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from api import PleiadeLLM
from typing import List
from decouple import config

"""
Module d'indexation et de recherche avec LlamaIndex.

Ce module permet de charger, indexer et interroger des documents à l'aide
de la bibliothèque LlamaIndex et du modèle de langage Pleiade.
"""





# Configuration des modèles pour LlamaIndex
Settings.embed_model = HuggingFaceEmbedding(
  model_name="sentence-transformers/all-MiniLM-L6-v2"
)

Settings.llm = PleiadeLLM(api_key=config("API_KEY"))


def chargeDocuments(cheminDocuments: List[str]):
    """
    Charge les documents à partir des chemins spécifiés.
    
    Cette fonction charge les documents depuis un répertoire et traite spécifiquement
    les PDF scannés qui nécessitent un traitement particulier.
    
    Args:
        cheminDocuments (List[str]): Liste des chemins vers les documents PDF à charger.
        
    Returns:
        List[Document]: Liste des documents chargés et convertis au format LlamaIndex.
    """
    # On sauvegarde l'ensemble des documents sous un format un peu particulier que l'on enregistre dans une variable documents
    documents = SimpleDirectoryReader(data_dir).load_data()
    print(len(documents)," intermeidiare longueur\n")
    for cheminDocument in cheminDocuments:
        if ".pdf" in cheminDocument:
            if est_pdf_scanne(cheminDocument):
                documentCourant = pdfScanneLoad(cheminDocument)
                documents.append(convert_langchain_to_llama(documentCourant))
    print("Longueur documents : ",len(documents))
    return documents



# Définition des chemins et répertoires
basedir = os.path.dirname(__file__)  # répertoire du script actuel
data_dir = os.path.abspath(os.path.join(basedir, "..", "media", "documents")) # On cherche les documents dans le dossier passé en param.

# Recherche des fichiers PDF dans le répertoire de données
cheminsDocumentsPdfs = lister_fichiers(data_dir, extensions=[".pdf"]) # Liste des documents PDF potentiellement problématiques
print(cheminsDocumentsPdfs)

# Chargement des documents
liste_documents = chargeDocuments(cheminsDocumentsPdfs) # Appel de la fonction pour charger tous les documents

# Création de l'index vectoriel et du moteur de requête
index = VectorStoreIndex.from_documents(liste_documents) # Vectorisation et sauvegarde des documents
query_engine = index.as_query_engine()

# Interface utilisateur simple pour tester le système
question = input("Pose ta question :")
response = query_engine.query(question)  # Interrogation sur les documents indexés
print(response)


## faire plus tard, un appel à openai pour pimper la requête de l'utilisateur
# penser à améliorer en utilisatn le cag
# tester la censure




