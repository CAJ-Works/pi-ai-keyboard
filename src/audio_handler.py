
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
        self.device_index = None
        
        # Find USB Audio Device
        print("\n--- Audio Devices ---")
        found = False
        for i in range(self.audio.get_device_count()):
            dev = self.audio.get_device_info_by_index(i)
            print(f"Index {i}: {dev.get('name')} (Input Channels: {dev.get('maxInputChannels')})")
            # Look for USB Audio Codec or similar, and ensure it has inputs
            if not found and dev.get('maxInputChannels') > 0:
                name = dev.get('name').lower()
                if "usb" in name or "codec" in name or "pcm2902" in name:
                    self.device_index = i
                    print(f"*** Selected Input Device: {dev.get('name')} ***")
                    found = True
        print("---------------------\n")
        
        if self.device_index is None:
             print("WARNING: No specific USB Audio device found. Using system default.")

    def start_recording(self):
        self.frames = []
        self.is_recording = True
        try:
            self.stream = self.audio.open(format=FORMAT, channels=CHANNELS,
                                          rate=RATE, input=True,
                                          input_device_index=self.device_index,
                                          frames_per_buffer=CHUNK)
            print("Recording started...")
        except Exception as e:
            print(f"Error starting audio stream: {e}")
            self.is_recording = False

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
        print(f"DEBUG: Saving {len(self.frames)} audio frames.")
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
