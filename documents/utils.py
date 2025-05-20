import os
import shutil
import tempfile
import zipfile

from django.conf import settings
from .models import Document
from workspace.models import Workspace
from src.ingererDonnee import ingest_documents

"""
Module d'utilitaires pour l'application documents.

Ce module fournit des fonctions utilitaires pour la gestion des documents,
notamment l'upload, l'extraction de fichiers ZIP, l'ingestion dans la base de données
vectorielle et l'attachement aux espaces de travail.
"""

def save_uploaded_file(fichier, workspace=None):
    """
    Sauvegarde un fichier uploadé dans le répertoire approprié.
    
    Args:
        fichier: Le fichier uploadé à sauvegarder.
        workspace (Workspace, optional): L'espace de travail associé au fichier. Defaults to None.
        
    Returns:
        tuple: Un tuple contenant (chemin absolu du fichier, chemin relatif pour la base de données).
    """
    if workspace:
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'documents', workspace.name)
        doc_path = f'documents/{workspace.name}/{fichier.name}'
    else:
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'documents')
        doc_path = f'documents/{fichier.name}'

    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, fichier.name)

    with open(file_path, 'wb+') as dest:
        for chunk in fichier.chunks():
            dest.write(chunk)

    return file_path, doc_path

def extract_zip(zip_path):
    """Extrait un fichier ZIP et retourne la liste des fichiers extraits.
    
    Args:
        zip_path (str): Chemin vers le fichier ZIP à extraire
        
    Returns:
        tuple: (liste des fichiers extraits, répertoire d'extraction)
        
    Raises:
        zipfile.BadZipFile: Si le fichier ZIP est corrompu
        Exception: Pour toute autre erreur d'extraction
    """
    try:
        # Vérifier que le fichier existe
        if not os.path.exists(zip_path):
            raise FileNotFoundError(f"Le fichier ZIP {zip_path} n'existe pas")
            
        # Vérifier que c'est bien un fichier ZIP
        if not zipfile.is_zipfile(zip_path):
            raise zipfile.BadZipFile(f"Le fichier {zip_path} n'est pas un fichier ZIP valide")
        
        # Créer un répertoire temporaire pour l'extraction
        extract_dir = tempfile.mkdtemp()
        
        # Extraire le fichier ZIP
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # Récupérer la liste des fichiers extraits
        extracted_files = []
        for root, _, files in os.walk(extract_dir):
            for file in files:
                # Ignorer les fichiers cachés et les fichiers système
                if not file.startswith('.') and not file.startswith('__MACOSX'):
                    extracted_files.append(os.path.join(root, file))
        
        if not extracted_files:
            print(f"Attention: Aucun fichier trouvé dans {zip_path}")
            
        return extracted_files, extract_dir
        
    except zipfile.BadZipFile as e:
        print(f"Erreur: Le fichier ZIP est corrompu - {e}")
        raise
    except Exception as e:
        print(f"Erreur lors de l'extraction du fichier ZIP: {e}")
        # Nettoyer le répertoire temporaire si une erreur se produit
        if 'extract_dir' in locals() and os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
        raise

def ingest_file(file_path, workspace=None):
    """
    Ingère un fichier dans la base de données vectorielle.
    
    Args:
        file_path (str): Chemin vers le fichier à ingérer.
        workspace (Workspace, optional): L'espace de travail associé au fichier. Defaults to None.
        
    Returns:
        tuple: Un tuple contenant (liste des chunks ingérés, liste des fichiers ignorés).
    """
    try:
        chunks, ignored_files = ingest_documents([file_path], workspace=workspace.name if workspace else None)
        if ignored_files or chunks is None or len(chunks) == 0:
            return False
        return True
    except Exception as e:
        print(f"⚠️ Erreur ingestion fichier {file_path}: {e}")
        return False

def clean_file(path):
    """
    Supprime un fichier s'il existe.
    
    Args:
        path (str): Chemin vers le fichier à supprimer.
        
    Returns:
        bool: True si le fichier a été supprimé, False sinon.
    """
    if os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)

def attach_document_to_workspace(file_path, workspace=None):
    """
    Attache un document à un workspace et copie physiquement le fichier vers le bon répertoire.
    
    Args:
        file_path (str): Chemin vers le fichier à attacher.
        workspace (Workspace, optional): Workspace auquel attacher le document. Defaults to None.
        
    Returns:
        Document: L'instance du document créé ou mis à jour.
    """
    file_name = os.path.basename(file_path)
    
    # Déterminer le répertoire de destination
    if workspace:
        dest_dir = os.path.join(settings.MEDIA_ROOT, 'documents', workspace.name)
        doc_path = f'documents/{workspace.name}/{file_name}'
    else:
        dest_dir = os.path.join(settings.MEDIA_ROOT, 'documents')
        doc_path = f'documents/{file_name}'
    
    # Créer le répertoire de destination s'il n'existe pas
    os.makedirs(dest_dir, exist_ok=True)
    
    # Chemin complet du fichier de destination
    dest_path = os.path.join(dest_dir, file_name)
    
    # Copier le fichier du répertoire temporaire vers le répertoire de destination
        # Copier le fichier du répertoire temporaire vers le répertoire de destination
    try:
        if os.path.abspath(file_path) != os.path.abspath(dest_path):
            shutil.copy2(file_path, dest_path)
            print(f"Fichier copié avec succès de {file_path} vers {dest_path}")
        else:
            print(f"Fichier déjà à sa place ({file_path}) – aucune copie nécessaire")
    except Exception as e:
        print(f"Erreur lors de la copie du fichier {file_path} vers {dest_path}: {e}")
        return False

    
    # Créer l'entrée dans la base de données
    doc = Document(nom=file_name)
    doc.fichier.name = doc_path
    doc.save()
    
    # Associer le document au workspace si nécessaire
    if workspace:
        workspace.document.add(doc)
        
    return True
