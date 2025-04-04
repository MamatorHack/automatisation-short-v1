#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Orchestrateur principal pour la génération de shorts vidéo

Ce module coordonne l'ensemble du processus de génération de shorts vidéo
à partir d'articles Medium, en intégrant toutes les composantes développées.
"""

import os
import json
import logging
import argparse
from pathlib import Path

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Importer les modules développés
try:
    from parser.medium_simple_parser import MediumSimpleParser
except ImportError:
    logger.warning("Module d'extraction d'articles Medium non disponible, utilisation de données d'exemple")
    MediumSimpleParser = None

try:
    from generator.script_generator import ShortScriptGenerator
except ImportError:
    logger.error("Module de génération de scripts non disponible")
    raise ImportError("Le module de génération de scripts est requis")

try:
    from generator.video_generator import ShortVideoGenerator
except ImportError:
    logger.error("Module de génération de vidéos non disponible")
    raise ImportError("Le module de génération de vidéos est requis")

try:
    from voice_avatar.voice_generator import VoiceGenerator
except ImportError:
    logger.error("Module de génération de voix non disponible")
    raise ImportError("Le module de génération de voix est requis")

try:
    from voice_avatar.alternative_integrator import AlternativeIntegrator
except ImportError:
    logger.error("Module d'intégration voix-vidéo non disponible")
    raise ImportError("Le module d'intégration voix-vidéo est requis")


class ShortsGenerator:
    """Classe principale pour orchestrer la génération de shorts vidéo."""
    
    def __init__(self, output_dir=None, language='fr'):
        """
        Initialise l'orchestrateur de génération de shorts.
        
        Args:
            output_dir (str): Répertoire de sortie pour les fichiers générés.
            language (str): Code de langue pour la synthèse vocale.
        """
        self.output_dir = output_dir
        self.language = language
        
        # Créer les sous-répertoires de sortie
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            self.articles_dir = os.path.join(output_dir, 'articles')
            self.scripts_dir = os.path.join(output_dir, 'scripts')
            self.videos_dir = os.path.join(output_dir, 'videos')
            self.audio_dir = os.path.join(output_dir, 'audio')
            self.final_dir = os.path.join(output_dir, 'final')
            
            os.makedirs(self.articles_dir, exist_ok=True)
            os.makedirs(self.scripts_dir, exist_ok=True)
            os.makedirs(self.videos_dir, exist_ok=True)
            os.makedirs(self.audio_dir, exist_ok=True)
            os.makedirs(self.final_dir, exist_ok=True)
        else:
            self.articles_dir = None
            self.scripts_dir = None
            self.videos_dir = None
            self.audio_dir = None
            self.final_dir = None
        
        # Initialiser les composants
        if MediumSimpleParser:
            self.article_parser = MediumSimpleParser(output_dir=self.articles_dir)
        else:
            self.article_parser = None
        
        self.script_generator = ShortScriptGenerator(max_duration=60, max_words=150)
        self.video_generator = ShortVideoGenerator(output_dir=self.videos_dir)
        self.voice_generator = VoiceGenerator(output_dir=self.audio_dir, language=language)
        self.integrator = AlternativeIntegrator(output_dir=self.final_dir)
    
    def generate_from_url(self, url):
        """
        Génère un short vidéo à partir d'une URL d'article Medium.
        
        Args:
            url (str): URL de l'article Medium.
            
        Returns:
            str: Chemin de la vidéo finale générée.
        """
        logger.info(f"Génération d'un short vidéo à partir de l'URL: {url}")
        
        try:
            # Étape 1: Extraire l'article
            if self.article_parser:
                article_data = self.article_parser.extract_article(url)
                if not article_data:
                    logger.error(f"Échec de l'extraction de l'article: {url}")
                    return None
            else:
                # Utiliser l'article d'exemple
                example_path = os.path.join(os.path.dirname(__file__), 'generator', 'example_article.json')
                if os.path.exists(example_path):
                    with open(example_path, 'r', encoding='utf-8') as f:
                        article_data = json.load(f)
                else:
                    logger.error("Article d'exemple non disponible")
                    return None
            
            # Sauvegarder les données de l'article
            article_json = None
            if self.articles_dir:
                title = article_data.get('title', 'article').lower().replace(' ', '-')
                article_json = os.path.join(self.articles_dir, f"{title}.json")
                with open(article_json, 'w', encoding='utf-8') as f:
                    json.dump(article_data, f, ensure_ascii=False, indent=2)
            
            return self.generate_from_article(article_data, article_json)
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du short vidéo: {str(e)}")
            return None
    
    def generate_from_article(self, article_data, article_json=None):
        """
        Génère un short vidéo à partir des données d'un article.
        
        Args:
            article_data (dict): Données de l'article.
            article_json (str): Chemin du fichier JSON de l'article.
            
        Returns:
            str: Chemin de la vidéo finale générée.
        """
        logger.info(f"Génération d'un short vidéo à partir de l'article: {article_data.get('title', 'Sans titre')}")
        
        try:
            # Étape 2: Générer le script
            script_data = self.script_generator.generate_script(article_data)
            if not script_data:
                logger.error("Échec de la génération du script")
                return None
            
            # Sauvegarder le script
            script_json = None
            if self.scripts_dir:
                title = script_data.get('title', 'script').lower().replace(' ', '-')
                script_json = os.path.join(self.scripts_dir, f"{title}-script.json")
                self.script_generator.save_script(script_data, self.scripts_dir)
                script_json = os.path.join(self.scripts_dir, f"{title}-script.json")
            
            # Étape 3: Générer la vidéo
            video_path = self.video_generator.generate_video(script_data)
            if not video_path:
                logger.error("Échec de la génération de la vidéo")
                return None
            
            # Étape 4: Générer l'audio
            audio_path = self.voice_generator.generate_audio(script_data)
            if not audio_path:
                logger.error("Échec de la génération de l'audio")
                return None
            
            # Étape 5: Intégrer l'audio à la vidéo
            final_path = self.integrator.integrate(video_path, audio_path)
            if not final_path:
                logger.error("Échec de l'intégration audio-vidéo")
                return None
            
            logger.info(f"Short vidéo généré avec succès: {final_path}")
            return final_path
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du short vidéo: {str(e)}")
            return None
    
    def generate_from_json(self, json_path):
        """
        Génère un short vidéo à partir d'un fichier JSON d'article.
        
        Args:
            json_path (str): Chemin du fichier JSON de l'article.
            
        Returns:
            str: Chemin de la vidéo finale générée.
        """
        logger.info(f"Génération d'un short vidéo à partir du fichier JSON: {json_path}")
        
        try:
            # Charger les données de l'article
            with open(json_path, 'r', encoding='utf-8') as f:
                article_data = json.load(f)
            
            return self.generate_from_article(article_data, json_path)
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du short vidéo: {str(e)}")
            return None


def main():
    """Fonction principale pour exécuter l'orchestrateur."""
    parser = argparse.ArgumentParser(description='Générer un short vidéo à partir d\'un article Medium')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--url', '-u', help='URL de l\'article Medium')
    group.add_argument('--json', '-j', help='Chemin du fichier JSON de l\'article')
    parser.add_argument('--output', '-o', help='Répertoire de sortie pour les fichiers générés')
    parser.add_argument('--language', '-l', default='fr', help='Code de langue pour la synthèse vocale')
    
    args = parser.parse_args()
    
    # Initialiser l'orchestrateur
    generator = ShortsGenerator(output_dir=args.output, language=args.language)
    
    # Générer le short vidéo
    if args.url:
        final_path = generator.generate_from_url(args.url)
    else:
        final_path = generator.generate_from_json(args.json)
    
    if final_path:
        print(f"Short vidéo généré avec succès: {final_path}")
    else:
        print("Échec de la génération du short vidéo")


if __name__ == "__main__":
    main()
