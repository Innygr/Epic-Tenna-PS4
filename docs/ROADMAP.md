# Roadmap

## Phase 0 — Foundation
- [x] Establish project name: EPIC-TENNA-PS4
- [x] Define TV TIME visual direction
- [x] Document target console and reported firmware
- [x] Create a 1920×1080 wallpaper master
- [x] Establish asset naming, dimensions, and source-credit guidelines
- [x] Add an original ETN broadcast mark
- [x] Document static-theme and dynamic-theme research tracks
- [x] Specify the red/yellow system-background requirement separately from wallpaper

## Phase 1 — Static theme
- [x] Document a provisional staging tree and packaging blockers
- [x] Add a reproducible SVG-to-PNG asset staging script
- [x] Add a red/yellow TV TIME theme-list icon master
- [x] Add a PNG/manifest staging validator
- [x] Add GitHub Actions render, validation, and review-artifact workflow
- [ ] Run the asset preparation script locally and inspect generated PNGs
- [ ] Review the first successful CI artifact
- [ ] Verify PS4 custom-theme format and metadata for the target firmware
- [ ] Confirm wallpaper, icon, preview, and audio formats, dimensions, and limits
- [x] Create a Tenna-inspired TV TIME home-screen wallpaper concept (SVG source master)
- [ ] Export and preview the home-screen wallpaper in the verified PS4 format
- [ ] Decide whether to retain the simpler title-card wallpaper as an alternate
- [x] Create six matching system icon artwork masters (Settings, Network, Friends, Messages, Media, Power)
- [ ] Export icons to verified PS4 formats and map them to correct theme slots
- [ ] Set the built-in theme colour fallback to red or gold, based on console preview
- [x] Create an original static red/yellow system-background concept master (PS4 export/validation still pending)
- [ ] Prepare optional background music and sound effects, subject to format/size constraints
- [ ] Create and validate theme.xml and param.sfo using the selected toolchain
- [ ] Build a package using a documented, trusted toolchain
- [ ] Validate package contents before console testing

## Phase 2 — Dynamic presentation research
- [ ] Confirm the supported dynamic-theme scene format and target-firmware compatibility
- [x] Create a looping red/yellow animated SVG motion study (source master only)
- [ ] Render the motion study into a supported frame sequence and assemble the PS4 scene
- [ ] Determine whether the desired channel-switch effect can run in a theme or requires a separate homebrew application
- [ ] Document reboot/persistence limitations and firmware compatibility

## Acceptance criteria
- Theme installs and uninstalls cleanly using a verified method.
- The system background visibly uses red and yellow, independently of the wallpaper.
- Wallpaper remains legible with the PS4 UI overlaid.
- No unverified firmware or exploit requirement is presented as fact.
- Every included asset has a documented source or is original project artwork.
