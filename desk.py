#!/usr/bin/env python3
"""CLI controller for IKEA Idasen standing desk via Bluetooth."""
import asyncio
import argparse
import json
import struct
import sys
from pathlib import Path
from bleak import BleakClient, BleakScanner

COMMAND_UUID = "99fa0002-338a-1024-8a49-009c0215f78a"
HEIGHT_UUID = "99fa0021-338a-1024-8a49-009c0215f78a"
REFERENCE_INPUT_UUID = "99fa0031-338a-1024-8a49-009c0215f78a"

CMD_UP = 71
CMD_DOWN = 70
CMD_STOP = 255
CMD_WAKEUP = 254

CONFIG_DIR = Path.home() / ".config" / "idasen"
CONFIG_PATH = CONFIG_DIR / "config.json"
DEFAULT_PRESETS = {"sit": 700, "stand": 1000}


class IdasenDesk:
    def __init__(self, client: BleakClient):
        self.client = client

    async def _write_command(self, command: int):
        await self.client.write_gatt_char(COMMAND_UUID, struct.pack("<H", command))

    async def get_height(self) -> float:
        data = await self.client.read_gatt_char(HEIGHT_UUID)
        raw = struct.unpack("<I" if len(data) == 4 else "<H", data)[0]
        return (raw / 10.0) + 620.0  # Convert raw to mm

    async def stop(self):
        await self._write_command(CMD_STOP)

    async def move_to(self, target_mm: float):
        current = await self.get_height()
        if abs(target_mm - current) < 5:
            print(f"Already at target ({current:.0f}mm)")
            return

        print(f"Moving to {target_mm:.0f}mm...")

        await self._write_command(CMD_WAKEUP)
        await self._write_command(CMD_STOP)
        await asyncio.sleep(0.1)

        target_raw = int((target_mm - 620) * 10)  # Invert height formula
        target_bytes = struct.pack("<H", target_raw)

        last_height = current
        stable_count = 0

        for _ in range(150):  # 30s timeout
            await self.client.write_gatt_char(REFERENCE_INPUT_UUID, target_bytes)
            await asyncio.sleep(0.2)

            current = await self.get_height()

            if abs(current - target_mm) < 5:  # Reached target
                break

            if abs(current - last_height) < 1:  # Stopped moving
                stable_count += 1
                if stable_count >= 3:
                    break
            else:
                stable_count = 0

            last_height = current

        await self._write_command(CMD_STOP)
        await asyncio.sleep(0.2)
        print(f"{await self.get_height():.0f}mm")


def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            config = json.load(f)
            config.setdefault("presets", DEFAULT_PRESETS.copy())
            return config
    return {"presets": DEFAULT_PRESETS.copy()}


def save_config(data):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2)


async def scan_for_desk():
    print("Scanning for desk...")
    devices = await BleakScanner.discover(timeout=10.0)

    for device in devices:
        if device.name and "desk" in device.name.lower():
            print(f"Found: {device.name} ({device.address})")
            config = {
                "mac_address": device.address,
                "presets": DEFAULT_PRESETS.copy()
            }
            save_config(config)
            print(f"Saved config to {CONFIG_PATH}")
            print(f"Presets: sit={config['presets']['sit']}mm, stand={config['presets']['stand']}mm")
            return device.address

    print("No desk found. Check power and Bluetooth.")
    return None


async def connect_to_desk():
    config = load_config()
    mac = config.get("mac_address")

    if not mac:
        print("No desk configured. Run first-time setup:")
        print()
        print("  nix run ~/git/ikea-desk -- scan")
        print()
        print(f"This will scan for your desk and create {CONFIG_PATH}")
        print(f"with presets: sit={DEFAULT_PRESETS['sit']}mm, stand={DEFAULT_PRESETS['stand']}mm")
        sys.exit(1)

    try:
        client = BleakClient(mac, timeout=20.0)
        await client.connect()
        return client
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)


async def main():
    config = load_config()
    presets = config.get("presets", {})

    if presets:
        preset_list = ", ".join(f"{k}={v}mm" for k, v in presets.items())
        move_help = f"Move to preset or height. Presets: {preset_list}"
    else:
        move_help = "Move to height in mm"

    parser = argparse.ArgumentParser(description="Control IKEA Idasen desk")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("scan", help="Find and configure desk")
    sub.add_parser("height", help="Show current height")
    sub.add_parser("move", help=move_help).add_argument("target")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "scan":
        await scan_for_desk()
        return

    client = await connect_to_desk()
    desk = IdasenDesk(client)

    try:
        if args.command == "height":
            print(f"{await desk.get_height():.0f}mm")

        elif args.command == "move":
            if args.target in presets:
                target = presets[args.target]
            else:
                try:
                    target = float(args.target)
                except ValueError:
                    print(f"Unknown preset: {args.target}")
                    if presets:
                        print(f"Available: {', '.join(presets.keys())}")
                    sys.exit(1)

            await desk.move_to(target)

    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
