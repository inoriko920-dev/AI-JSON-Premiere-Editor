# STEP 02 — Audit sembilan gambar revisi (9 Oktober 2026)

**G1A SPEC PASS · G2 BLOCKED · G1B NOT_STARTED · DILARANG CODING**

Sembilan gambar diberikan melalui percakapan dan diperiksa secara visual tanpa membuat atau menyunting PNG oleh AI. Seluruh sembilan PNG native **1672 × 941**; target spesifikasi 1920 × 1080 sehingga deviasi resolusi perlu persetujuan pengguna atau hasil baru dari generator miliknya.

| Layar | QA | Temuan |
|---|---|---|
| UI02 | SESUAI substansi | Berkas dipilih namun belum divalidasi |
| UI03 | SESUAI substansi | READY dan BOTH (IN+OUT) ditandai SIMULASI |
| UI04 | SESUAI substansi | Cue di dalam rentang 11 detik; NEEDS_REVIEW tetap aman |
| UI05 | SESUAI substansi | Missing A003, fail-closed, tidak ada dummy |
| UI07 | **REVISI** | General (15) mengandung efek Reveal; PAN (preset) dan FROM_LEFT (arah) tertukar |
| UI08 | **REVISI** | Sequence target sudah ada SEBELUM dialog konfirmasi; aset MOV/MP4 padahal seharusnya PNG |
| UI09 | **REVISI** | Host verified/belum diperiksa kontradiktif; label media 24 FPS bukan 30; log dan timeline tidak sinkron |
| UI10 | **REVISI** | 3 scene/10 detik, seharusnya 2 scene/330 frame/11 detik |
| UI11 | **REVISI** | A003 RIGHT ditaruh di V2, seharusnya V3; timeline berhenti 10 detik bukan 11 detik |

UI01, UI06, UI12 tetap memakai desain lama yang pada QA sebelumnya sudah dianggap sesuai secara substansial, tetapi **tidak otomatis APPROVED FINAL**.

## Acuan yang wajib konsisten
- DEMO_001: 2 scene V001 [0,150) dan V002 [150,330), total 330 frame @30 FPS = 11 detik.
- A001.png V2, A002.png (LEFT) V2, A003.png (RIGHT) V3 start frame192.
- Background background.mp4 V1; narasi.wav A1.
- Registry read-only ANIMATION_PLAN.json, satu preset dengan BOTH IN+OUT per aset, pilot MEDIUM.
- Tidak ada klaim Premiere host/animasi sudah terbukti berjalan.

## Tindakan berikutnya
[**Satu TXT berisi 5 prompt revisi**](revisions/BATCH_01_REVISI_LANJUTAN_5_UI07_UI11.txt) untuk digenerate sendiri oleh pemilik. Setelah 5 gambar dibagikan dan audit lulus, minta persetujuan eksplisit **semua 12 gambar final** termasuk resolusi native jika diterima. Setelah persetujuan, satu UI_REFERENCE_FINAL.docx yang menampilkan seluruh gambar serta hash PNG wajib diarsipkan ke repo. G2 baru bisa diperiksa; sampai saat itu SOL coding, merge dan release dilarang.