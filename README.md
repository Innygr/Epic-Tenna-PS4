# EPIC-TENNA-PS4

**TV TIME — A Tenna Broadcast Network production.**

A fan-made PS4 theme project for El Quatro (CUH-1115A; firmware 14.02 and GoldHEN reported). The goal is a broadcast-themed home-screen experience with wallpaper, matching theme assets, and dynamic effects only where the platform supports them.

> The repository includes original artwork and a reproducible PNG asset-staging pipeline. It does **not** yet contain a tested or installable PS4 theme package.

## Vision
- Tenna-inspired TV TIME home-screen wallpaper (default concept), with a Deltarune broadcast aesthetic.
- Alternate option: a simpler TV TIME title-card wallpaper.
- Broadcast red and signal yellow over near-black, with warm-white text.
- CRT scanlines, signal noise, channel markers, neon panels, and television motifs.
- Research verified PS4 theme capabilities before promising animated wallpaper or launch transitions.

## Packaging preparation
- [Packaging readiness and staging instructions](docs/PACKAGING-READINESS.md)
- [Asset preparation](tools/prepare_assets.py) · [Validator](tools/validate_staging.py)
- [Contact sheet](tools/make_review_sheet.py) · [Home UI preview](tools/preview_home_ui.py)
- Install dependencies: `python -m pip install -r requirements-packaging.txt`.
- Generate: `python tools/prepare_assets.py`.
- Validate: `python tools/validate_staging.py`.
- Create review sheet: `python tools/make_review_sheet.py --staging build/tv-time/Image0 --output build/tv-time/review-sheet.png`.
- Create UI preview: `python tools/preview_home_ui.py --wallpaper build/tv-time/Image0/texture/background/homescreen.png --output build/tv-time/home-ui-preview.png`.
- GitHub Actions runs the pipeline and uploads review outputs with the staging assets.
- The UI overlay is illustrative, not an exact PS4 screenshot. No theme metadata or installable package is generated.

## Target
| Item | Target |
|---|---|
| Console | Original PS4 CUH-1115A |
| Firmware | 14.02 (reported) |
| Environment | GoldHEN (reported) |
| Theme | TV TIME |

## Status
Artwork and asset staging are in progress. See [roadmap](docs/ROADMAP.md) and [packaging readiness](docs/PACKAGING-READINESS.md).

## Safety and compatibility
- Keep the console's current firmware documented; do not update solely for this project.
- Back up important data before testing third-party packages.
- Verify package origin, contents, and compatibility before installation.

## Credits
Fan project inspired by *Deltarune*. DELTARUNE and its characters belong to their respective creator(s). Unofficial; not affiliated with them or Sony.
