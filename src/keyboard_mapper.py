
import time
import os

# HID Keyboard Usage Codes
# https://usb.org/sites/default/files/hut1_2.pdf (Page 53)

NULL_CHAR = chr(0)

# Scancode mapping for standard US layout
# Format: char -> (modifier, usage_code)
# Modifier: 2 = Shift, 0 = None
KEY_MAP = {
    'a': (0, 0x04), 'b': (0, 0x05), 'c': (0, 0x06), 'd': (0, 0x07), 'e': (0, 0x08),
    'f': (0, 0x09), 'g': (0, 0x0A), 'h': (0, 0x0B), 'i': (0, 0x0C), 'j': (0, 0x0D),
    'k': (0, 0x0E), 'l': (0, 0x0F), 'm': (0, 0x10), 'n': (0, 0x11), 'o': (0, 0x12),
    'p': (0, 0x13), 'q': (0, 0x14), 'r': (0, 0x15), 's': (0, 0x16), 't': (0, 0x17),
    'u': (0, 0x18), 'v': (0, 0x19), 'w': (0, 0x1A), 'x': (0, 0x1B), 'y': (0, 0x1C),
    'z': (0, 0x1D),
    '1': (0, 0x1E), '2': (0, 0x1F), '3': (0, 0x20), '4': (0, 0x21), '5': (0, 0x22),
    '6': (0, 0x23), '7': (0, 0x24), '8': (0, 0x25), '9': (0, 0x26), '0': (0, 0x27),
    '\n': (0, 0x28), '\t': (0, 0x2B), ' ': (0, 0x2C), '-': (0, 0x2D), '=': (0, 0x2E),
    '[': (0, 0x2F), ']': (0, 0x30), '\\': (0, 0x31), ';': (0, 0x33), '\'': (0, 0x34),
    '`': (0, 0x35), ',': (0, 0x36), '.': (0, 0x37), '/': (0, 0x38),
    
    'A': (2, 0x04), 'B': (2, 0x05), 'C': (2, 0x06), 'D': (2, 0x07), 'E': (2, 0x08),
    'F': (2, 0x09), 'G': (2, 0x0A), 'H': (2, 0x0B), 'I': (2, 0x0C), 'J': (2, 0x0D),
    'K': (2, 0x0E), 'L': (2, 0x0F), 'M': (2, 0x10), 'N': (2, 0x11), 'O': (2, 0x12),
    'P': (2, 0x13), 'Q': (2, 0x14), 'R': (2, 0x15), 'S': (2, 0x16), 'T': (2, 0x17),
    'U': (2, 0x18), 'V': (2, 0x19), 'W': (2, 0x1A), 'X': (2, 0x1B), 'Y': (2, 0x1C),
    'Z': (2, 0x1D),
    '!': (2, 0x1E), '@': (2, 0x1F), '#': (2, 0x20), '$': (2, 0x21), '%': (2, 0x22),
    '^': (2, 0x23), '&': (2, 0x24), '*': (2, 0x25), '(': (2, 0x26), ')': (2, 0x27),
    '_': (2, 0x2D), '+': (2, 0x2E), '{': (2, 0x2F), '}': (2, 0x30), '|': (2, 0x31),
    ':': (2, 0x33), '"': (2, 0x34), '~': (2, 0x35), '<': (2, 0x36), '>': (2, 0x37),
    '?': (2, 0x38),
}

HID_DEV = "/dev/hidg0"

def write_report(report):
    try:
        if not os.path.exists(HID_DEV):
             # For testing/development on non-gadget devices, we just print
             print(f"DEBUG: HID device {HID_DEV} not found! Skipping write.")
             print("TIP: Run 'sudo ./scripts/usb_gadget.sh' to configure the device.")
             return

        with open(HID_DEV, "wb+") as fd:
            fd.write(report)
    except IOError as e:
        print(f"Error writing to {HID_DEV}: {e}")

def send_key(char):
    if char not in KEY_MAP:
        # Fallback or ignore unknown chars
        return
    
    mod, code = KEY_MAP[char]
    
    # 8 byte report: 
    # Byte 0: Modifier (2=Left Shift)
    # Byte 1: Reserved (0)
    # Byte 2: Keycode
    # Byte 3-7: Zeros
    
    report = bytearray([mod, 0, code, 0, 0, 0, 0, 0])
    write_report(report)
    
    # Hold key for a bit so host sees it
    time.sleep(0.02)
    
    # Release key
    write_report(bytearray([0]*8))
    
    # Small delay between keystrokes to prevent buffer overruns on host
    time.sleep(0.018) 


# Common substitutions for smart quotes, dashes, etc. produced by LLMs
SMART_REPLACEMENTS = {
    '“': '"',
    '”': '"',
    '‘': "'",
    '’': "'",
    '—': '--',
    '–': '-',
    '…': '...',
    '\u00A0': ' ',
}

def type_string(text):
    # Normalize text to ASCII-compatible characters
    for old, new in SMART_REPLACEMENTS.items():
        text = text.replace(old, new)

    for char in text:
        send_key(char)
        # Extra delay after sentence-ending punctuation to allow host processing (e.g. auto-capitalization)
        if char in ['.', '!', '?', '\n']:
            time.sleep(0.15)

if __name__ == "__main__":
    print("Testing keyboard mapper...")
    # Test typing 'Hello World!'
    type_string("Hello World!\n")
