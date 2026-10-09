# Mulai di sini — ASTRA / SOL

**STEP01 ASTRA — G1A BLOCKED; G1B NOT_STARTED; G2 NOT_STARTED; CODING PROHIBITED.**

Urutan baca: [AGENTS](../AGENTS.md) → [STATUS](STATUS.md) → Master V3 DOCX/transkrip dalam docs/source → STEP00 plan → STEP01 kontrak V1 → pemulihan 7 sumber V2 → Gate Closure Review V4 DOCX/MD → [audit statis JSON DEMO_001](planning/STEP01_V3_DEMO_STATIC_AUDIT.md) → [68 fixture rencana](planning/STEP01_FIXTURE_CATALOG.csv) → [10 keputusan](planning/STEP01_REVIEW_QUEUE.csv) dan [blockers](planning/BLOCKERS.md).

AUDIT JSON DEMO_001: 18/18 cek struktur dan durasi referensi PASS; **tidak membuktikan** source media asli, registry allowed direction, implementasi codec, host Premiere, UI ataupun AC. Semua checksum media contoh adalah placeholder.

F026 pada fixture 48 awal stale: half-frame rounding kini source-supported, diperbaiki menjadi 50ms@30FPS→frame2. Fixtures diperluas menjadi 68; belum ada test code.

MEDIUM-only untuk MVP tetap opsi yang direkomendasikan, bukan keputusan user yang sudah eksplisit. B01 source archive dan Q02 directions/Q03 schema masih membutuhkan keputusan. Jangan infer approval dari chat 'lanjutkan'. Setelah G1A PASS, STEP02 prompt UI lalu STOP wajib sampai gambar+approval+UI_REFERENCE_FINAL.docx di repo.
