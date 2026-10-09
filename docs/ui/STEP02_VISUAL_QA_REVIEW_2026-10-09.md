# STEP02 — Visual QA hasil 12 gambar UI

**Tanggal 9 Oktober 2026** · AI-JSON-Premiere-Editor · **status REVIEW COMPLETE / REVISI REQUIRED / G2 BLOCKED**

Pengguna menyatakan 12 gambar dari dua batch sudah dibuat dan meminta melanjutkan. Audit ini memeriksa gambar asli yang tersedia dalam percakapan. **Semua 12 PNG belum diunggah ke GitHub**, belum disetujui eksplisit sebagai UI final, dan `UI_REFERENCE_FINAL.docx` belum dibuat. Paket DOCX review terpisah dan gambar asli tersedia dalam percakapan tetapi **bukan** dokumen final UI.

## Hasil

- 12/12 gambar ditemukan: **3 SESUAI, 2 CATATAN, 7 REVISI** (5 wajib karena kontrak/alur, 2 perapian konsistensi contoh).
- Semua gambar asli berukuran **1672 × 941**, bukan target 1920×1080. Normalisasi/aspek final perlu direview; perbesaran resolusi tidak menambahkan detail asli.
- 21 preset masih **0/21 host verified**, AC01–AC30 **0/30**. Ini desain statis, bukan screenshot host Premiere berjalan.

| Layar | QA | Temuan | Langkah |
|---|---|---|---|
| UI01 | SESUAI | Panel awal kosong, host belum diperiksa, assembly disabled | Tidak perlu |
| UI02 | CATATAN | Indikator centang berpotensi tampak seperti file tervalidasi | Ganti status menjadi Dipilih / Belum divalidasi |
| UI03 | REVISI_WAJIB | READY tapi Host belum diperiksa dan BOTH disalahartikan output video+animasi | Tampilkan host sudah diverifikasi secara simulasi; BOTH berarti animasi IN+OUT |
| UI04 | REVISI_TERARAH | Contoh cue SRT 1:12/3:45 tidak masuk timeline DEMO_001 yang 11 detik | Gunakan cue contoh di 0-11 detik atau beri ID proyek lain |
| UI05 | CATATAN | A004 dan B001 muncul sebagai media demo padahal project summary 3 asset occurrences | Konsistenkan daftar file dengan DEMO_001 |
| UI06 | SESUAI | V002 DOUBLE A002 PAN dan A003 WIPE dalam frame benar dan read-only | Tidak perlu |
| UI07 | REVISI_WAJIB | Registry menawarkan pilih/ubah preset dan menyimpan ke EDIT_PLAN.json | Read-only dari ANIMATION_PLAN.json; tanpa tombol simpan/edit pada EDIT_PLAN |
| UI08 | REVISI_WAJIB | Modal BUILD READY di atas panel kosong NO_PROJECT dan sumber belum dipilih | Latar harus menunjukkan preflight READY dengan DEMO_001 terpilih |
| UI09 | REVISI_WAJIB | ASSEMBLING 43% tapi host belum diperiksa dan timeline kiri kosong | Simulasikan sequence baru sudah terbentuk dan host sudah diverifikasi |
| UI10 | REVISI_WAJIB | ASSEMBLED namun no sequences; A002/A003 ditampilkan sebagai Narasi/Audio | Tampilkan sequence di host simulasi; tabel scene/asset/track/preset; pisahkan voice audio |
| UI11 | REVISI_TERARAH | 7 dari 9 scene bertentangan dengan DEMO_001 2 scene; host no sequence | Samakan contoh 2 scene, beri sequence _INCOMPLETE di timeline atau ganti ID proyek |
| UI12 | SESUAI | 25.x ditolak, 24.x diwajibkan, assembly disabled | Tidak perlu |

## Cacat kontrak yang harus ditutup

1. `UI07`: **ANIMATION_PLAN.json memiliki satu pilihan preset per kemunculan aset, mode BOTH = masuk/keluar**. Tidak boleh menyimpan animasi ke EDIT_PLAN, membuat pilihan efek manual yang melanggar JSON, atau mengubah dua efek IN/OUT secara terpisah. Registry bersifat baca-saja di pilot.
2. `UI03`: BOTH **bukan** kode output Video Final + Animasi. `READY` juga tidak boleh terjadi jika host belum terverifikasi.
3. `UI08`, `UI09`, `UI10`: state machine harus konsisten dengan representasi sequence Premiere yang dibuat. Tidak boleh READY/ASSEMBLING/ASSEMBLED berbarengan dengan `NO_PROJECT`, host belum diperiksa atau timeline kosong.
4. `UI10`: V002/A002 dan V002/A003 adalah pasangan scene/aset visual; jangan menamainya kolom Narasi/Audio.
5. `UI04`,`UI11`: data simulasi sebaiknya memakai durasi/rentang scene dan jumlah media yang konsisten dengan DEMO_001 atau secara eksplisit berganti proyek demo.

## Gate

**G1A SPEC PASS tetap berlaku. G1B NOT_STARTED. G2 = WAIT_REVISION_AND_EXPLICIT_APPROVAL**, bukan PASS. STEP02 masih aktif di tahap pemeriksaan gambar. Jangan coding SOL, merge, merilis plugin, atau menulis UI_REFERENCE_FINAL.docx yang berpura-pura berisi gambar final yang telah disetujui.

**Next:** revisi 7 gambar menggunakan [batch revisi TXT](revisions/STEP02_REVISION_BATCH_01_7_UI.txt), cek ulang semua 12, minta persetujuan eksplisit pengguna, lalu arsipkan 12 PNG final beserta SHA dan satu UI_REFERENCE_FINAL.docx di repo sebelum G2 gate.