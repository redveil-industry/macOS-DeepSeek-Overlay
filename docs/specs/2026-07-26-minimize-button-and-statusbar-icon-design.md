# Design: Minimize Button & Status Bar Icon Fix

**Date:** 2026-07-26
**Scope:** `macos_deepseek_overlay/app.py` (single file)
**Status:** Approved

## Goal

Two small, well-scoped changes to the macOS DeepSeek overlay app:

1. **Fix the missing menu bar icon.** The status bar slot exists and is clickable, but the icon renders blank at runtime because `logo_white.png` is a ~145-byte transparent placeholder (the readme confirms these PNGs are Grok placeholders awaiting real DeepSeek branding). Replace the PNG-based image with an SF Symbol rendered as a template image, so the icon shows reliably in both light and dark mode without bundling PNG assets.
2. **Add a minimize button.** A `minus.circle.fill` button in the existing top drag bar, placed next to the current close button. Repurpose the existing close (`xmark.circle.fill`) button to **quit the app** (standard macOS convention: red x = quit, yellow minus = hide), while the new minus button takes over the **hide** (keep app running) behavior the xmark previously held.

## Out of Scope (YAGNI)

- Window-state badge / visual feedback on the status bar icon.
- Collapsing the window to a pill/bar or any custom minimized visual state.
- Standard `miniaturize:` to the Dock (accessory apps have no Dock icon; behavior would be odd).
- Replacing the PNG logo assets with real DeepSeek branding.
- Adding a "Minimize" item to the status bar menu (the existing "Hide DeepSeek" menu item already covers hide-on-demand).

## Notable Behavior Change

The existing `xmark.circle.fill` close button currently calls `hideWindow:`, which performs `NSApp.hide_(None)` and keeps the app running. This design repurposes it to call `terminate:`, fully quitting the app. Users who relied on the xmark to merely hide the window will now need to use the new minus button, the `Option+Space` hotkey, the "Hide DeepSeek" status menu item, or `Cmd+H`. This matches standard macOS conventions (x = close/quit, minus = minimize/hide) and gives the two buttons distinct, non-redundant semantics. Intentional and called out for review.

## Components & Changes

All changes are in `macos_deepseek_overlay/app.py`. No new files, no asset changes.

### A. Status bar icon — replace PNG with SF Symbol

**Current** (`app.py:144-157`): loads `logo_white.png` / `logo_black.png`, stores them as `self.logo_white` / `self.logo_black`, sets the initial image via `updateStatusItemImage()`, and registers a KVO observer on `effectiveAppearance` to swap images when the system appearance changes.

**New:**

```python
status_button = self.status_item.button()
symbol = NSImage.imageWithSystemSymbolName_accessibilityDescription_("bubble.left.fill", APP_TITLE)
if symbol is None:
    print("Failed to load SF Symbol bubble.left.fill", flush=True)
else:
    symbol.setSize_(NSSize(18, 18))  # keep current 18pt sizing
    symbol.setTemplate_(True)  # auto-adapts to light/dark — no appearance observer needed
    status_button.setImage_(symbol)
```

`setTemplate_(True)` causes the system to tint the symbol black in light mode and white in dark mode automatically. This eliminates the need for:

- `self.logo_white`, `self.logo_black` instance variables.
- `updateStatusItemImage()` (`app.py:354-359`) — deleted.
- `observeValueForKeyPath_ofObject_change_context_` (`app.py:362-364`) — deleted.
- `appearanceDidChange_` (`app.py:367-368`) — deleted.
- The KVO observer registration at `app.py:155-157` — deleted.

The `STATUS_ITEM_CONTEXT` constant in `constants.py:18` becomes unused by `app.py`. It is removed from `app.py`'s import list; the constant itself is left in `constants.py` untouched (cheap to leave, avoids touching a shared file). `LOGO_WHITE_PATH` and `LOGO_BLACK_PATH` are similarly removed from `app.py`'s import list but left in `constants.py` since the DMG builder and `logo/` assets still reference the logo directory.

### B. Minimize button + close button repurpose

