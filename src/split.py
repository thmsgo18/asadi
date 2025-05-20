from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from copy import deepcopy
import re

"""
Ce fichier python contient l'ensemble des fonctions qui permettent de séparer les chaines de caractères extraites des différents documents.
"""

def split_base(doc):
    """
    Fonction de base pour découper un document en chunks.
    
    Analyse la structure du document pour détecter des titres ou sections,
    puis segmente le texte en conséquence. Si aucune structure n'est détectée,
    utilise un découpage récursif par caractères.
    
    Args:
        doc (Document): Document Langchain à découper.
        
    Returns:
        list: Liste de Documents Langchain représentant les chunks.
    """
    chunks=[]
    texte = doc.page_content
    # Vérifier si le texte contient des titres (ex: "1. Introduction", "Chapitre X", "Article Y")
    if re.search(r"^\d+\.\s[A-Z]", texte, re.MULTILINE) or  "CHAPITRE" in texte.upper() or  re.search(r"ARTICLE\s+\d+", texte.upper()):
        # segmentation par titres
        sections = re.split(r"(\d+\.\s[A-Z].*|CHAPITRE\s+\d+.*|ARTICLE\s+\d+.*)", texte)
        sections = [s.strip() for s in sections if s.strip()]  # Supprimer espaces vides
        
        for i in range(0, len(sections), 2):  # On regroupe titre + contenu ensemble
            titre = sections[i] if i < len(sections) else ""
            contenu = sections[i+1] if i+1 < len(sections) else ""

            chunks.append(Document(
                page_content=f"{titre}\n{contenu}",
                metadata=doc.metadata
            ))
    else:
        # segmentation classique si pas de structure détectée
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,  #augmenter la taille des chunks
            chunk_overlap=150,  # augmenter le chevauchement pour éviter les coupures importantes
            length_function=len,
            add_start_index=True
        )
        chunks.extend(text_splitter.split_documents([doc]))

    return chunks

def split_textMd(doc, level="##", separator="*"):
    """
    Découpe un document Markdown en fonction des titres.
    
    Utilise les titres Markdown (##, ###, etc.) pour segmenter le document
    en sections logiques.
    
    Args:
        doc (Document): Document Markdown à découper.
        level (str, optional): Niveau de titre Markdown à utiliser comme séparateur. Defaults to "##".
        separator (str, optional): Séparateur additionnel. Defaults to "*".
        
    Returns:
        list: Liste de Documents Langchain représentant les chunks.
    """
    texte = doc.page_content
    chunks = []
    metadonnee = doc.metadata
    pattern = rf"({level} .*?\n)"
    parts = re.split(pattern, texte)

    chunks = []
    current_chunk = ""

    for part in parts:
        if part.startswith(level):
            if current_chunk.strip():
                chunks.append(
                    Document(
                        page_content=current_chunk.strip(),
                        metadata= metadonnee
                    )    
                )
                current_chunk = ""
            current_chunk += part
        else:
            current_chunk += part

    if current_chunk.strip():
        chunks.append(
            Document(
                page_content=current_chunk.strip(),
                metadata= metadonnee
            ) 
        )
    return chunks

    

