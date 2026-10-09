# STEP03 — Laporan diagnostik P0 untuk pengujian Premiere 2024

**Penting:** Ini panel read-only untuk bukti G3, bukan plugin editing yang telah selesai. G3 tidak otomatis PASS karena teks laporan terbentuk.

## Urutan pengujian di Premiere asli

1. Gunakan build P0 TEST ONLY dari commit terkait. Periksa checksum ZIP dengan `P0_Windows_Pilot.ps1 -Mode Inspect`; staging instalasi hanya atas persetujuan eksplisit `-Mode Stage -ConfirmStage`. Jangan mengubah registry/Developer Mode tanpa izin dan jangan menguji pada proyek kerja penting.
2. Pada **Adobe Premiere Pro 2024 24.x** asli di Windows 11, buka panel AI JSON Premiere Editor (P0) jika pemasangan CEP didukung.
3. Klik **PERIKSA HOST**; salin hasil di layar. Jika status cocok, opsional klik **PERIKSA HELPER** (Python lokal harus sudah dikonfigurasi dengan izin).
4. Klik **TAMPILKAN LAPORAN P0**. Teks muncul di kotak **Laporan diagnostik P0**, siap diseleksi dan disalin manual. Tidak ada upload otomatis.
5. Serahkan teks dan **screenshot nyata** yang memperlihatkan panel, serta versi Windows/Premiere, hasil dock/resize/reopen, dan catatan apakah proyek/timeline tetap tidak berubah. Hapus informasi pribadi dari screenshot/log.
6. Jika menu Extensions tidak menampilkan plugin atau helper gagal, laporkan persis kode dan jangan memaksakan konfigurasi tidak resmi.

## Format contoh — hanya ilustrasi, bukan hasil uji

```text
AI_JSON_PREMIERE_P0_DIAGNOSTIK_V1
JENIS=LAPORAN_LOKAL_BELUM_DIVERIFIKASI
HOST_STATUS=NOT_CHECKED
HOST_CODE=HOST_NOT_CHECKED
HOST_VERSION=TIDAK_TERSEDIA
HELPER_STATUS=NOT_CHECKED
HELPER_CODE=HELPER_NOT_CHECKED
HELPER_VERSION=TIDAK_TERSEDIA
G3=BLOCKED_HOST_SAMPAI_UJI_PREMIERE_ASLI
UI_IMPORT_PREFLIGHT_ASSEMBLY=DINONAKTIFKAN
BUKTI_DOCKING_REOPEN=PERLU_PEMERIKSAAN_MANUAL
```

Hasil yang dihasilkan panel tetap **laporan lokal yang belum diaudit**. Lulus host versi atau helper P0 **tidak sama dengan** G3 PASS, AC01/AC02 PASS, 21 animasi PASS, atau aplikasi selesai.

## Privasi dan batasan

Laporan hanya berisi kode yang dikenal dan versi numerik host/helper. Laporan tidak membaca path Python, username, nama file, media, JSON proyek, serial Adobe, atau isi disk. Tidak ada network/clipboard otomatis; pengguna menyalin sendiri. Tombol impor, preflight, assembly dan ekspor tidak aktif. Semua perbedaan desain mock tidak mengubah spesifikasi JSON/timing normatif.