**Current** (`app.py:112-117`): single close button at `x=5, y=5`, 20×20, `xmark.circle.fill`, bordered=False, target=`self`, action=`hideWindow:`.

**New:** two buttons in the drag area, anchored top-left with a 5px gap between them:

| Button | Symbol | Frame | Target | Action | Semantics |
|---|---|---|---|---|---|
| Minimize | `minus.circle.fill` | `x=5, y=5, 20×20` | `self` | `hideWindow:` | Hide window, app keeps running |
| Close | `xmark.circle.fill` | `x=30, y=5, 20×20` | `NSApp` | `terminate:` | Fully quit the app |

Both buttons keep `setBordered_(False)` and use the existing `imageWithSystemSymbolName_accessibilityDescription_` pattern. No new helper methods are introduced: `hideWindow_` already exists at `app.py:246`; `terminate:` is a built-in `NSApplication` selector.

### C. Drag area & resize handling — unchanged

`handleLocalMouseEvent` (`app.py:325-334`) and `windowDidResize:` (`app.py:337-341`) are unaffected. The two buttons sit in the drag area but do not interfere with click-and-drag (same as the existing single close button does today). Buttons stay anchored top-left after resize because they are positioned absolutely within the drag area, which itself is re-laid-out to span the full top of the content view on resize.

## Data Flow & Behavior

### Window state machine

```
[running, hidden] --showWindow: (hotkey / status menu)--> [running, visible]
[running, visible] --hideWindow: (minus button / hotkey / status menu Hide / Cmd+H)--> [running, hidden]
[running, visible] --terminate: (xmark button / Cmd+Q / status menu Quit)--> [terminated]
```

**No new state, no new instance variables.** The visible/hidden distinction already existed implicitly (the window is always instantiated; hiding via `NSApp.hide_` does not destroy it). Quit is terminal. The only persisted state across launches is the existing `FRAME_SAVE_NAME` window-position autosave, which is untouched.

### Show paths (unchanged)

- `Option+Space` global hotkey → `showWindow_` (via the event tap in `listener.py`).
- Status menu "Show DeepSeek" → `showWindow_`.
- `applicationDidFinishLaunching_` calls `showWindow_(None)` at launch.

### Hide paths (now owned by the minus button)

- Minus button click → `hideWindow_` → `NSApp.hide_(None)`.
- `Option+Space` hotkey (toggles).
- Status menu "Hide DeepSeek" → `hideWindow_`.
- `Cmd+H` keyboard shortcut (handled in `keyDown_` at `app.py:318-319`).

### Quit paths (now owned by the xmark button)

- Xmark button click → `terminate:`.
- `Cmd+Q` keyboard shortcut (handled in `keyDown_` at `app.py:320-322`).
- Status menu "Quit" → `terminate:` (`app.py:199-201`).

### SF Symbol rendering flow

One-time at launch: `imageWithSystemSymbolName_` → `setSize_(18, 18)` → `setTemplate_(True)` → `button.setImage_`. No observer, no per-appearance swap. The system tints the template image automatically.

### Edge cases

- **Hidden window, xmark/minus click:** unreachable — both buttons live in the hidden window's drag bar, so they are only clickable when the window is visible. Quit and minimize both originate from the visible state only. Correct.
- **SF Symbol availability:** `bubble.left.fill` has existed since macOS 11; the app requires macOS 12+ (readme line 68), so the lookup is safe. The nil-guard print is defensive only.
- **Custom-trigger path** (`listener.py`): untouched. The hotkey show/hide still routes through the same `showWindow_` / `hideWindow_` selectors, so the new button semantics do not affect the hotkey flow.
- **Status bar icon visibility:** a template SF Symbol is guaranteed to render a glyph, unlike the broken transparent PNG. This directly resolves the reported "slot exists, icon blank" symptom.

## Error Handling

No new failure modes are introduced. No new I/O, persistence, network, or permissions are added; existing accessibility and microphone permission flows are unaffected.

