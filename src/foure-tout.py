import pdfplumber
import pymupdf
from api import resumeDocument
from chargeFichier import get_text_from_any_pdf

"""
Module de fonctions diverses pour l'extraction de texte.

Ce module contient des fonctions utilitaires pour extraire du texte
de différents formats de fichiers, notamment PDF et TXT.
Il inclut également des fonctions pour détecter si un PDF est scanné.
"""

# méthode pour extraire le texte d'un fichier .txt
def extraireText(cheminTxt):
    """
    Extrait et affiche le texte d'un fichier texte.
    
    Args:
        cheminTxt (str): Chemin vers le fichier texte à lire.
        
    Returns:
        None: La fonction affiche le contenu ligne par ligne.
    """
    fichier  = open(cheminTxt,'r')
    lignes = fichier.readlines()
    for ligne in lignes:
        print(ligne)




# méthode pour extraire le teexte d'un fichier pdf (non scanné) (on fait exprès de ne pas capturer d'images et de tableaux)
def extraire_textePyMu(chemin_pdf):
    """
    Extrait le texte d'un fichier PDF non scanné en utilisant PyMuPDF.
    
    Cette fonction ignore volontairement les images et les tableaux,
    se concentrant uniquement sur le texte brut du document.
    
    Args:
        chemin_pdf (str): Chemin vers le fichier PDF à traiter.
        
    Returns:
        str: Texte extrait du PDF.
    """
    texte_complet = ""
    doc = pymupdf.open(chemin_pdf)
    for page in doc:
        texte_complet += page.get_text() + "\n"
    return texte_complet

# méthode pour extraire le texte d'un fichier .pdf(non scanné ) avec la bibliothèque pdfplumber 
# on utilise ici 2 bibliothèques pour ainsi faire des tests de performances ( temps, précision)

def extraireTextPlumber(cheminPdf):
    """
    Extrait le texte d'un fichier PDF non scanné en utilisant pdfplumber.
    
    Cette fonction est une alternative à extraire_textePyMu et permet
    de comparer les performances (temps, précision) entre les deux bibliothèques.
    
    Args:
        cheminPdf (str): Chemin vers le fichier PDF à traiter.
        
    Returns:
        str: Texte extrait du PDF.
    """
    with pdfplumber.open(cheminPdf) as pdf:
        res=""
        for page in pdf.pages:
            res+= page.extract_text()
        return res

# méhode pur extraire des tableaux d'un pdf non scanné (meilleur bibliothèque pour cette extraction précise)
def extraireTableauxPdf(cheminPdf):
    """
    Extrait les tableaux d'un fichier PDF non scanné.
    
    Utilise pdfplumber, qui est particulièrement efficace pour
    l'extraction de tableaux structurés dans les documents PDF.
    
    Args:
        cheminPdf (str): Chemin vers le fichier PDF à traiter.
        
    Returns:
        list: Liste des tableaux extraits du PDF.
    """
    res = []
    with pdfplumber.open(cheminPdf) as pdf:
        a= None
        for page in pdf.pages:
            a= page.extract_table()
            if a is not None:
                res.append(a)
        return res




# Arrêt dès qu'on trouve du texte
def est_scanne(path):
    """
    Détermine si un fichier PDF est scanné ou contient du texte extractible.
    
    Vérifie chaque page du PDF pour détecter la présence de texte.
    S'arrête dès qu'un texte est trouvé.
    
    Args:
        path (str): Chemin vers le fichier PDF à analyser.
        
    Returns:
        bool: True si le PDF est scanné (pas de texte), False sinon.
    """
    with fitz.open(path) as doc:
        return all(not page.get_text().strip() for page in doc)

#extraireText("cheminFichier.txt")

#start = time.perf_counter()

#print(extraireTextPlumber("cheminFichier.pdf"))

#end = time.perf_counter()

#print("Temps Plumber",end-start)

#print("..............")


#start = time.perf_counter()

#print(extraire_textePyMu("cheminFichier.pdf"))

#end = time.perf_counter()
#print("Temps PyMu",end-start)
#print("..............")

#print(extraireTableauxPdf("cheminFichier.pdf"))


rep = resumeDocument(get_text_from_any_pdf("media/documents/VP/Note campagne CRCT CNU 2025-2026 modifiée.pdf"))

print(rep)

