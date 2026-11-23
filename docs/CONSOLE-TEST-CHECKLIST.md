# TV TIME console test checklist

This checklist is for a future, compatible test build. It does not claim that the current CI artifact is installable.

## Current handoff state

- [x] Static Image0 staging renders in CI.
- [x] Theme descriptor, PNG dimensions, and staging manifest validate.
- [x] Original 32-second WAV master generates and passes source analysis.
- [x] Review artifact is uploaded by GitHub Actions.
- [ ] Compatible ATRAC9 encoder supplied locally; convert and inspect the home-music file.
- [ ] Confirm theme format and icon/background slot requirements for the exact target firmware.
- [ ] Create and independently inspect a real installable test package using the supported, locally supplied toolchain.
- [ ] Test the static theme on a compatible test console.
- [ ] Test the dynamic scene separately; it replaces both background screens.

## Before any console test

- Confirm the exact console model and firmware.
- Confirm that the test package is intended for that firmware and environment.
- Back up important saves and console data using supported backup options.
- Keep a known-good recovery path and the original theme available.
- Do not update firmware just to attempt this theme.
- Do not use a package whose origin or contents cannot be verified.

## Static TV TIME visual review

Record each result as Pass, Fail, or Not tested, with a photo or short note where useful.

| Check | Expected result | Result |
|---|---|---|
| Theme selection preview | TV TIME identity and preview are legible | Not tested |
| Home screen | Tenna wallpaper remains the home background | Not tested |
| Function screen | Red/yellow broadcast background appears | Not tested |
| Text contrast | Warm-white system text remains readable | Not tested |
| Focus state | Yellow focus accent is visible and distinguishable | Not tested |
| Function icons | Supported icons render cleanly at normal UI scale | Not tested |
| Reboot persistence | Theme remains selected after a normal restart | Not tested |
| Stability | No missing textures, visual corruption, or UI instability | Not tested |

## Home music review

Only perform this after a valid AT9 file is included in the test build.

- Confirm the theme's home-music setting is enabled only when the file is present.
- Listen at a moderate volume on both headphones and TV speakers.
- Check the intro, section transitions, ending, and loop boundary.
- Listen for clicks, abrupt level changes, distortion, or channel imbalance.
- Record whether the music starts and loops reliably after returning to the home screen.

## Dynamic-scene review

Treat this as a separate experiment, not part of the default static-theme acceptance test.

- Confirm the animation displays on both background screens as expected.
- Check frame pacing and whether transitions appear stable.
- Check that the scene does not obscure important interface text.
- Compare stability behaviour with the static theme.
- Restore the static theme if the animation behaves unexpectedly.

## Test report template

- Console model:
- Firmware:
- Test build identifier:
- Static theme result:
- Home music result:
- Dynamic scene result (if tested):
- Screenshots / observations:
- Issues to fix before wider testing:

A successful CI run validates generated files and automated checks only. It does not count as a console test or establish compatibility with firmware 14.02.
