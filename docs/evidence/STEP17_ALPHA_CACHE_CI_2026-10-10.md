# STEP17 FFmpeg Alpha Cache — Windows/Linux QA evidence

**Repo:** `inoriko920-dev/AI-JSON-Premiere-Editor`  
**Step17 source SHA:** `c1e51a07a0ab28480aa804dddc5415c62cce818c`  
**Workflow:** [GitHub Actions #37998026165 SUCCESS](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/actions/runs/37998026165)

## Real implementation tests
- Tests actually execute the isolated Python worker, hash/copy header-byte fixture media to a private temp workspace, call **mocked** `subprocess.run`, parse mocked FFprobe metadata, atomically publish a synthetic binary cache file and check SHA/dimensions/frame count/result flags. This is a *simulation of subprocess outputs*, not a real FFmpeg output clip or generated visual UI.
- 11 tests include: successful worker mock, source unchanged, source SHA spoofing, unsupported alpha mode, input root traversal, cache/media root collision, no source overwrite, missing binaries, malformed codec/frame-count readback, FFmpeg exception or timeout, cleanup of partial output.
- Ubuntu first run succeeded; Windows failed on case-sensitive textual matching of absolute resolved binary path in the test mock. Corrected the test harness to use filesystem identity `Path.samefile()`, then retested both systems.

## Results on fixed code revision
| Platform | Focused worker | Full Python | Full Node |
|---|---|---|---|
| Windows | 11/11 PASS | 253 PASS, 3 SKIP (256 total) | 99 PASS |
| Ubuntu | 11/11 PASS | 253 PASS, 3 SKIP (256 total) | 97 PASS, 2 Windows-only SKIP |

The skipped Python tests are environment-specific. No failed tests remain for this revision. CI specifically enforces that the CEP ScriptPath is read-only and that no Premiere or Canva visual certification is claimed.

## Explicit limits

FFmpeg output is validated through a **mock** FFprobe JSON response, so this evidence does NOT prove actual QTRLE alpha channel correctness, Canva preset fidelity, Premiere MOV decoding, real user PNG hash/run compatibility or 21/21 effect delivery. Alpha content readback and real host acceptance remain future work. No main merge, installer, release or final MP4 yet.
