# Redragon Harpe K503 Lite (Microdia Chip) - Linux Modifier Keys Fix

This small Python script fixes a hardware/firmware bug on Linux for the **Redragon Harpe K503 Lite** keyboard (Vendor ID: `0x0C45`, Product ID: `0x7603`).

## 🛑 The Problem
Without this script, certain modifier keys on Linux (specifically **Left CTRL, Left ALT, Right ALT, Super/Windows Key, Right CTRL, and Right Shift**) do not work properly. Instead, whenever you press any of these keys, the system registers a **Left Shift** press regardless of which modifier key was actually hit.

## 💡 The Solution
The script grabs the original event device, listens directly to the raw HID data (`hidraw`) to correctly interpret the modifier bits sent by the Microdia chip, and maps them to a virtual `uinput` device (`redragon-k503-fixed`) with the correct keycodes.

---

## 🚀 Installation & Requirements

### 1. System Dependencies
You need a Linux system with Python 3, `libudev`, and permissions to access input and hidraw devices.

### 2. Python Packages
Install the required Python libraries via pip:
```bash
pip install pyudev evdev
