#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Intégrateur de voix et vidéo pour shorts (version simplifiée)

Ce module permet d'intégrer un fichier audio à une vidéo,
créant ainsi un short vidéo complet avec voix.
Cette version simplifiée utilise directement moviepy sans vérifications complexes.
"""

import os
import json
import logging
from pathlib import Path
from moviepy.editor import VideoFileClip, AudioFileClip

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleVoiceVideoIntegrator:
    """Classe simplifiée pour intégrer des fichiers audio à des vidéos."""
    
    def __init__(self, output_dir=None):
        """
        Initialise l'intégrateur de voix et vidéo.
        
        Args:
            output_dir (str): Répertoire de sortie pour les vidéos finales.
        """
        self.output_dir = output_dir
        
        # Créer le répertoire de sortie s'il n'existe pas
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def integrate(self, video_path, audio_path, output_filename=None):
        """
        Intègre un fichier audio à une vidéo.
        
        Args:
            video_path (str): Chemin de la vidéo d'entrée.
            audio_path (str): Chemin du fichier audio à intégrer.
            output_filename (str): Nom du fichier de sortie.
            
        Returns:
            str: Chemin de la vidéo générée.
        """
        logger.info(f"Intégration du fichier audio {audio_path} à la vidéo {video_path}")
        
        try:
            # Définir le nom du fichier de sortie
            if not output_filename:
                video_name = os.path.splitext(os.path.basename(video_path))[0]
                output_filename = f"{video_name}-with-voice.mp4"
            
            if not output_filename.endswith('.mp4'):
                output_filename += '.mp4'
            
            output_path = os.path.join(self.output_dir, output_filename) if self.output_dir else output_filename
            
            # Charger la vidéo et l'audio
            video_clip = VideoFileClip(video_path)
            audio_clip = AudioFileClip(audio_path)
            
            # Ajuster la durée de la vidéo ou de l'audio si nécessaire
            if video_clip.duration > audio_clip.duration:
                video_clip = video_clip.subclip(0, audio_clip.duration)
            
            # Ajouter l'audio à la vidéo
            final_clip = video_clip.set_audio(audio_clip)
            
            # Exporter la vidéo finale
            final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
            
            # Fermer les clips
            video_clip.close()
            audio_clip.close()
            final_clip.close()
            
            logger.info(f"Vidéo avec voix générée: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Erreur lors de l'intégration audio-vidéo: {str(e)}")
            return None


def main():
    """Fonction principale pour tester l'intégrateur de voix et vidéo."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Intégrer un fichier audio à une vidéo')
    parser.add_argument('video_path', help='Chemin de la vidéo d\'entrée')
    parser.add_argument('audio_path', help='Chemin du fichier audio à intégrer')
    parser.add_argument('--output', '-o', help='Répertoire de sortie pour la vidéo finale')
    parser.add_argument('--output-filename', '-f', help='Nom du fichier de sortie')
    
    args = parser.parse_args()
    
    # Intégrer l'audio à la vidéo
    integrator = SimpleVoiceVideoIntegrator(output_dir=args.output)
    output_path = integrator.integrate(args.video_path, args.audio_path, args.output_filename)
    
    if output_path:
        print(f"Vidéo avec voix générée: {output_path}")
    else:
        print("Échec de l'intégration audio-vidéo")


if __name__ == "__main__":
    main()
