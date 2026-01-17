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
- Nix package manager ([install](https://nixos.org/download))
- Bluetooth adapter

**With Nix (recommended):**

No installation needed! Just run:
```bash
nix run github:yourusername/ikea-desk -- height
```

Or clone and use locally:
```bash
git clone <repo>
cd ikea-desk
nix run . -- height
```

**Without Nix:**
```bash
pip install bleak
python desk.py height
```

## Setup

**1. Find your desk:**
```bash
nix run . -- scan
```

Or if installed:
```bash
desk scan
```

This discovers your desk and saves its address to `~/.config/idasen/config.json` with default presets (sit=700mm, stand=1000mm).

**2. Configure presets (optional):**

Edit `~/.config/idasen/config.json`:
```json
{
  "mac_address": "XX:XX:XX:XX:XX:XX",
  "presets": {
    "sit": 700,
    "stand": 1000
  }
}
```

Heights are in millimeters. Typical ranges:
- Sitting: 650-750mm
- Standing: 1000-1200mm

## Usage

With Nix:
```bash
nix run . -- height              # Show current height
nix run . -- move sit            # Move to preset
nix run . -- move stand          # Move to preset
nix run . -- move 850            # Move to specific height (mm)
```

Or install once:
```bash
nix profile install .
desk height
desk move sit
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

## Quick Access with Nix

For convenient daily use, add these aliases to your `~/.bashrc` or `~/.zshrc`:

```bash
alias stand="nix run ~/git/ikea-desk#stand"
alias sit="nix run ~/git/ikea-desk#sit"
alias desk="nix run ~/git/ikea-desk#desk --"
```

Adjust the path (`~/git/ikea-desk`) to match where you cloned the repository.

After sourcing your shell config, simply run:
```bash
stand    # Move desk to standing position
sit      # Move desk to sitting position
desk height   # Check current height
```

The Nix flake handles all Python dependencies automatically - no manual installation required.

## Credits

Protocol information from:
- [newAM/idasen](https://github.com/newAM/idasen)
- [Home Assistant Idasen integration](https://www.home-assistant.io/integrations/idasen_desk/)

## License

MIT
