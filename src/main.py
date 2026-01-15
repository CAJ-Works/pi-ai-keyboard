
import time
import os
import signal
import sys
import evdev 
from select import select
from evdev import InputDevice, categorize, ecodes
from audio_handler import AudioHandler
from llm_client import LLMClient
from keyboard_mapper import type_string
from ctypes import *
from contextlib import contextmanager

# Suppress ALSA/Jack error messages
ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)
def py_error_handler(filename, line, function, err, fmt):
    pass
c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)

@contextmanager
def no_alsa_err():
    asound = cdll.LoadLibrary('libasound.so.2')
    asound.snd_lib_error_set_handler(c_error_handler)
    yield
    asound.snd_lib_error_set_handler(None)

# Input Configuration
# Search for a device with this name. Common for USB Keyboards.
# You might need to check 'evtest' if your keyboard is named differently.
DEVICE_NAME_SEARCH = "Keyboard" 

# Map Button Codes to Instructions
# Using Function keys to avoid accidental typing if the keyboard is also doing other things (though we grab it).
INPUT_MAP = {
    ecodes.KEY_F1: "Transcribe the following audio precisely.",
    ecodes.KEY_F2: "Summarize the following audio into a concise paragraph.",
    ecodes.KEY_F3: "Format the following code or text structure cleanly.",
}

# State
current_instruction = None
is_processing = False

def find_device():
    print("Scanning for input devices...")
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    
    # First pass: Look for exact or partial match of DEVICE_NAME_SEARCH
    for d in devices:
        print(f"  Found: {d.path}: {d.name}")
        if DEVICE_NAME_SEARCH.lower() in d.name.lower():
            print(f"Selecting device: {d.name} ({d.path})")
            return d
    
    # Fallback: If no "Keyboard" found, maybe it's just a generic "USB Device"
    # User can verify with evtest.
    return None

def main():
    global current_instruction, is_processing

    # Initialize handlers
    print("Initializing services...")
    llm_client = LLMClient()
    
    # Initialize AudioHandler with ALSA suppression
    with no_alsa_err():
        audio_handler = AudioHandler()

    print("Looking for input device...")
    device = find_device()
    while device is None:
        print(f"Device matching '{DEVICE_NAME_SEARCH}' not found. Retrying in 5s...")
        time.sleep(5)
        device = find_device()

    print(f"Listening for events on {device.name}...")
    
    # Grab device
    try:
        device.grab()
    except Exception as e:
        print(f"Warning: Could not grab device: {e}")

    try:
        while True:
            # 1. Handle Audio Recording
            if audio_handler.is_recording:
                # Record a chunk. This is non-blocking (short duration)
                audio_handler.record_chunk()
            
            # 2. Handle Input Events (Non-blocking check)
            try:
                # read() returns a generator of events, or None?
                # actually read() yields events available. 
                # causing a block if we iterate? No, read() is usually blocking on file descriptor.
                # using read_one() might be better if we want strict non-blocking, but evdev blocking is intricate.
                # Better approach: select/poll
                
                # We can use read_loop() if we use async, but here we are synchronous.
                # Let's use select on the file descriptor with a timeout of 0
                r, w, x = select([device.fd], [], [], 0.0)
                if r:
                    for event in device.read():
                        if event.type == ecodes.EV_KEY:
                            if event.value == 1: # Key Down
                                if event.code in INPUT_MAP:
                                    instruction = INPUT_MAP[event.code]
                                    if not is_processing and not audio_handler.is_recording:
                                        print(f"Button {event.code} pressed. Recording...")
                                        current_instruction = instruction
                                        with no_alsa_err():
                                            audio_handler.start_recording()
                                            
                            elif event.value == 0: # Key Up
                                if event.code in INPUT_MAP and audio_handler.is_recording:
                                    print(f"Button {event.code} released. Processing...")
                                    is_processing = True
                                    
                                    print("Stopping recording...")
                                    audio_path = audio_handler.stop_recording()
                                    
                                    if audio_path:
                                        print("Sending to LLM...")
                                        try:
                                            response = llm_client.process_audio(audio_path, current_instruction)
                                            print(f"DEBUG: Response from Gemini:\n{response}")
                                            print(f"Response received ({len(response)} chars). Typing...")
                                            type_string(response)
                                            print("Done.")
                                        except Exception as e:
                                            print(f"Error processing: {e}")
                                    else:
                                        print("No audio recorded.")
                                    
                                    current_instruction = None
                                    is_processing = False
            except BlockingIOError:
                pass
            except Exception as e:
                # print(f"Event Error: {e}")
                pass
                
            # Small sleep to prevent 100% CPU when idle (recording handles its own timing mostly)
            time.sleep(0.001)

    except KeyboardInterrupt:
        print("Exiting...")
    except Exception as e:
        print(f"Error in event loop: {e}")
    finally:
        audio_handler.cleanup()
        try:
            device.ungrab()
        except:
            pass

if __name__ == "__main__":
    main()
