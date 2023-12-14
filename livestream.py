import subprocess
import os
import signal

class Livestream:
    
    
    #stream_key = 'mfgf-w1qd-04kd-bqg1-4vgj'
    #stream_url = 'rtmp://a.rtmp.youtube.com/live2'
    ffmpeg_process = None

    def __init__(self, url = 'rtmp://a.rtmp.youtube.com/live2', key = 'mfgf-w1qd-04kd-bqg1-4vgj'):
        self.stream_key = key
        self.stream_url = url

        # Define the FFmpeg command as a list of arguments
        self.ffmpeg_command = [
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
            f'{self.stream_url}/{self.stream_key}'
        ]
        self.bash_command = f"/home/purrfectplate/PYTHON/stream_to_youtube.sh {self.stream_url} {self.stream_key}"

    def run_livestream(self):
        # Run the FFmpeg command
        try:
            subprocess.run(
                self.bash_command,
                shell=True,
                #stdout=subprocess.DEVNULL,
                #stderr=subprocess.DEVNULL
            )
            
            
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
        except KeyboardInterrupt:
            print("Livestream interrupted by user.")
        finally:
            # Set a flag or handle the livestream stopping event here
            pass
            
def stop_livestream():
    try:
        subprocess.run("killall ffmpeg", shell=True)
    except Exception as e:
        print(f"Error stopping livestream: {e}")
