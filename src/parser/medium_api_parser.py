#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Medium Article Parser (API Version)

Ce module permet d'extraire le contenu des articles Medium en utilisant
l'API non officielle de Medium (medium-api).
"""

import os
import json
import re
from urllib.parse import urlparse
import logging
import requests
from medium_api import Medium

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MediumAPIParser:
    """Classe pour extraire le contenu des articles Medium via l'API non officielle."""
    
    def __init__(self, output_dir=None):
        """
        Initialise le parser Medium.
        
        Args:
            output_dir (str, optional): Répertoire de sortie pour les images et les données.
                Si None, aucune image ne sera téléchargée.
        """
        self.output_dir = output_dir
        self.medium_api = Medium()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            os.makedirs(os.path.join(output_dir, 'images'), exist_ok=True)
    
    def extract_article(self, url):
        """
        Extrait le contenu d'un article Medium à partir de son URL.
        
        Args:
            url (str): URL de l'article Medium.
            
        Returns:
            dict: Dictionnaire contenant les données de l'article.
        """
        logger.info(f"Extraction de l'article: {url}")
        
        try:
            # Extraire l'identifiant de l'article à partir de l'URL
            article_id = self._extract_article_id(url)
            
            if not article_id:
                logger.error(f"Impossible d'extraire l'identifiant de l'article à partir de l'URL: {url}")
                return None
            
            # Récupérer les données de l'article via l'API
            article_data = self.medium_api.get_article(article_id)
            
            if not article_data:
                logger.error(f"Impossible de récupérer les données de l'article: {article_id}")
                return None
            
            # Structurer les données de l'article
            processed_data = self._process_article_data(article_data, url)
            
            # Télécharger les images si un répertoire de sortie est spécifié
            if self.output_dir and processed_data.get('images'):
                processed_data['local_images'] = self._download_images(processed_data['images'])
                
                # Sauvegarde des données de l'article au format JSON
                self._save_article_data(processed_data)
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction de l'article: {str(e)}")
            return None
    
    def _extract_article_id(self, url):
        """
        Extrait l'identifiant de l'article à partir de l'URL.
        
        Args:
            url (str): URL de l'article Medium.
            
        Returns:
            str: Identifiant de l'article ou None si non trouvé.
        """
        # Essayer d'extraire l'ID à partir de l'URL
        path = urlparse(url).path
        
        # Format typique: /@username/article-slug-hash
        match = re.search(r'/@[\w-]+/([\w-]+)-([a-f0-9]+)$', path)
        if match:
            return match.group(2)
        
        # Format alternatif: /p/article-id
        match = re.search(r'/p/([a-f0-9]+)$', path)
        if match:
            return match.group(1)
        
        # Si l'ID n'est pas dans l'URL, essayer de le récupérer à partir de la page
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            # Chercher l'ID dans le contenu de la page
            match = re.search(r'"postId":"([a-f0-9]+)"', response.text)
            if match:
                return match.group(1)
            
            # Autre format possible
            match = re.search(r'"id":"([a-f0-9]+)"', response.text)
            if match:
                return match.group(1)
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'ID de l'article: {str(e)}")
        
        return None
    
    def _process_article_data(self, article_data, url):
        """
        Traite les données brutes de l'article pour les structurer.
        
        Args:
            article_data (dict): Données brutes de l'article.
            url (str): URL de l'article.
            
        Returns:
            dict: Données structurées de l'article.
        """
        # Extraire les sections de contenu
        content = []
        if 'content' in article_data:
            for section in article_data['content'].get('bodyModel', {}).get('paragraphs', []):
                section_type = section.get('type', 'P')
                section_text = section.get('text', '')
                
                if section_text:
                    content.append({
                        'type': section_type,
                        'text': section_text
                    })
        
        # Extraire les images
        images = []
        if 'content' in article_data:
            for section in article_data['content'].get('bodyModel', {}).get('paragraphs', []):
                if section.get('type') == 'IMG' and 'metadata' in section:
                    metadata = section.get('metadata', {})
                    img_id = metadata.get('id', '')
                    img_url = f"https://miro.medium.com/max/1400/{img_id}"
                    
                    images.append({
                        'url': img_url,
                        'alt': section.get('text', '')
                    })
        
        # Extraire les tags
        tags = []
        if 'tags' in article_data:
            for tag in article_data['tags']:
                tags.append(tag.get('name', ''))
        
        # Structurer les données
        processed_data = {
            'url': url,
            'title': article_data.get('title', 'Titre non disponible'),
            'author': article_data.get('author', {}).get('name', 'Auteur inconnu'),
            'published_date': article_data.get('firstPublishedAt', 'Date inconnue'),
            'content': content,
            'summary': article_data.get('previewContent', {}).get('subtitle', ''),
            'images': images,
            'tags': tags
        }
        
        return processed_data
    
    def _download_images(self, images):
        """Télécharge les images et retourne les chemins locaux."""
        if not self.output_dir:
            return []
        
        local_images = []
        for i, img in enumerate(images):
            try:
                img_url = img['url']
                img_ext = '.jpg'  # Extension par défaut pour les images Medium
                
                local_path = os.path.join(self.output_dir, 'images', f'image_{i}{img_ext}')
                
                # Téléchargement de l'image
                response = requests.get(img_url, headers=self.headers)
                response.raise_for_status()
                
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                
                local_images.append({
                    'url': img['url'],
                    'local_path': local_path,
                    'alt': img['alt']
                })
                
                logger.info(f"Image téléchargée: {local_path}")
                
            except Exception as e:
                logger.error(f"Erreur lors du téléchargement de l'image {img['url']}: {str(e)}")
        
        return local_images
    
    def _save_article_data(self, article_data):
        """Sauvegarde les données de l'article au format JSON."""
        if not self.output_dir:
            return
        
        # Créer un nom de fichier basé sur le titre
        filename = re.sub(r'[^\w\s-]', '', article_data['title']).strip().lower()
        filename = re.sub(r'[-\s]+', '-', filename)
        
        json_path = os.path.join(self.output_dir, f'{filename}.json')
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(article_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Données de l'article sauvegardées: {json_path}")


def main():
    """Fonction principale pour tester le parser."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extraire le contenu d\'un article Medium via l\'API')
    parser.add_argument('url', help='URL de l\'article Medium')
    parser.add_argument('--output', '-o', help='Répertoire de sortie pour les données et images')
    
    args = parser.parse_args()
    
    medium_parser = MediumAPIParser(output_dir=args.output)
    article_data = medium_parser.extract_article(args.url)
    
    if article_data:
        print(f"Titre: {article_data['title']}")
        print(f"Auteur: {article_data['author']}")
        print(f"Date: {article_data['published_date']}")
        print(f"Tags: {', '.join(article_data['tags'])}")
        print(f"Nombre d'images: {len(article_data['images'])}")
        print(f"Nombre de sections de contenu: {len(article_data['content'])}")
    else:
        print("Échec de l'extraction de l'article")


if __name__ == "__main__":
    main()
