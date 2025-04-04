#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Medium Article Parser (Selenium Version)

Ce module permet d'extraire le contenu des articles Medium en utilisant
Selenium pour rendre le JavaScript et extraire le contenu dynamique.
"""

import os
import json
import re
import time
import logging
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MediumSeleniumParser:
    """Classe pour extraire le contenu des articles Medium via Selenium."""
    
    def __init__(self, output_dir=None, headless=True):
        """
        Initialise le parser Medium avec Selenium.
        
        Args:
            output_dir (str, optional): Répertoire de sortie pour les images et les données.
                Si None, aucune image ne sera téléchargée.
            headless (bool): Si True, le navigateur s'exécute en mode headless (sans interface graphique).
        """
        self.output_dir = output_dir
        self.headless = headless
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            os.makedirs(os.path.join(output_dir, 'images'), exist_ok=True)
    
    def _setup_driver(self):
        """Configure et retourne un driver Selenium."""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument(f"user-agent={self.headers['User-Agent']}")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    
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
            driver = self._setup_driver()
            driver.get(url)
            
            # Attendre que le contenu soit chargé
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "article"))
            )
            
            # Faire défiler la page pour charger tout le contenu
            self._scroll_to_bottom(driver)
            
            # Extraire le contenu avec BeautifulSoup
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Extraction des données de base
            article_data = {
                'url': url,
                'title': self._extract_title(soup),
                'author': self._extract_author(soup),
                'published_date': self._extract_date(soup),
                'content': self._extract_content(soup),
                'summary': self._extract_summary(soup),
                'images': self._extract_images(soup, url),
                'tags': self._extract_tags(soup)
            }
            
            # Fermer le navigateur
            driver.quit()
            
            # Téléchargement des images si un répertoire de sortie est spécifié
            if self.output_dir and article_data['images']:
                article_data['local_images'] = self._download_images(article_data['images'])
                
                # Sauvegarde des données de l'article au format JSON
                self._save_article_data(article_data)
            
            return article_data
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction de l'article: {str(e)}")
            if 'driver' in locals():
                driver.quit()
            return None
    
    def _scroll_to_bottom(self, driver):
        """Fait défiler la page jusqu'en bas pour charger tout le contenu."""
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        while True:
            # Défiler vers le bas
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Attendre le chargement
            time.sleep(2)
            
            # Calculer la nouvelle hauteur
            new_height = driver.execute_script("return document.body.scrollHeight")
            
            # Si la hauteur n'a pas changé, on a atteint le bas
            if new_height == last_height:
                break
                
            last_height = new_height
    
    def _extract_title(self, soup):
        """Extrait le titre de l'article."""
        title_tag = soup.find('h1')
        if title_tag:
            return title_tag.text.strip()
        
        # Essayer d'autres sélecteurs si h1 n'est pas trouvé
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.text.strip()
            # Supprimer le suffixe "| Medium" s'il existe
            return re.sub(r'\s*\|\s*Medium$', '', title_text)
        
        return "Titre non trouvé"
    
    def _extract_author(self, soup):
        """Extrait l'auteur de l'article."""
        # Plusieurs sélecteurs possibles pour l'auteur
        author_tag = soup.find('a', {'rel': 'author'})
        if author_tag:
            return author_tag.text.strip()
        
        # Essayer d'autres sélecteurs
        author_tag = soup.find('a', {'class': 'ds-link'})
        if author_tag:
            return author_tag.text.strip()
        
        # Chercher dans les métadonnées
        meta_author = soup.find('meta', {'name': 'author'})
        if meta_author and meta_author.get('content'):
            return meta_author['content']
        
        return "Auteur inconnu"
    
    def _extract_date(self, soup):
        """Extrait la date de publication de l'article."""
        # Recherche de balises time
        date_tag = soup.find('time')
        if date_tag:
            if date_tag.has_attr('datetime'):
                return date_tag['datetime']
            return date_tag.text.strip()
        
        # Chercher dans les métadonnées
        meta_date = soup.find('meta', {'property': 'article:published_time'})
        if meta_date and meta_date.get('content'):
            return meta_date['content']
        
        # Chercher des div contenant des dates
        date_div = soup.find('div', string=re.compile(r'\w+\s+\d+,\s+\d{4}'))
        if date_div:
            return date_div.text.strip()
        
        return "Date inconnue"
    
    def _extract_summary(self, soup):
        """Extrait le résumé de l'article."""
        # Chercher dans les métadonnées
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content']
        
        # Essayer de trouver un sous-titre ou une introduction
        subtitle = soup.find('h2')
        if subtitle:
            return subtitle.text.strip()
        
        # Prendre le premier paragraphe comme résumé
        first_p = soup.find('article').find('p')
        if first_p:
            return first_p.text.strip()
        
        return ""
    
    def _extract_content(self, soup):
        """Extrait le contenu principal de l'article."""
        # Trouver le conteneur principal de l'article
        article_container = soup.find('article')
        
        if not article_container:
            logger.warning("Conteneur d'article non trouvé, recherche d'alternatives")
            # Essayer de trouver un conteneur de section
            article_container = soup.find('div', {'class': 'section-content'})
            
            if not article_container:
                logger.warning("Conteneur de section non trouvé, utilisation du body")
                article_container = soup.body
        
        # Extraire tous les paragraphes, titres et listes
        content_elements = article_container.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'blockquote', 'pre', 'figure'])
        
        # Filtrer les éléments non pertinents et construire le contenu
        content = []
        for element in content_elements:
            # Ignorer les éléments vides ou les éléments de navigation
            if not element.text.strip() or element.find_parent('nav'):
                continue
                
            # Traitement spécial pour les figures (images)
            if element.name == 'figure':
                img = element.find('img')
                if img:
                    caption = element.find('figcaption')
                    caption_text = caption.text.strip() if caption else ""
                    
                    content.append({
                        'type': 'IMG',
                        'text': caption_text,
                        'src': img.get('src', '')
                    })
                    continue
            
            # Ajouter le texte avec le type d'élément
            content.append({
                'type': element.name.upper(),
                'text': element.text.strip()
            })
        
        return content
    
    def _extract_images(self, soup, base_url):
        """Extrait les URLs des images de l'article."""
        images = []
        img_tags = soup.find_all('img')
        
        for img in img_tags:
            # Ignorer les petites images (avatars, icônes)
            if img.has_attr('width') and img.has_attr('height'):
                try:
                    width = int(img['width'])
                    height = int(img['height'])
                    if width < 200 or height < 200:
                        continue
                except (ValueError, TypeError):
                    pass
            
            # Obtenir l'URL de l'image
            img_url = None
            for attr in ['src', 'data-src', 'srcset']:
                if img.has_attr(attr):
                    img_url = img[attr].split(' ')[0]  # Pour srcset, prendre la première URL
                    break
            
            if img_url:
                # Convertir en URL absolue si nécessaire
                if not img_url.startswith(('http://', 'https://')):
                    img_url = urlparse(base_url)._replace(path=img_url).geturl()
                
                # Ajouter l'URL à la liste
                if img_url not in [img['url'] for img in images]:
                    alt_text = img.get('alt', '')
                    images.append({
                        'url': img_url,
                        'alt': alt_text
                    })
        
        return images
    
    def _extract_tags(self, soup):
        """Extrait les tags/catégories de l'article."""
        tags = []
        # Recherche des tags dans différentes structures possibles
        tag_elements = soup.find_all('a', {'class': re.compile(r'tag')})
        
        if not tag_elements:
            tag_elements = soup.find_all('a', {'href': re.compile(r'/tag/')})
        
        for tag in tag_elements:
            tag_text = tag.text.strip()
            if tag_text and tag_text not in tags:
                tags.append(tag_text)
        
        return tags
    
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
    
    parser = argparse.ArgumentParser(description='Extraire le contenu d\'un article Medium via Selenium')
    parser.add_argument('url', help='URL de l\'article Medium')
    parser.add_argument('--output', '-o', help='Répertoire de sortie pour les données et images')
    parser.add_argument('--headless', action='store_true', help='Exécuter en mode headless')
    
    args = parser.parse_args()
    
    medium_parser = MediumSeleniumParser(output_dir=args.output, headless=args.headless)
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
