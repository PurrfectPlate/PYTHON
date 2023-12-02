import subprocess
import os
import signal

class Livestream:
    
    
    stream_key = 'mfgf-w1qd-04kd-bqg1-4vgj'
    stream_url = 'rtmp://a.rtmp.youtube.com/live2'
    ffmpeg_process = None

    def __init__(self, url = stream_url, key = stream_key):
        self.stream_key = key
        self.stream_url = url

    # Define the FFmpeg command as a list of arguments
    ffmpeg_command = [
        'ffmpeg',
        '-f', 'v4l2',
        '-framerate', '25',
        '-video_size', '640x480',
        '-i', '/dev/video1',
        '-f', 'lavfi',
        '-i', 'anullsrc=r=44100:cl=stereo',
        '-vf', 'format=yuv420p',
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-tune', 'zerolatency',
        '-b:v', '1000k',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-max_interleave_delta', '0',
        '-f', 'flv',
        f'{stream_url}/{stream_key}'
    ]

    def run_livestream(self):
        # Run the FFmpeg command
        try:
            self.ffmpeg_process = subprocess.Popen(self.ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, preexec_fn=os.setsid, universal_newlines=True)
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")

    def stop_livestream(self):
        if self.ffmpeg_process is not None:
            # Send a SIGINT signal to terminate the FFmpeg process gracefully
            try:
                os.killpg(os.getpgid(self.ffmpeg_process.pid), signal.SIGINT)
                self.ffmpeg_process.communicate()
            except Exception as e:
                print(f"Error stopping livestream: {e}")
            finally:
                self.ffmpeg_process = None
                
