# TV TIME packaging readiness

## Scope

This repository prepares and reviews original visual assets for a PS4 theme concept. The current pipeline creates a staging asset tree from SVG masters, validates the resulting PNGs and manifest, and produces a labelled visual review sheet. It does not create, sign, or install a PS4 package.

A future packaging decision must be based on a verified, legitimate toolchain and authoritative compatibility information. Do not treat an asset staging folder or ZIP as an installable theme.

## Staging layout

The preparation script writes to `build/tv-time/Image0/`:

```text
Image0/
  texture/
    background/
      homescreen.png                Tenna-inspired TV TIME wallpaper
      functionscreen.png            red/yellow Flow-style static background
    preview.png                     generated 16:9 theme preview
    function_icon/
      setting.png                   generated from icons/settings.svg
      friend.png                    generated from icons/friends.svg
      message.png                   generated from icons/messages.svg
      power.png                     generated from icons/power.svg
      <name>_glow.png               generated focus/glow variants
  sce_sys/
    icon0.png                       theme-list icon from tv-time-theme-icon.svg
  STAGING-MANIFEST.json             dimensions, modes, byte sizes, SHA-256
```

The current export dimensions are a provisional builder profile, not a universal guarantee. Confirm the selected format's exact paths, dimensions, colour modes, preview dimensions, and limits before treating these assets as final exports.

The six concept icons are not six interchangeable PS4 function slots. The staging script maps four concepts to the conventional `setting`, `friend`, `message`, and `power` names. Network and Media remain source artwork until their correct destination slots are confirmed.

## Generate and review assets

Requirements: Python 3.10+, Pillow, and CairoSVG.

```bash
python -m pip install -r requirements-packaging.txt
python tools/prepare_assets.py
python tools/validate_staging.py
python tools/make_review_sheet.py --staging build/tv-time/Image0 --output build/tv-time/review-sheet.png
```

Use `--force` only when intentionally replacing an existing staging directory:

```bash
python tools/prepare_assets.py --force
```

The validator checks all 12 expected PNGs, file formats and dimensions, manifest metadata, and SHA-256 hashes. It also verifies that the manifest labels the output as staging-only.

The review-sheet generator assembles the wallpaper, system background, theme icon, preview, and mapped function icons into one labelled image. GitHub Actions runs all three scripts and uploads the staging tree plus review sheet as a temporary `tv-time-staging-assets` artifact.

## Remaining design and compatibility questions

- [x] Review the generated contact sheet for composition, contrast, transparency, and icon readability; the current staging images render cleanly.
- [ ] Confirm the exact theme format and export limits against a maintained, trustworthy reference and the target console's compatibility.
- [ ] Decide whether the static function-screen background is sufficient; animated SVG is source artwork, not a console-ready animation.
- [ ] Confirm whether a separate, supported dynamic scene format is appropriate before investing in frame conversion.
- [ ] Confirm correct slots for the Network and Media icon concepts.
- [ ] Review accessibility/legibility of menu text over the wallpaper and function background.
- [ ] Keep the game-launch channel-switch idea separate: a wallpaper/theme asset should not be assumed to intercept game launches.

## Important limitations

- The animated SVG motion study is source artwork, not a console-ready scene.
- The Tenna-inspired wallpaper is original project artwork; no game-ripped assets or soundtrack are bundled.
- The channel-switch transition is a separate research idea, not part of this visual asset pipeline.
- The console model and firmware information are user-reported; no compatibility claim is made by this repository.

## Research references

- PS4 Developer Wiki — [Themes](https://www.psdevwiki.com/ps4/Themes)
- PS4 Developer Wiki — [PARAM.SFO](https://www.psdevwiki.com/ps4/PARAM.SFO)
- Imxnxl — [PS4 Ultimate Theme Creator](https://github.com/Imxnxl/PS4-Ultimate-Theme-Creator) (builder-specific format notes)

These are community/technical references, not universal guarantees. Re-check them before making any compatibility claim.
