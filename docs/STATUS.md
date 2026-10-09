# Status proyek

- Tanggal pembaruan: 9 Oktober 2026 WIB.
- Baseline main: `e28e08f818d92f01996ce6a6ca6db52606728bfb` (STEP00 ASTRA planning).
- Tahap kerja: **STEP01 ASTRA — DRAFT_WITH_BLOCKERS**, pada branch `astra/step01-contract-spec-20261009`. Hasil terdiri dari DOCX kontrak, Markdown, katalog 48 fixture, dan keputusan terbuka.
- G0 kesiapan penuh: BLOCKED pada sumber V2/layout/efek dan jalur host nyata.
- G1A spesifikasi: **BLOCKED** (B01, B02, B06). Belum dapat disahkan untuk coding.
- G1B schema tests: NOT_STARTED; baru boleh dibuat/diuji SOL STEP04 setelah UI gate.
- G2 gambar UI + DOCX referensi final + approval: NOT_STARTED. **Coding PROHIBITED**.
- G3–G10: NOT_STARTED; P0–P6 NOT_TESTED.
- AC01–AC30: 0/30 diuji; 21 preset 0/21 disertifikasi.
- Produk, executable, CI produk, installer dan release: belum ada.

## Serah terima

Lihat [STEP01 DOCX](planning/ASTRA_STEP01_KONTRAK_TEKNIS_V1_DRAFT_2026-10-09.docx), [STEP01 Markdown](planning/ASTRA_STEP01_KONTRAK_TEKNIS_V1_DRAFT_2026-10-09.md) dan [Fixture katalog](planning/STEP01_FIXTURE_CATALOG.csv). Planning draft bukan hasil tes host atau keputusan mengganti Master V2. Jangan mengubah G1A menjadi PASS sebelum seluruh definisi normatif benar-benar lengkap dan disetujui.

## Berikutnya

Masih STEP01: tutup B01/B02/B06 dengan sumber resmi atau spesifikasi pengganti yang disetujui, bekukan kontrak, perbarui DOCX/MD dan catat approval. Sesudah G1A PASS, STEP02 menyiapkan prompt UI dan STOP menunggu gambar final serta approval. Jangan merge implementasi sebelum gate lengkap.
