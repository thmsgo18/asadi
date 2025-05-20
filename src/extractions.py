import pdfplumber
from docx import Document
import pandas as pd 
import re
from pdf2image import convert_from_path
import pytesseract
import fitz  # PyMuPDF

"""
Module d'extraction de texte à partir de différents formats de documents.

Ce module fournit diverses fonctions pour extraire le texte de documents
de différents formats (PDF, DOCX, XLSX, etc.) et déterminer si un PDF est scanné.
"""

def convert_from_pdf(lien_pdf):
    """
    Convertit un fichier PDF en une liste d'images.
    
    Args:
        lien_pdf (str): Chemin vers le fichier PDF à convertir.
        
    Returns:
        List[Image]: Liste des images correspondant aux pages du PDF.
    """
    return convert_from_path(lien_pdf)


def convert_image_to_text(file):
    """
    Extrait le texte d'une image à l'aide d'OCR (Reconnaissance Optique de Caractères).
    
    Args:
        file (Image): L'image à partir de laquelle extraire le texte.
        
    Returns:
        str: Le texte extrait de l'image.
    """
    # gray_image = image.convert("L")  # Convertir en niveaux de gris
    text = pytesseract.image_to_string(file)
    return text


def get_text_from_any_pdf(lien_pdf):
    """
    Extrait le texte d'un fichier PDF en utilisant l'OCR.
    
    Cette fonction est particulièrement utile pour les PDF scannés
    qui ne contiennent pas de texte directement extractible.
    
    Args:
        lien_pdf (str): Chemin vers le fichier PDF.
        
    Returns:
        str: Le texte extrait du PDF.
    """
    pages = convert_from_pdf(lien_pdf)
    texteFinale = ""
    
    for img in pages:
        page_text = convert_image_to_text(img) 
        if page_text:
            texteFinale += page_text  
    return texteFinale


def extraireTextPlumber(cheminPdf):
    """
    Extraction de texte d'un PDF non scanné avec conservation de la structure.
    
    Utilise la bibliothèque pdfplumber pour extraire le texte d'un PDF
    en préservant au mieux la structure du document.
    
    Args:
        cheminPdf (str): Chemin vers le fichier PDF à traiter.
        
    Returns:
        str: Le texte extrait du PDF avec structure préservée.
    """
    texte_complet = ""
    
    with pdfplumber.open(cheminPdf) as pdf:
        for page in pdf.pages:
            texte = page.extract_text()
            if texte:
                texte_complet += texte + "\n\n"  # Ajouter des sauts de ligne pour préserver la structure
                
    return texte_complet.strip()




# méhode pur extraire des tableaux d'un pdf non scanné (meilleur bibliothèque pour cette extraction précise)
def extraireTableauxPdf(cheminPdf):
    """
    Extraction des tableaux et conversion en format texte structuré.
    
    Utilise pdfplumber pour extraire spécifiquement les tableaux d'un PDF
    et les convertir en texte structuré avec délimiteurs.
    
    Args:
        cheminPdf (str): Chemin vers le fichier PDF contenant des tableaux.
        
    Returns:
        str: Texte structuré représentant les tableaux extraits, ou chaîne vide si aucun tableau n'est trouvé.
    """
    res = []
    
    with pdfplumber.open(cheminPdf) as pdf:
        for i, page in enumerate(pdf.pages):
            tableau = page.extract_table()
            if tableau:
                texte_tableau = "\n".join([" | ".join(str(cell) if cell is not None else "" for cell in row) for row in tableau if row]
)
                res.append(f"Tableau (Page {i+1}):\n{texte_tableau}\n")
    
    return "\n\n".join(res) if res else ""


#ne pas s'en servir pour le moment, ça perturbe le rag
def clean_text(text):
    """
    Nettoie un texte en supprimant les caractères spéciaux et les espaces multiples.
    
    Note: Cette fonction n'est pas recommandée pour le RAG car elle peut perturber les résultats.
    
    Args:
        text (str): Texte à nettoyer.
        
    Returns:
        str: Texte nettoyé en minuscules.
    """
    text = re.sub(r"\s+", " ", text)  # Supprime les espaces multiples
    text = re.sub(r"[^a-zA-Z0-9éèêàùçâôûïü'’ ]", "", text)  # Supprime caractères spéciaux
    return text.strip().lower()



