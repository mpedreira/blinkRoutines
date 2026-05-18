#!/usr/bin/env python3
"""
Prescript: reads config.ini and generates blink_devices.json for the HA component.

Run this on the blinkRoutines server before copying the component to Home Assistant:

    python homeassistant/generate_config.py

The output file (blink_devices.json) contains only camera names, IDs and types.
No credentials or tokens are included — safe to copy to any machine.
"""

import json
import os
import sys

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "config.ini")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "blink_devices.json")


def main() -> None:
    config_path = os.path.abspath(CONFIG_PATH)
    output_path = os.path.abspath(OUTPUT_PATH)

    if not os.path.exists(config_path):
        print(f"Error: config.ini not found at {config_path}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: config.ini is not valid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    cameras_raw = config.get("cameras", {})
    if not cameras_raw:
        print("Error: no 'cameras' key found in config.ini", file=sys.stderr)
        sys.exit(1)

    cameras = [
        {"name": name, "id": str(data["id"]), "type": data.get("type", "cam")}
        for name, data in cameras_raw.items()
        if data.get("id")
    ]

    if not cameras:
        print("Error: all cameras have empty IDs in config.ini", file=sys.stderr)
        sys.exit(1)

    devices = {"cameras": cameras}

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(devices, f, indent=2, ensure_ascii=False)

    print(f"Generated: {output_path}")
    print(f"  {len(cameras)} camera(s) found:")
    for cam in cameras:
        print(f"    - {cam['name']}  (id={cam['id']}, type={cam['type']})")
    print()
    print("Next step: copy blink_devices.json and custom_components/blink_routines/")
    print("to your Home Assistant server.")


if __name__ == "__main__":
    main()
