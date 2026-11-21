# PS4 Theme Implementation Notes

This document separates verified project requirements from items that still need validation on the target console.

## TV TIME base palette

The default theme is **red and yellow**, not purple and cyan:
- Broadcast red: `#ED1C24`
- Deep red: `#760D12`
- Signal yellow: `#FFD400`
- Warm highlight: `#FFF08A`
- Near-black background: `#100707`
- Warm white text: `#FFF8E5`

Use red for major frames, active states, and ON AIR indicators. Use yellow for titles, channel labels, separators, and highlights. Purple/cyan may appear only in a separately named alternate theme, not in the default build.

## Separate system background and wallpaper

The requested red/yellow Flow-style background is a separate deliverable from the TV TIME wallpaper.

The PS4 theme format exposes a built-in `themecolor` preset. Documented choices include blue, pink, red, navy, dark gray, gold, light steel blue, and purple. It selects one built-in colour; it does not create a custom red/yellow gradient by itself.

- Fallback: use the built-in red or gold preset, chosen after previewing on the console.
- Target: create an original red-and-yellow flowing background scene, subject to verification of the dynamic-theme scene format and target firmware.
- Static fallback: create a red/yellow background image if a dynamic scene cannot be validated.
- Keep the title-card wallpaper as a separate asset.

See [System Background Design](SYSTEM-BACKGROUND-DESIGN.md) for the specific visual target and research references.

## Static theme first

The first deliverable is a conventional static custom theme. Do not package or install anything until the format, required metadata, asset dimensions, and installation path have been checked against a reliable PS4 theme specification and the exact target firmware.

Expected asset groups:
- Home-screen wallpaper.
- Separate system background image or dynamic scene.
- System icon artwork in the exact formats and dimensions required by the theme format.
- Optional theme background audio, encoded to the supported format and within documented size limits.
- Theme metadata and preview artwork.

## Dynamic background production target

The repository now includes `assets/tv-time-flow-motion-study.svg`, a looping animated SVG motion study. It is not itself a PS4 theme resource. The PS4 theme scene format uses a `scene/background.raf/` directory with DXT1a DDS frames, a plane model, and an `index.xml` scene description. A current community theme-builder documents a limit of 48 frames and 6 MiB total for the DDS frames; its example trade-off is 24 frames at 960×540 or 48 frames at 640×360. Treat these as builder-specific validation targets, not a universal guarantee.

Initial export target: 24 frames at 960×540, with a slow seamless loop. Validate frame weight, playback timing, and compatibility before packaging. The SVG remains the editable visual master.

## Dynamic background investigation

Do not assume that a GIF, MP4, animated SVG, or web page can be used directly as a PS4 theme wallpaper. The native theme format may support predefined dynamic-theme resources, but that is not equivalent to arbitrary video playback.

Research questions:
1. Which dynamic theme scene resources are accepted by the PS4 theme format?
2. Can an original Flow-style red/yellow scene be authored with a documented toolchain?
3. Does the target firmware accept the resulting package?
4. Does the animation persist after a normal reboot and after GoldHEN is no longer active?

## Game-launch channel transition

A theme alone should not be assumed to intercept game-launch events or play a custom full-screen transition. Treat the Tenna-style channel switch as a separate research track. Any implementation must be optional, reversible, and tested without modifying game data or core system files.

## Validation checklist

- [ ] Identify a trustworthy theme-format specification or tool source.
- [ ] Record supported image/audio formats and exact limits.
- [ ] Confirm firmware compatibility for the build and install method.
- [ ] Inspect the final package contents before installation.
- [ ] Test install, apply, reboot persistence, and uninstall.
- [ ] Keep a static fallback theme available.

## Current status

The red/yellow system-background design requirement is documented. No installable package or custom animated system background has been built or tested yet. The repository contains original visual concept artwork and documentation only.
