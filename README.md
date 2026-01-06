# Idasen Desk Controller

Minimal CLI to control IKEA Idasen standing desks via Bluetooth.

## How It Works

The Idasen desk uses a Linak DPG controller with Bluetooth Low Energy (BLE). This tool communicates directly with the desk's BLE characteristics:

- **Height reading** (`99fa0021`): Returns current position as raw value in tenths of millimeters with a 620mm offset
- **Reference input** (`99fa0031`): Accepts target position - the desk's controller handles the movement automatically
- **Commands** (`99fa0002`): Wake, stop, and direct control signals

Instead of timing-based movement, we send the target height to the reference input characteristic repeatedly. The desk's internal controller moves smoothly to the exact position and stops automatically.

## Installation

**Requirements:**
- Python 3.7+
- Bluetooth adapter

**Install:**
```bash
pip install bleak
```

Or with a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install bleak
```

## Setup

**1. Find your desk:**
```bash
python idasen.py scan
```

This discovers your desk and saves its address to `.idasen-config.json` in the current directory.

**2. Configure presets (optional):**

Edit `.idasen-config.json`:
```json
{
  "mac_address": "XX:XX:XX:XX:XX:XX",
  "presets": {
    "sit": 700,
    "stand": 1100
  }
}
```

Heights are in millimeters. Typical ranges:
- Sitting: 650-750mm
- Standing: 1000-1200mm

## Usage

```bash
python idasen.py height           # Show current height
python idasen.py move sit         # Move to preset
python idasen.py move stand       # Move to preset
python idasen.py move 850         # Move to specific height (mm)
```

## Troubleshooting

**Desk not found:**
- Power on the desk
- Enable Bluetooth on your computer
- Grant Bluetooth permissions if prompted (macOS/Linux)

**Connection fails:**
- Run `scan` again
- Ensure no other device is connected to the desk
- Restart desk (unplug/replug power)

**Height readings seem off:**
- The desk reports values in raw units that are converted to millimeters
- Formula: `height_mm = (raw_value / 10) + 620`
- Use a tape measure to verify and adjust presets if needed

## Protocol Details

Based on the Linak BLE protocol used by Idasen desks:

**UUIDs:**
- Service: `99fa0020-338a-1024-8a49-009c0215f78a`
- Height: `99fa0021-338a-1024-8a49-009c0215f78a` (read)
- Reference Input: `99fa0031-338a-1024-8a49-009c0215f78a` (write target)
- Command: `99fa0002-338a-1024-8a49-009c0215f78a` (write control codes)

**Height encoding:**
- Raw values are in tenths of millimeters from minimum position
- Minimum desk height is ~620mm (raw value 0)
- Convert: `height_mm = (raw / 10) + 620`

**Movement:**
- Target position written to reference input characteristic
- Written repeatedly (every 0.2s) until desk reaches target
- Desk's controller handles acceleration, deceleration, and stopping

## Credits

Protocol information from:
- [newAM/idasen](https://github.com/newAM/idasen)
- [Home Assistant Idasen integration](https://www.home-assistant.io/integrations/idasen_desk/)

## License

MIT
