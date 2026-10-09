# STEP09 — video-only background / FFmpeg safety evidence

- Base branch `sol/step08-track-preflight-20261010`, SHA `b3cb72512d73a38d2fdd2705497b16f653db2b95`. No main merge.
- New worker `core/background_audio.py` never mutates input MP4 or existing cache. Requires explicitly configured ffmpeg+ffprobe binaries and separate existing cache folder. Both calls use fixed argv / `shell=False`. Source SHA-256 pinned, checked before and after, generated MP4 is probed to confirm one video stream and zero audio; output path is new and atomically refuses duplicates. Returned record is NOT executable/authorized.
- New FFprobe fail-closed `E_BACKGROUND_AUDIO_NOT_ISOLATED`, `E_BACKGROUND_STREAM_TOPOLOGY_UNKNOWN`, `E_BACKGROUND_VIDEO_STREAM_AMBIGUOUS`. Missing video retains `E_FFPROBE_STREAM_MISSING`.
- Published CI workflow `.github/workflows/step09-background-audio.yml` runs entire JS/Python suite on Linux+Windows. [First complete green CI #37986661664](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/actions/runs/37986661664).
- Manual isolated local FFmpeg 7.1.5 smoke using synthesized 1s black video + sine AAC: input tracks `mpeg4,video` and `aac,audio`, output only `mpeg4,video`; input 12,093 bytes, new copy 1,786 bytes. No user files.
- Final host Premiere 24.x validation has not occurred. Background duration equivalence, exact source-frame trims, native linked audio, full decode, 21 effects remain unresolved. Do not claim MP4 feature completes video editor.
