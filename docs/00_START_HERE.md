# Mulai di sini untuk ASTRA dan SOL

Baca [STATUS](STATUS.md) dahulu. **Saat ini belum boleh coding.** Repo ini berisi handoff planning, bukan plugin Premiere yang dapat dijalankan.

## Urutan baca

1. [Instruksi agent](../AGENTS.md).
2. [Master V3 asli](source/MASTER_PLAN_V3_PLUGIN_ADOBE_PREMIERE_PRO_2024_JSON_BOTH.docx) dan [transkripnya](source/MASTER_PLAN_V3_TRANSCRIPT.md).
3. [Rencana ASTRA STEP00 DOCX](planning/ASTRA_STEP00_RENCANA_IMPLEMENTASI_SOL_V3_A1_2026-10-09.docx), [Markdown](planning/ASTRA_STEP00_RENCANA_IMPLEMENTASI_SOL_V3_A1_2026-10-09.md).
4. [STEP01 Kontrak draft DOCX](planning/ASTRA_STEP01_KONTRAK_TEKNIS_V1_DRAFT_2026-10-09.docx), [Markdown](planning/ASTRA_STEP01_KONTRAK_TEKNIS_V1_DRAFT_2026-10-09.md), [katalog fixture](planning/STEP01_FIXTURE_CATALOG.csv).
5. [Blocker](planning/BLOCKERS.md), [audit sumber](planning/SOURCE_AUDIT.md), [acceptance 30 AC](planning/ACCEPTANCE_MATRIX.csv), [21 preset](planning/PRESET_MATRIX.csv).

## Instruksi penerus

Kontrak STEP01 ini masih DRAFT_WITH_BLOCKERS, bukan G1A PASS. Inventaris dan penyelesaian B01/B02/B06 diutamakan. Tidak boleh membuat parser, executable schema, tests, panel, worker, host JSX atau installer berdasarkan keputusan sementara. Missing required project files harus stop; jangan pakai dummy input untuk menyelamatkan job nyata.

Setelah sumber disahkan serta G1A PASS, dan hanya dengan instruksi lanjut yang sesuai, ASTRA masuk STEP02 untuk membuat prompt UI **lalu wajib STOP**. Setelah gambar UI final disetujui secara eksplisit, masukkan gambar beserta satu UI_REFERENCE_FINAL.docx dan approval hash ke repo; baru buka G2. SOL tidak boleh mulai coding sebelum semua planning DOCX + UI final ada di repo dan G2 PASS.

## Roadmap ringkas

STEP00 audit/handoff → STEP01 kontrak/fixture katalog (current, blocked) → STEP02 prompt UI STOP lalu final UI approval → STEP03 panel CEP + P0 Premiere nyata → STEP04 schema/validator/dry-run → STEP05 timeline SINGLE/DOUBLE → STEP06 efek native awal → STEP07 cache RGBA alpha → STEP08 seluruh 21 preset → STEP09 stress/reopen/manual edit/export → STEP10 paket/installer.

Tidak ada klaim tes host sebelum uji pada Adobe Premiere Pro 2024 build aktual dengan evidence.
