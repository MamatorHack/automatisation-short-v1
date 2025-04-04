#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Medium Article Parser (Version simplifiée)

Ce module permet d'extraire le contenu des articles Medium en utilisant
une approche simplifiée combinant requests et BeautifulSoup.
"""

import os
import json
import re
import time
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MediumSimpleParser:
    """Classe pour extraire le contenu des articles Medium via une approche simplifiée."""
    
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
            # Contourner la protection de Medium en ajoutant un paramètre
            if '?' not in url:
                url = url + '?format=json'
            else:
                url = url + '&format=json'
                
            # Télécharger le contenu de la page
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            # Medium renvoie un préfixe JSON suivi du JSON réel
            json_str = response.text.split('])}while(1);</x>')[1] if '])}while(1);</x>' in response.text else response.text
            
            # Parser le JSON
            data = json.loads(json_str)
            
            # Extraire les données de l'article
            article_data = self._extract_from_json(data, url)
            
            # Télécharger les images si un répertoire de sortie est spécifié
            if self.output_dir and article_data.get('images'):
                article_data['local_images'] = self._download_images(article_data['images'])
                
                # Sauvegarde des données de l'article au format JSON
                self._save_article_data(article_data)
            
            return article_data
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction de l'article: {str(e)}")
            
            # Essayer une approche alternative avec BeautifulSoup
            try:
                logger.info("Tentative d'extraction avec BeautifulSoup...")
                return self._extract_with_beautifulsoup(url)
            except Exception as e2:
                logger.error(f"Échec de l'extraction avec BeautifulSoup: {str(e2)}")
                return None
    
    def _extract_from_json(self, data, url):
        """
        Extrait les données de l'article à partir de la réponse JSON de Medium.
        
        Args:
            data (dict): Données JSON de l'article.
            url (str): URL de l'article.
            
        Returns:
            dict: Données structurées de l'article.
        """
        # Trouver les données de l'article dans la structure JSON
        post = None
        if 'payload' in data and 'value' in data['payload']:
            post = data['payload']['value']
        elif 'payload' in data and 'references' in data['payload'] and 'Post' in data['payload']['references']:
            # Prendre le premier post
            posts = data['payload']['references']['Post']
            if posts:
                post = list(posts.values())[0]
        
        if not post:
            raise ValueError("Structure JSON non reconnue")
        
        # Extraire le contenu
        content = []
        if 'content' in post and 'bodyModel' in post['content'] and 'paragraphs' in post['content']['bodyModel']:
            for paragraph in post['content']['bodyModel']['paragraphs']:
                p_type = paragraph.get('type', 'P')
                p_text = paragraph.get('text', '')
                
                if p_text:
                    content.append({
                        'type': p_type,
                        'text': p_text
                    })
        
        # Extraire les images
        images = []
        if 'content' in post and 'bodyModel' in post['content'] and 'paragraphs' in post['content']['bodyModel']:
            for paragraph in post['content']['bodyModel']['paragraphs']:
                if paragraph.get('type') == 'IMG' and 'metadata' in paragraph:
                    metadata = paragraph.get('metadata', {})
                    img_id = metadata.get('id', '')
                    
                    if img_id:
                        img_url = f"https://miro.medium.com/max/1400/{img_id}"
                        alt_text = paragraph.get('text', '')
                        
                        images.append({
                            'url': img_url,
                            'alt': alt_text
                        })
        
        # Extraire les tags
        tags = []
        if 'virtuals' in post and 'tags' in post['virtuals']:
            for tag in post['virtuals']['tags']:
                tag_name = tag.get('name', '')
                if tag_name:
                    tags.append(tag_name)
        
        # Extraire les métadonnées
        title = post.get('title', 'Titre non disponible')
        
        # Extraire l'auteur
        author = "Auteur inconnu"
        if 'creator' in post and 'name' in post['creator']:
            author = post['creator']['name']
        elif 'payload' in data and 'references' in data['payload'] and 'User' in data['payload']['references']:
            users = data['payload']['references']['User']
            if users:
                first_user = list(users.values())[0]
                author = first_user.get('name', 'Auteur inconnu')
        
        # Extraire la date
        published_date = "Date inconnue"
        if 'firstPublishedAt' in post:
            timestamp = post['firstPublishedAt']
            try:
                from datetime import datetime
                published_date = datetime.fromtimestamp(timestamp / 1000).isoformat()
            except:
                published_date = str(timestamp)
        
        # Extraire le résumé
        summary = ""
        if 'virtuals' in post and 'subtitle' in post['virtuals']:
            summary = post['virtuals']['subtitle']
        elif content and len(content) > 0:
            summary = content[0]['text']
        
        return {
            'url': url,
            'title': title,
            'author': author,
            'published_date': published_date,
            'content': content,
            'summary': summary,
            'images': images,
            'tags': tags
        }
    
    def _extract_with_beautifulsoup(self, url):
        """
        Extrait les données de l'article en utilisant BeautifulSoup.
        
        Args:
            url (str): URL de l'article.
            
        Returns:
            dict: Données structurées de l'article.
        """
        # Télécharger le contenu de la page
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extraire le titre
        title_tag = soup.find('h1')
        title = title_tag.text.strip() if title_tag else "Titre non trouvé"
        
        # Extraire l'auteur
        author_tag = soup.find('a', {'rel': 'author'})
        author = author_tag.text.strip() if author_tag else "Auteur inconnu"
        
        # Extraire la date
        date_tag = soup.find('time')
        published_date = date_tag['datetime'] if date_tag and date_tag.has_attr('datetime') else "Date inconnue"
        
        # Extraire le contenu
        content = []
        article_tag = soup.find('article')
        
        if article_tag:
            for element in article_tag.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                if element.text.strip():
                    content.append({
                        'type': element.name.upper(),
                        'text': element.text.strip()
                    })
        
        # Extraire les images
        images = []
        for img in soup.find_all('img'):
            if img.has_attr('src') and not img.has_attr('width') or (img.has_attr('width') and int(img['width']) > 200):
                img_url = img['src']
                alt_text = img['alt'] if img.has_attr('alt') else ""
                
                images.append({
                    'url': img_url,
                    'alt': alt_text
                })
        
        # Extraire les tags
        tags = []
        for tag in soup.find_all('a', {'href': re.compile(r'/tag/')}):
            tag_text = tag.text.strip()
            if tag_text:
                tags.append(tag_text)
        
        # Extraire le résumé
        summary = ""
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc and meta_desc.has_attr('content'):
            summary = meta_desc['content']
        elif content and len(content) > 0:
            summary = content[0]['text']
        
        return {
            'url': url,
            'title': title,
            'author': author,
            'published_date': published_date,
            'content': content,
            'summary': summary,
            'images': images,
            'tags': tags
        }
    
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
    
    parser = argparse.ArgumentParser(description='Extraire le contenu d\'un article Medium')
    parser.add_argument('url', help='URL de l\'article Medium')
    parser.add_argument('--output', '-o', help='Répertoire de sortie pour les données et images')
    
    args = parser.parse_args()
    
    medium_parser = MediumSimpleParser(output_dir=args.output)
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
