# SOL STEP15 — jadwal BOTH semua 21 preset (10 Oktober 2026)

## Aturan kerja pemilik dan gate
SOL harus menyelesaikan coding, integrasi dan semua CI yang memungkinkan tanpa meminta pemilik menguji Premiere Pro 2024 pada setiap tahap. Pengujian host asli dilakukan pada akhir. **G3 BLOCKED_HOST / NOT VERIFIED**; mock dan durasi referensi tidak boleh dinyatakan sebagai efek benar-benar berfungsi di Premiere. UI PNG final tetap milik pengguna, tidak dibuat/disunting AI. PR Draft, `main` tidak berubah.

## Fitur baru yang sudah dikoding
- `core/animation_timings_b02.json`: 21 preset terpisah dengan `in_frames`, `out_frames`, dan tingkat bukti menurut `docs/planning/STEP01_B02_PROPOSED_21_DIRECTION_REGISTRY.csv` (tepat angka sumber MEDIUM, bukan estimasi). **Referensi/proposal B02, belum kalibrasi visual atau backend final.**
- `core/animation_phases.py`: untuk setiap kemunculan scene/asset yang cocok dua JSON, buat rentang frame `IN`, `HOLD`, `OUT` secara deterministik, memakai **preset, arah, dan MEDIUM persis**; tidak ada pemilihan ulang, swap IN/OUT, interpolasi durasi, auto-random, atau fallback. Jika `D<IN+OUT`, gagal `E_TIME_006`. Jika `D==IN+OUT`, `zero_hold_needs_visual_review` benar dan tidak menyatakan visual sudah layak. Keputusan SLOW/FAST/locked=false/unknown field tetap diblokir. Hasil `REFERENCE_SCHEDULE_ONLY`, `can_render=false`, `can_assemble=false`.
- `core/validate_cli.py`: `--include-animation-phases --max-animation-instances N` (batas developer wajib) menggabungkan pemeriksaan fase ke preflight offline. UI hanya menerima jumlah visual, jumlah hold-nol dan digest; detail file/path tidak disalurkan.
- `panel/validation_bridge.js` dan `panel/validation_ui.js`: menampilkan ringkasan fase BOTH yang *belum dapat dirender*, menolak hasil palsu `READY`, `can_render=true`, dan angka tak valid; tombol timeline tetap terkunci.
- Paket CEP **TEST ONLY** diubah menjadi 26 file / 25 checksum, termasuk katalog waktu dan scheduler; inspector/staging aman serta CI packaging lama diselaraskan. **Tidak ada engine efek native atau FFmpeg output tambahan.**

## Bukti CI
[STEP15 Windows/Linux GitHub Actions #37994743727 — SUCCESS](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/actions/runs/37994743727), implementation SHA `69049289b4b04e4763eae44287135536e8e96851`:
- Dedicated **11/11 Python tests PASS**, termasuk pembandingan semua 21 angka IN/OUT/evidence terhadap CSV ASTRA.
- Windows **234 Python tests tanpa kegagalan** (2 opsional dapat SKIP tergantung runner), **99/99 JavaScript PASS**, termasuk proses Node→Python nyata.
- Ubuntu **234 Python tests tanpa kegagalan** (opsional environment SKIP), **97 JS PASS, 2 Windows-only SKIP**.
- Cakupan tes: 21 arah/preset, frame continuity, E_TIME_006, zero hold, per-occurrence same asset, digest stabil, cap wajib, parser UI sanitization.
- CI adalah unit/integrasi sintetis, tidak membuktikan animasi visual Canva/Premiere atau alpha hasil ekspor.

## Belum selesai
STEP16 perlu mengimplementasikan **backend efek riil** berdasarkan per-preset sesuai semantik disetujui, keyframes native atau FFmpeg RGBA (mask/reveal), produksi asset & cache yang aman, readback, layout/crop dan host dispatcher dengan bukti Premiere asli. **0/21 preset host certified, 0/30 AC host live verified.** Belum installer/MP4 final, jangan merge/release.
