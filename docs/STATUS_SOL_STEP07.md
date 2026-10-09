# SOL STEP07 — perencana empat track dan adapter penempatan klip (10 Oktober 2026)

**Arahan pemilik:** tuntaskan coding, integrasi, perbaikan bug, CI yang memungkinkan, baru pada akhir minta pengujian nyata Windows 11 / Adobe Premiere Pro 2024. `LANJUTKAN` selalu kerjakan progres nyata. G3 tetap **BLOCKED_HOST/NOT_VERIFIED**, tidak memblokir coding aman. Dilarang generate/mengubah desain gambar UI final dan dilarang merge/release tanpa otorisasi.

## Kode yang selesai pada Draft PR #7
- `host/timeline_placement_adapter.jsx` adalah implementasi calon ExtendScript ES3 `$._AIJSON_PLACEMENT_V1`, **tidak terhubung ke CEP live**.
  - Memiliki fungsi inspeksi read-only seluruh V1/V2/V3/A1 (dan track tambahan). Memverifikasi `nodeId`, source item, `start.ticks` dan `end.ticks` persis string.
  - `placeOne(request, auth)` hanya mencoba **satu** klip pada sequence AIJSON baru yang identitasnya diverifikasi, setelah otorisasi host/layout/FX/media, snapshot baseline semua track persis cocok, dan target track **kosong**. Memakai `Track.overwriteClip(item, startTicks)` setelah semua pemeriksaan pra-mutasi. **Tidak menggunakan** insertClip ripple, setInPoint/OutPoint ProjectItem, proyek user lama, auto-retry, hapus klip, export MP4 atau QE DOM.
  - Durasi `endTicks-startTicks` dihitung dengan pengurangan digit string (ES3, tanpa JS floating point/BigInt). Semua track setelah mutasi dibaca lagi; jika clip/durasi/identitas tidak sama atau audio tertaut muncul di track lain, hasilnya **INCOMPLETE**, klip baru tidak dihapus secara otomatis.
  - **Pembatasan penting**: ini bukan engine yang dapat menyusun album 100+ klip; pada revisi ini setiap operasi hanya boleh ke track kosong dengan bukti durasi sumber exact. Source trim/loop background dan image still durasi masih terblokir. Kode belum di-load host CEP, sehingga tombol produksi belum aktif.
- `core/timeline_lanes.py` menghitung V1 background loop, V2/V3 placement dari draft frame, dan A1 narration secara **deterministik** hanya jika durasi sumber sudah dipastikan whole-frame oleh host. Contoh input eksplisit: total 330 frame, background 120 frame menghasilkan [0,120), [120,240), [240,330) dengan segmen terakhir `requires_source_trim=true`; A1 tepat [0,330). Narasi dengan durasi tidak cocok ditolak, bukan ditambah silence atau dipangkas.
- Semua hasil berbentuk `DRAFT_NOT_EXECUTABLE` dengan `can_assemble=false`. Tidak ada janji layout, durasi gambar, source trim, animasi atau kemampuan Premiere.
- `tests/timeline_placement_adapter.test.cjs` 14 kasus, `tests/test_core_timeline_lanes.py` 8 kasus; repo tetap menjalankan tes lintas STEP sebelumnya.

## Bukti
[STEP07 GitHub Actions #37985006310 SUCCESS](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/actions/runs/37985006310), source commit `1b8ca49643724c5ae613eb5909fe0176badb25c5`:
- Windows: 14/14 adapter khusus PASS, **92/92 seluruh JS PASS**, **114 tes Python: 113 PASS + 1 skip** karena binary FFmpeg/FFprobe tak ada.
- Linux: 14/14 khusus PASS, **90/92 JS PASS + 2 skip Windows-only**, **114 Python: 113 PASS + 1 skip**.
- CI memeriksa `timeline_placement_adapter.jsx` tidak dimuat oleh `CSXS/manifest.xml` maupun `panel/index.html`, sehingga tidak ada operasi edit host aktif.
- Commit awal `e8157beb` gagal pada tes statis palsu yang membaca komentar, diperbaiki `dae5b40b` sekaligus penguatan ES3 aritmetika durasi ticks. Commit terkini PASS.

## Yang belum selesai dan berikutnya dikerjakan
- Otorisasi terikat sumber/media project yang kebal TOCTOU; aturan kelanjutan track nonkosong dengan baseline transaksional; source outpoint/still image duration yang benar; V1 loop/trim actual, V2/V3 komposisi layout/crop, A1 narasi, journal/readback dan penanganan linked audio/video.
- Semua 21 preset BOTH native/FFmpeg dengan timing dan transparansi tersertifikasi; integration Windows host pada akhir setelah fitur siap.
- Belum ada real clip yang ditempatkan di Premiere asli; G3 tetap BLOCKED_HOST, 0/21 efek host-certified, 0/30 host AC verified. PR Draft, tidak merge main, tidak rilis.
