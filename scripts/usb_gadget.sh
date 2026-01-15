#!/bin/bash

# USB Gadget configuration script for Raspberry Pi
# Configures the Pi as a HID Keyboard
# Must be run as root

set -e

# 1. Load the libcomposite module
modprobe libcomposite

# 2. Create the gadget directory
cd /sys/kernel/config/usb_gadget/
mkdir -p g1
cd g1

# 3. Set Device IDs (vid/pid)
# Using generic IDs or Raspberry Pi foundation IDs
# 0x1d6b = Linux Foundation, 0x0104 = Multifunction Composite Gadget
echo "0x1d6b" > idVendor
echo "0x0104" > idProduct
echo "0x0100" > bcdDevice
echo "0x0200" > bcdUSB

# 4. Set String Descriptors
mkdir -p strings/0x409
echo "fedcba9876543210" > strings/0x409/serialnumber
echo "Pi AI Team" > strings/0x409/manufacturer
echo "Pi AI Keyboard" > strings/0x409/product

# 5. Create the Config
mkdir -p configs/c.1/strings/0x409
echo "Config 1: ECM network" > configs/c.1/strings/0x409/configuration
echo 250 > configs/c.1/MaxPower

# 6. Create the Function (HID)
mkdir -p functions/hid.usb0
echo 1 > functions/hid.usb0/protocol
echo 1 > functions/hid.usb0/subclass
echo 8 > functions/hid.usb0/report_length

# standard keyboard report descriptor
echo -ne \\x05\\x01\\x09\\x06\\xa1\\x01\\x05\\x07\\x19\\xe0\\x29\\xe7\\x15\\x00\\x25\\x01\\x75\\x01\\x95\\x08\\x81\\x02\\x95\\x01\\x75\\x08\\x81\\x03\\x95\\x05\\x75\\x01\\x05\\x08\\x19\\x01\\x29\\x05\\x91\\x02\\x95\\x01\\x75\\x03\\x91\\x03\\x95\\x06\\x75\\x08\\x15\\x00\\x25\\x65\\x05\\x07\\x19\\x00\\x29\\x65\\x81\\x00\\xc0 > functions/hid.usb0/report_desc

# 7. Bind the function to the config
ln -s functions/hid.usb0 configs/c.1/

# 8. Enable the gadget
ls /sys/class/udc > UDC

echo "USB Gadget configured successfully"
