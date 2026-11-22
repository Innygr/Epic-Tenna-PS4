# EPIC-TENNA-PS4

**TV TIME — A Tenna Broadcast Network production.**

A fan-made PS4 theme project for El Quatro (CUH-1115A; firmware 14.02 and GoldHEN reported). The default theme keeps the Tenna-inspired home wallpaper and uses the red/yellow broadcast background on the function screen.

> The repository generates and validates the static theme staging tree, a separate experimental dynamic-background scene, and a theme-specific `.pkg` maker. The maker requires a compatible `orbis-pub-cmd` toolchain supplied locally; no production package has been generated yet.

## Vision
- Tenna-inspired TV TIME home-screen wallpaper as the default.
- Broadcast red and signal yellow over near-black, with warm-white text.
- CRT scanlines, signal noise, channel markers, neon panels, and television motifs.
- Optional dynamic broadcast-background experiment, kept separate from the default wallpaper theme.
- Game-launch channel-switch effect remains separate research; theme assets are not assumed to intercept game launches.

## Packaging preparation
- [Packaging readiness and staging instructions](docs/PACKAGING-READINESS.md)
- [Asset preparation](tools/prepare_assets.py) · [Theme descriptor generator](tools/build_theme_descriptor.py) · [SFO metadata input generator](tools/build_param_sfx.py) · [Binary SFO writer](tools/build_param_sfo.py) · [GP4 project generator](tools/build_gp4.py) · [Package input audit](tools/audit_package_inputs.py) · [Theme PKG maker](tools/build_theme_pkg.py) · [Validator](tools/validate_staging.py)
- [Dynamic-scene proof of concept](docs/DYNAMIC-SCENE-POC.md)
- Install dependencies: `python -m pip install -r requirements-packaging.txt`.
- Generate the static theme tree: `python tools/prepare_assets.py`.
- Validate the static theme tree: `python tools/validate_staging.py`.
- Generate the package metadata input (using your chosen title ID): `python tools/build_param_sfx.py --title-id CUSA12345`.
- Convert that XML input to a binary SFO: `python tools/build_param_sfo.py --input build/tv-time/package-input/param.sfx --output build/tv-time/package-input/param.sfo`.
- Stage it in an `Image0` folder: `python tools/prepare_assets.py --output build/tv-time/production/Image0 --param-sfo build/tv-time/package-input/param.sfo`.
- Validate the staging tree: `python tools/validate_staging.py --staging build/tv-time/production/Image0`.
- Generate the GP4 project description: `python tools/build_gp4.py --staging build/tv-time/production/Image0 --output build/tv-time/package-input/tv-time.gp4`.
- Audit the production Image0 + GP4 inputs: `python tools/audit_package_inputs.py --staging build/tv-time/production/Image0 --gp4 build/tv-time/package-input/tv-time.gp4` (rejects the CI-only fixture ID by default).
- Build the theme package: `python tools/build_theme_pkg.py --staging build/tv-time/production/Image0 --gp4 build/tv-time/package-input/tv-time.gp4 --output build/tv-time/package-output/TV-TIME.pkg`.
- Generate the optional dynamic scene candidate separately: `python tools/build_dynamic_scene.py --output build/tv-time-dynamic`.
- Create review outputs with `tools/make_review_sheet.py` and `tools/preview_home_ui.py`.

The static `Image0` tree includes `theme.xml`, the Tenna home wallpaper, the red/yellow function-screen background, preview artwork, four mapped function icons, `sce_sys/icon0.png`, and `sce_sys/pic1.png`. The descriptor selects the red system theme colour and a yellow focus accent. Home music remains disabled unless a converted `.at9` file is supplied with `--at9`.

The dynamic RAF candidate is a separate experiment because an active animated scene replaces both theme background screens. It is not included in the default static tree, preserving the Tenna home wallpaper as the actual home background.

The theme PKG maker requires a compatible, separately supplied `orbis-pub-cmd` executable and its adjacent `ext/` directory; these proprietary tools are not bundled. On Windows, the default location is `tools/orbis-pub-cmd.exe`. On Linux, pass that Windows executable with `--orbis-pub-cmd /path/to/orbis-pub-cmd.exe --wine` after installing Wine. The maker preflights the adjacent `ext/sc.exe` and `ext/di.exe` helpers, re-runs the input audit, invokes `img_create`, checks the PS4 PKG header, then invokes `img_file_list --oformat long` to verify the expected `Image0` and `Sc0` entries. It writes a JSON build report next to the package. GitHub CI tests the orchestration with a stub executable; it does not generate a real package.

GitHub Actions validates the static assets, theme descriptor, dynamic scene, and original WAV music master, then uploads a reviewable artifact. The UI overlay is illustrative, not an exact PS4 screenshot.

## Target
| Item | Target |
|---|---|
| Console | Original PS4 CUH-1115A |
| Firmware | 14.02 (reported) |
| Environment | GoldHEN (reported) |
| Theme | TV TIME |

## Status
Static theme staging, dynamic-scene generation, the binary SFO writer, theme GP4 generator, pre-package audit, and theme-specific PKG maker wrapper are implemented. The maker has stubbed unit tests; a real build requires a compatible local `orbis-pub-cmd` toolchain and a chosen non-conflicting production title ID. CI uses a separate fixture identity and does not create a package. No production `.pkg` has been generated yet. AT9 music conversion and real-console compatibility testing also remain outstanding. See [roadmap](docs/ROADMAP.md) and [packaging readiness](docs/PACKAGING-READINESS.md).

## Safety and compatibility
- Keep the console's current firmware documented; do not update solely for this project.
- Back up important data before testing third-party packages.
- Verify package origin, contents, and compatibility before installation.
- Community format references do not establish compatibility with firmware 14.02.

## Credits
Fan project inspired by *Deltarune*. DELTARUNE and its characters belong to their respective creator(s). Unofficial; not affiliated with them or Sony.