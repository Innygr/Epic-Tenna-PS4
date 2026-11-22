# TV TIME dynamic-scene proof of concept

## Current output

`tools/build_dynamic_scene.py` renders the original
`assets/tv-time-flow-motion-study.svg` into a looping sequence of 12
640×360 RGB frames, encodes each frame as a legacy DXT1 DDS texture, and writes
an RAF `index.xml` with one material and actor per frame.

The exporter is intentionally separate from the static artwork staging. It
writes to `build/tv-time-dynamic/` by default and refuses to overwrite a
non-empty output directory unless `--force` is supplied.

## Conservative budget

The current candidate uses 12 frames at 640×360. DXT1 stores 4×4 blocks in
8 bytes, so each frame payload is 115,200 bytes plus a 128-byte DDS header.
The full frame set is approximately 1.32 MiB, comfortably below the
conservative 6 MiB DDS budget reported by the newer PS4 Ultimate Theme Creator
documentation.

Older community tutorials report a 16 MiB frame/video limit and recommend
34 frames at 1280×720. These figures conflict with the newer tool's reported
6 MiB / 48-frame limits. We therefore keep the candidate small and treat both
figures as community-reported rather than guaranteed limits for every system
software version.

## Important limitations

This is an **experimental scene candidate**, not an installable theme:

- The exporter currently writes DDS frames and RAF XML only.
- The RAF references `BG.mdx`; a validated plane model is still outstanding.
- No `theme.xml`, `param.sfo`, keystone, GP4 project, or PKG is generated.
- The exact scene, model, texture, and package compatibility has not been
  tested on the target CUH-1115A / reported firmware 14.02.
- The 12-frame animation is a first motion pass. Frame pacing and visual
  smoothness need review in a real PS4 theme environment.

## Validation in CI

The workflow runs the exporter, checks the DDS headers and fixed-size frame
budget, and parses the RAF XML to verify that material, actor, and sequence
counts agree. Unit tests also check a rendered frame and the generated scene
structure.

A green CI run proves that the files are generated consistently; it does not
prove that the PS4 accepts or displays them.

## References

- PS4 Developer Wiki, Themes:
  https://www.psdevwiki.com/ps4/Themes
- ConsoleMods Wiki, PS4 Custom Themes:
  https://consolemods.org/wiki/PS4%3ACustom_Themes
- PS4 Ultimate Theme Creator (MIT-licensed project; its README documents its
  current real-console validation claims and format constraints):
  https://github.com/Imxnxl/PS4-Ultimate-Theme-Creator
- Dynamic theme sample:
  https://github.com/speedrod55/PS4DynamicThemeSample
