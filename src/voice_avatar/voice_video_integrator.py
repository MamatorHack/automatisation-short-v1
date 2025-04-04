#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Intégrateur de voix et vidéo pour shorts

Ce module permet d'intégrer un fichier audio à une vidéo,
créant ainsi un short vidéo complet avec voix.
"""

import os
import json
import logging
import subprocess
from pathlib import Path

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VoiceVideoIntegrator:
    """Classe pour intégrer des fichiers audio à des vidéos."""
    
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
            else:
                # Méthode alternative utilisant OpenCV et moviepy si disponibles
                try:
                    from moviepy.editor import VideoFileClip, AudioFileClip
                    
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
                    
                except ImportError:
                    logger.error("Ni ffmpeg ni moviepy ne sont disponibles pour l'intégration audio-vidéo")
                    return None
            
            logger.info(f"Vidéo avec voix générée: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Erreur lors de l'intégration audio-vidéo: {str(e)}")
            return None
    
    def integrate_sections(self, video_path, audio_paths, output_filename=None):
        """
        Intègre plusieurs fichiers audio à différentes sections d'une vidéo.
        
        Args:
            video_path (str): Chemin de la vidéo d'entrée.
            audio_paths (dict): Dictionnaire des chemins audio par section.
            output_filename (str): Nom du fichier de sortie.
            
        Returns:
            str: Chemin de la vidéo générée.
        """
        logger.info(f"Intégration de fichiers audio par section à la vidéo {video_path}")
        
        try:
            # Définir le nom du fichier de sortie
            if not output_filename:
                video_name = os.path.splitext(os.path.basename(video_path))[0]
                output_filename = f"{video_name}-with-voice.mp4"
            
            if not output_filename.endswith('.mp4'):
                output_filename += '.mp4'
            
            output_path = os.path.join(self.output_dir, output_filename) if self.output_dir else output_filename
            
            # Vérifier si moviepy est disponible
            try:
                from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
                moviepy_available = True
            except ImportError:
                moviepy_available = False
                logger.warning("moviepy n'est pas disponible, utilisation de la méthode alternative")
            
            if moviepy_available and len(audio_paths) > 0:
                # Charger la vidéo
                video_clip = VideoFileClip(video_path)
                
                # Calculer la durée de chaque section
                total_duration = video_clip.duration
                section_duration = total_duration / len(audio_paths)
                
                # Créer des sous-clips pour chaque section
                subclips = []
                current_time = 0
                
                for section, audio_path in audio_paths.items():
                    # Charger l'audio
                    audio_clip = AudioFileClip(audio_path)
                    
                    # Créer un sous-clip pour cette section
                    end_time = min(current_time + section_duration, total_duration)
                    subclip = video_clip.subclip(current_time, end_time)
                    
                    # Ajuster la durée de l'audio si nécessaire
                    if audio_clip.duration > subclip.duration:
                        audio_clip = audio_clip.subclip(0, subclip.duration)
                    
                    # Ajouter l'audio au sous-clip
                    subclip = subclip.set_audio(audio_clip)
                    subclips.append(subclip)
                    
                    current_time = end_time
                
                # Concaténer les sous-clips
                final_clip = concatenate_videoclips(subclips)
                
                # Exporter la vidéo finale
                final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
                
                # Fermer les clips
                video_clip.close()
                final_clip.close()
                
            else:
                # Si moviepy n'est pas disponible ou s'il n'y a pas de sections audio,
                # utiliser la méthode simple avec le premier fichier audio disponible
                if audio_paths:
                    first_audio = next(iter(audio_paths.values()))
                    return self.integrate(video_path, first_audio, output_filename)
                else:
                    logger.error("Aucun fichier audio fourni pour l'intégration")
                    return None
            
            logger.info(f"Vidéo avec voix générée: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Erreur lors de l'intégration audio-vidéo par sections: {str(e)}")
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
    integrator = VoiceVideoIntegrator(output_dir=args.output)
    output_path = integrator.integrate(args.video_path, args.audio_path, args.output_filename)
    
    if output_path:
        print(f"Vidéo avec voix générée: {output_path}")
    else:
        print("Échec de l'intégration audio-vidéo")


if __name__ == "__main__":
    main()
