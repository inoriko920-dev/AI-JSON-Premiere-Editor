# STEP02 G2 QA dan STOP gate

**12 prompt tersedia; PNG 0/12 dihasilkan; approved PNG 0/12; UI_REFERENCE_FINAL.docx BELUM ADA.**

1. Saat pengguna memberi perintah baru untuk generate UI, buat SATU gambar 1920x1080 per prompt individual; 12 PNG bernama sesuai STEP02_SCREEN_MANIFEST.csv.
2. Periksa label Bahasa Indonesia, panel kanan dockable dan header konsisten, watermark SIMULASI, ALL enabled/disabled states, tidak ada AI chat/Filmora clone, tidak ada MP4 export worker.
3. Periksa kesinambungan JSON/timing: V002 LEFT A002 PAN FROM_LEFT [150,330); RIGHT A003 WIPE RIGHT_TO_LEFT [192,330); MEDIUM, BOTH.
4. Pastikan UI-05 missing A003 stop, UI-04 ambiguous SRT review, UI-08 new sequence, UI-11 partial state tidak destructive, UI-12 host unsupported stop.
5. Minta persetujuan eksplisit terhadap SELURUH 12 PNG final. Jika ada perbedaan/revisi, jangan meneruskan ke implementasi.
6. Hanya setelah disetujui: catat checksum SHA-256, simpan seluruh PNG, kemudian susun SATU UI_REFERENCE_FINAL.docx yang menyertakan 12 PNG plus keputusan desain. Upload ke GitHub.
7. Baru audit G2 gate. SOL mulai coding STEP03 setelah semua DOCX planning + UI_FINAL ada di repo dan G2 PASS; tidak ada merge otomatis.

**Berhenti sekarang: STEP02_PROMPTS_COMPLETE_STOP_WAIT_UI_IMAGES.**