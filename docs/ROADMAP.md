# Roadmap

## Foundation
- [x] Establish EPIC-TENNA-PS4 and TV TIME visual direction
- [x] Document target console and reported firmware
- [x] Create 1920×1080 wallpaper and red/yellow system-background masters
- [x] Establish asset naming and source-credit guidelines
- [x] Add original broadcast mark and theme-list icon

## Visual assets and review
- [x] Create six icon artwork masters: Settings, Network, Friends, Messages, Media, Power
- [x] Add reproducible SVG-to-PNG staging
- [x] Add PNG/manifest validator
- [x] Add labelled contact sheet generator
- [x] Add illustrative home-screen UI overlay preview
- [x] Add GitHub Actions render, validation, and review-artifact workflow
- [x] Inspect initial staging images and contact sheet
- [ ] Review illustrative home-screen overlay and adjust artwork if necessary
- [ ] Confirm icon slots and export dimensions against selected supported format
- [ ] Confirm wallpaper readability with actual console UI
- [x] Build an experimental original TV TIME dynamic-scene candidate (12 DXT1 DDS frames + RAF XML)
- [x] Generate and validate the shared XDM plane model and align RAF XML with the reference scene structure
- [x] Generate static theme.xml descriptor with red system colour and yellow focus accent
- [x] Stage the `sce_sys/pic1.png` package image
- [x] Generate and CI-validate the PS4 theme `param.sfx` XML metadata input
- [x] Add binary PSF 1.1 writer and round-trip validator for `param.sfo`
- [x] Add optional `--param-sfo` staging and CI validation in a separate fixture tree
- [x] Generate and CI-validate a theme-mode GP4 project description
- [x] Add a pre-package input audit with per-file hashes and a CI fixture identity guard
- [x] Add a theme-specific PKG maker wrapper with a pre-build audit and post-build package inventory validation
- [x] Add stubbed unit tests for the PKG maker orchestration and failure paths
- [ ] Confirm the dynamic scene on a compatible PS4 theme test environment

## Packaging
- [x] Add measured AT9 loudness extraction and SFO metadata validation
- [ ] Complete home music ATRAC9 conversion and verify playback
- [ ] Generate a production `sce_sys/param.sfo` with a chosen non-conflicting title ID and stage it in Image0
- [ ] Run the PKG maker with a separately supplied compatible `orbis-pub-cmd` toolchain and inspect an actual production package
- [ ] Install and test the static TV TIME theme on a compatible console
- [ ] Test the dynamic candidate separately

## Platform compatibility
- [ ] Validate the theme format and package behaviour on a compatible test environment; firmware 14.02 compatibility is not yet confirmed
- [x] Research static versus dynamic background options; keep the dynamic scene separate because it replaces both theme background screens
- [x] Assess theme-level game-launch channel-switch support; no theme event interface is documented, so keep this separate from theme packaging
- [x] Document limitations without assuming community tools behave identically

## Acceptance criteria
- Artwork is original, consistently branded, and visually legible.
- The default theme keeps Tenna as the home-screen wallpaper.
- The function-screen and focus accents use the red/yellow broadcast palette.
- Every included asset has documented provenance.
- No unverified compatibility requirement is presented as fact.