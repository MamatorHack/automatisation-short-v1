#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Medium Article Parser (Newspaper3k Version)

Ce module permet d'extraire le contenu des articles Medium en utilisant
la bibliothèque newspaper3k, spécialisée dans l'extraction d'articles.
"""

import os
import json
import re
from urllib.parse import urlparse
import logging
import requests
from newspaper import Article
from newspaper import Config

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MediumNewspaperParser:
    """Classe pour extraire le contenu des articles Medium via newspaper3k."""
    
    def __init__(self, output_dir=None):
        """
        Initialise le parser Medium.
        
        Args:
            output_dir (str, optional): Répertoire de sortie pour les images et les données.
                Si None, aucune image ne sera téléchargée.
        """
        self.output_dir = output_dir
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Configuration de newspaper
        self.config = Config()
        self.config.browser_user_agent = self.headers['User-Agent']
        self.config.request_timeout = 10
        
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
            # Initialiser l'article
            article = Article(url, config=self.config)
            
            # Télécharger et parser l'article
            article.download()
            article.parse()
            
            # Extraire les métadonnées supplémentaires
            article.nlp()
            
            # Structurer les données de l'article
            article_data = self._process_article_data(article, url)
            
            # Télécharger les images si un répertoire de sortie est spécifié
            if self.output_dir and article_data.get('images'):
                article_data['local_images'] = self._download_images(article_data['images'])
                
                # Sauvegarde des données de l'article au format JSON
                self._save_article_data(article_data)
            
            return article_data
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction de l'article: {str(e)}")
            return None
    
    def _process_article_data(self, article, url):
        """
        Traite les données brutes de l'article pour les structurer.
        
        Args:
            article (Article): Objet Article de newspaper3k.
            url (str): URL de l'article.
            
        Returns:
            dict: Données structurées de l'article.
        """
        # Extraire les sections de contenu
        content = []
        
        # Diviser le texte en paragraphes
        paragraphs = article.text.split('\n\n')
        for paragraph in paragraphs:
            if paragraph.strip():
                content.append({
                    'type': 'P',
                    'text': paragraph.strip()
                })
        
        # Extraire les images
        images = []
        if article.top_image:
            images.append({
                'url': article.top_image,
                'alt': 'Image principale de l\'article'
            })
        
        for img_url in article.images:
            if img_url != article.top_image:  # Éviter les doublons
                images.append({
                    'url': img_url,
                    'alt': ''
                })
        
        # Extraire les tags (keywords)
        tags = article.keywords
        
        # Structurer les données
        published_date = article.publish_date.isoformat() if article.publish_date else "Date inconnue"
        
        processed_data = {
            'url': url,
            'title': article.title,
            'author': article.authors[0] if article.authors else "Auteur inconnu",
            'published_date': published_date,
            'content': content,
            'summary': article.summary,
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
                img_ext = os.path.splitext(urlparse(img_url).path)[1]
                if not img_ext:
                    img_ext = '.jpg'  # Extension par défaut
                
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
    
    parser = argparse.ArgumentParser(description='Extraire le contenu d\'un article Medium via newspaper3k')
    parser.add_argument('url', help='URL de l\'article Medium')
    parser.add_argument('--output', '-o', help='Répertoire de sortie pour les données et images')
    
    args = parser.parse_args()
    
    medium_parser = MediumNewspaperParser(output_dir=args.output)
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
