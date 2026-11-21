# EPIC-TENNA-PS4

**TV TIME — A Tenna Broadcast Network production.**

A fan-made PS4 theme project for El Quatro (CUH-1115A; firmware 14.02 and GoldHEN reported). The goal is a broadcast-themed home-screen experience with wallpaper, matching theme assets, and dynamic effects only where the platform supports them.

> The repository includes original artwork and a reproducible PNG asset-staging pipeline. It does **not** yet contain a tested or installable PS4 theme package.

## Vision
- Tenna-inspired TV TIME home-screen wallpaper (default concept), with a Deltarune broadcast aesthetic and menu-safe left-side composition.
- Alternate option: a simpler TV TIME title-card wallpaper.
- Broadcast red and signal yellow over near-black, with warm-white text. Purple/cyan are reserved for optional alternate variants.
- CRT scanlines, signal noise, channel markers, neon panels, and television motifs.
- Wallpaper, icon, and optional audio assets.
- Research verified PS4 theme capabilities before promising animated wallpaper or launch transitions.

## Packaging preparation
- [Packaging readiness and staging instructions](docs/PACKAGING-READINESS.md)
- [Asset preparation script](tools/prepare_assets.py)
- [Staging validator](tools/validate_staging.py)
- [Visual review sheet generator](tools/make_review_sheet.py)
- Install Python asset-rendering dependencies with `python -m pip install -r requirements-packaging.txt`.
- Run `python tools/prepare_assets.py` to generate a reviewable staging tree under `build/tv-time/Image0/`.
- Run `python tools/validate_staging.py` to check expected PNGs, dimensions, manifest entries, and SHA-256 hashes.
- Run `python tools/make_review_sheet.py --staging build/tv-time/Image0 --output build/tv-time/review-sheet.png` to create a labelled contact sheet.
- GitHub Actions performs the render, validation, and review-sheet generation, then uploads them as a short-lived `tv-time-staging-assets` artifact.
- The scripts do not generate theme metadata or an installable package; see the packaging-readiness document for remaining compatibility and validation questions.

## Target
| Item | Target |
|---|---|
| Console | Original PS4 CUH-1115A |
| Firmware | 14.02 (reported) |
| Environment | GoldHEN (reported) |
| Theme | TV TIME |

## Status
Artwork and asset staging are in progress. See [docs/ROADMAP.md](docs/ROADMAP.md) and [docs/PACKAGING-READINESS.md](docs/PACKAGING-READINESS.md).

## Safety and compatibility
- Keep the console's current firmware documented; do not update solely for this project.
- Back up important data before testing third-party packages.
- Verify package origin, contents, and compatibility before installation.
- A system-software reinstall is not guaranteed to undo every modification or preserve installed content.

## Credits
Fan project inspired by *Deltarune*. DELTARUNE and its characters belong to their respective creator(s). Unofficial; not affiliated with them or Sony.
