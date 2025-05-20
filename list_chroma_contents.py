#!/usr/bin/env python3
"""
Script pour lister les éléments dans la base vectorielle ChromaDB.
"""
import os
import django

# Initialisation de Django pour récupérer les settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ASADI.settings')
django.setup()

from django.conf import settings
import chromadb


def main():
    client = chromadb.PersistentClient(path=str(settings.CHROMA_DB_DIR))
    collection = client.get_or_create_collection("asadi_collection")

    # Récupérer uniquement les métadatas et grouper par source
    data = collection.get(include=["metadatas"])
    metas = data["metadatas"]
    summary = {}
    for meta in metas:
        src = meta.get("source", "<unknown>")
        ws = meta.get("workspace", "")
        entry = summary.setdefault(src, {"workspace": ws, "count": 0, "starts": []})
        entry["count"] += 1
        if "start_index" in meta:
            entry["starts"].append(meta["start_index"])
    # Affichage du tableau
    header = f"{'Fichier':50} | {'Workspace':15} | {'Chunks':6} | {'StartIdx Range':15}"
    print(header)
    print('-' * len(header))
    for src, info in summary.items():
        if info["starts"]:
            mn, mx = min(info["starts"]), max(info["starts"])
            minmax = f"{mn}-{mx}"
        else:
            minmax = "-"
        # Troncature du chemin si trop long
        fname = src if len(src) <= 50 else '...' + src[-47:]
        print(f"{fname:50} | {info['workspace']:15} | {info['count']:6} | {minmax:15}")


if __name__ == '__main__':
    main()
