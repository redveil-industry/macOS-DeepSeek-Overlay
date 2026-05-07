# macOS DeepSeek Overlay

A simple macOS overlay application for pinning `chat.deepseek.com` to a dedicated window, togglable via `Option+Space`.

Fork of [macos-grok-overlay](https://github.com/tchlux/macos-grok-overlay) by Thomas C.H. Lux, rebranded for DeepSeek.

## Installation

### DMG (Recommended)

Download and run the DMG installer, then drag to Applications.

### pip

```bash
python3 -m pip install -e .
```

### Set as startup app

```bash
macos-deepseek-overlay --install-startup
```

## Usage

Press `Option + Space` to show/hide the overlay. The window floats on top of other apps.

Menu bar icon provides: Show/Hide, Home, Clear Web Cache, Request Microphone Access, Install/Uninstall Autolauncher, Set New Trigger, Quit.

### Custom trigger

Click "Set New Trigger" in the menu, then press your desired key combo. Stored in `~/Library/Logs/macos-deepseek-overlay/custom_trigger.json`. Delete that file to reset to default.

### Uninstall

```bash
macos-deepseek-overlay --uninstall-startup
```

Or use the menu bar dropdown.

## Running from source

```bash
cd macOS-DeepSeek-Overlay
pip3 install pyobjc-core pyobjc-framework-Cocoa pyobjc-framework-WebKit pyobjc-framework-Quartz pyobjc-framework-ApplicationServices pyobjc-framework-AVFoundation
python3 -m macos_deepseek_overlay
```

## Building a DMG

```bash
cd dmg-builder-deepseek
# Edit config.sh with your Apple developer credentials
./build.sh
```

For local testing without signing:

```bash
cd dmg-builder-deepseek
./test_build.sh
```

## Requirements

- macOS 12+ (Monterey or later)
- Python 3.10+
- pyobjc-core, pyobjc-framework-Cocoa, pyobjc-framework-WebKit, pyobjc-framework-Quartz, pyobjc-framework-ApplicationServices, pyobjc-framework-AVFoundation
- Accessibility permissions (prompted on first launch)

## Note on logos

The included `logo/` files are placeholders copied from the Grok overlay. Replace `logo_white.png`, `logo_black.png`, and `icon.icns` with actual DeepSeek branding before distribution.

## License

MIT