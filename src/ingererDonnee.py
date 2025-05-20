from striprtf.striprtf import rtf_to_text
import chromadb
from django.conf import settings
from .chargeFichier import excelLoad, mdLoad, docxLoad, pdfScanneLoad, pdfNonScanneLoad, rtfLoad, htmlLoad, txtLoad, csvLoad, pptxLoad
from .split import split_textMd, split_textExcel, split_csv, split_docx, split_html, split_pdf, split_rtf, split_txt, split_pptx
from sentence_transformers import SentenceTransformer
from langchain.schema import Document

from .api import resumeDocument
from .extractions import est_pdf_scanne
import os
from pathlib import Path
from typing import List, Optional
import subprocess
import sys

"""
Module d'ingestion de documents pour la base de données vectorielle.

Ce module permet de charger des documents de différents formats,
de les segmenter en chunks, et de les stocker dans une base de données
vectorielle ChromaDB pour la recherche sémantique.

Ce fichier python nous permet d'appeler la bonne fonction de chargeFichiers 
en fonction du type du document.
"""

chroma_client = chromadb.PersistentClient(path=str(settings.CHROMA_DB_DIR))
collection = chroma_client.get_or_create_collection("asadi_collection")  # ici une collection c'est plus ou moins une table en sql

model_embedding = SentenceTransformer("all-mpnet-base-v2")


def chargeDocuments(cheminDocuments: List[str]):
    """
    Charge et segmente des documents de différents formats.
    
    Détermine automatiquement le type de chaque document en fonction de son extension
    et utilise les fonctions appropriées pour le chargement et la segmentation.
    
    Args:
        cheminDocuments (List[str]): Liste des chemins vers les documents à charger.
        
    Returns:
        tuple: Un tuple contenant (liste des chunks générés, liste des fichiers ignorés).
    """
    chunks = []
    ignored_files = []
    for cheminDocument in cheminDocuments:
        print("chemin : ", cheminDocument)
        cheminDocumentLower = cheminDocument.lower()
        documentCourant = None
        documentResumee = None

        try:
            if cheminDocumentLower.endswith(".xlsx"):
                documentCourant = excelLoad(cheminDocument)
                chunks.extend(split_textExcel(documentCourant))

            elif cheminDocumentLower.endswith(".md"):
                documentCourant = mdLoad(cheminDocument)
                chunks.extend(split_textMd(documentCourant))

            elif cheminDocumentLower.endswith(".docx") or cheminDocumentLower.endswith(".doc"):
                if cheminDocumentLower.endswith(".doc"):
                    cheminDocument = convert_doc_to_docx(cheminDocument)
                documentCourant = docxLoad(cheminDocument)
                chunks.extend(split_docx(documentCourant))

            elif cheminDocumentLower.endswith(".pdf"):
                if est_pdf_scanne(cheminDocument):
                    documentCourant = pdfScanneLoad(cheminDocument)
                else:
                    documentCourant = pdfNonScanneLoad(cheminDocument)
                chunks.extend(split_pdf(documentCourant))

            elif cheminDocumentLower.endswith(".rtf"):
                documentCourant = rtfLoad(cheminDocument)
                chunks.extend(split_rtf(documentCourant))

            elif cheminDocumentLower.endswith(".html") or cheminDocumentLower.endswith(".htm"):
                documentCourant = htmlLoad(cheminDocument)
                chunks.extend(split_html(documentCourant))

            elif cheminDocumentLower.endswith(".txt"):
                documentCourant = txtLoad(cheminDocument)
                chunks.extend(split_txt(documentCourant))

            elif cheminDocumentLower.endswith(".csv"):
                documentCourant = csvLoad(cheminDocument)
                chunks.extend(split_csv(documentCourant))

            elif cheminDocumentLower.endswith(".pptx"):
                documentCourant = pptxLoad(cheminDocument)
                chunks.extend(split_pptx(documentCourant))

            else:
                print(f"⚠️ Fichier ignoré (type non supporté) : {cheminDocument}")
                ignored_files.append(os.path.basename(cheminDocument))
                continue

            # ➕ Résumé
            if documentCourant:
                documentResumee = resumeDocument(documentCourant.page_content)
                metadata = documentCourant.metadata.copy()
                metadata["chunk_index"] = -1
                metadata["is_summary"] = True
                resume_chunk = Document(
                    page_content=documentResumee,
                    metadata=metadata
                )
                chunks.insert(0, resume_chunk)

        except Exception as e:
            print(f"⚠️ Erreur lors du traitement de {cheminDocument} : {e}")
            ignored_files.append(os.path.basename(cheminDocument))

    print(f"Segmenté {len(cheminDocuments)} documents en {len(chunks)} chunks.")
    return chunks, ignored_files


