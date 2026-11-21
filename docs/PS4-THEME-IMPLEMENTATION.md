# PS4 Theme Implementation Notes

This document separates verified project requirements from items that still need validation on the target console.

## Static theme first

The first deliverable is a conventional static custom theme. Do not package or install anything until the format, required metadata, asset dimensions, and installation path have been checked against a reliable PS4 theme specification and the exact target firmware.

Expected asset groups:
- Home-screen wallpaper.
- System icon artwork in the exact formats and dimensions required by the theme format.
- Optional theme background audio, encoded to the supported format and within documented size limits.
- Theme metadata and preview artwork.

## Dynamic background investigation

Do not assume that a GIF, MP4, animated SVG, or web page can be used directly as a PS4 theme wallpaper. The native theme format may support predefined dynamic-theme resources, but that is not equivalent to arbitrary video playback.

Research questions:
1. Which dynamic theme resource types are accepted by the PS4 theme format?
2. Can a user-created dynamic theme be authored with a documented toolchain?
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

No installable package has been built or tested yet. The repository currently contains original visual concept artwork and documentation only.