def split_textExcel (doc, nombre_de_caracteres=1000):
    """
    Découpe un document Excel en chunks par feuille.
    
    Traite chaque feuille séparément et découpe le contenu en chunks
    de taille fixe, en préservant l'information sur la feuille d'origine.
    
    Args:
        doc (Document): Document Excel à découper.
        nombre_de_caracteres (int, optional): Taille maximale de chaque chunk. Defaults to 1000.
        
    Returns:
        list: Liste de Documents Langchain représentant les chunks.
    """
    texte = doc.page_content
    #print("TEXTE : \n",texte,"Fin texte\n")
    chunks = []
    metadonnee = deepcopy(doc.metadata)

    nomsFeuilles = doc.metadata.get("nomsFeuilles", "")
    nomsFeuilles = [nom.strip() for nom in nomsFeuilles.split(",")]

    contenu_feuilles = re.split("Feuille", texte)[1:] 

    #for i in contenu_feuilles: 
    #   print("DEB CONTENT\n",i,"FIN CONTENT\n")
    for num_feuille, feuille in enumerate(contenu_feuilles): 
        
        #print("FEUILLE DEB\n"*2,feuille,"FEUILLE STOP\n"*2)
        #print(len(feuilles),feuilles)
        #print("Numero FEUILLE : ",numFeuille,"nomsFeuilles : ",metadonnee["nomsFeuilles"])
        metadonnee["feuille_courante"] = nomsFeuilles[num_feuille]
        for i in range (0, len(feuille),nombre_de_caracteres):
            contenu = feuille[i:i+nombre_de_caracteres]
            chunks.append(Document(
                page_content=contenu,
                metadata= metadonnee
            ))
            #print(chunks,num_feuille)
            #print("\nCONTENT****",i,len(feuille),"****CONTENT,\n")
    #print(chunks)        
    return chunks


# Specialized splitting functions for important file types
def split_docx(doc):
    """
    Découpe un document Word (DOCX) en chunks.
    
    Détecte les titres et sections dans le document Word et
    segmente le texte en fonction de ces éléments structurels.
    
    Args:
        doc (Document): Document Word à découper.
        
    Returns:
        list: Liste de Documents Langchain représentant les chunks.
    """
    texte = doc.page_content
    chunks = []
    metadonnee = doc.metadata
    # Detect Word-like headings (e.g., "Heading 1", "Heading 2") by pattern
    pattern = r"(?:^|\n)(#+|\d+\.\d*|\bChapitre\b|\bSection\b).+"
    parts = re.split(pattern, texte, flags=re.IGNORECASE)

    current_chunk = ""
    for part in parts:
        current_chunk += part
        if len(current_chunk) > 700:
            chunks.append(
                Document(
                    page_content=current_chunk.strip(),
                    metadata=metadonnee
                )
            )
            current_chunk = ""
    if current_chunk.strip():
        chunks.append(
            Document(
                page_content=current_chunk.strip(),
                metadata=metadonnee
            )
        )
    return chunks

def split_pdf(doc):
    """
    Découpe un document PDF en chunks.
    
    Spécifique aux PDFs, cette fonction détecte les chapitres, articles
    et sections numérotées pour segmenter le document de manière logique.
    
    Args:
        doc (Document): Document PDF à découper.
        
    Returns:
        list: Liste de Documents Langchain représentant les chunks.
    """
    texte = doc.page_content
    chunks = []
    metadonnee = doc.metadata
    # Specific for PDFs: split at "Chapter", "Article", or numbered sections
    pattern = r"(?:^|\n)(Chapter\s+\d+|CHAPITRE\s+\d+|ARTICLE\s+\d+|\d+\.\d+)"
    parts = re.split(pattern, texte, flags=re.IGNORECASE)

    current_chunk = ""
    for part in parts:
        current_chunk += part
        if len(current_chunk) > 700:
            chunks.append(
                Document(
                    page_content=current_chunk.strip(),
                    metadata=metadonnee
                )
            )
            current_chunk = ""
    if current_chunk.strip():
        chunks.append(
            Document(
                page_content=current_chunk.strip(),
                metadata=metadonnee
            )
        )
    return chunks

def split_rtf(doc):
    """
    Découpe un document RTF en chunks.
    
    Utilise la fonction de découpage de base pour traiter les documents RTF
    comme du texte riche structuré.
    
    Args:
        doc (Document): Document RTF à découper.
        
    Returns:
        list: Liste de Documents Langchain représentant les chunks.
    """
    # Treat like structured rich text: fall back to general text split
    return split_base(doc)

