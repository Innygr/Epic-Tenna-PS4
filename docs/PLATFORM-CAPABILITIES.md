# TV TIME platform capabilities and design decisions

This note separates documented PS4 theme features from experimental ideas. The
target console is reported as an original PS4 CUH-1115A on firmware 14.02 with
GoldHEN. None of the community references below is a firmware-specific
compatibility guarantee.

## Native theme features

The PS4 theme system supports:

- A home-screen background and a function-screen background.
- Theme colour, font colour, shadow colour, and focus colour.
- Home-screen background music.
- Interface sound effects.
- Static backgrounds, or dynamic backgrounds built from a scene with models,
  camera, and animation data controlled by XML.

References:
- PS4 Developer Wiki — Themes:
  https://www.psdevwiki.com/ps4/Themes
- ConsoleMods Wiki — PS4 Custom Themes:
  https://consolemods.org/wiki/PS4%3ACustom_Themes

## Dynamic-background research

The ConsoleMods dynamic-theme guide describes a frame-based scene format using
DDS images and an XML sequence under `scene/background.raf/`. Its example
workflow uses 34 frames, recommends 1280×720 source video, and reports a 16 MB
limit for dynamic-theme video/frame assets. It also describes editing frame
wait values in `scene/background.raf/index.xml`.

These are community guide values and a particular sample workflow, not a
universal guarantee for every firmware or theme builder. We must validate the
actual scene structure and package on a compatible test environment before
using it as the TV TIME export profile.

### TV TIME decision

- Keep the current 1920×1080 SVG wallpaper as the high-resolution source master.
- Keep the existing static PNG staging pipeline as the reliable baseline.
- Develop a separate dynamic-scene proof of concept using an original TV TIME
  animation. Do not overwrite or replace the static masters.
- Test frame count, DDS format, frame timing, scene XML, package size, and
  application behaviour before marking dynamic support complete.
- Do not treat an animated SVG or GIF as a PS4-ready dynamic theme.

## Home-screen music

The theme system has a home-screen BGM slot. The current TV TIME project has an
original 48 kHz stereo WAV source master and an optional local ATRAC9 conversion
helper. The WAV is not the console format; a converted AT9 file still needs
validation and playback testing on the target console.

See [HOME-MUSIC.md](HOME-MUSIC.md).

## Game-launch channel-switch effect

A regular theme changes the appearance and sounds of the system interface; the
theme documentation does not describe a theme event that intercepts application
launches. GoldHEN's plugin ecosystem documents system/game hooks, but those are
separate from theme packaging and are not a stable, theme-level launch
transition API.

Decision: preserve the channel-switch effect as a separate research idea. Do
not claim it can be implemented by the theme alone, and do not make it a
packaging requirement until a safe, firmware-compatible approach is verified.

Reference:
- GoldHEN Plugins Repository:
  https://github.com/GoldHEN/GoldHEN_Plugins_Repository

## Compatibility and packaging boundary

The repository currently prepares original artwork and a WAV music master. It
does not yet create a validated dynamic scene, `theme.xml`, `param.sfo`, or an
installable PS4 theme package. A successful asset-staging workflow is not
evidence of console compatibility.
