# SOL STEP07 — Timeline placement V1/V2/V3/A1 (10 Oktober 2026)

## Status saat ini
**IMPLEMENTASI KODE CANDIDATE + AUTOMATED TEST PASS · REAL PREMIERE HOST UNVERIFIED.** Pemilik meminta seluruh coding, integrasi, dan test otomatis diselesaikan lebih dulu; pengujian Premiere Pro 2024 Windows 11 dilakukan pada tahap akhir. `G3=BLOCKED_HOST` sampai uji nyata. Tidak ada perubahan pada gambar UI final, `main`, installer maupun release.

## Kode yang sudah dikerjakan
- `core/timeline_candidate.py`: *pure deterministic planner* dari kontrak `EDIT_PLAN.json` dan `ANIMATION_PLAN.json`, hash snapshot STEP06 dan timebase ticks string STEP05. Background V1 di-loop otomatis dengan trim tepat di ujung, visual V2/V3 ditempatkan dari setiap scene/asset, A1 satu clip narasi dari frame nol sampai total scene. Gagal dengan `E_NARRATION_DURATION_MISMATCH` jika frame audio tidak persis panjang timeline (tidak memotong narasi otomatis). Track overlap dan resource cap aman; keluaran tetap `CANDIDATE_NOT_EXECUTABLE` serta `can_assemble=false`.
- `host/track_placement_adapter.jsx`: calon **ExtendScript ES3** berbasis `Track.overwriteClip(ProjectItem, ticksString)` pada **sequence baru yang kosong dan tervalidasi**; memeriksa ID proyek, timebase, role source, dan semua track kosong; menempatkan V1/V2/V3/A1 satu per satu, memangkas hanya `TrackItem.inPoint/outPoint/end` milik klip baru, lalu membaca ulang clip start/end/trim dan ProjectItem.nodeId. Jika muncul linked-audio atau track lain berubah, menghentikan dengan `INCOMPLETE` serta tidak menghapus/mengulang operasi. Sebelum operasi dibutuhkan otorisasi host/layout/FX/media/preflight yang belum tersedia.
- Semua tick diverifikasi dengan **perkalian desimal tepat di ES3**, tanpa mengubah tick besar ke floating point JavaScript. Background V1 wajib kontigu hingga frame terakhir dan audio A1 tepat sepanjang total video.
- `tests/test_core_timeline_candidate.py`: loop/last segment, sumber A1, digest stabil, source asset hilang, tidak cocok durasi dan batas jumlah operasi.
- `tests/track_placement_adapter.test.cjs`: mocked Adobe sequence/Track/TrackItem, otorisasi negatif, sumber salah, perubahan pada track lain, gagal API, readback trim salah, overlap, tick palsu, dan ketahanan sequence lama. Tidak ada host asli.
- `.github/workflows/step07-timeline-mock.yml`: Windows + Linux regressions penuh, tetap melarang mutator ini masuk P0 CEP ScriptPath atau ZIP.

## Bukti CI
[Actions run #37995908038 SUCCESS](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/actions/runs/37995908038) pada implementasi SHA `0eda45af17bbd65f8beae8e5b25c384c6b87769b`:
- Windows: **13/13** adapter, **11/11** timeline Python, seluruh **91/91** Node, Python **117 berjalan (116 PASS + 1 optional real-FFprobe SKIP)**.
- Ubuntu: **13/13** adapter, **11/11** timeline Python, Node **89 PASS + 2 Windows-only SKIP** dari 91; Python **117 berjalan (116 PASS + 1 real-FFprobe SKIP)**.
- `NO_UNVERIFIED_HOST_MUTATION_ROUTE=PASS` pada kedua OS. Ini **bukan** sertifikat keberhasilan Premiere.

## Penting: masih belum selesai
Importer STEP06 dan sequence creator STEP05 masih calon kode yang belum diaktifkan dari CEP; proses penempatan klip ini juga **tidak di-load oleh live panel**. Perlu host-proof pengaturan Time/overwrite behavior, media sumber dan durasi sebenarnya, backend transisi/layout/crop PNG, semua **21 preset BOTH**, FFmpeg alpha dan cache/journal, readback serta pemeriksaan audio linked, production packaging, dan pengujian end-to-end akhir di Windows 11.

**G1A SPEC PASS · G2 UI FINAL PASS · G3 BLOCKED_HOST (deferred to final testing).** No main merge, release, 21 FX certification, completed app or final MP4.