def extraireXLSX(cheminXlsx):
    """
    Extrait le contenu d'un fichier Excel au format texte.
    
    Parcourt toutes les feuilles du fichier Excel et convertit
    les données en texte structuré ligne par ligne.
    
    Args:
        cheminXlsx (str): Chemin vers le fichier Excel à traiter.
        
    Returns:
        tuple: Contient (texte extrait, liste des noms de feuilles).
    """
    # sheet = feuille au cas où 
    text=""
    xls = pd.ExcelFile(cheminXlsx)
    for sheet in xls.sheet_names:
        df = xls.parse(sheet)
        text += f"Feuille: {sheet}\n" if sheet else ""
        for ligne, colonne in df.iterrows():
            texte_colonne = ", ".join([f"{col}: {colonne[col]}" for col in df.columns])
            text += f"Ligne {ligne + 1}: {texte_colonne}\n"

    return (text, xls.sheet_names) 


def extraireDOCX(cheminDocx):
    """
    Extrait le texte d'un fichier Word (DOCX).
    
    Récupère le texte de tous les paragraphes non vides du document Word.
    
    Args:
        cheminDocx (str): Chemin vers le fichier Word à traiter.
        
    Returns:
        str: Texte extrait du document Word.
    """
    # Pour les fichiers Word
    doc = Document(cheminDocx)
    texte_complet = "\n\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    return texte_complet.strip()


def extraire_text_md_Et_txt(cheminFichier):
    """
    Extrait le contenu de fichiers texte (TXT) ou Markdown (MD).
    
    Lit simplement le contenu du fichier en supposant un encodage UTF-8.
    
    Args:
        cheminFichier (str): Chemin vers le fichier texte ou markdown.
        
    Returns:
        str: Contenu du fichier sans espaces superflus.
    """
    with open(cheminFichier, 'r', encoding='utf-8') as fichier:
        texte = fichier.read()
    return texte.strip()



def est_pdf_scanne(chemin_pdf: str) -> bool:
    """
    Détermine si un PDF est scanné en vérifiant la présence de texte extractible.
    
    Un PDF est considéré comme scanné s'il ne contient pas de texte extractible
    directement (c'est-à-dire qu'il s'agit d'une image sans couche de texte).
    
    Args:
        chemin_pdf (str): Chemin vers le fichier PDF à analyser.
        
    Returns:
        bool: True si le PDF est scanné, False sinon.
    """    
    doc = fitz.open(chemin_pdf)
    for page in doc:
        texte = page.get_text()
        if texte.strip():  # du texte détecté
            return False  # donc pas scanné
    return True  

"""
import os

# Chemin absolu vers le fichier, basé sur l'emplacement du script
basedir = os.path.dirname(__file__)
chemin_pdf = os.path.join(basedir, "..", "data", "CR_Algo1.pdf")
chemin_pdf = os.path.abspath(chemin_pdf)

print(est_pdf_scanne(chemin_pdf))

#print(extraire_text_md_Et_txt("miniRag.md"))


#print(extraireXLSX("data/Questions_web.xlsx"))



# méthode pour extraire le texte d'un fichier pdf (non scanné) (on fait exprès de ne pas capturer d'images et de tableaux)
def extraire_textePyMu(chemin_pdf):
    
    texte_complet = ""
    doc = pymupdf.open(chemin_pdf)

    for page in doc:
        blocks = page.get_text("blocks")  # Extraction par blocs (respecte mieux la mise en page)
        blocks = sorted(blocks, key=lambda b: (b[1], b[0]))  # Trie par position (top-left)

        for block in blocks:
            texte_complet += block[4] + "\n\n"  # Ajouter un saut de ligne entre les blocs

        texte_complet += "\n\n"  # Ajouter un saut de ligne entre les pages
    
    return texte_complet.strip()
# méthode pour extraire le texte d'un fichier .pdf(non scanné ) avec la bibliothèque pdfplumber 
# on utilise ici 2 bibliothèques pour ainsi faire des tests de performances ( temps, précision)


"""






#extraireText("cheminFichier.txt")

#start = time.perf_counter()
#print("\n..............\n")


#print(extraire_textePyMu("data/Labyrinthe_PartieB copie.pdf"))

#print("\n..............\n")

#print(extraireTextPlumber("data/Labyrinthe_PartieB copie.pdf"))

#end = time.perf_counter()

#print("Temps Plumber",end-start)

#print("..............")


#start = time.perf_counter()

#print(extraire_textePyMu("cheminFichier.pdf"))

#end = time.perf_counter()
#print("Temps PyMu",end-start)
#print("..............")

#print(extraireTableauxPdf("data/Labyrinthe_PartieB copie.pdf"))
