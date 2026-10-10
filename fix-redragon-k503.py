#!/usr/bin/env python3
import threading
import time
import pyudev
from evdev import InputDevice, UInput, ecodes as e, list_devices

VID = 0x0C45
PID = 0x7603

MOD_BITS = {
    0x01: e.KEY_LEFTCTRL,
    0x02: e.KEY_LEFTSHIFT,
    0x04: e.KEY_LEFTALT,
    0x08: e.KEY_LEFTMETA,
    0x10: e.KEY_RIGHTCTRL,
    0x20: e.KEY_RIGHTSHIFT,
    0x40: e.KEY_RIGHTALT,
    0x80: e.KEY_RIGHTMETA,
}


def find_source_event():
    """Găsește interfața evdev corectă: cea cu litere, nu cea de multimedia."""
    for path in list_devices():
        dev = InputDevice(path)
        if dev.info.vendor == VID and dev.info.product == PID:
            caps = dev.capabilities().get(e.EV_KEY, [])
            if e.KEY_A in caps:
                return dev
    raise RuntimeError("Nu am găsit interfața evdev a tastaturii (VID/PID nepotrivit sau fără taste de literă)")


def find_hidraw_nodes():
    """Găsește toate nodurile hidraw care aparțin de VID:PID-ul tastaturii."""
    context = pyudev.Context()
    nodes = []
    for device in context.list_devices(subsystem="hidraw"):
        usb_dev = device.find_parent("usb", "usb_device")
        if usb_dev is None:
            continue
        try:
            vid = int(usb_dev.get("ID_VENDOR_ID") or "0", 16)
            pid = int(usb_dev.get("ID_MODEL_ID") or "0", 16)
        except ValueError:
            continue
        if vid == VID and pid == PID:
            nodes.append(device.device_node)
    if not nodes:
        raise RuntimeError("Nu am găsit niciun nod hidraw pentru VID:PID dat")
    return nodes


def hidraw_thread(path, ui, lock, state):
    while True:
        try:
            with open(path, "rb", buffering=0) as f:
                while True:
                    data = f.read(8)
                    if not data or len(data) < 2 or data[0] != 0x04:
                        continue
                    new_byte = data[1]
                    with lock:
                        diff = new_byte ^ state["prev"]
                        for bit, code in MOD_BITS.items():
                            if diff & bit:
                                value = 1 if (new_byte & bit) else 0
                                ui.write(e.EV_KEY, code, value)
                        ui.syn()
                        state["prev"] = new_byte
        except (OSError, FileNotFoundError):
            break  # Ieșim din buclă și închidem thread-ul dacă dispozitivul a fost scos

def main():
    src = find_source_event()
    src.grab()
    ui = UInput.from_device(src, name="redragon-k503-fixed")

    lock = threading.Lock()
    state = {"prev": 0}

    for node in find_hidraw_nodes():
        threading.Thread(target=hidraw_thread, args=(node, ui, lock, state), daemon=True).start()

    try:
        for ev in src.read_loop():
            if ev.type == e.EV_KEY and ev.code == e.KEY_LEFTSHIFT:
                continue
            ui.write(ev.type, ev.code, ev.value)
            ui.syn()
    except (KeyboardInterrupt, OSError):
        pass
    finally:
        src.ungrab()


if __name__ == "__main__":
    main()
