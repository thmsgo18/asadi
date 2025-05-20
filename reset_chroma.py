import chromadb
client = chromadb.PersistentClient(path="./chroma_db")
client.delete_collection("asadi_collection")
print("✅ base ChromaDB vidée.")