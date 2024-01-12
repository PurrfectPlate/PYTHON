#!/bin/bash

# Extract YouTube URL and stream key from arguments
youtube_url=$1
stream_key=$2

# Run ffmpeg command with the provided YouTube URL and stream key
ffmpeg -f v4l2 -framerate 25 -video_size 640x480 -i /dev/video0 -f lavfi -i anullsrc=r=44100:cl=stereo -vf format=yuv420p -c:v libx264 -preset ultrafast -tune zerolatency -b:v 1000k -c:a aac -b:a 128k -max_interleave_delta 0 -f flv "$youtube_url/$stream_key"
