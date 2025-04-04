#!/bin/bash

# Script pour combiner la vidéo et l'audio
# Nécessite ffmpeg

ffmpeg -y -i video.mp4 -i audio.mp3 -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 -shortest combined.mp4
