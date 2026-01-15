
import pyaudio
import wave
import os

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
TEMP_FILENAME = "/tmp/recording.wav"

class AudioHandler:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.frames = []
        self.stream = None
        self.is_recording = False

    def start_recording(self):
        self.frames = []
        self.is_recording = True
        self.stream = self.audio.open(format=FORMAT, channels=CHANNELS,
                                      rate=RATE, input=True,
                                      frames_per_buffer=CHUNK)
        print("Recording started...")

    def record_chunk(self):
        if self.is_recording and self.stream:
            data = self.stream.read(CHUNK, exception_on_overflow=False)
            self.frames.append(data)

    def stop_recording(self):
        if not self.is_recording:
            return None
        
        self.is_recording = False
        print("Recording stopped.")
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

        return self._save_file()

    def _save_file(self):
        # Ensure tmp dir exists (it usually does on Linux)
        if not os.path.exists(os.path.dirname(TEMP_FILENAME)):
            return None

        wf = wave.open(TEMP_FILENAME, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(self.audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        return TEMP_FILENAME

    def cleanup(self):
        self.audio.terminate()

if __name__ == "__main__":
    import time
    handler = AudioHandler()
    try:
        handler.start_recording()
        for _ in range(0, int(RATE / CHUNK * 3)): # Record for 3 seconds
            handler.record_chunk()
        filename = handler.stop_recording()
        print(f"Saved to {filename}")
    finally:
        handler.cleanup()
