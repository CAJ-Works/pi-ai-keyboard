
import time
import os
import signal
import sys
import subprocess
import evdev 
from select import select
from evdev import InputDevice, categorize, ecodes
from audio_handler import AudioHandler
from llm_client import LLMClient
from keyboard_mapper import type_string
from ctypes import *
from contextlib import contextmanager
from dotenv import load_dotenv
import threading

# Load environment variables
load_dotenv()

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
    ecodes.KEY_F1: "The following text was transcribed by a an AI voice recorder. Correct any gramatical errors. Output ONLY the transcription. Do not converse. Do not put it in quotes or respond starting with 'transcription'.  Spell check the output and ensure that it is proper english grammer and spelling.  Do not answer and questions that are asked or provide any information besides the transcription.",
    ecodes.KEY_F2: "The following text was transcribed by a an AI voice recorder. Expand it into a concise paragraph.",
    ecodes.KEY_F3: "The following text was transcribed by a an AI voice recorder.  Perform the task requested. Be concise and intelligent.",
    ecodes.KEY_F4: "The following text was transcribed by a an AI voice recorder.  Rephrase the content as a pirate would say it. Return only the pirate speech.",
    ecodes.KEY_F5: "The following text was transcribed by a an AI voice recorder.  Rephrase the content in the style of Shakespeare. Return only the rephrased text.",
}

# State
current_instruction = None
is_processing = False

def find_device():
    print("Scanning for all input devices...")
    try:
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    except Exception as e:
        print(f"Error listing devices: {e}")
        return None
    
    candidates = []
    
    # Iterate through ALL devices first to log them
    for d in devices:
        print(f"  Found: {d.path}: {d.name}")
        if DEVICE_NAME_SEARCH.lower() in d.name.lower():
            candidates.append(d)
            
    # Selection Logic:
    # 1. Look for a candidate that does NOT contain "Consumer Control" or "System Control"
    #    (These usually handle media keys, not typing keys)
    for d in candidates:
        name_lower = d.name.lower()
        if "consumer control" not in name_lower and "system control" not in name_lower:
            print(f"Selecting best match: {d.name} ({d.path})")
            return d

    # 2. Fallback: If we only found filtered devices (e.g. only Consumer Control), pick the first one.
    if candidates:
        print(f"Warning: Only found partial matches (likely media interfaces). Selecting: {candidates[0].name} ({candidates[0].path})")
        return candidates[0]
    
    return None

def monitor_usb_connection():
    """
    Monitors the USB gadget state (via /sys/class/udc).
    If the state transitions from disconnected -> configured,
    it re-initializes the gadget to ensure the host sees it correctly.
    """
    print("Starting USB Connection Monitor...")
    last_state = "unknown"
    
    # Allow some time for initial setup to settle 
    time.sleep(5)
    
    while True:
        try:
            udc_dir = "/sys/class/udc"
            current_state = "unknown"
            
            if os.path.exists(udc_dir):
                udc_entries = os.listdir(udc_dir)
                if udc_entries:
                    # Assuming the first entry is our UDC (e.g. fe980000.usb)
                    udc_name = udc_entries[0]
                    state_file = os.path.join(udc_dir, udc_name, "state")
                    
                    if os.path.exists(state_file):
                        with open(state_file, "r") as f:
                            current_state = f.read().strip()
                    else:
                        current_state = "no_state_file"
                else:
                    current_state = "no_udc_entry"
            else:
                current_state = "no_udc_dir"
            
            # Handle Startup/First Loop
            if last_state == "unknown":
                last_state = current_state
                time.sleep(2)
                continue

            # Check for Reconnection (Transition to 'configured')
            if (last_state != "configured") and (current_state == "configured"):
                print(f"USB Reconnection Detected (State: {current_state}).")
                # We previously tried resetting the gadget here, but that interrupts the host enumeration
                # causing "Device Not Recognized". Since we fixed the blocking write issue, 
                # we likely don't need to reset the gadget at all.
                
                # Update state to configured
                last_state = "configured"
                continue

            elif (last_state == "configured") and (current_state != "configured"):
                print(f"USB Disconnected (State: {current_state})")
            
            last_state = current_state

        except Exception as e:
            print(f"Monitor Error: {e}")
        
        time.sleep(2)


def timeout_handler(signum, frame):
    raise TimeoutError("LLM Request Timed Out")


def main():
    global current_instruction, is_processing

    # Initialize handlers
    print("Initializing services...")
    
    # Configure USB Gadget
    try:
        print("Configuring USB Gadget...")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        reset_script = os.path.join(project_root, "scripts", "reset_gadget.sh")
        gadget_script = os.path.join(project_root, "scripts", "usb_gadget.sh")

        subprocess.run(["sudo", reset_script], check=False)
        time.sleep(1) # Give it a moment to clear
        subprocess.run(["sudo", gadget_script], check=True)
        time.sleep(2) # Allow gadget to register
    except Exception as e:
        print(f"Warning: Failed to configure USB gadget: {e}")

    # Start Monitor Thread
    monitor_thread = threading.Thread(target=monitor_usb_connection, daemon=True)
    monitor_thread.start()

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
                                            
                            elif event.code == ecodes.KEY_W:
                                print(f"Button {event.code} pressed. Typing password...")
                                password = os.getenv("SAVED_PASSWORD")
                                if password:
                                    type_string(password + "\n")
                                else:
                                    print("Warning: SAVED_PASSWORD not found in environment.")

                            elif event.code == ecodes.KEY_E:
                                print(f"Button {event.code} pressed. Typing email...")
                                email = os.getenv("SAVED_EMAIL")
                                if email:
                                    type_string(email)
                                else:
                                    print("Warning: SAVED_EMAIL not found in environment.")

                            elif event.value == 0: # Key Up
                                if event.code in INPUT_MAP and audio_handler.is_recording:
                                    print(f"Button {event.code} released. Processing...")
                                    is_processing = True
                                    
                                    print("Stopping recording...")
                                    audio_path = audio_handler.stop_recording()
                                    
                                    if audio_path:
                                        print("Sending to LLM...")
                                        try:
                                            # Set timeout for 8 seconds
                                            signal.signal(signal.SIGALRM, timeout_handler)
                                            signal.alarm(8)
                                            
                                            response = llm_client.process_audio(audio_path, current_instruction)
                                            
                                            # Disable alarm if successful
                                            signal.alarm(0)
                                            
                                            print(f"DEBUG: Response from Groq:\n{response}")
                                            print(f"Response received ({len(response)} chars). Typing...")
                                            type_string(response)
                                            print("Done.")
                                            
                                        except TimeoutError:
                                            print("Error: specific LLM request timed out after 8 seconds.")
                                            # No specific cleanup needed other than resetting state which happens below
                                        except Exception as e:
                                            signal.alarm(0) # Ensure alarm is off
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
