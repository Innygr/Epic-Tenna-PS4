# TV TIME Home Screen Music

The repository includes an original procedural instrumental for the TV TIME PS4
theme. It is a bright retro-broadcast / arcade-game-show cue with warm synth
chords, a bouncing bass line, a short repeating lead hook, and light electronic
percussion. It contains no game-ripped recordings or third-party samples.

## Generate the source master

Requires Python 3.10+ and only the Python standard library:

```bash
python tools/generate_home_bgm.py --output build/tv-time/sound/bgm_home.wav
```

The master is 32 seconds, stereo, 48 kHz, 16-bit PCM WAV, with symmetric 25 ms
fades at the start and end. Its arrangement now has four broad energy sections:
a quieter intro, fuller main section, quieter breakdown, and stronger finale.
Short gain ramps soften the transitions, and the final section returns to the
opening level at the loop boundary. The edge samples meet at digital silence; this
reduces a hard wrap click but is not a true overlapping crossfade, so the final
loop still needs listening tests after ATRAC9 conversion.

## Analyze the source master

Run the standard-library analyzer after generating the WAV:

```bash
python tools/analyze_home_bgm.py build/tv-time/sound/bgm_home.wav \
  --output build/tv-time/sound/bgm_home-analysis.json
```

The report records per-channel peak and RMS levels, DC offset, clipping count,
stereo correlation, mean absolute channel difference, and left/right RMS
balance. It fails on an unexpected format, duration, silence, full-scale
clipping, effectively duplicated channels, or substantially unbalanced channel
levels. GitHub Actions runs this analyzer and uploads its JSON report with the
review assets.

The workflow also creates a stereo amplitude-envelope PNG alongside the JSON
report. It uses separate red and yellow channel traces on a dark broadcast-style
canvas, with a four-second timeline. This makes the overall arrangement,
channel activity, and fade edges easier to inspect at a glance. It is an
amplitude overview, not a spectrogram, loudness meter, or substitute for
listening.

These are measurable source-master checks, not a subjective mix review. They
cannot establish whether the cue sounds good on headphones or TV speakers, and
they do not replace listening to the final ATRAC9 encode.

## Convert to the PS4 theme format

The PS4 theme music slot is `sound/bgm_home.at9`. Current PS4 theme references
specify 48 kHz audio, stereo for this slot, and a 2 MiB maximum file size. The
maintained PS4 Ultimate Theme Creator reference documents 144 kbps ATRAC9 with
whole-loop metadata for its theme builder profile.

Conversion requires a compatible Sony `at9tool` executable supplied locally by
the user. This project does not download, bundle, or redistribute that
proprietary encoder.

```bash
python tools/convert_home_bgm.py \
  --input build/tv-time/sound/bgm_home.wav \
  --output build/tv-time/sound/bgm_home.at9 \
  --at9tool /path/to/at9tool
```

On Windows, pass the path to the local `at9tool.exe`. The script checks the WAV
format and duration before invoking the encoder with the 144 kbps whole-loop
profile. It then checks that a non-empty output exists and is no larger than
2 MiB. It refuses to overwrite an existing output.

These checks do not prove that the console will play the file. The resulting
AT9 still needs playback testing on the target PS4. Do not set
`homebgm-enable` to `True` in `theme.xml` until the AT9 file is actually
included in the theme.

## Packaging status

The WAV is the editable source master, not a console-ready audio asset. The
repository's automated workflow validates and uploads the WAV for review; it
does not run the proprietary encoder, generate `theme.xml` or `param.sfo`,
or build an installable PKG.
