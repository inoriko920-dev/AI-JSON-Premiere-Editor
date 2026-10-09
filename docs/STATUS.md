# Status proyek — 9 Oktober 2026 WIB

**STEP01 G1A SPEC PASS. STEP02 G2 BLOCKED — USER-ONLY UI IMAGE GENERATION.**

- Pengguna menetapkan aturan tetap: **AI hanya membuat prompt gambar TXT; pemilik membuat semua gambar UI sendiri.** Dua percobaan kolase serta redraw/PNG yang dihasilkan asisten sebelumnya **tidak boleh dianggap UI final dan tidak menjadi basis G2 PASS**.
- Audit awal terhadap 12 gambar: **7 revisi** (UI03, UI04, UI07, UI08, UI09, UI10, UI11), **2 perbaikan kecil** (UI02, UI05), **3 tidak perlu revisi** (UI01, UI06, UI12).
- [Batch tunggal 9 prompt revisi siap digunakan pemilik](ui/revisions/BATCH_01_REVISI_9_UI02_UI11_OWNER_GENERATES.txt). Setiap prompt mandiri; maksimum 10 prompt per TXT dipatuhi.
- Selanjutnya pemilik membuat 9 PNG revisi sendiri dan menyerahkan untuk QA; asisten hanya meninjau dan bila perlu menulis TXT revisi, **tidak mengedit/generate gambar**.
- G2 belum PASS karena hasil akhir 12 PNG belum disetujui secara eksplisit dan satu UI_REFERENCE_FINAL.docx belum diarsipkan di GitHub.
- G1B executable tests NOT_STARTED; host Premiere 24.x, 21 efek dan AC01–AC30 belum terverifikasi. PR masih Draft, main belum di-merge. **SOL coding dilarang sampai G2 PASS**.
