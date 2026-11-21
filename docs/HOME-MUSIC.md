# TV TIME Home Screen Music

The repository now includes an original, procedural instrumental for the TV TIME
PS4 theme. It is a bright retro-broadcast / arcade-game-show cue with warm synth
chords, a bouncing bass line, a short repeating lead hook, and light electronic
percussion. The track is original project audio and contains no game-ripped
recordings or third-party samples.

## Generate the source master

Requires Python 3.10+ and only the Python standard library:

\`\`\`bash
python tools/generate_home_bgm.py --output build/tv-time/sound/bgm_home.wav
\`\`\`

The master is 32 seconds, stereo, 48 kHz, 16-bit PCM WAV, with a short loop
crossfade. GitHub Actions generates it and includes it in the temporary review
artifact alongside the visual assets.

## PS4 export status

The PS4 theme slot is \`sound/bgm_home.at9\`, and \`theme.xml\` must enable
\`homebgm-enable\` when that file is present. The WAV is the editable source
master, **not** the console-ready AT9 export. AT9 conversion and a verified
theme descriptor/package build remain separate steps; the pipeline does not
pretend a WAV is installable or silently substitute a fake AT9 file.

The reference toolchain describes 48 kHz theme audio and AT9 conversion. The
specific encoder and final bitrate/loop metadata must be validated against the
selected builder and target-console behavior before packaging.
