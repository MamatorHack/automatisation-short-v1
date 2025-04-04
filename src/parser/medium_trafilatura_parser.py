#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Medium Article Parser (Trafilatura Version)

Ce module permet d'extraire le contenu des articles Medium en utilisant
la bibliothèque trafilatura, spécialisée dans l'extraction d'articles.
"""

import os
import json
import re
from urllib.parse import urlparse
import logging
import requests
import trafilatura
from trafilatura.metadata import extract_metadata
from datetime import datetime

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MediumTrafilaturaParser:
    """Classe pour extraire le contenu des articles Medium via trafilatura."""
    
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
            # Télécharger le contenu de la page
            downloaded = trafilatura.fetch_url(url)
            
            if not downloaded:
                logger.error(f"Impossible de télécharger la page: {url}")
                return None
            
            # Extraire le contenu principal
            result = trafilatura.extract(downloaded, output_format='xml', include_images=True, include_links=True)
            
            if not result:
                logger.error(f"Impossible d'extraire le contenu de la page: {url}")
                return None
            
            # Extraire les métadonnées
            metadata = extract_metadata(downloaded)
            
            # Structurer les données de l'article
            article_data = self._process_article_data(result, metadata, url)
            
            # Télécharger les images si un répertoire de sortie est spécifié
            if self.output_dir and article_data.get('images'):
                article_data['local_images'] = self._download_images(article_data['images'])
                
                # Sauvegarde des données de l'article au format JSON
                self._save_article_data(article_data)
            
            return article_data
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction de l'article: {str(e)}")
            return None
    
    def _process_article_data(self, xml_content, metadata, url):
        """
        Traite les données brutes de l'article pour les structurer.
        
        Args:
            xml_content (str): Contenu XML extrait par trafilatura.
            metadata (dict): Métadonnées extraites par trafilatura.
            url (str): URL de l'article.
            
        Returns:
            dict: Données structurées de l'article.
        """
        # Extraire les sections de contenu
        content = []
        
        # Convertir le XML en texte structuré
        from lxml import etree
        
        try:
            root = etree.fromstring(xml_content)
            
            # Extraire les paragraphes, titres, etc.
            for element in root.xpath('//p | //h1 | //h2 | //h3 | //h4 | //h5 | //h6 | //list | //quote'):
                element_type = element.tag.upper()
                element_text = ''.join(element.itertext()).strip()
                
                if element_text:
                    content.append({
                        'type': element_type,
                        'text': element_text
                    })
            
            # Extraire les images
            images = []
            for img in root.xpath('//graphic'):
                img_url = img.get('url', '')
                if img_url:
                    alt_text = img.get('alt', '')
                    images.append({
                        'url': img_url,
                        'alt': alt_text
                    })
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du XML: {str(e)}")
            # Fallback: diviser le texte en paragraphes
            text_content = trafilatura.extract(xml_content, output_format='text')
            paragraphs = text_content.split('\n\n')
            
            for paragraph in paragraphs:
                if paragraph.strip():
                    content.append({
                        'type': 'P',
                        'text': paragraph.strip()
                    })
            
            # Pas d'images dans ce cas
            images = []
        
        # Extraire les tags (keywords)
        tags = []
        if metadata and 'tags' in metadata:
            tags = metadata['tags']
        
        # Structurer les données
        title = metadata.get('title', 'Titre non disponible') if metadata else 'Titre non disponible'
        author = metadata.get('author', 'Auteur inconnu') if metadata else 'Auteur inconnu'
        
        # Formater la date
        published_date = "Date inconnue"
        if metadata and 'date' in metadata and metadata['date']:
            try:
                date_obj = datetime.fromisoformat(metadata['date'])
                published_date = date_obj.isoformat()
            except (ValueError, TypeError):
                published_date = metadata['date']
        
        # Extraire le résumé
        summary = ""
        if metadata and 'description' in metadata:
            summary = metadata['description']
        elif content and len(content) > 0:
            # Utiliser le premier paragraphe comme résumé
            summary = content[0]['text']
        
        processed_data = {
            'url': url,
            'title': title,
            'author': author,
            'published_date': published_date,
            'content': content,
            'summary': summary,
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
    
    parser = argparse.ArgumentParser(description='Extraire le contenu d\'un article Medium via trafilatura')
    parser.add_argument('url', help='URL de l\'article Medium')
    parser.add_argument('--output', '-o', help='Répertoire de sortie pour les données et images')
    
    args = parser.parse_args()
    
    medium_parser = MediumTrafilaturaParser(output_dir=args.output)
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
