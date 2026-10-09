# ASTRA STEP02 — Paket Prompt Gambar UI CEP

**Tanggal:** 9 Oktober 2026 | **Status:** PROMPTS COMPLETE / STOP WAIT UI IMAGES

G1A SPEC PASS berdasarkan approval B02 Issue #2. G1B belum diuji; G2 belum bisa PASS karena belum ada PNG final.

## Acuan

Master V3 §9, dua JSON terpisah, 21 preset BOTH V6 dengan MEDIUM pilot, panel dockable kanan putih-biru Bahasa Indonesia, tanpa AI chat, final export Premiere, fail-closed. Semua screenshot bertanda SIMULASI dan bukan bukti host.

## Prompt dasar (selalu gabungkan dengan prompt tiap layar)

Buat SATU gambar statis berupa screenshot mockup UI profesional 1920x1080 landscape untuk Windows 11; BUKAN aplikasi atau source code yang dapat dijalankan.
Adobe Premiere Pro 2024 berada di area kiri sekitar 1360 piksel, workspace gelap netral. Panel ekstensi CEP dockable berada di sisi KANAN, lebar sekitar 560 piksel, putih dan biru (#FFFFFF, #F6FAFF, #1268C7) dengan teks navy, hierarki sangat rapi, font sans-serif compact 12-15px tetapi jelas dibaca.
Semua teks panel menggunakan Bahasa Indonesia. Header AI JSON Premiere Editor, Mode BOTH, status host, dan label kecil SIMULASI DESAIN UI wajib terlihat. Data proyek DEMO_001 adalah MOCKUP; jangan mengklaim hasil host atau Premiere teruji.
Panel harus menghormati input dua JSON terpisah dan folder media; satu preset BOTH per pasangan scene/aset. Kecepatan awal hanya MEDIUM; FAST/SLOW menunggu kalibrasi. Timeline dan preview utama tetap milik Premiere; MP4 final diekspor menggunakan Premiere.
Jangan membuat AI chat, meniru Filmora, merancang landing page, membuat thumbnail, menampilkan 21 efek PASS, menawarkan aset otomatis saat file hilang, mengganti preset menjadi Fade diam-diam, atau membuat tombol ekspor MP4 via FFmpeg.
Pertahankan whitespace, scroll list, ikon garis sederhana, state enabled/disabled tombol yang jelas, dan tanda watermark SIMULASI. Tidak perlu menampilkan kumpulan 12 layar: hanya satu UI sesuai prompt ini.

## Manifest dan prompt

### UI01 — Panel awal

**State:** NO_PROJECT | **QA:** Header host belum diperiksa; tiga pilihan file kosong; tombol tidak aktif

Panel CEP kanan dengan header AI JSON Premiere Editor, label BOTH, status Host belum diperiksa. Tiga pemilih terpisah EDIT_PLAN.json, ANIMATION_PLAN.json, Folder Media Proyek masih kosong. Ringkasan proyek kosong. PERIKSA PROYEK dan SUSUN TIMELINE OTOMATIS dinonaktifkan. Instruksi: Pilih dua JSON dan folder media. Tidak ada perubahan timeline.

### UI02 — Berkas dipilih

**State:** FILES_SELECTED | **QA:** JSON dan media masih belum divalidasi

Tampilkan tiga input telah dipilih (EDIT_PLAN.json, ANIMATION_PLAN.json, folder media contoh). Ringkasan DEMO_001, revisi edit 2, animasi 1, 2 scene, 3 kemunculan aset, 1920x1080 30 FPS; label DATA CONTOH. SRT, audio, PNG, background status Belum diperiksa. Tombol PERIKSA PROYEK aktif, SUSUN TIMELINE OTOMATIS dinonaktifkan.

### UI03 — Preflight siap

**State:** READY | **QA:** Assembly aktif hanya jika seluruh preflight lulus

Tampilkan state READY besar dengan tanda SIMULASI. Kartu cek dua JSON cocok, media lengkap, timing valid, registry relevan tersedia (seluruhnya data contoh, bukan uji host). Ringkasan 2 scene, 3 aset, 30 FPS, BOTH dan MEDIUM. Tombol SUSUN TIMELINE OTOMATIS aktif, sublabel Sequence baru, edit manual aman. Tersedia Buka Laporan.

### UI04 — Review bukti SRT

**State:** NEEDS_REVIEW | **QA:** Jangan mengarang timestamp kata

Tampilkan NEEDS_REVIEW. Kartu Scene V002 A003: kutipan muncul dua kali, SRT hanya timestamp cue, kode E_SRT_AMBIGUOUS; bedakan EXACT_CUE dari ESTIMATED_FROM_AUDIO. Tombol Lihat Bukti SRT dan Buka Laporan aktif. SUSUN TIMELINE OTOMATIS nonaktif; instruksi memperbaiki occurrence dan konfirmasi bukti.

### UI05 — File PNG hilang

**State:** PREFLIGHT_FAIL | **QA:** Missing file memblokir assembly tanpa dummy

Tampilkan PREFLIGHT FAIL dengan kode E_MEDIA_MISSING: A003.png belum tersedia, Scene V002 mulai frame 192. Solusi: Tambahkan file ke assets lalu klik Periksa Proyek. Sumber file lain hanya dinyatakan terdeteksi sebagai simulasi. Tombol PERIKSA ULANG aktif; SUSUN TIMELINE OTOMATIS nonaktif. Jangan tawarkan aset pengganti.

### UI06 — Inspektor scene DOUBLE

**State:** FILES_SELECTED | **QA:** Timing/preset read-only dari JSON terpisah

Tampilkan scene V001 SINGLE dan V002 DOUBLE, pilih V002. Rentang scene [150,330) 30 FPS. Dua kartu independen: LEFT A002 [150,330), PAN FROM_LEFT MEDIUM BOTH; RIGHT A003 [192,330), WIPE RIGHT_TO_LEFT MEDIUM BOTH. Cue 2 dan cue 3 masing-masing, identitas PNG dan status Backend belum diverifikasi. Diagram kecil LEFT/RIGHT. Tidak ada edit timing/preset langsung dari UI.

### UI07 — Registry 21 efek

**State:** FILES_SELECTED | **QA:** MEDIUM awal; FAST/SLOW menunggu kalibrasi

Panel Registry Animasi dua tab GENERAL (15) dan REVEAL (6), daftar gulir efek Rise, Pan, Fade, Pop, Wipe, Blur, Breathe, Brush, Ink, Digital, Spray Paint, Sketch, Gradient. Card contoh PAN FROM_LEFT MEDIUM BOTH IN 21 frame OUT 8 frame, label Durasi referensi, belum diuji di host. FAST dan SLOW disable dengan teks Menunggu kalibrasi. Tulisan Host 0/21 terverifikasi; jangan tampilkan 21 PASS atau tombol Acak.

### UI08 — Konfirmasi sequence baru

**State:** READY | **QA:** Jangan overwrite sequence lama

Modal Konfirmasi Susun Timeline, mode wajib BUAT SEQUENCE BARU, nama contoh DEMO_001_AI_JSON_R2_A1. Ringkasan 2 scene, 3 klip visual, background V1, SINGLE/LEFT V2, RIGHT V3 dan narasi A1. Notice Timeline yang sudah ada dan edit manual tidak akan diubah. Tombol Batal dan Buat Sequence Baru. Jangan tawarkan overwrite atau ekspor MP4 FFmpeg.

### UI09 — Progress assembly

**State:** ASSEMBLING | **QA:** Cegah pekerjaan ganda dan simpan log

Panel status ASSEMBLING, simulasi progress 43%, tahap Memasukkan A002 di V2. Daftar log ringkas verifikasi hash, impor media, buat sequence baru, tempatkan audio/background, terapkan animasi. SUSUN TIMELINE nonaktif saat berjalan, tombol Batalkan dengan aman. Info: jika gagal, tandai INCOMPLETE, jangan hapus hasil atau media.

### UI10 — Laporan selesai

**State:** ASSEMBLED | **QA:** Edit manual dan ekspor dilakukan di Premiere

Panel status ASSEMBLED dengan watermark SIMULASI: 2 scene, 3 klip visual, 1 narasi, 1 background, sequence DEMO_001_AI_JSON. Kartu mapping V002/A002 dan V002/A003, BOTH. Tombol Buka Sequence di Premiere, Buka Laporan. Catatan: Edit manual dan ekspor MP4 dilakukan melalui Adobe Premiere Pro. Jangan tawarkan ekspor MP4 langsung dari plugin.

### UI11 — Error parsial dan perbaikan

**State:** INCOMPLETE | **QA:** Jangan hapus cache/sequence tanpa izin

Panel status INCOMPLETE, kode E_HOST_PARTIAL Scene V002 A003, sequence contoh berakhiran _INCOMPLETE, pesan gagal memasang efek. Pilihan Bangun Sequence Baru, Perbaiki Cache dan Batal; tampilkan peringatan jangan overwrite edit manual, jangan hapus linked cache. Tidak ada retry otomatis atau tombol Hapus Semua.

### UI12 — Versi Premiere tidak didukung

**State:** NO_PROJECT | **QA:** Host 25.x tidak boleh diperlakukan sebagai PPRO 24.x

Panel status HOST TIDAK DIDUKUNG, E_HOST_UNSUPPORTED, Premiere terdeteksi 25.x hanya DATA SIMULASI; persyaratan 2024 major 24.x. Status CEP/alpha/native masih BELUM DIVERIFIKASI. Tombol Periksa Host Lagi aktif, SUSUN TIMELINE nonaktif, link Persyaratan Kompatibilitas; tidak menawarkan bypass, downgrade atau fake PASS.

## STOP setelah prompt selesai

DILARANG membuat 12 gambar otomatis, menganggap gambar telah disetujui, membuat UI_REFERENCE_FINAL.docx kosong, menulis kode plugin, melakukan merge, atau klaim real-host PASS. Tahap selanjutnya membutuhkan instruksi baru untuk menghasilkan 12 PNG satu per satu, revisi dan approval pemilik, lalu tepat satu UI_REFERENCE_FINAL.docx bergambar di GitHub.
