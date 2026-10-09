# Mulai di sini — ASTRA / SOL

**Masih STEP01. B06 validator ADR telah didokumentasikan namun belum final review. G1A BLOCKED; G2 NOT_STARTED; CODING DILARANG.**

Urutan: AGENTS.md → Master V3 di docs/source → STEP00 plan → STEP01 kontrak V1–V5 DOCX/MD → **[ADR-001 B06](planning/ADR_001_VALIDASI_KONTRAK_B06_2026-10-09.md)** → [field policy](planning/STEP01_B06_FIELD_POLICY.csv) → [error crosswalk](planning/STEP01_B06_ERROR_CROSSWALK.csv) → [12 tech decisions](planning/STEP01_B06_TECH_DECISIONS.csv) → 21 direction matrix + 10 review queue + 68 fixture plans → [blockers](planning/BLOCKERS.md).

ADR-001 tidak mengubah dua JSON. Root V2 11/9 tetap wajib; extra metadata nested dan locked=false butuh signoff. Field `render` adalah legacy hint saja, bukan izin ekspor via FFmpeg. Missing media dan unknown backend stop sebelum host mutation.

MEDIUM-only belum user-approved, 21 direction belum certified. Jangan anggap perintah `lanjutkan` sebagai approval. Setelah G1A PASS, STEP02 prompt UI **WAJIB STOP** menunggu seluruh gambar final + approval + satu UI_REFERENCE_FINAL.docx di repo. Baru SOL dapat coding.
