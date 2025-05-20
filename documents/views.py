import os
import zipfile
import tempfile
import shutil
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q

from src.ingererDonnee import ingest_documents, collection
from .models import Document
from workspace.models import Workspace
from ASADI.views import est_admin
from .utils import save_uploaded_file, extract_zip, ingest_file, clean_file, attach_document_to_workspace

"""
Module de vues pour l'application documents.

Ce module contient les vues pour la gestion des documents et des espaces de travail,
notamment l'upload, la suppression, la recherche et l'organisation des documents.
"""

@user_passes_test(est_admin)
def documents(request):
    """
    Vue principale pour la gestion des documents.
    
    Cette vue gère plusieurs actions :
    - Modification de l'espace de travail d'un document
    - Upload de fichiers (individuels ou archives ZIP)
    - Suppression de documents
    - Recherche et filtrage des documents
    
    La vue est réservée aux administrateurs et gère également l'indexation
    des documents dans ChromaDB pour la recherche vectorielle.
    
    Args:
        request: La requête HTTP.
        
    Returns:
        HttpResponse: La page de gestion des documents ou redirection.
    """
    # ───── Modif de workspace en POST « doc_id » ─────
    if request.method == 'POST' and 'doc_id' in request.POST and 'new_workspace' in request.POST:
        doc   = Document.objects.get(id=request.POST['doc_id'])
        new_ws_id = request.POST['new_workspace']

        # Retire de tous les anciens workspaces
        for ws in doc.workspaces.all():
            ws.document.remove(doc)

        if new_ws_id:
            new_ws = Workspace.objects.get(id=new_ws_id)
            new_ws.document.add(doc)
            old = os.path.join(settings.MEDIA_ROOT, str(doc.fichier))
            new_dir = os.path.join(settings.MEDIA_ROOT, 'documents', new_ws.name)
            os.makedirs(new_dir, exist_ok=True)
            if os.path.exists(old):
                new_path = os.path.join(new_dir, os.path.basename(doc.fichier.name))
                os.rename(old, new_path)
                doc.fichier.name = f'documents/{new_ws.name}/{os.path.basename(doc.fichier.name)}'
                doc.save()
                # Mettre à jour ChromaDB : suppression anciens chunks et réingestion
                try:
                    collection.delete(where={"source": doc.fichier.name})
                except Exception as e:
                    print(f"⚠️ Erreur suppression anciens chunks: {e}")
                ingest_documents([new_path], workspace=new_ws.name)
        else:
            # passe en dossier « documents/ »
            if doc.fichier:
                old_source = doc.fichier.name
                old = os.path.join(settings.MEDIA_ROOT, str(doc.fichier))
                new_dir = os.path.join(settings.MEDIA_ROOT, 'documents')
                os.makedirs(new_dir, exist_ok=True)
                if os.path.exists(old):
                    new_path = os.path.join(new_dir, os.path.basename(doc.fichier.name))
                    os.rename(old, new_path)
                    doc.fichier.name = f'documents/{os.path.basename(doc.fichier.name)}'
                    doc.save()
                    # Mettre à jour ChromaDB : suppression anciens chunks et réingestion
                    try:
                        collection.delete(where={"source": old_source})
                    except Exception as e:
                        print(f"⚠️ Erreur suppression anciens chunks: {e}")
                    ingest_documents([new_path], workspace=None)

        return redirect('documents')

    # ───── Upload en POST fichier ─────
    if request.method == 'POST' and 'fichier' in request.FILES:
        fichiers = request.FILES.getlist('fichier')
        workspace_id = request.POST.get('workspace')
        new_workspace_name = request.POST.get('new_workspace')
        workspace = None
        if new_workspace_name:
            workspace, _ = Workspace.objects.get_or_create(name=new_workspace_name)
        elif workspace_id:
            workspace = Workspace.objects.filter(id=workspace_id).first()

        failed_files = set()

        for f in fichiers:
            if f.name.lower().endswith('.zip'):
                temp_zip_path, _ = save_uploaded_file(f)
                extracted_files, extract_dir = extract_zip(temp_zip_path)

                for file_path in extracted_files:
                    if ingest_file(file_path, workspace):
                        attach_document_to_workspace(file_path, workspace)
                    else:
                        clean_file(file_path)
                        failed_files.add(os.path.basename(file_path))

                clean_file(temp_zip_path)
                clean_file(extract_dir)

            else:
                file_path, _ = save_uploaded_file(f, workspace)
                if ingest_file(file_path, workspace):
                    attach_document_to_workspace(file_path, workspace)
                else:
                    clean_file(file_path)
                    failed_files.add(f.name)

        if failed_files:
            return JsonResponse({'success': False, 'failed_files': list(failed_files)})
        else:
            return JsonResponse({'success': True})

    # ───── Suppression document ─────
    if request.method == 'POST' and 'delete_doc_id' in request.POST:
        document = get_object_or_404(Document, id=request.POST['delete_doc_id'])
        path = os.path.join(settings.MEDIA_ROOT, str(document.fichier))
        if os.path.isfile(path):
            os.remove(path)
        document.delete()
        return redirect('documents')

    # ───── Recherche / filtre / affichage ─────
    query           = request.GET.get('q', '')
    filter_workspace= request.GET.get('filter_workspace', '')
    fichiers        = Document.objects.all()

    if query:
        fichiers = fichiers.filter(Q(nom__icontains=query))
    if filter_workspace:
        fichiers = fichiers.filter(workspaces__id=filter_workspace)

    fichiers   = fichiers.order_by('nom')
    workspaces = Workspace.objects.all()

    return render(request, "documents.html", {
        "fichiers": fichiers,
        "query": query,
        "filter_workspace": filter_workspace,
        "workspaces": workspaces,
    })

