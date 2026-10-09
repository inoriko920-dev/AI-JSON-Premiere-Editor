# SOL STEP06 — Import media candidate (10 Oktober 2026)

**Instruksi pemilik:** lanjut coding seluruh fitur, integrasi dan pengujian otomatis dahulu; pengujian PC Windows 11 + Premiere 2024 dilakukan pada fase akhir. Status G3 = **BLOCKED_HOST/UNVERIFIED** meskipun semua mock CI lulus. Tidak ada perubahan gambar UI pengguna, `main`, installer atau release.

## Implementasi baru di PR #6 (dari STEP05)

- **`core/import_snapshot.py`**: menghasilkan snapshot media lokal *read-only*, mencakup SRT (hanya diperiksa, **tidak** diimpor), narasi audio, background MP4, dan setiap PNG. Path wajib tetap di media root, SHA-256 yang dipin di JSON harus cocok dengan isi file, file harus dibaca sampai selesai, ukuran + mtime diperiksa sebelum/sesudah hashing, duplikasi path/alias dan file hilang ditolak. `recheck_media_snapshot()` meng-hash ulang semua file dan membatalkan snapshot kedaluwarsa. Semua source punya limit developer eksplisit, belum limit produksi sah.
- **`core/validate_cli.py`**: opsi `--include-import-snapshot --max-import-items N` hanya bekerja setelah validasi JSON/media tidak punya ERROR. Keluaran ke CEP **hanya** jumlah file, jumlah kandidat impor, digest; tidak mencantumkan path atau metadata privat, `can_import=false` dan `can_assemble=false`.
- **`panel/validation_bridge.js` + `panel/validation_ui.js`**: otomatis meminta snapshot kandidat read-only bersama validasi; mengecek format status dan batas jumlah file; menampilkan ringkasan `HANYA KANDIDAT, belum izin impor`. Tidak ada tombol impor aktif, tidak ada file proyek berubah.
- **`host/media_import_adapter.jsx`**: implementasi calon ExtendScript ES3 via metode resmi `Project.importFiles([path], true, targetBin, false)`, `rootItem.createBin(name)`, `ProjectItem.getMediaPath()`, dan `findItemsMatchingMediaPath()`. Memerlukan flag otorisasi host/layout/preflight/hashing yang diverifikasi terpisah, menolak duplikat bin dan media yang sudah ada, cek keberadaan/ukuran media, membuat **bin baru saja** setelah semua prasyarat, impor satu per satu, dan readback jumlah item/path. Jika gagal setelah bin dibuat, hentikan sebagai **INCOMPLETE**; tidak menghapus, retry, overwrite atau mengubah sequence pengguna. **Belum dimasukkan ke CEP ScriptPath atau paket runtime.**
- Kode parser menerima asset_id sah dengan `.`, `_`, dan `-`, sesuai kontrak EDIT_PLAN V2.
- Paket CEP TEST ONLY diperbarui: 19 file runtime (termasuk `core/import_snapshot.py`), satu README + satu checksum manifest = 21 file total dan **20 hash**. Tetap unsigned dan installer belum dibuat.

## Bukti otomatis
- [Windows/Linux CI #37978073723 — SUCCESS](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/actions/runs/37978073723): Windows **77 JavaScript PASS, 105 Python PASS**; Ubuntu **75 JavaScript PASS, 2 Windows-only skip**, 105 Python tests (optional real-FFprobe smoke skipped jika binary tidak ada). Staging izin eksplisit, 20 checksum ZIP dan 8 ZIP negatif PASS.
- Commit berikutnya menambahkan dukungan ID asset V2 sah dan dua tes; nilai CI untuk commit baru tetap harus diverifikasi terpisah.
- `tests/media_import_adapter.test.cjs` memakai mock Project/ProjectItem Adobe; `tests/test_core_import_snapshot.py` memeriksa bytes SHA/path serta berkas berubah; `tests/test_core_cli.py` memeriksa proses Python tanpa membocorkan path; Windows Node → Python smoke tetap aktif.
- **Tidak ada host Premiere Pro 2024 nyata yang dijalankan.** CI ini hanya bukti kode unit/integrasi mock, bukan bukti importFiles berhasil di host.

## Pekerjaan masih perlu dikoding
Full operator host memakai capability/authorization yang diverifikasi terhadap instalasi host, pembuatan sequence dan pemetaan nodeId clip secara aman, V1 loop background, V2/V3 penempatan gambar, A1 narasi, crop/layout asli, preset BOTH 21/21 native atau baked FFmpeg, journal/recovery serta paket Windows final. **Jangan klaim fitur ini selesai** sampai implementasi dan tesnya tersedia.

Gate: G1A SPEC PASS · G2 UI PASS · G3 BLOCKED_HOST (uji final); AC host 0/30 dan animasi host 0/21. Draft PR, `main` tidak disentuh.