def convert_doc_to_docx(doc_path: str) -> str:
    """
    Convertit un fichier .doc en .docx en utilisant LibreOffice (soffice).
    
    Args:
        doc_path (str): Chemin vers le fichier .doc à convertir.
        
    Returns:
        str: Chemin vers le fichier .docx généré.
        
    Raises:
        FileNotFoundError: Si la conversion échoue.
    """
    output_dir = os.path.dirname(doc_path)
    subprocess.run([
        "soffice", "--headless", "--convert-to", "docx", doc_path, "--outdir", output_dir
    ], check=True)
    
    base = os.path.splitext(doc_path)[0]
    docx_path = f"{base}.docx"
    if not os.path.exists(docx_path):
        raise FileNotFoundError(f"Conversion échouée pour {doc_path}")
    return docx_path

def ingest_documents(file_paths: List[str], workspace: Optional[str] = None, record_progress=None):
    """
    Ingère des documents dans la base de données vectorielle.
    
    Charge, segmente et stocke les documents dans ChromaDB avec leurs embeddings.
    Peut suivre la progression de l'ingération si un objet de suivi est fourni.
    
    Args:
        file_paths (List[str]): Liste des chemins vers les fichiers à ingérer.
        workspace (Optional[str], optional): Espace de travail associé aux documents. Defaults to None.
        record_progress: Objet pour suivre la progression de l'ingération. Defaults to None.
        
    Returns:
        tuple: Un tuple contenant (liste des chunks ingérés, liste des fichiers ignorés).
    """
    file_chunks_map = {}
    total_chunks = 0
    ignored_files = []
    for fp in file_paths:
        chunks, ignored = chargeDocuments([fp])
        file_chunks_map[fp] = chunks
        total_chunks += len(chunks)
        ignored_files.extend(ignored)
    if record_progress:
        record_progress.set_progress(0, total_chunks)

    done = 0
    for fp, chunks in file_chunks_map.items():
        for i, chunk in enumerate(chunks):
            meta = chunk.metadata.copy()
            rel = os.path.relpath(fp, settings.MEDIA_ROOT).replace(os.sep, "/")
            meta["source"] = rel
            if "start_index" in meta:
                metadata_raw = {
                    "source": meta["source"],
                    "chunk_index": i,
                    "start_index": meta["start_index"],
                    "workspace": workspace,
                }
            else:
                meta["chunk_index"] = i
                meta["workspace"] = workspace
                metadata_raw = meta

            metadata = {
                k: (v if v is not None else "")
                for k, v in metadata_raw.items()
            }

            embedding = model_embedding.encode(chunk.page_content).tolist()
            chunk_id = f"{metadata.get('source', 'unknown')}_chunk_{i}"

            collection.upsert(
                ids=[chunk_id],
                documents=[chunk.page_content],
                metadatas=[metadata],
                embeddings=[embedding],
            )

            done += 1
            if record_progress:
                record_progress.set_progress(done, total_chunks)

    # After upserting all chunks
    all_chunks = []
    for chunks in file_chunks_map.values():
        all_chunks.extend(chunks)

    return all_chunks, ignored_files

def ingest_all_documents(base_dir: str) -> None:
    """
    Parcourt tous les fichiers du dossier base_dir et les ingère.
    
    Le nom du sous-dossier après base_dir est utilisé comme nom d'espace de travail
    pour l'organisation des documents dans la base de données vectorielle.
    
    Args:
        base_dir (str): Répertoire de base contenant les documents à ingérer.
        
    Returns:
        None
    """
    p = Path(base_dir)
    files = [str(f) for f in p.rglob("*.*") if f.is_file()]
    to_ingest = []  # on pourrait filtrer ici si besoin

    for f in files:
        rel_parts = Path(f).relative_to(p).parts
        ws = rel_parts[0] if len(rel_parts) > 1 else None
        ingest_documents([f], ws)

if __name__ == "__main__":
    basedir = os.path.dirname(__file__)
    data_dir = os.path.abspath(os.path.join(basedir, "..", "media", "documents"))
    ingest_all_documents(data_dir)