@user_passes_test(est_admin)
def delete_document(request, doc_id):
    """
    Supprime un document et ses embeddings associés.
    
    Cette vue supprime le fichier physique du document, ses références dans la base de données
    et ses embeddings dans ChromaDB. Elle est réservée aux administrateurs.
    
    Args:
        request: La requête HTTP.
        doc_id (int): L'identifiant du document à supprimer.
        
    Returns:
        JsonResponse: Réponse JSON indiquant le succès ou l'échec de l'opération.
    """
    document = get_object_or_404(Document, id=doc_id)
    # 1) Supprime le fichier physique
    fichier_path = os.path.join(settings.MEDIA_ROOT, str(document.fichier))
    if os.path.isfile(fichier_path):
        os.remove(fichier_path)

    # 2) Supprime les embeddings dans ChromaDB
    #    On supprime tous les chunks dont la métadonnée "source" correspond au chemin relatif
    #    tel que tu l'as stocké dans `document.fichier.name`
    try:
        # ta collection importée depuis src.ingererDonnee
        from src.ingererDonnee import collection
        # on supprime par filtre
        collection.delete(where={"source": document.fichier.name})
    except Exception as e:
        # tu peux logger ou ignorer si la suppr. échoue
        print(f"⚠️ Erreur lors de la suppression dans ChromaDB : {e}")

    # 3) Supprime l’objet Django
    document.delete()
    return redirect('documents')

@user_passes_test(est_admin)
def delete_workspace(request):
    """
    Supprime un espace de travail et gère ses documents associés.
    
    Cette vue supprime un espace de travail et, selon l'option choisie, supprime
    ou déplace les documents associés. Elle est réservée aux administrateurs.
    
    Args:
        request: La requête HTTP contenant l'ID de l'espace de travail et l'option de traitement.
        
    Returns:
        JsonResponse: Réponse JSON indiquant le succès ou l'échec de l'opération.
    """
    if request.method == 'POST':
        ws_id = request.POST.get('ws_id')
        mode = request.POST.get('mode')  # 'keep' ou 'delete'

        try:
            ws = Workspace.objects.get(id=ws_id)
            documents = ws.document.all()

            if mode == 'keep':
                # Supprimer les chunks existants du workspace dans ChromaDB
                try:
                    collection.delete(where={"workspace": ws.name})
                except Exception as e:
                    print(f"⚠️ Erreur suppression chunks du workspace {ws.name}: {e}")
                for doc in documents:
                    ws.document.remove(doc)
                    old_path = os.path.join(settings.MEDIA_ROOT, str(doc.fichier))
                    new_dir = os.path.join(settings.MEDIA_ROOT, 'documents')
                    new_path = os.path.join(new_dir, os.path.basename(doc.fichier.name))
                    os.makedirs(new_dir, exist_ok=True)
                    if os.path.exists(old_path):
                        os.rename(old_path, new_path)
                        doc.fichier.name = f'documents/{os.path.basename(doc.fichier.name)}'
                        doc.save()
                        # Ré-ingérer les chunks dans ChromaDB avec workspace None
                        try:
                            ingest_documents([new_path], workspace=None)
                        except Exception as e:
                            print(f"⚠️ Erreur ré-ingestion du document {doc.nom}: {e}")
                ws.delete()

            elif mode == 'delete':
                # Supprimer tous les chunks associés au workspace dans ChromaDB
                try:
                    collection.delete(where={"workspace": ws.name})
                except Exception as e:
                    print(f"⚠️ Erreur suppression chunks du workspace {ws.name}: {e}")
                for doc in documents:
                    fichier_path = os.path.join(settings.MEDIA_ROOT, str(doc.fichier))
                    if os.path.isfile(fichier_path):
                        os.remove(fichier_path)
                    doc.delete()
                ws.delete()

            else:
                messages.error(request, "Action inconnue.")

            # 🔁 Supprimer le dossier physique du workspace
            workspace_path = os.path.join(settings.MEDIA_ROOT, 'documents', ws.name)
            if os.path.exists(workspace_path):
                import shutil
                shutil.rmtree(workspace_path)

        except Workspace.DoesNotExist:
            messages.error(request, "Ce workspace n'existe pas.")

    return redirect('documents')