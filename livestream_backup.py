import subprocess
import os
import signal

class Livestream:
    
    
    stream_key = 'mfgf-w1qd-04kd-bqg1-4vgj'
    stream_url = 'rtmp://a.rtmp.youtube.com/live2'
    credentials = None
    ffmpeg_process = None
    def __init__(self):
        self.stream_key = 'mfgf-w1qd-04kd-bqg1-4vgj'
        self.stream_url = 'rtmp://a.rtmp.youtube.com/live2'
        self.credentials = None
        self.ffmpeg_process = None

    def __init__(self, url, key, credentials):
        self.stream_key = key
        self.stream_url = url
        self.credentials = credentials

    # Define the FFmpeg command as a list of arguments
    ffmpeg_command = [
        'ffmpeg',
        '-f', 'v4l2',
        '-framerate', '25',
        '-video_size', '640x480',
        '-i', '/dev/video0',
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

livestream = Livestream('mfgf-w1qd-04kd-bqg1-4vgj', 'rtmp://a.rtmp.youtube.com/live2', None)

if __name__ == "__main__":
    try:
        livestream.run_livestream()
    except KeyboardInterrupt:
        livestream.stop_livestream()