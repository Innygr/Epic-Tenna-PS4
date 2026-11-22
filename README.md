# EPIC-TENNA-PS4

**TV TIME — A Tenna Broadcast Network production.**

A fan-made PS4 theme project for El Quatro (CUH-1115A; firmware 14.02 and GoldHEN reported). The default theme keeps the Tenna-inspired home wallpaper and uses the red/yellow broadcast background on the function screen.

> The repository now generates and validates a static theme staging tree and a separate experimental dynamic-background scene. It does **not** yet contain an installable PS4 theme package.

## Vision
- Tenna-inspired TV TIME home-screen wallpaper as the default.
- Broadcast red and signal yellow over near-black, with warm-white text.
- CRT scanlines, signal noise, channel markers, neon panels, and television motifs.
- Optional dynamic broadcast-background experiment, kept separate from the default wallpaper theme.
- Game-launch channel-switch effect remains separate research; theme assets are not assumed to intercept game launches.

## Packaging preparation
- [Packaging readiness and staging instructions](docs/PACKAGING-READINESS.md)
- [Asset preparation](tools/prepare_assets.py) · [Theme descriptor generator](tools/build_theme_descriptor.py) · [Validator](tools/validate_staging.py)
- [Dynamic-scene proof of concept](docs/DYNAMIC-SCENE-POC.md)
- Install dependencies: `python -m pip install -r requirements-packaging.txt`.
- Generate the static theme tree: `python tools/prepare_assets.py`.
- Validate the static theme tree: `python tools/validate_staging.py`.
- Generate the optional dynamic scene candidate separately: `python tools/build_dynamic_scene.py --output build/tv-time-dynamic`.
- Create review outputs with `tools/make_review_sheet.py` and `tools/preview_home_ui.py`.

The static `Image0` tree includes `theme.xml`, the Tenna home wallpaper, the red/yellow function-screen background, preview artwork, four mapped function icons, `sce_sys/icon0.png`, and `sce_sys/pic1.png`. The descriptor selects the red system theme colour and a yellow focus accent. Home music remains disabled unless a converted `.at9` file is supplied with `--at9`.

The dynamic RAF candidate is a separate experiment because an active animated scene replaces both theme background screens. It is not included in the default static tree, preserving the Tenna home wallpaper as the actual home background.

GitHub Actions validates the static assets, theme descriptor, dynamic scene, and original WAV music master, then uploads a reviewable artifact. The UI overlay is illustrative, not an exact PS4 screenshot.

## Target
| Item | Target |
|---|---|
| Console | Original PS4 CUH-1115A |
| Firmware | 14.02 (reported) |
| Environment | GoldHEN (reported) |
| Theme | TV TIME |

## Status
Static theme staging and dynamic-scene generation are automated and CI-validated. `sce_sys/param.sfo`, a complete package build, AT9 music conversion, and real-console compatibility testing remain outstanding. See [roadmap](docs/ROADMAP.md) and [packaging readiness](docs/PACKAGING-READINESS.md).

## Safety and compatibility
- Keep the console's current firmware documented; do not update solely for this project.
- Back up important data before testing third-party packages.
- Verify package origin, contents, and compatibility before installation.
- Community format references do not establish compatibility with firmware 14.02.

## Credits
Fan project inspired by *Deltarune*. DELTARUNE and its characters belong to their respective creator(s). Unofficial; not affiliated with them or Sony.