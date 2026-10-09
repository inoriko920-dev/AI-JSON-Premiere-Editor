# SOL STEP09 — Background audio isolation safety (10 Oktober 2026)

**Owner rule:** selesaikan coding, integrasi dan automated QA dahulu. Uji Premiere Pro 2024 nyata di Windows 11 dilakukan pemilik pada fase terakhir. **G3 tetap BLOCKED_HOST/UNVERIFIED.**

## Mengapa STEP09 diperlukan
Kode STEP08 membaca metadata stream video background tetapi tidak sebelumnya menolak file MP4 yang juga berisi audio meskipun JSON menyatakan `audio_policy=MUTE`. Karena adapter host `Track.overwriteClip` belum terverifikasi tidak menambahkan audio ter-link, ini berpotensi menghasilkan suara background yang tidak diinginkan.

## Kode dikerjakan (bukan planning)
- `core/ffprobe.py`: inspeksi semua stream background, bukan hanya memilih video pertama. `E_BACKGROUND_AUDIO_NOT_ISOLATED` untuk MP4 video+audio; `E_BACKGROUND_STREAM_TOPOLOGY_UNKNOWN` untuk data/subtitle/attachment atau stream tidak dikenal; `E_BACKGROUND_VIDEO_STREAM_AMBIGUOUS` untuk video ganda; `E_FFPROBE_STREAM_MISSING` untuk video wajib kosong. Semua sebelum host write dan return `PREFLIGHT_FAIL`.
- `core/track_preflight.py` mengembalikan report tanpa `track_candidate` jika FFprobe mendeteksi kondisi di atas; tidak ada fallback audio otomatis.
- `core/background_audio.py`: worker offline calon pembuat MP4 **video saja**. Perlu media root + cache root terpisah yang sudah ada, path sumber dibatasi dalam root, SHA-256 sumber dicocokkan, ulang hash setelah FFprobe/FFmpeg, fixed FFmpeg `-map 0:v:0 -c:v copy -an -sn -dn` dengan `shell=False`, validasi output FFprobe harus tepat satu video tanpa audio, cache name content-addressed dan commit dengan hardlink tanpa overwrite. File asli tidak ditimpa; cache lama tidak ditimpa. `can_import=false` dan `can_assemble=false` selamanya pada hasil worker.
- `tests/test_core_ffprobe.py`, `tests/test_core_track_preflight.py`, `tests/test_core_background_audio.py`, `tests/test_core_background_audio_real.py`: kasus file campuran, side streams, 2 video, kosong, hash berubah, cache duplikat, kegagalan subprocess, batas ukuran, symlink/traversal serta tes integrasi MP4 sintetis opsional.
- `.github/workflows/step09-background-audio.yml`: Linux+Windows Python/JS regressions, optional real FFmpeg smoke dan guard bahwa worker/modul mutasi belum dipaketkan dalam runtime CEP P0.

## Bukti / keterbatasan
- [Run #37986661664 SUCCESS](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/actions/runs/37986661664) setelah perbaikan awal: Windows 90/90 JS PASS, Linux 88/90 JS PASS dengan 2 Windows-only skipped, Python 145 tests dengan 2 optional smoke skipped dan 0 FAIL.
- Commit lebih baru `b10c71ed` menambah perlindungan source berubah saat FFprobe dan perbaikan fixture Windows; lihat CI commit terbaru sebelum menyatakan PASS.
- Tes FFmpeg nyata di lingkungan Linux terisolasi (FFmpeg 7.1.5): dibuat MP4 64x64 dengan stream `mpeg4 video + aac audio`; perintah copy `-an` menghasilkan MP4 video-only berukuran lebih kecil, dengan stream `mpeg4 video` tanpa audio. Ini memeriksa pipeline FFmpeg, **bukan Premiere, worker CEP atau animasi**.
- Pada GitHub CI, tes optional FFmpeg/FFprobe REAL dapat SKIP jika runner tidak punya executable. Jest/Node, unit Python mock dan integrasi offline tidak membuktikan Adobe host.
- **Worker ini belum terhubung ke tombol CEP atau penggantian SOURCE_BACKGROUND** secara otomatis. Snapshot/manifest host harus diperbarui secara aman dan di-hash lagi setelah membuat copy; jangan memakai hasil worker sebagai izin Premiere. Belum ada auto mutes/overwrite klip Premiere.
- STEP08 track candidate/JSX placement tetap bersifat `CANDIDATE_NOT_EXECUTABLE`. UI approval 12 PNG dari pemilik tidak berubah; tidak ada UI image baru. PR Draft, `main` tidak diubah, tanpa installer/rilis.

## Langkah implementasi berikutnya
Lanjutkan pembentukan derived media overlay yang memetakan source background yang telah disanitasi ke candidate immutable snapshot + provenance hash, lalu validasi durasi dan video-only output; implementasi source trim V1 serta penjagaan linked audio dalam sequence, pengujian host mock, kemudian 21 preset BOTH dan Windows package. Semua host G3 tetap menunggu fase akhir.

**Aplikasi BELUM selesai; 0/30 host AC dan 0/21 preset efek Adobe host tersertifikasi.**
