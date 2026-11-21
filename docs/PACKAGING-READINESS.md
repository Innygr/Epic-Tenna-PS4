# TV TIME packaging readiness

## Scope

This repository is preparing the source assets for a PS4 system-software theme. The current work can create a **staging asset tree** from the original SVG masters. It does not create, sign, or install a PS4 `.pkg`.

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
    icon0.png                       # theme-list icon, from ETN broadcast mark
    param.sfo                        # not generated; requires verified theme metadata
```

The theme format research source describes a 1920×1080 home/function background, 128×128 function icons, 512×512 content icons, and a 512×512 theme-list icon. A separate recent theme-builder documents a 152×152 function-icon glow image and a 740×416 preview. These values are treated as the selected builder's export profile, not a claim that every PS4 firmware or toolchain has identical requirements. Confirm them against the exact builder and target firmware before package creation.

The six concept icons are not six interchangeable PS4 function slots. The staging script maps only the four known function concepts to the conventional `setting`, `friend`, `message`, and `power` slots. Unprovided slots retain the system defaults. Network and Media remain source artwork until their correct content/function slot mapping is decided.

## Generate staging assets

Requirements: Python 3.10+, Pillow, and CairoSVG.

```bash
python -m pip install Pillow CairoSVG
python tools/prepare_assets.py
```

The script:
- renders the original SVG masters to PNG;
- creates the four mapped function icons and soft focus variants;
- writes a staging manifest with source paths, output dimensions, and SHA-256 hashes;
- refuses to overwrite an existing staging directory unless `--force` is supplied.

It does not fetch tools, execute third-party binaries, create SFO metadata, or build a package.

## Still required before packaging

- [ ] Run the asset preparation script and inspect every PNG.
- [ ] Confirm the selected PS4 theme builder's exact paths, dimensions, XML schema, icon slot names, and preview dimensions.
- [ ] Decide whether the static function-screen background or the dynamic RAF scene is the final background path. Do not include both unless the selected builder explicitly supports that combination.
- [ ] Confirm the theme's title/provider/version fields and create valid theme `param.sfo` metadata.
- [ ] Create `theme.xml` from the verified schema and select the red built-in theme colour as the fallback.
- [ ] Validate that generated PNGs meet the selected toolchain's colour mode, alpha, and file-size constraints.
- [ ] Build with a legitimate, locally installed packaging toolchain whose provenance and compatibility are known. Proprietary Sony packaging binaries are not included in this repository.
- [ ] Run the package validator and inspect the package contents before any console test.
- [ ] Test installation, application, reboot behaviour, and removal on the documented target firmware.

## Important limitations

- The animated SVG motion study is source artwork, not a PS4 scene. Dynamic RAF scene export remains a separate, uncompleted task.
- The Tenna-inspired wallpaper is original project artwork; no game-ripped assets or soundtrack are bundled.
- The game-launch channel-switch effect is not part of a normal theme asset package.
- A community tool's reported package behaviour is not a guarantee for every firmware. The target console's reported firmware remains 14.02; do not update it solely to make this project work.

## Research references

- PS4 Developer Wiki — [Themes](https://www.psdevwiki.com/ps4/Themes)
- GlitchMod — [PS4 Custom Themes](https://glitchmod.com/wiki/page/ps4-custom-themes)
- Imxnxl — [PS4 Ultimate Theme Creator](https://github.com/Imxnxl/PS4-Ultimate-Theme-Creator) (builder-specific layout and export profile)

These are community/technical references, not official Sony guarantees. Re-check them when the packaging toolchain is selected.
