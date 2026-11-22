# TV TIME dynamic-scene proof of concept

## Generated scene

Run:

```bash
python -m pip install -r requirements-packaging.txt
python tools/build_dynamic_scene.py --output build/tv-time-dynamic
```

The exporter writes `scene/background.raf/` containing twelve original 640×360 DXT1 frames, a shared `plane.mdx` XDM model, and the RAF `index.xml`. The scene uses one plane model, a material and actor for each frame, and a looping sequence that switches frame visibility every 0.12 seconds (about 8.3 frames per second).

The model generator derives the plane dimensions from the reference perspective camera's 29-degree vertical field of view and 16:9 aspect ratio. The output model is parsed again by the exporter before it is written; tests also verify the XDM record structure, four 14-byte vertices, and index buffer.

The XML model entry uses the scene format's `file="plane.fbx"` identifier, while the physical XDM model is stored as `plane.mdx` in the same RAF folder. This pairing follows the documented working-theme convention.

## Conservative budget

Each 640×360 DXT1 frame has a 128-byte DDS header and 115,200-byte payload. Twelve frames therefore use 1,383,936 bytes (about 1.32 MiB), before the small model and XML files, comfortably below the newer tool's reported 6 MiB DDS budget and 48-frame ceiling.

Older community tutorials report a 16 MiB frame/video limit and recommend 34 frames at 1280×720. These figures conflict with the newer tool's reported 6 MiB / 48-frame limits. We keep this candidate small and treat community figures as reported constraints, not universal firmware guarantees.

## Relationship to the default TV TIME theme

A RAF scene is the active background on both the home and function screens. It therefore replaces the normal `homescreen.png` and `functionscreen.png` backgrounds while active. The default TV TIME theme keeps the Tenna home wallpaper, so the animation remains a separate alternate/test candidate and is not copied into the default static `Image0` tree.

## Compatibility boundary

This is a **complete dynamic-scene candidate**, not an installable theme:

- The RAF XML, XDM shared plane, and compressed frames are generated together.
- The candidate does not include `theme.xml`, `param.sfo`, keystone, GP4 project, or PKG; those belong to the separate package staging pipeline.
- The scene has not been tested on the target CUH-1115A / reported firmware 14.02. A green CI run proves deterministic generation and structural checks, not that the target PS4 accepts or displays it.
- The 12-frame animation and its pacing still need visual review on a compatible theme test environment.
- The static Tenna wallpaper remains the default fallback.

## References

- PS4 Developer Wiki, Themes: https://www.psdevwiki.com/ps4/Themes
- ConsoleMods Wiki, PS4 Custom Themes: https://consolemods.org/wiki/PS4%3ACustom_Themes
- PS4 Ultimate Theme Creator (MIT; reference for the documented MDX/RAF working-theme layout): https://github.com/Imxnxl/PS4-Ultimate-Theme-Creator
- Dynamic theme sample: https://github.com/speedrod55/PS4DynamicThemeSample

See [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md) for the reference project's license notice.