# STEP02 final UI — 12 images approved, binary archive pending

Pemilik **menyetujui seluruh 12 gambar UI** sebagai desain final pada 9 Oktober 2026, termasuk:
- Ketidaktepatan ilustrasi UI08–UI11 (tidak mengubah kontrak yang harus ditaati SOL).
- Resolusi asli 1672×941 pada 10 gambar, 1920×1080 pada UI01 dan UI06.
- Izin menyimpan dua belas PNG final **dan satu** `UI_REFERENCE_FINAL.docx` ke GitHub.

**Status GitHub saat ini:** dokumen dan 12 PNG **BELUM TERUNGGAH**. Koneksi GitHub yang tersedia untuk ASTRA hanya mendukung isi teks atau `create_blob` dengan string base64 yang harus tersedia di konektor; tidak dapat mengambil byte mentah dari file container secara langsung. G2 **PENDING_BINARY_ARCHIVE**. Jangan klaim PASS sekarang.

## Berkas yang harus diunggah ke folder ini

`UI01.png`, `UI02.png`, `UI03.png`, `UI04.png`, `UI05.png`, `UI06.png`, `UI07.png`, `UI08.png`, `UI09.png`, `UI10.png`, `UI11.png`, `UI12.png`, dan **tepat satu** `UI_REFERENCE_FINAL.docx`.

File `UI_FINAL_SHA256.csv` sudah tersimpan di folder ini dan merupakan checksum yang **harus cocok**. Jangan merekam ulang PNG, melakukan upscale, atau mengganti desain. Local DOCX sudah diverifikasi 13 halaman dan mengandung ke-12 original PNG dengan SHA-256 cocok. SHA256 DOCX kerja: `a922ba42013d63352605dd22080a00afd081618f78f1ed8879254d81be724ccd`.

## Cara unggah dengan browser GitHub (jika pengunggahan otomatis belum tersedia)

1. Buka folder ini pada branch `astra/step01-contract-spec-20261009`, **bukan** main.
2. Klik **Add file → Upload files**.
3. Ekstrak `UNGGAH_GITHUB_STEP02_UI_FINAL_13_FILE.zip` yang diberikan dalam chat; seret **12 PNG dan 1 DOCX** dari hasil ekstraksi ke GitHub. `CARA_UNGGAH_GITHUB.txt` hanya petunjuk, bukan file final.
4. Commit perubahan **langsung pada branch development ini**, jangan merge ke main.
5. Kembali ke chat dan minta pemeriksaan **"cek G2"**. ASTRA akan memverifikasi semua 12 sha, DOCX dan status gate, kemudian hanya jika semuanya memenuhi ketentuan dapat mencatat G2 PASS.

**Dilarang mulai coding SOL sebelum G2 PASS**, dan G1B executable schema tests serta host Premiere Pro 2024 tetap belum diuji.
