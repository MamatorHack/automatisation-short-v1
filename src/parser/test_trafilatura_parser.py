#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test du parser d'articles Medium avec Trafilatura

Ce script permet de tester le parser d'articles Medium basé sur Trafilatura.
"""

import os
import sys
import json
from pathlib import Path

# Ajouter le répertoire parent au chemin de recherche des modules
sys.path.append(str(Path(__file__).parent.parent))

from parser.medium_trafilatura_parser import MediumTrafilaturaParser

def main():
    """Fonction principale pour tester le parser."""
    
    # Créer un répertoire de sortie pour les tests
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output', 'test_trafilatura_parser')
    os.makedirs(output_dir, exist_ok=True)
    
    # URL d'exemple d'un article Medium
    test_url = "https://medium.com/illumination/7-simple-habits-that-will-make-you-mentally-strong-for-life-a1f0442a9c6e"
    
    print(f"Test du parser Trafilatura avec l'article: {test_url}")
    print(f"Sortie dans: {output_dir}")
    
    # Initialiser le parser
    parser = MediumTrafilaturaParser(output_dir=output_dir)
    
    # Extraire l'article
    article_data = parser.extract_article(test_url)
    
    if article_data:
        print("\nExtraction réussie!")
        print(f"Titre: {article_data['title']}")
        print(f"Auteur: {article_data['author']}")
        print(f"Date: {article_data['published_date']}")
        print(f"Tags: {', '.join(article_data['tags'])}")
        print(f"Nombre d'images: {len(article_data['images'])}")
        print(f"Nombre de sections de contenu: {len(article_data['content'])}")
        
        # Afficher un aperçu du contenu
        print("\nAperçu du contenu:")
        for i, section in enumerate(article_data['content'][:5]):  # Afficher les 5 premières sections
            print(f"  {section['type']}: {section['text'][:100]}...")
        
        # Afficher le chemin du fichier JSON
        json_files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
        if json_files:
            print(f"\nFichier JSON créé: {os.path.join(output_dir, json_files[0])}")
        
        # Afficher les images téléchargées
        if 'local_images' in article_data and article_data['local_images']:
            print("\nImages téléchargées:")
            for img in article_data['local_images'][:3]:  # Afficher les 3 premières images
                print(f"  {img['local_path']}")
    else:
        print("Échec de l'extraction de l'article")

if __name__ == "__main__":
    main()
