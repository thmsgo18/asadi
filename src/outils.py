from typing import List
import os
import re
from llama_index.core.schema import Document as LlamaDocument
from langchain_core.documents import Document as LangchainDocument

"""
Module d'outils utilitaires pour le projet ASADI.

Ce module fournit diverses fonctions utilitaires pour la manipulation de fichiers,
le traitement de texte et la conversion entre différents formats de documents.
"""

def lister_fichiers(dossier: str, extensions: List[str] = None, recursive: bool = True) -> List[str]:
    """
    Liste tous les fichiers d'un dossier, avec option de filtre par extension et récursivité.
    
    Parcourt un dossier et retourne la liste des chemins vers les fichiers correspondant
    aux critères spécifiés (extensions et récursivité).
    
    Args:
        dossier (str): Le chemin du dossier à explorer.
        extensions (List[str], optional): Extensions des fichiers à inclure (ex: ['.pdf', '.md']).
        recursive (bool): Si True, explore aussi les sous-dossiers.

    Returns:
        List[str]: Liste des chemins vers les fichiers valides.
    """
    fichiers = []

    for root, dirs, files in os.walk(dossier):
        for file in files:
            if not extensions or os.path.splitext(file)[1].lower() in extensions:
                fichiers.append(os.path.join(root, file))
        if not recursive:
            break

    return fichiers

def preprocess(text):
    """
    Prétraite un texte en extrayant tous les mots en minuscules.
    
    Cette fonction utilise une expression régulière pour extraire tous les mots
    d'un texte et les convertit en minuscules.
    
    Args:
        text (str): Le texte à prétraiter.
        
    Returns:
        List[str]: Liste des mots extraits du texte, en minuscules.
    """
    return re.findall(r'\w+', text.lower())


def convert_langchain_to_llama(doc: LangchainDocument) -> LlamaDocument:
    """
    Convertit un document Langchain en document LlamaIndex.
    
    Cette fonction permet d'assurer la compatibilité entre les formats de documents
    utilisés par Langchain et LlamaIndex.
    
    Args:
        doc (LangchainDocument): Document au format Langchain à convertir.
        
    Returns:
        LlamaDocument: Document converti au format LlamaIndex.
    """
    return LlamaDocument(text=doc.page_content, metadata=doc.metadata)

