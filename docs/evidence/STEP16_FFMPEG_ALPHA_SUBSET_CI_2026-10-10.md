# STEP16 FFmpeg alpha filter compilation – regression evidence

**Scope:** Only 2 uniquely implemented families out of 21: FADE (opacity) and WIPE (four cardinal alpha-mask coverage modes). All other presets fail closed. No substitutes or inference of a Canva-approved backend.

## Source code/tests
- `core/fx_alpha_backend.py`: outputs FFmpeg `format=gbrap,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='<mask>',format=argb` where mask depends only on B02-verified IN/OUT duration and the fixed preset/direction. Fixed decimal frame math, 30fps, no source resize/crop/transform.
- Exact phase extrema: first IN 0, last IN 1, first OUT 1, last OUT 0; blend existing source alpha (never erase transparency).
- `build_ffmpeg_command` constructs `ffmpeg -hide_banner -nostdin -loglevel error -n -loop 1 -framerate 30 -i <user-source.png> -vf <validated-filter> -frames:v N -an -c:v qtrle -pix_fmt argb -f mov <new-derived.mov>` argv without a shell or subprocess invocation. Caller must later validate media root, source hash, target isolation and output frame/alpha readback before using this in host.
- The code rebuilds the filter from the immutable B02 preset reference when passed a candidate: a malicious caller cannot insert `movie=/private/path`, other FFmpeg expressions or change phase budgets without immediate rejection.
- 11 isolated Python tests plus all previous Python/JS regressions on Windows and Linux. No approved final UI/asset images created or edited.

## Tests
[Actions #37997018885 — SUCCESS](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/actions/runs/37997018885) on code `6215bd4c`: Windows 99 JS PASS, 245 Python tests (3 SKIP); Ubuntu 97 JS PASS, 2 Windows skips, 245 Python tests (3 SKIP). Additional exact-endpoint tweak is a later commit, see latest STEP16 CI.

Linux developer container had ffmpeg installed. In-memory `lavfi color` + `format=gbrap` input was fed to `-vf` and `-f null -` for FADE, WIPE left-to-right and WIPE top-to-bottom; all three exit code 0, no output images/assets. This is only FFmpeg parser/runtime smoke, NOT alpha-frame readback or user project approval.

**G3 NOT VERIFIED:** no Premiere Pro 2024 24.x running, no live host clip effects, no final exports. Do not report effects "certified" until source media and rendered alpha, layout and real Premiere host are verified.
