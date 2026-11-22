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
- [ ] Build and validate a separate original TV TIME dynamic-scene proof of concept (DDS frames and scene XML); keep static exports as fallback

## Platform compatibility
- [ ] Validate the documented theme format and package behaviour on a compatible test environment; firmware 14.02 compatibility is not yet confirmed
- [x] Research static versus dynamic background options; retain static staging baseline and plan a separate dynamic-scene proof of concept
- [x] Assess theme-level game-launch channel-switch support; no theme event interface is documented, so keep this separate from theme packaging
- [ ] Document limitations without assuming community tools behave identically

## Acceptance criteria
- Artwork is original, consistently branded, and visually legible.
- System background uses red/yellow independently of wallpaper.
- Wallpaper remains legible with PS4 UI overlaid.
- Every included asset has documented provenance.
- No unverified compatibility requirement is presented as fact.
