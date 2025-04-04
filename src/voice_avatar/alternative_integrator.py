#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Solution alternative pour l'intégration audio-vidéo sans dépendances externes

Ce module fournit une solution simple pour combiner les fichiers audio et vidéo
en créant un script shell qui utilise ffmpeg (s'il est disponible) ou fournit
les deux fichiers séparément si l'intégration n'est pas possible.
"""

import os
import json
import logging
import subprocess
import shutil
from pathlib import Path

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AlternativeIntegrator:
    """Classe pour combiner des fichiers audio et vidéo sans dépendances externes."""
    
    def __init__(self, output_dir=None):
        """
        Initialise l'intégrateur alternatif.
        
        Args:
            output_dir (str): Répertoire de sortie pour les fichiers finaux.
        """
        self.output_dir = output_dir
        
        # Créer le répertoire de sortie s'il n'existe pas
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def integrate(self, video_path, audio_path, output_filename=None):
        """
        Tente d'intégrer un fichier audio à une vidéo, ou fournit les deux fichiers séparément.
        
        Args:
            video_path (str): Chemin de la vidéo d'entrée.
            audio_path (str): Chemin du fichier audio à intégrer.
            output_filename (str): Nom du fichier de sortie.
            
        Returns:
            str: Chemin de la vidéo générée ou du répertoire contenant les fichiers.
        """
        logger.info(f"Tentative d'intégration du fichier audio {audio_path} à la vidéo {video_path}")
        
        try:
            # Définir le nom du fichier de sortie
            if not output_filename:
                video_name = os.path.splitext(os.path.basename(video_path))[0]
                output_filename = f"{video_name}-with-voice.mp4"
            
            if not output_filename.endswith('.mp4'):
                output_filename += '.mp4'
            
            output_path = os.path.join(self.output_dir, output_filename) if self.output_dir else output_filename
            
            # Vérifier si ffmpeg est disponible
            try:
                subprocess.run(['ffmpeg', '-version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                ffmpeg_available = True
            except (subprocess.SubprocessError, FileNotFoundError):
                ffmpeg_available = False
                logger.warning("ffmpeg n'est pas disponible, utilisation de la méthode alternative")
            
            if ffmpeg_available:
                # Utiliser ffmpeg pour intégrer l'audio à la vidéo
                subprocess.run([
                    'ffmpeg', '-y',
                    '-i', video_path,
                    '-i', audio_path,
                    '-c:v', 'copy',
                    '-c:a', 'aac',
                    '-map', '0:v:0',
                    '-map', '1:a:0',
                    '-shortest',
                    output_path
                ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                logger.info(f"Vidéo avec voix générée: {output_path}")
                return output_path
            else:
                # Méthode alternative: créer un répertoire avec les deux fichiers et un script shell
                output_dir = os.path.splitext(output_path)[0]
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                
                # Copier les fichiers dans le répertoire
                video_dest = os.path.join(output_dir, "video.mp4")
                audio_dest = os.path.join(output_dir, "audio.mp3")
                shutil.copy2(video_path, video_dest)
                shutil.copy2(audio_path, audio_dest)
                
                # Créer un script shell pour l'intégration manuelle
                script_path = os.path.join(output_dir, "combine.sh")
                with open(script_path, 'w') as f:
                    f.write('#!/bin/bash\n\n')
                    f.write('# Script pour combiner la vidéo et l\'audio\n')
                    f.write('# Nécessite ffmpeg\n\n')
                    f.write('ffmpeg -y -i video.mp4 -i audio.mp3 -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 -shortest combined.mp4\n')
                
                # Rendre le script exécutable
                os.chmod(script_path, 0o755)
                
                # Créer un fichier README
                readme_path = os.path.join(output_dir, "README.txt")
                with open(readme_path, 'w') as f:
                    f.write("INSTRUCTIONS POUR COMBINER LA VIDÉO ET L'AUDIO\n\n")
                    f.write("Option 1: Utiliser le script shell (nécessite ffmpeg)\n")
                    f.write("1. Ouvrez un terminal dans ce répertoire\n")
                    f.write("2. Exécutez ./combine.sh\n\n")
                    f.write("Option 2: Utilisation manuelle\n")
                    f.write("1. Ouvrez la vidéo (video.mp4) dans votre lecteur vidéo\n")
                    f.write("2. Lancez l'audio (audio.mp3) en même temps\n\n")
                    f.write("Option 3: Utiliser un outil en ligne\n")
                    f.write("1. Utilisez un service en ligne comme https://www.kapwing.com/studio/editor\n")
                    f.write("2. Importez la vidéo et l'audio\n")
                    f.write("3. Exportez la vidéo combinée\n")
                
                logger.info(f"Fichiers audio et vidéo préparés dans: {output_dir}")
                return output_dir
            
        except Exception as e:
            logger.error(f"Erreur lors de l'intégration audio-vidéo: {str(e)}")
            return None


def main():
    """Fonction principale pour tester l'intégrateur alternatif."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Intégrer un fichier audio à une vidéo')
    parser.add_argument('video_path', help='Chemin de la vidéo d\'entrée')
    parser.add_argument('audio_path', help='Chemin du fichier audio à intégrer')
    parser.add_argument('--output', '-o', help='Répertoire de sortie pour les fichiers finaux')
    parser.add_argument('--output-filename', '-f', help='Nom du fichier de sortie')
    
    args = parser.parse_args()
    
    # Intégrer l'audio à la vidéo
    integrator = AlternativeIntegrator(output_dir=args.output)
    output_path = integrator.integrate(args.video_path, args.audio_path, args.output_filename)
    
    if output_path:
        print(f"Intégration réussie: {output_path}")
    else:
        print("Échec de l'intégration audio-vidéo")


if __name__ == "__main__":
    main()
