# TV TIME packaging readiness

## Scope
This repository prepares and reviews original visual assets for a PS4 theme concept. The pipeline creates a staging tree, validates PNGs and the manifest, produces a labelled contact sheet, and creates an illustrative home-screen overlay preview. It does not create, sign, or install a PS4 package.

A future packaging decision must use a verified, legitimate toolchain and compatibility information. A staging folder or ZIP is not an installable theme.

## Staging layout
`build/tv-time/Image0/` contains:
- `texture/background/homescreen.png` — Tenna-inspired wallpaper
- `texture/background/functionscreen.png` — red/yellow static background
- `texture/preview.png` — theme preview
- `texture/function_icon/` — four mapped icons and glow variants
- `sce_sys/icon0.png` — theme-list icon
- `STAGING-MANIFEST.json` — dimensions, modes, byte sizes, SHA-256

The export dimensions are a provisional builder profile, not a universal guarantee. Confirm exact paths, dimensions, colour modes, preview dimensions, and limits against the selected supported format before treating these as final exports.

The six concept icons are not six interchangeable PS4 function slots. The staging script maps four concepts to `setting`, `friend`, `message`, and `power`. Network and Media remain source artwork until their correct destination slots are confirmed.

## Generate and review
Requirements: Python 3.10+, Pillow, and CairoSVG.

```bash
python -m pip install -r requirements-packaging.txt
python tools/prepare_assets.py
python tools/validate_staging.py
python tools/make_review_sheet.py --staging build/tv-time/Image0 --output build/tv-time/review-sheet.png
python tools/preview_home_ui.py --wallpaper build/tv-time/Image0/texture/background/homescreen.png --output build/tv-time/home-ui-preview.png
```

Use `--force` only when intentionally replacing an existing staging directory.

The validator checks all 12 expected PNGs, formats, dimensions, manifest metadata, and hashes. The contact sheet assembles the artwork. The UI preview adds an illustrative status row and app shelf to check contrast and composition; it is not an exact PS4 UI capture. GitHub Actions runs all four scripts and uploads the staging tree and review images as a temporary artifact.

## Remaining questions
- [x] Generate and inspect initial artwork contact sheet.
- [x] Add illustrative home-screen overlay preview.
- [x] Review overlay preview; move the illustrative app shelf lower so Tenna's face and main title remain unobstructed.
- [ ] Confirm theme format and export limits against maintained references and target-console compatibility.
- [ ] Decide whether static function-screen background is sufficient; animated SVG is source artwork, not a console-ready animation.
- [ ] Confirm correct slots for Network and Media.
- [ ] Keep the game-launch channel-switch idea separate; theme assets should not be assumed to intercept game launches.

## Limitations
- Animated SVG is source artwork, not a console-ready scene.
- The wallpaper is original project artwork; no game-ripped assets or soundtrack are bundled.
- Console model and firmware details are user-reported; no compatibility guarantee is made.

## References
- PS4 Developer Wiki — [Themes](https://www.psdevwiki.com/ps4/Themes)
- PS4 Developer Wiki — [PARAM.SFO](https://www.psdevwiki.com/ps4/PARAM.SFO)
- Imxnxl — [PS4 Ultimate Theme Creator](https://github.com/Imxnxl/PS4-Ultimate-Theme-Creator) (builder-specific notes)

These are technical/community references, not universal guarantees.
