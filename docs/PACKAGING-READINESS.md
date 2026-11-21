# TV TIME packaging readiness

## Scope

This repository is preparing the source assets for a PS4 system-software theme. The current work can create a **staging asset tree** from the original SVG masters and validate the resulting PNGs and manifest. It does not create, sign, or install a PS4 `.pkg`.

A final package still requires a verified theme descriptor, SFO metadata, a compatible packaging toolchain, and a validation pass on the resulting package. Do not treat an asset staging folder or ZIP as an installable theme.

## Staging layout

The preparation script writes to `build/tv-time/Image0/`:

```text
Image0/
  theme.xml                         # not generated; requires verified descriptor schema
  texture/
    background/
      homescreen.png                # Tenna-inspired TV TIME wallpaper
      functionscreen.png            # red/yellow Flow-style static fallback
    preview.png                     # generated 16:9 theme preview
    function_icon/
      setting.png                   # generated from icons/settings.svg
      friend.png                    # generated from icons/friends.svg
      message.png                   # generated from icons/messages.svg
      power.png                     # generated from icons/power.svg
      <name>_glow.png               # generated focus/glow variants
  sce_sys/
    icon0.png                       # theme-list icon, from tv-time-theme-icon.svg
    param.sfo                        # not generated; requires verified theme metadata
```

The PS4 Developer Wiki describes the theme feature set. A recent community theme-builder documents this staging layout and a 740×416 preview, while the GlitchMod guide lists a 1920×1080 preview and different icon export details. Those differences are why the dimensions in the script are a **provisional builder profile**, not a universal guarantee. Confirm the selected builder's exact paths, dimensions, colour modes, and limits before packaging.

The six concept icons are not six interchangeable PS4 function slots. The staging script maps only four concepts to the conventional `setting`, `friend`, `message`, and `power` slots. Unprovided slots retain system defaults. Network and Media remain source artwork until their correct content/function slot mapping is decided.

## Generate staging assets

Requirements: Python 3.10+, Pillow, and CairoSVG.

```bash
python -m pip install -r requirements-packaging.txt
python tools/prepare_assets.py
python tools/validate_staging.py
```

Use `--force` only when intentionally replacing the existing staging directory:

```bash
python tools/prepare_assets.py --force
```

The preparation script:
- renders the original SVG masters to PNG;
- creates four mapped function icons and soft focus variants;
- writes a staging manifest with output dimensions, colour modes, byte sizes, and SHA-256 hashes;
- refuses to overwrite an existing staging directory unless `--force` is supplied.

The validator checks all 12 expected PNGs, their file format and dimensions, manifest metadata, and SHA-256 hashes. It also checks that the manifest clearly labels the output as staging-only and says no installable package was generated.

A GitHub Actions workflow runs both scripts on pushes, pull requests, and manual dispatch. It uploads a `tv-time-staging-assets` artifact for review; the artifact is temporary and contains only staging assets, not an installable package.

The scripts do not fetch tools, execute third-party binaries, create SFO metadata, or build a package.

## Still required before packaging

- [ ] Run the asset preparation and validation scripts locally and inspect every PNG.
- [ ] Review the first successful CI artifact and confirm the image composition, transparency, icon glow, and colour treatment.
- [ ] Confirm the selected PS4 theme builder's exact paths, dimensions, XML schema, icon slot names, colour modes, preview dimensions, and file-size limits.
- [ ] Decide whether the static function-screen background or the dynamic RAF scene is the final background path. Do not include both unless the selected builder explicitly supports that combination.
- [ ] Confirm the theme's title/provider/version fields and create valid theme `param.sfo` metadata.
- [ ] Create `theme.xml` from the verified schema and select the red built-in theme colour as the fallback.
- [ ] Validate generated PNGs against the selected toolchain's alpha and file-size constraints.
- [ ] Build with a legitimate, locally installed packaging toolchain whose provenance and compatibility are known. Proprietary Sony packaging binaries are not included in this repository.
- [ ] Run the package validator and inspect package contents before any console test.
- [ ] Test installation, application, reboot behaviour, and removal on the documented target firmware.

## Important limitations

- The animated SVG motion study is source artwork, not a PS4 scene. Dynamic RAF scene export remains uncompleted.
- The Tenna-inspired wallpaper is original project artwork; no game-ripped assets or soundtrack are bundled.
- The game-launch channel-switch effect is not part of a normal theme asset package.
- A community tool's reported package behaviour is not a guarantee for every firmware. The target console's reported firmware remains 14.02; do not update it solely to make this project work.

## Research references

- PS4 Developer Wiki — [Themes](https://www.psdevwiki.com/ps4/Themes)
- GlitchMod — [PS4 Custom Themes](https://glitchmod.com/wiki/page/ps4-custom-themes)
- Imxnxl — [PS4 Ultimate Theme Creator](https://github.com/Imxnxl/PS4-Ultimate-Theme-Creator) (builder-specific layout and export profile)

These are community/technical references, not official Sony guarantees. Re-check them when the packaging toolchain is selected.
