# Guide d'utilisation - Générateur de Shorts Vidéo

## Introduction

Le Générateur de Shorts Vidéo est un outil open-source qui automatise la création de courts clips vidéo (shorts) à partir d'articles Medium. Cet outil vous permet de transformer rapidement vos articles en contenu vidéo engageant pour YouTube, Instagram et TikTok, avec votre voix et une présentation visuelle attrayante.

## Fonctionnalités

- Extraction du contenu des articles Medium
- Génération automatique de scripts adaptés au format court
- Création de vidéos au format vertical (1080x1920) optimisé pour les shorts
- Synthèse vocale pour la narration
- Intégration audio-vidéo (ou préparation des fichiers pour assemblage)

## Prérequis

- Python 3.8 ou supérieur
- Pip (gestionnaire de paquets Python)
- Connexion Internet (pour l'extraction d'articles et la synthèse vocale)

## Installation

1. Clonez le dépôt ou téléchargez l'archive du projet
2. Installez les dépendances requises :

```bash
pip install beautifulsoup4 requests gTTS opencv-python pillow
```

3. Pour une intégration audio-vidéo optimale, installez également :

```bash
pip install moviepy
```

4. (Optionnel) Pour une meilleure qualité d'intégration, installez FFmpeg :
   - Sur Ubuntu/Debian : `sudo apt install ffmpeg`
   - Sur macOS avec Homebrew : `brew install ffmpeg`
   - Sur Windows : Téléchargez depuis [ffmpeg.org](https://ffmpeg.org/download.html)

## Structure du projet

```
shorts_generator/
├── src/
│   ├── parser/              # Extraction d'articles Medium
│   ├── generator/           # Génération de scripts et vidéos
│   ├── voice_avatar/        # Génération de voix et intégration
│   └── shorts_generator.py  # Script principal
├── output/                  # Répertoire de sortie
│   ├── articles/            # Articles extraits (JSON)
│   ├── scripts/             # Scripts générés (JSON)
│   ├── videos/              # Vidéos sans audio
│   ├── audio/               # Fichiers audio générés
│   └── final/               # Shorts vidéo finaux
└── README.md                # Documentation
```

## Utilisation

### Ligne de commande

Pour générer un short à partir d'une URL Medium :

```bash
python src/shorts_generator.py --url https://medium.com/votre-article --output output
```

Pour générer un short à partir d'un fichier JSON d'article :

```bash
python src/shorts_generator.py --json chemin/vers/article.json --output output
```

Options disponibles :
- `--url` ou `-u` : URL de l'article Medium
- `--json` ou `-j` : Chemin vers un fichier JSON d'article
- `--output` ou `-o` : Répertoire de sortie (optionnel)
- `--language` ou `-l` : Code de langue pour la synthèse vocale (par défaut : fr)

### Résultats

Après exécution, vous trouverez dans le répertoire de sortie :
- L'article extrait au format JSON
- Le script généré au format JSON
- La vidéo sans audio
- Le fichier audio de narration
- Le résultat final (vidéo avec audio ou dossier avec instructions)

## Personnalisation

### Modification du style visuel

Pour personnaliser l'apparence des vidéos, modifiez les paramètres dans `src/generator/video_generator.py` :
- Couleurs de fond et de texte
- Police et taille du texte
- Durée des transitions

### Ajustement de la voix

Pour modifier les paramètres de la voix, ajustez les options dans `src/voice_avatar/voice_generator.py` :
- Langue de la synthèse vocale
- Vitesse de parole

## Limitations connues

- L'extraction d'articles Medium peut être limitée par les protections anti-scraping
- L'intégration audio-vidéo nécessite FFmpeg ou moviepy pour un résultat optimal
- La synthèse vocale utilise gTTS et nécessite une connexion Internet

## Dépannage

### Problèmes d'extraction d'articles

Si l'extraction d'un article échoue, essayez :
1. Vérifier que l'URL est correcte et accessible
2. Utiliser un article public (non réservé aux membres)
3. Créer manuellement un fichier JSON d'article (voir format dans `src/generator/example_article.json`)

### Problèmes d'intégration audio-vidéo

Si l'intégration audio-vidéo échoue :
1. Vérifiez que FFmpeg est installé et accessible dans le PATH
2. Installez moviepy : `pip install moviepy`
3. Utilisez les fichiers séparés (vidéo et audio) fournis dans le dossier final

## Contribution

Ce projet est open-source et les contributions sont les bienvenues. N'hésitez pas à :
- Signaler des bugs
- Proposer des améliorations
- Soumettre des pull requests

## Licence

Ce projet est distribué sous licence MIT.