def split_html(doc):
    """
    Découpe un document HTML en chunks.
    
    Détecte les balises de titre et de paragraphe pour segmenter
    le document HTML de manière logique.
    
    Args:
        doc (Document): Document HTML à découper.
        
    Returns:
        list: Liste de Documents Langchain représentant les chunks.
    """
    texte = doc.page_content
    chunks = []
    metadonnee = doc.metadata
    # HTML specific: split at headings or major breaks
    pattern = r"(?:^|\n)(<h[1-6]>.+?</h[1-6]>|<p>.+?</p>)"
    parts = re.split(pattern, texte, flags=re.IGNORECASE)

    current_chunk = ""
    for part in parts:
        current_chunk += part
        if len(current_chunk) > 700:
            chunks.append(
                Document(
                    page_content=current_chunk.strip(),
                    metadata=metadonnee
                )
            )
            current_chunk = ""
    if current_chunk.strip():
        chunks.append(
            Document(
                page_content=current_chunk.strip(),
                metadata=metadonnee
            )
        )
    return chunks


# Splitting for plain text files (.txt)
def split_txt(doc):
    """
    Découpe un document texte (TXT) en chunks.
    
    Segmente le texte en paragraphes délimités par des doubles sauts de ligne
    et crée des chunks de taille appropriée.
    
    Args:
        doc (Document): Document texte à découper.
        
    Returns:
        list: Liste de Documents Langchain représentant les chunks.
    """
    texte = doc.page_content
    chunks = []
    metadonnee = doc.metadata

    # Split the text into paragraphs by double newlines
    paragraphs = texte.split("\n\n")
    current_chunk = ""

    for paragraph in paragraphs:
        current_chunk += paragraph + "\n\n"
        if len(current_chunk) > 500:
            chunks.append(
                Document(
                    page_content=current_chunk.strip(),
                    metadata=metadonnee
                )
            )
            current_chunk = ""
    if current_chunk.strip():
        chunks.append(
            Document(
                page_content=current_chunk.strip(),
                metadata=metadonnee
            )
        )
    return chunks

# Splitting for CSV files (.csv)
def split_csv(doc):
    """
    Découpe un document CSV en chunks.
    
    Segmente le fichier CSV en blocs de 10 lignes pour faciliter
    le traitement et l'indexation.
    
    Args:
        doc (Document): Document CSV à découper.
        
    Returns:
        list: Liste de Documents Langchain représentant les chunks.
    """
    texte = doc.page_content
    chunks = []
    metadonnee = doc.metadata

    # Split CSV into blocks of 10 lines
    lines = texte.strip().split("\n")
    for i in range(0, len(lines), 10):
        chunk_lines = lines[i:i+10]
        chunk_text = "\n".join(chunk_lines)
        chunks.append(
            Document(
                page_content=chunk_text.strip(),
                metadata=metadonnee
            )
        )
    return chunks


# Splitting for PPTX files (.pptx)
def split_pptx(doc):
    """
    Découpe un document PowerPoint (PPTX) en chunks.
    
    Segmente la présentation par diapositive et découpe les diapositives
    trop longues en sous-chunks de taille appropriée.
    
    Args:
        doc (Document): Document PowerPoint à découper.
        
    Returns:
        list: Liste de Documents Langchain représentant les chunks.
    """
    texte = doc.page_content
    chunks = []
    metadonnee = doc.metadata

    # Split based on the slide markers "--- Slide X ---"
    parts = texte.split("--- Slide")
    for part in parts:
        part = part.strip()
        if part:
            slide_content = "--- Slide " + part if not part.startswith("--- Slide") else part
            if len(slide_content) > 700:
                for i in range(0, len(slide_content), 700):
                    sub_chunk = slide_content[i:i+700]
                    chunks.append(
                        Document(
                            page_content=sub_chunk.strip(),
                            metadata=metadonnee
                        )
                    )
            else:
                chunks.append(
                    Document(
                        page_content=slide_content.strip(),
                        metadata=metadonnee
                    )
                )
    return chunks