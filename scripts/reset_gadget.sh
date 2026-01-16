#!/bin/bash

# Reset USB Gadget configuration
# Run as root

set -x

GADGET_DIR="/sys/kernel/config/usb_gadget/g1"

if [ -d "$GADGET_DIR" ]; then
    echo "Cleaning up gadget..."
    cd "$GADGET_DIR"
    
    # Disable gadget
    if [ -f "UDC" ]; then
        echo "" > UDC
    fi

    # Remove configs linkage
    rm configs/c.1/hid.usb0 2>/dev/null
    
    # Remove strings
    rmdir configs/c.1/strings/0x409 2>/dev/null
    rmdir configs/c.1 2>/dev/null
    
    # Remove functions
    rmdir functions/hid.usb0 2>/dev/null
    
    # Remove gadget strings
    rmdir strings/0x409 2>/dev/null
    
    # Remove gadget dir
    cd ..
    rmdir g1 2>/dev/null
    
    echo "Gadget cleaned."
else
    echo "No gadget directory found at $GADGET_DIR"
fi
