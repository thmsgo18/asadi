import chromadb
from api import reponseAssistant, pimp
from sentence_transformers import SentenceTransformer

"""
Ce document python permet de poser une question. Prendre cette question et la donner à la base de donnée pour trouver les chunks associés.
Pour construire la réponse on donne au LLM la question et les chunks.
"""

# On se connecte à la bdd vectorielle 
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_collection("asadi_collection") # ici une collection c'est plus ou moins une table en sql 

# Chargement du modèle d'embedding pour la recherche sémantique
model_embedding= SentenceTransformer("all-mpnet-base-v2")

# Interface utilisateur pour poser une question
question= input("Pose une question sur le document administratif : ")

# Encodage de la question en vecteur                             
query_embedding= model_embedding.encode(question) #On encode le prompt de l'utilisateur en utilisant la meme fonction d'embedding que dans notre bdd chromadb

# Recherche des chunks les plus pertinents dans la base vectorielle
results = collection.query(
    query_embeddings=[query_embedding.tolist()],
    n_results=4 # On précise qu'on veut obtenir les 4 meilleurs résultats
)
print(results)

# Génération de la réponse avec le modèle de langage
print("************Réponse Assistant *************")
reponse = reponseAssistant(results, question)

# Affichage de la réponse générée
print(reponse)