- **SF Symbol lookup failure:** `imageWithSystemSymbolName_accessibilityDescription_("bubble.left.fill", ...)` returns `nil` only if the symbol name is invalid or the system is older than the symbol's introduction. Both are ruled out by the macOS 12+ requirement and the well-known symbol name. A defensive nil-guard print is included, matching the existing print-on-failure style at `app.py:227`.
- **Button target/action resolution:** `terminate:` is a guaranteed `NSApplication` method; `hideWindow_` already exists and is unchanged. No new selector-resolution risk.

## Testing Approach

This is a GUI PyObjC app with no existing automated test suite (verified: no `tests/` directory, no pytest configuration, no lint/typecheck config beyond `setup_deepseek.py`). Adding a unit-test harness for AppKit windows is heavy and low-value for changes of this size. Instead:

### Manual verification checklist

Run via the readme's "Running from source" entry point:

```bash
python3 -m macos_deepseek_overlay
```

Then verify:

1. Launch app → a visible chat-bubble icon appears in the menu bar in **light mode**.
2. Switch system appearance to dark → the icon remains visible and correctly tinted (white). No relaunch needed.
3. Click the menu bar icon → the existing menu drops down with all items intact (Show / Hide / Home / Clear Cache / Mic / Install / Uninstall / Trigger / Quit).
4. Click the **minus** button in the drag bar → the window hides; the app keeps running (menu bar icon remains; `Option+Space` brings the window back).
5. Click the **xmark** button → the app fully terminates (menu bar icon disappears, process exits, terminal returns to prompt).
6. `Cmd+H` while the window is visible → hides the window (unchanged).
7. `Cmd+Q` while the window is visible → quits the app (unchanged).
8. Click-and-drag on empty drag-area space (not on a button) → window still drags.
9. Resize the window → both buttons stay anchored at the top-left of the drag area; drag area and webview reflow correctly.

### Automated guard

The only automated check available is a syntax compile, since no lint/typecheck/test command exists in the repo:

```bash
python3 -m py_compile macos_deepseek_overlay/app.py
```

This will be run after edits to catch syntax errors before manual verification.

## File Change Summary

Exactly one file modified: `macos_deepseek_overlay/app.py`. No new files, no asset changes, no changes to `constants.py`, `listener.py`, `launcher.py`, `main.py`, `health_checks.py`, `setup_deepseek.py`, `dmg-builder-deepseek/`, or `logo/`.

| Location | Change |
|---|---|
| `app.py:14-24` (imports) | Remove `LOGO_WHITE_PATH`, `LOGO_BLACK_PATH`, `STATUS_ITEM_CONTEXT` from the import list (no longer used by `app.py`). Constants remain in `constants.py` untouched. |
| `app.py:112-117` (close button setup) | Replace the single close button with two buttons: minimize (`minus.circle.fill`, `x=5`, target `self`, action `hideWindow:`) and close (`xmark.circle.fill`, `x=30`, target `NSApp`, action `terminate:`). |
| `app.py:144-157` (status item image + KVO setup) | Replace PNG loading and appearance observer with SF Symbol: `imageWithSystemSymbolName_accessibilityDescription_("bubble.left.fill", APP_TITLE)`, `setSize_(NSSize(18,18))`, `setTemplate_(True)`, `button.setImage_(symbol)`, with a nil-guard print. |
| `app.py:354-368` (appearance methods) | Delete `updateStatusItemImage`, `observeValueForKeyPath_ofObject_change_context_`, and `appearanceDidChange_` — all unused once a template image is set. |

**Net diff:** ~25 lines removed, ~10 lines added. One behavior change: xmark = quit (was hide).

## Self-Review

- **Placeholders:** none. Symbol name, sizes, frames, actions, and targets are all concrete.
- **Contradictions:** none. The behavior-change callout in Section 1 and the state machine in Data Flow agree (xmark = terminate, minus = hide). The file change table agrees with the component descriptions.
- **Ambiguity:** none. All button frames, targets, actions, and the SF Symbol name are specified. The minimize behavior was explicitly chosen as "hide window, keep app running" during brainstorming.
- **Scope:** minimal and YAGNI-trimmed. Touches a single file; leaves shared `constants.py`, the DMG builder, and logo assets untouched.