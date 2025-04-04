#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Générateur de scripts pour shorts vidéo

Ce module permet de générer un script court à partir du contenu d'un article,
adapté pour les shorts vidéo sur YouTube, Instagram et TikTok.
"""

import os
import json
import re
import logging
from pathlib import Path

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ShortScriptGenerator:
    """Classe pour générer des scripts de shorts vidéo à partir d'articles."""
    
    def __init__(self, max_duration=60, max_words=150):
        """
        Initialise le générateur de scripts.
        
        Args:
            max_duration (int): Durée maximale du short en secondes.
            max_words (int): Nombre maximum de mots dans le script.
        """
        self.max_duration = max_duration
        self.max_words = max_words
    
    def generate_script(self, article_data):
        """
        Génère un script pour un short vidéo à partir des données d'un article.
        
        Args:
            article_data (dict): Données de l'article (titre, contenu, etc.).
            
        Returns:
            dict: Script généré avec différentes sections.
        """
        logger.info(f"Génération d'un script pour l'article: {article_data.get('title', 'Sans titre')}")
        
        try:
            # Extraire les informations clés de l'article
            title = article_data.get('title', 'Sans titre')
            author = article_data.get('author', 'Auteur inconnu')
            summary = article_data.get('summary', '')
            content = article_data.get('content', [])
            url = article_data.get('url', '')
            
            # Générer l'introduction
            intro = self._generate_intro(title, author)
            
            # Générer le corps du script
            body = self._generate_body(content, summary)
            
            # Générer la conclusion
            conclusion = self._generate_conclusion(title, url)
            
            # Assembler le script complet
            full_script = f"{intro}\n\n{body}\n\n{conclusion}"
            
            # Vérifier et ajuster la longueur du script
            full_script = self._adjust_script_length(full_script)
            
            # Structurer le script en sections
            script_data = {
                'title': title,
                'intro': intro,
                'body': body,
                'conclusion': conclusion,
                'full_script': full_script,
                'word_count': len(full_script.split()),
                'estimated_duration': self._estimate_duration(full_script),
                'article_url': url
            }
            
            return script_data
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du script: {str(e)}")
            return None
    
    def _generate_intro(self, title, author):
        """
        Génère l'introduction du script.
        
        Args:
            title (str): Titre de l'article.
            author (str): Auteur de l'article.
            
        Returns:
            str: Introduction du script.
        """
        intro_templates = [
            f"Bonjour à tous ! Aujourd'hui, je vous présente un article intéressant intitulé \"{title}\".",
            f"Salut ! Je vais vous parler de \"{title}\", un article qui mérite votre attention.",
            f"Bienvenue ! Dans cette vidéo, je vais vous résumer l'article \"{title}\"."
        ]
        
        # Choisir aléatoirement un template
        import random
        intro = random.choice(intro_templates)
        
        # Ajouter l'auteur si disponible
        if author and author != "Auteur inconnu":
            intro += f" Cet article a été écrit par {author}."
        
        return intro
    
    def _generate_body(self, content, summary):
        """
        Génère le corps du script.
        
        Args:
            content (list): Contenu de l'article.
            summary (str): Résumé de l'article.
            
        Returns:
            str: Corps du script.
        """
        # Si un résumé est disponible, l'utiliser comme base
        if summary and len(summary) > 20:
            return summary
        
        # Sinon, extraire les points clés du contenu
        key_points = []
        
        # Filtrer les sections pertinentes (titres, paragraphes importants)
        for section in content:
            section_type = section.get('type', '').upper()
            section_text = section.get('text', '')
            
            # Prioriser les titres et les paragraphes courts
            if section_type in ['H1', 'H2', 'H3', 'H4'] and section_text:
                key_points.append(section_text)
            elif section_type == 'P' and 20 <= len(section_text) <= 200:
                key_points.append(section_text)
            
            # Limiter le nombre de points clés
            if len(key_points) >= 3:
                break
        
        # Si aucun point clé n'a été trouvé, utiliser les premiers paragraphes
        if not key_points:
            for section in content:
                if section.get('type', '').upper() == 'P' and section.get('text', ''):
                    key_points.append(section.get('text', ''))
                    if len(key_points) >= 2:
                        break
        
        # Assembler les points clés
        if key_points:
            body = "Voici ce que vous devez retenir : "
            for i, point in enumerate(key_points):
                # Limiter la longueur de chaque point
                if len(point) > 100:
                    point = point[:97] + "..."
                
                body += f"{point} "
            
            return body.strip()
        
        # Fallback si aucun contenu n'est disponible
        return "Cet article contient des informations intéressantes que vous pourrez découvrir en lisant l'article complet."
    
    def _generate_conclusion(self, title, url):
        """
        Génère la conclusion du script.
        
        Args:
            title (str): Titre de l'article.
            url (str): URL de l'article.
            
        Returns:
            str: Conclusion du script.
        """
        conclusion_templates = [
            f"Pour en savoir plus sur \"{title}\", consultez le lien dans la description.",
            f"Si ce sujet vous intéresse, je vous invite à lire l'article complet. Le lien est dans la description.",
            f"Pour un tutoriel détaillé, cliquez sur le lien dans la description pour accéder à l'article complet."
        ]
        
        # Choisir aléatoirement un template
        import random
        conclusion = random.choice(conclusion_templates)
        
        # Ajouter une phrase d'engagement
        engagement_phrases = [
            "N'oubliez pas de liker et de vous abonner pour plus de contenus comme celui-ci !",
            "Si cette vidéo vous a plu, n'hésitez pas à la partager et à vous abonner !",
            "Merci d'avoir regardé ! Abonnez-vous pour ne manquer aucun de mes prochains shorts !"
        ]
        
        conclusion += f" {random.choice(engagement_phrases)}"
        
        return conclusion
    
    def _adjust_script_length(self, script):
        """
        Ajuste la longueur du script pour respecter les contraintes.
        
        Args:
            script (str): Script complet.
            
        Returns:
            str: Script ajusté.
        """
        words = script.split()
        
        if len(words) <= self.max_words:
            return script
        
        # Réduire le script en conservant l'introduction et la conclusion
        parts = script.split('\n\n')
        
        if len(parts) >= 3:
            intro = parts[0]
            conclusion = parts[-1]
            
            # Réduire le corps du texte
            body_words = ' '.join(parts[1:-1]).split()
            max_body_words = self.max_words - len(intro.split()) - len(conclusion.split())
            
            if max_body_words > 0:
                adjusted_body = ' '.join(body_words[:max_body_words])
                return f"{intro}\n\n{adjusted_body}\n\n{conclusion}"
        
        # Si la structure n'est pas comme attendue, simplement tronquer
        return ' '.join(words[:self.max_words])
    
    def _estimate_duration(self, script):
        """
        Estime la durée du script en secondes.
        
        Args:
            script (str): Script complet.
            
        Returns:
            int: Durée estimée en secondes.
        """
        # Estimation basée sur le nombre de mots (environ 2.5 mots par seconde)
        word_count = len(script.split())
        return min(int(word_count / 2.5), self.max_duration)
    
    def save_script(self, script_data, output_dir):
        """
        Sauvegarde le script généré au format JSON.
        
        Args:
            script_data (dict): Données du script.
            output_dir (str): Répertoire de sortie.
            
        Returns:
            str: Chemin du fichier JSON créé.
        """
        if not output_dir:
            return None
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Créer un nom de fichier basé sur le titre
        title = script_data.get('title', 'script')
        filename = re.sub(r'[^\w\s-]', '', title).strip().lower()
        filename = re.sub(r'[-\s]+', '-', filename)
        
        json_path = os.path.join(output_dir, f'{filename}-script.json')
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(script_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Script sauvegardé: {json_path}")
        return json_path


def main():
    """Fonction principale pour tester le générateur de scripts."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Générer un script pour un short vidéo')
    parser.add_argument('article_json', help='Chemin vers le fichier JSON de l\'article')
    parser.add_argument('--output', '-o', help='Répertoire de sortie pour le script')
    parser.add_argument('--duration', '-d', type=int, default=60, help='Durée maximale du short en secondes')
    
    args = parser.parse_args()
    
    # Charger les données de l'article
    with open(args.article_json, 'r', encoding='utf-8') as f:
        article_data = json.load(f)
    
    # Générer le script
    generator = ShortScriptGenerator(max_duration=args.duration)
    script_data = generator.generate_script(article_data)
    
    if script_data:
        print(f"Script généré pour: {script_data['title']}")
        print(f"Nombre de mots: {script_data['word_count']}")
        print(f"Durée estimée: {script_data['estimated_duration']} secondes")
        print("\nScript complet:")
        print(script_data['full_script'])
        
        # Sauvegarder le script
        if args.output:
            json_path = generator.save_script(script_data, args.output)
            if json_path:
                print(f"\nScript sauvegardé: {json_path}")
    else:
        print("Échec de la génération du script")


if __name__ == "__main__":
    main()
