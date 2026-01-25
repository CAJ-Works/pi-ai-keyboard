# Deployment Instructions

## 1. Prepare the Raspberry Pi
Ensure you are running **Raspberry Pi OS Legacy (64-bit)** (or Lite).
Connect to your Pi via SSH.

## 2. Dependencies
Install system dependencies:
```bash
sudo apt-get update
sudo apt-get install -y python3-pip portaudio19-dev libatlas-base-dev git
```
*Note: `portaudio19-dev` is required for `pyaudio`.*

## 3. Clone/Copy Code
Copy this repository to the Pi (e.g., to `~/pi-ai-keyboard`).

## 4. Install Python Requirements
```bash
cd ~/pi-ai-keyboard
sudo apt install -y python3-venv libasound2-dev portaudio19-dev libportaudio2 libportaudiocpp0
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
```

## 5. Configure USB Gadget
To enable the Pi to act as a keyboard, we need to run the `usb_gadget.sh` script at boot.

1. Make the script executable:
   ```bash
   chmod +x scripts/usb_gadget.sh
   ```
2. Add it to `/etc/rc.local` (before `exit 0`):
   ```bash
   sudo nano /etc/rc.local
   # Add this line:
   # /home/cajames/pi-ai-keyboard/scripts/usb_gadget.sh &
   ```
   *Adjust the path if you placed the code elsewhere.*
3. **Enable `dwc2` overlay (CRITICAL)**:
   This allows the Pi's USB port to act as a device.
   
   Edit your config file:
   ```bash
   sudo nano /boot/config.txt
   # OR if that file is empty/missing, try:
   # sudo nano /boot/firmware/config.txt
   ```
   Add the following lines to the bottom:
   ```
   dtoverlay=dwc2,dr_mode=peripheral
   ```
   *Save and exit (Ctrl+O, Enter, Ctrl+X).*

4. Enable Modules:
   ```bash
   echo "dwc2" | sudo tee -a /etc/modules
   echo "libcomposite" | sudo tee -a /etc/modules
   ```
   
5. **REBOOT**:
   You must reboot for these changes to take effect.
   ```bash
   sudo reboot
   ```
   
6. Verify after reboot:
   ```bash
   ls /sys/class/udc
   ```
   *This should return a value (e.g. `fe980000.usb`). If empty, check config.txt again.*

## 6. Setup Input Device (Keyboard)
1. By default, the script looks for a device with "Keyboard" in its name.
2. It listens for **F1**, **F2**, and **F3** keys to trigger different prompts.
3. If your keyboard is not detected:
   - Run `sudo evtest` to find your keyboard's event ID (e.g., `/dev/input/event0`).
   - Check its name.
   - Update `src/main.py`: `DEVICE_NAME_SEARCH` to match the name.
4. If you want to use different keys:
   - Update `src/main.py`: `INPUT_MAP` with new `ecodes`.

## 7. Setup API Key
Create a `.env` file in the root directory:
```bash
nano .env
```
Add your Mistral API Key:
```
MISTRAL_API_KEY=your_api_key_here
```

## 8. Run the Application
You can run it manually to test. Since we are using a virtual environment but need root for hardware access, run:

```bash
sudo .venv/bin/python3 src/main.py
```

*(Sudo is needed for HID gadget and Input device access. Using `.venv/bin/python3` ensures we use the installed dependencies)*

*(Sudo might be needed for GPIO and HID device access)*

To run on boot, consider adding a systemd service.

## 9. Troubleshooting

### "HID device /dev/hidg0 not found"
This means the USB Gadget script did not run successfully.
1. Check `ls /sys/class/udc`. If empty, checking Step 5 (Config.txt).
2. If the gadget is stuck ("Device or resource busy"), run the reset script:
   ```bash
   sudo ./scripts/reset_gadget.sh
   ```
   Then try configuring again:
   ```bash
   sudo ./scripts/usb_gadget.sh
   ```

### "Mistral Error / Model not found"
If you encounter errors regarding the model, check `src/llm_client.py`. We are using `mistral-small-latest` (or a Voxtral model) for multimodal support. Ensure your API key has access to this model or update the `model` variable in `src/llm_client.py` to a valid model name.

### Audio recording silent
The `src/audio_handler.py` attempts to auto-select USB microphones. Watch the console on startup for `*** Selected Input Device: ... ***`. If it selects a different device, you may need to edit the filtering logic in `src/audio_handler.py`.
