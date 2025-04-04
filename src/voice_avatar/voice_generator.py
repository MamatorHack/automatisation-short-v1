#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Générateur de voix pour shorts vidéo

Ce module permet de générer un fichier audio à partir d'un script,
en utilisant la synthèse vocale gTTS (Google Text-to-Speech).
"""

import os
import json
import logging
import tempfile
from pathlib import Path
from gtts import gTTS

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VoiceGenerator:
    """Classe pour générer des fichiers audio à partir de scripts."""
    
    def __init__(self, output_dir=None, language='fr', slow=False):
        """
        Initialise le générateur de voix.
        
        Args:
            output_dir (str): Répertoire de sortie pour les fichiers audio.
            language (str): Code de langue pour la synthèse vocale.
            slow (bool): Si True, la voix sera générée plus lentement.
        """
        self.output_dir = output_dir
        self.language = language
        self.slow = slow
        
        # Créer le répertoire de sortie s'il n'existe pas
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def generate_audio(self, script_data, output_filename=None):
        """
        Génère un fichier audio à partir d'un script.
        
        Args:
            script_data (dict): Données du script.
            output_filename (str): Nom du fichier de sortie.
            
        Returns:
            str: Chemin du fichier audio généré.
        """
        logger.info(f"Génération d'un fichier audio pour le script: {script_data.get('title', 'Sans titre')}")
        
        try:
            # Définir le nom du fichier de sortie
            if not output_filename:
                title = script_data.get('title', 'audio')
                output_filename = title.lower().replace(' ', '-')
            
            if not output_filename.endswith('.mp3'):
                output_filename += '.mp3'
            
            output_path = os.path.join(self.output_dir, output_filename) if self.output_dir else output_filename
            
            # Extraire le texte complet du script
            full_script = script_data.get('full_script', '')
            
            if not full_script:
                # Construire le script à partir des sections individuelles
                intro = script_data.get('intro', '')
                body = script_data.get('body', '')
                conclusion = script_data.get('conclusion', '')
                full_script = f"{intro}\n\n{body}\n\n{conclusion}"
            
            # Générer le fichier audio
            tts = gTTS(text=full_script, lang=self.language, slow=self.slow)
            tts.save(output_path)
            
            logger.info(f"Fichier audio généré: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du fichier audio: {str(e)}")
            return None
    
    def generate_section_audio(self, script_data, output_dir=None):
        """
        Génère des fichiers audio séparés pour chaque section du script.
        
        Args:
            script_data (dict): Données du script.
            output_dir (str): Répertoire de sortie pour les fichiers audio.
            
        Returns:
            dict: Chemins des fichiers audio générés pour chaque section.
        """
        if not output_dir:
            output_dir = self.output_dir
        
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        logger.info(f"Génération de fichiers audio par section pour le script: {script_data.get('title', 'Sans titre')}")
        
        try:
            title = script_data.get('title', 'audio').lower().replace(' ', '-')
            
            # Générer un fichier audio pour chaque section
            audio_paths = {}
            
            # Intro
            intro = script_data.get('intro', '')
            if intro:
                intro_path = os.path.join(output_dir, f"{title}-intro.mp3")
                tts = gTTS(text=intro, lang=self.language, slow=self.slow)
                tts.save(intro_path)
                audio_paths['intro'] = intro_path
                logger.info(f"Fichier audio d'introduction généré: {intro_path}")
            
            # Corps
            body = script_data.get('body', '')
            if body:
                body_path = os.path.join(output_dir, f"{title}-body.mp3")
                tts = gTTS(text=body, lang=self.language, slow=self.slow)
                tts.save(body_path)
                audio_paths['body'] = body_path
                logger.info(f"Fichier audio du corps généré: {body_path}")
            
            # Conclusion
            conclusion = script_data.get('conclusion', '')
            if conclusion:
                conclusion_path = os.path.join(output_dir, f"{title}-conclusion.mp3")
                tts = gTTS(text=conclusion, lang=self.language, slow=self.slow)
                tts.save(conclusion_path)
                audio_paths['conclusion'] = conclusion_path
                logger.info(f"Fichier audio de conclusion généré: {conclusion_path}")
            
            return audio_paths
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération des fichiers audio par section: {str(e)}")
            return {}


def main():
    """Fonction principale pour tester le générateur de voix."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Générer un fichier audio pour un short vidéo')
    parser.add_argument('script_json', help='Chemin vers le fichier JSON du script')
    parser.add_argument('--output', '-o', help='Répertoire de sortie pour le fichier audio')
    parser.add_argument('--language', '-l', default='fr', help='Code de langue pour la synthèse vocale')
    parser.add_argument('--slow', '-s', action='store_true', help='Générer la voix plus lentement')
    parser.add_argument('--sections', action='store_true', help='Générer des fichiers audio séparés pour chaque section')
    
    args = parser.parse_args()
    
    # Charger les données du script
    with open(args.script_json, 'r', encoding='utf-8') as f:
        script_data = json.load(f)
    
    # Générer le fichier audio
    generator = VoiceGenerator(output_dir=args.output, language=args.language, slow=args.slow)
    
    if args.sections:
        audio_paths = generator.generate_section_audio(script_data)
        if audio_paths:
            print(f"Fichiers audio générés par section:")
            for section, path in audio_paths.items():
                print(f"  {section}: {path}")
    else:
        audio_path = generator.generate_audio(script_data)
        if audio_path:
            print(f"Fichier audio généré: {audio_path}")
        else:
            print("Échec de la génération du fichier audio")


if __name__ == "__main__":
    main()
