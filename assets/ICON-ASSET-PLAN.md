# TV TIME Icon Asset Plan

The six editable icon masters define the current TV TIME system-icon artwork. Their visual language follows the default red/yellow broadcast identity.

## Visual system

- Broadcast red: `#ED1C24`
- Signal yellow: `#FFD400`
- Transparent canvas with simple, high-contrast line art.
- Consistent 256 × 256 SVG viewBox and canvas.
- Keep icons recognizable without relying on small text or fine detail.

## Source masters

| System area | Master | Concept |
|---|---|---|
| Settings | `settings.svg` | Broadcast tuning dial / controls |
| Network | `network.svg` | Signal arcs |
| Friends | `friends.svg` | Connected people / screens |
| Messages | `messages.svg` | Broadcast message |
| Media | `media.svg` | Playback / CRT |
| Power | `power.svg` | Standby / ON AIR |

All six source masters are checked by `tests/test_icon_masters.py` for SVG structure, canvas dimensions, title, and palette consistency.

## Current staging boundary

The current staging validator expects four function-icon families: Settings, Friends, Messages, and Power (each with a normal and glow PNG). Network and Media remain source masters only; they are not currently exported as function-icon assets.

Do not add Network or Media to the staging tree until a documented PS4 theme slot and its expected resource names, dimensions, and behaviour have been confirmed. The presence of an SVG master does not prove that a corresponding theme slot exists.

## Export and compatibility rules

- Keep editable SVG masters in this directory.
- Generate raster resources through the project's asset-preparation pipeline.
- Treat the dimensions currently enforced by `tools/validate_staging.py` as project staging requirements, not proof of universal firmware compatibility.
- Do not guess additional slots, resource names, colour modes, or alpha behaviour.
- Confirm the theme format against reliable documentation and the target firmware before installation testing.

## Status

- [x] Six consistent source masters.
- [x] Automated source-master validation in CI.
- [x] Four supported staging icon families validated by the staging manifest.
- [ ] Confirm whether Network and Media have valid additional PS4 theme slots.
- [ ] Verify icon appearance and focus/glow behaviour on the target console.
