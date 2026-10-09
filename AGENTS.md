# Instruksi untuk ASTRA dan SOL

Lingkup hanya repository AI-JSON-Premiere-Editor. Baca docs/00_START_HERE.md dan docs/STATUS.md sebelum bekerja.

1. ASTRA merencanakan; SOL mengimplementasikan. Instruksi pengguna terbaru dan Master V3 di docs/source adalah otoritas. Paket ASTRA A1 mengoperasionalkan master, tidak menggantikannya.
2. Target Premiere Pro 2024 Windows 11: CEP + ExtendScript + FFmpeg hybrid. Jangan berpindah ke UXP atau standalone renderer.
3. Dua JSON tetap terpisah; tepat satu preset per (scene_id, asset_id), BOTH wajib. Tidak ada pemilihan ulang, split IN/OUT atau fallback preset diam-diam.
4. Missing required file atau unreadable input menghentikan proses. Jangan mengganti dengan dummy untuk proyek nyata.
5. Tahap UI wajib STOP setelah prompt selesai. Coding tidak boleh dimulai sebelum seluruh gambar final disetujui dan satu DOCX referensi UI beserta seluruh planning tersedia di repo.
6. Kerjakan satu STEP per giliran, laporkan gate dan next STEP lalu tunggu lanjutkan. Kata lanjutkan tidak mengalahkan STOP UI, file wajib, atau host gate yang belum terpenuhi.
7. STEP01 hanya spesifikasi dan katalog fixture. Implementasi schema/tests dilakukan setelah G2, pada STEP04. Bedakan G1A SPEC dan G1B SCHEMA TEST.
8. Tiap STEP planning menghasilkan DOCX detail dan salinan teks untuk AI lain. Implementasi tidak memerlukan DOCX rutin kecuali kontrak/arsitektur berubah.
9. Simulasi/CI tidak membuktikan Premiere. Rekam exact build dan evidence; status untested bukan PASS.
10. Default CREATE_NEW_SEQUENCE. Jangan menimpa edit manual, menghapus media/cache linked, atau retry ke sequence parsial tanpa inspeksi.
11. Paket/installer akhir setelah pengujian. Tidak ada merge implementasi, force push, tag/release otomatis tanpa otorisasi yang sesuai. Publikasi planning awal telah diminta pengguna.
12. Jangan mengarang ukuran layout, FAST/SLOW, direction, codec tersertifikasi, lisensi proyek, atau hasil tes. Lihat docs/planning/BLOCKERS.md.
13. **ATURAN KHUSUS UI FINAL (PERINTAH PENGGUNA 2026-10-09): ASTRA/SOL/ASISTEN DILARANG membuat, generate, menggambar ulang, menyunting, atau menghasilkan PNG UI sendiri.** Tugas AI adalah menulis prompt gambar lengkap sebagai file TXT, dengan MAKSIMAL 10 prompt per batch (contoh 39 gambar = 4 TXT: 10+10+10+9). **Pengguna sendiri yang melakukan generasi gambar** dan menyerahkan hasil untuk diaudit. Jangan memakai mockup buatan asisten sebagai UI final; jangan infer approval dari "lanjutkan". Revisi pun diberikan dalam TXT, bukan gambar. Setelah seluruh gambar dibuat pengguna, periksa, revisi via prompt jika perlu, tunggu approval eksplisit, lalu satu UI_REFERENCE_FINAL.docx baru boleh dibuat dan disimpan di repo.

14. **PEMBARUAN OTORISASI PENGGUNA (10 Oktober 2026, mengungguli aturan urutan lama #6 untuk fase implementasi):** SOL harus terus menyelesaikan coding UI, fitur, integrasi, CI, audit dan perbaikan bug secara bertahap; kata "LANJUTKAN" berarti mengerjakan coding nyata berikutnya, bukan meminta uji aplikasi berulang. Pengujian manual Premiere oleh pemilik **dipindah ke fase paling akhir** setelah seluruh pengujian otomatis yang mungkin selesai. Gate G3 host tetap **NOT_VERIFIED/BLOCKED_HOST** dan tidak boleh diklaim PASS karena pemilik menunda tes; namun ini **bukan lagi STOP untuk coding aman/offline STEP04 dan modul lanjutan**. Fitur yang memerlukan akses Premiere asli tetap diberi label UNTESTED, jangan merilis atau mengklaim aplikasi selesai sebelum uji nyata final. Tetap jaga aturan larangan generate/mengubah PNG UI, larangan overwrite manual, fail-closed, dan larangan merge/release tanpa izin.
