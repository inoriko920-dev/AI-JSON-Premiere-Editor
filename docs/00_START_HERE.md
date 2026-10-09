# Mulai di sini untuk ASTRA dan SOL

Repo ini adalah handoff planning. Baca [STATUS](STATUS.md) dahulu. **Belum boleh coding.**

## Urutan baca

1. [Instruksi agent](../AGENTS.md).
2. [Master V3 asli](source/MASTER_PLAN_V3_PLUGIN_ADOBE_PREMIERE_PRO_2024_JSON_BOTH.docx) atau [transkrip lengkap](source/MASTER_PLAN_V3_TRANSCRIPT.md).
3. [Rencana ASTRA A1 DOCX](planning/ASTRA_STEP00_RENCANA_IMPLEMENTASI_SOL_V3_A1_2026-10-09.docx) dan [Markdown](planning/ASTRA_STEP00_RENCANA_IMPLEMENTASI_SOL_V3_A1_2026-10-09.md).
4. [Blocker](planning/BLOCKERS.md) dan [audit sumber](planning/SOURCE_AUDIT.md).
5. [Acceptance 30 AC](planning/ACCEPTANCE_MATRIX.csv) dan [21 preset](planning/PRESET_MATRIX.csv).

## Instruksi siap pakai untuk AI penerus

Anda melanjutkan AI-JSON-Premiere-Editor. Baca semua dokumen di atas. Jangan memulai kode karena G2 UI belum PASS. Tugas terdekat adalah STEP01 ASTRA: lengkapi sumber kontrak V2/layout/animasi/prompt atau minta keputusan penggantinya, lalu buat DOCX spesifikasi rinci. Laporkan kebutuhan berkas secara spesifik, jangan mengarang nilai yang belum tersedia. Pada STEP02 buat prompt UI lalu berhenti sampai seluruh gambar final disetujui, dimasukkan ke satu DOCX referensi UI, dan disimpan di repo. SOL mulai STEP03 hanya sesudah semua prasyarat PASS. Ikuti backlog STEP03–STEP10 dalam plan A1, satu STEP per giliran. Bedakan planning, CI dan bukti host nyata. Jangan merge kode atau release tanpa izin yang sesuai.

## Roadmap singkat

| STEP | Hasil | Gate |
| --- | --- | --- |
| 00 | Audit dan handoff | Planning lengkap; kesiapan masih blocked |
| 01 | Kontrak dan arsitektur detail DOCX | G1A SPEC; bukan executable tests |
| 02 | Prompt lalu UI final dan DOCX | STOP untuk approval; G2 |
| 03 | Panel minimal di Premiere | G3 real host P0 |
| 04 | Validator dan dry run | G1B serta G4 |
| 05 | Timeline SINGLE/DOUBLE | G5 P1/P2 |
| 06 | Fade/Pan native, probe Wipe | G6 native subset, P3 |
| 07 | Brush alpha dan cache | G7 P4; tutup P3 Wipe jika baked |
| 08 | Semua 21 preset | G8 P5 seluruh kombinasi advertised |
| 09 | Stress, manual edit, reopen, export | G9 P6 AC01–AC30 |
| 10 | Paket plugin dan install test | G10 release |

Semua status implementasi sekarang NOT_STARTED. Dokumen roadmap bukan bukti bahwa tahap tersebut telah dijalankan.
