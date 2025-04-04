#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Générateur de vidéos pour shorts

Ce module permet de générer une vidéo à partir d'un script,
adaptée pour les shorts vidéo sur YouTube, Instagram et TikTok.
"""

import os
import json
import logging
import subprocess
from pathlib import Path
import textwrap
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ShortVideoGenerator:
    """Classe pour générer des vidéos de shorts à partir de scripts."""
    
    def __init__(self, output_dir=None, font_path=None, background_color=(25, 25, 112), 
                 text_color=(255, 255, 255), width=1080, height=1920, fps=30):
        """
        Initialise le générateur de vidéos.
        
        Args:
            output_dir (str): Répertoire de sortie pour les vidéos.
            font_path (str): Chemin vers la police à utiliser pour le texte.
            background_color (tuple): Couleur de fond (R, G, B).
            text_color (tuple): Couleur du texte (R, G, B).
            width (int): Largeur de la vidéo en pixels.
            height (int): Hauteur de la vidéo en pixels.
            fps (int): Images par seconde.
        """
        self.output_dir = output_dir
        self.background_color = background_color
        self.text_color = text_color
        self.width = width
        self.height = height
        self.fps = fps
        
        # Créer le répertoire de sortie s'il n'existe pas
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Définir la police
        if font_path and os.path.exists(font_path):
            self.font_path = font_path
        else:
            # Utiliser une police par défaut
            self.font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            if not os.path.exists(self.font_path):
                # Chercher une police disponible
                font_dirs = [
                    "/usr/share/fonts/truetype",
                    "/usr/share/fonts",
                    "/usr/local/share/fonts"
                ]
                for font_dir in font_dirs:
                    if os.path.exists(font_dir):
                        for root, _, files in os.walk(font_dir):
                            for file in files:
                                if file.endswith(('.ttf', '.otf')):
                                    self.font_path = os.path.join(root, file)
                                    break
                            if hasattr(self, 'font_path'):
                                break
                    if hasattr(self, 'font_path'):
                        break
        
        logger.info(f"Police utilisée: {self.font_path}")
    
    def generate_video(self, script_data, output_filename=None):
        """
        Génère une vidéo à partir d'un script.
        
        Args:
            script_data (dict): Données du script.
            output_filename (str): Nom du fichier de sortie.
            
        Returns:
            str: Chemin de la vidéo générée.
        """
        logger.info(f"Génération d'une vidéo pour le script: {script_data.get('title', 'Sans titre')}")
        
        try:
            # Définir le nom du fichier de sortie
            if not output_filename:
                title = script_data.get('title', 'video')
                output_filename = title.lower().replace(' ', '-')
            
            if not output_filename.endswith('.mp4'):
                output_filename += '.mp4'
            
            output_path = os.path.join(self.output_dir, output_filename) if self.output_dir else output_filename
            
            # Créer les images pour chaque partie du script
            frames = []
            
            # Intro
            intro_frames = self._create_text_frames(
                script_data.get('intro', ''),
                duration=5,  # 5 secondes pour l'intro
                title=script_data.get('title', '')
            )
            frames.extend(intro_frames)
            
            # Corps
            body_frames = self._create_text_frames(
                script_data.get('body', ''),
                duration=script_data.get('estimated_duration', 30) - 10,  # Durée totale - intro - conclusion
                title=''
            )
            frames.extend(body_frames)
            
            # Conclusion
            conclusion_frames = self._create_text_frames(
                script_data.get('conclusion', ''),
                duration=5,  # 5 secondes pour la conclusion
                title='',
                include_url=True,
                url=script_data.get('article_url', '')
            )
            frames.extend(conclusion_frames)
            
            # Générer la vidéo à partir des images
            self._create_video_from_frames(frames, output_path)
            
            logger.info(f"Vidéo générée: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de la vidéo: {str(e)}")
            return None
    
    def _create_text_frames(self, text, duration, title='', include_url=False, url=''):
        """
        Crée une série d'images avec du texte.
        
        Args:
            text (str): Texte à afficher.
            duration (int): Durée en secondes.
            title (str): Titre à afficher en haut.
            include_url (bool): Si True, inclut l'URL en bas.
            url (str): URL à afficher.
            
        Returns:
            list: Liste d'images (numpy arrays).
        """
        # Calculer le nombre d'images
        num_frames = int(duration * self.fps)
        
        # Créer une image de base
        img = Image.new('RGB', (self.width, self.height), color=self.background_color)
        draw = ImageDraw.Draw(img)
        
        # Définir les polices
        try:
            title_font = ImageFont.truetype(self.font_path, 60)
            text_font = ImageFont.truetype(self.font_path, 48)
            url_font = ImageFont.truetype(self.font_path, 36)
        except Exception as e:
            logger.error(f"Erreur lors du chargement des polices: {str(e)}")
            # Utiliser les polices par défaut
            title_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
            url_font = ImageFont.load_default()
        
        # Dessiner le titre si présent
        if title:
            # Wrapper le texte
            wrapped_title = textwrap.fill(title, width=30)
            title_bbox = draw.textbbox((0, 0), wrapped_title, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_height = title_bbox[3] - title_bbox[1]
            
            draw.text(
                ((self.width - title_width) // 2, 100),
                wrapped_title,
                font=title_font,
                fill=self.text_color,
                align='center'
            )
            
            # Ajuster le point de départ du texte principal
            text_y = 100 + title_height + 50
        else:
            text_y = 200
        
        # Wrapper le texte principal
        wrapped_text = textwrap.fill(text, width=40)
        
        # Dessiner le texte principal
        text_bbox = draw.textbbox((0, 0), wrapped_text, font=text_font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        draw.text(
            ((self.width - text_width) // 2, text_y),
            wrapped_text,
            font=text_font,
            fill=self.text_color,
            align='center'
        )
        
        # Dessiner l'URL si nécessaire
        if include_url and url:
            url_text = "Lien dans la description"
            url_bbox = draw.textbbox((0, 0), url_text, font=url_font)
            url_width = url_bbox[2] - url_bbox[0]
            
            draw.text(
                ((self.width - url_width) // 2, self.height - 200),
                url_text,
                font=url_font,
                fill=self.text_color,
                align='center'
            )
        
        # Convertir l'image en array numpy
        img_array = np.array(img)
        
        # Créer une liste d'images identiques pour la durée spécifiée
        frames = [img_array] * num_frames
        
        return frames
    
    def _create_video_from_frames(self, frames, output_path):
        """
        Crée une vidéo à partir d'une liste d'images.
        
        Args:
            frames (list): Liste d'images (numpy arrays).
            output_path (str): Chemin du fichier de sortie.
        """
        # Vérifier qu'il y a des images
        if not frames:
            raise ValueError("Aucune image à inclure dans la vidéo")
        
        # Créer le writer vidéo
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video = cv2.VideoWriter(output_path, fourcc, self.fps, (self.width, self.height))
        
        # Ajouter chaque image à la vidéo
        for frame in frames:
            # Convertir de RGB à BGR (OpenCV utilise BGR)
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            video.write(frame_bgr)
        
        # Fermer le writer
        video.release()
        
        # Optimiser la vidéo avec FFmpeg si disponible
        try:
            temp_output = output_path + ".temp.mp4"
            subprocess.run([
                'ffmpeg', '-y', '-i', output_path, 
                '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
                '-c:a', 'aac', '-b:a', '128k',
                temp_output
            ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Remplacer le fichier original
            os.replace(temp_output, output_path)
            logger.info("Vidéo optimisée avec FFmpeg")
        except Exception as e:
            logger.warning(f"Impossible d'optimiser la vidéo avec FFmpeg: {str(e)}")


def main():
    """Fonction principale pour tester le générateur de vidéos."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Générer une vidéo pour un short')
    parser.add_argument('script_json', help='Chemin vers le fichier JSON du script')
    parser.add_argument('--output', '-o', help='Répertoire de sortie pour la vidéo')
    parser.add_argument('--font', '-f', help='Chemin vers la police à utiliser')
    
    args = parser.parse_args()
    
    # Charger les données du script
    with open(args.script_json, 'r', encoding='utf-8') as f:
        script_data = json.load(f)
    
    # Générer la vidéo
    generator = ShortVideoGenerator(output_dir=args.output, font_path=args.font)
    video_path = generator.generate_video(script_data)
    
    if video_path:
        print(f"Vidéo générée: {video_path}")
    else:
        print("Échec de la génération de la vidéo")


if __name__ == "__main__":
    main()
