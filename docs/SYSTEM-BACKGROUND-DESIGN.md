# TV TIME — System Background Design

## The requested effect

The default PS4 Flow-style blue background should become a **red-and-yellow broadcast wave**. This is a system background treatment, separate from the TV TIME wallpaper artwork.

Visual target:
- Deep broadcast red as the main field.
- Bright signal-yellow flowing wave/ribbon accents.
- Subtle darker-red shading for depth.
- No blue/cyan in the default variant.
- Keep the wave motion calm and low-contrast enough that the home-screen tiles remain readable.

Palette:
- Broadcast red: `#ED1C24`
- Deep red: `#760D12`
- Signal yellow: `#FFD400`
- Warm highlight: `#FFF08A`
- Near-black: `#100707`

## What the PS4 theme system exposes

The PS4 theme format has a `themecolor` setting that selects one of the console's built-in theme colours. Documented built-in choices include blue, pink, red, navy, dark gray, gold, light steel blue, and purple. This setting is a single preset; it does not define a custom two-colour gradient.

For TV TIME, use the built-in **red** or **gold** preset as a fallback when no custom background scene is present. The combined red/yellow wave requires custom background artwork or a dynamic background scene.

## Implementation direction

1. Investigate the dynamic-theme scene format and whether it can recreate the PS4 Flow-style animated wave with original red/yellow assets.
2. If a dynamic scene is not practical or cannot be validated for the target firmware, provide a static red/yellow system-background image as the fallback.
3. Set the theme's built-in colour to red or gold where the theme format requires a `themecolor` value; do not describe this alone as the red/yellow wave.
4. Keep the wallpaper master independent. The system background is the underlying menu treatment; the wallpaper is the separate TV TIME title-card image.
5. Verify the result on the target console before marking the feature complete.

## References

- PS4 theme format overview and theme-colour options: https://www.psdevwiki.com/ps4/Themes
- Background colour selection in the PS4 Flow theme: https://www.pushsquare.com/news/2014/10/guide_how_to_change_your_ps4s_background_colour
- Community custom-theme documentation describing `themecolor` and custom background resources: https://glitchmod.com/wiki/page/ps4-custom-themes

These references are implementation research, not proof that a particular package will work on the project's target firmware.

## Status

Design requirement confirmed. The custom red/yellow animated system background has not yet been built or tested on El Quatro.
