# Prasyarat terbuka

Status ini merupakan fakta saat paket STEP00 dibuat. Jangan mengubahnya menjadi PASS hanya karena dokumen plan selesai.

| ID | Yang belum tersedia | Pemilik tindakan berikut | Menutup dengan | Menghalangi |
| --- | --- | --- | --- | --- |
| B01 | Master V2, Layout Zoom/Crop, Animation Engine General Reveal, durasi 21 efek, Prompt 1 dan Prompt_panel, Prompt 4 | ASTRA meminta sumber spesifik kepada pengguna | Berkas dibaca dan hash dicatat, atau spesifikasi pengganti disetujui eksplisit | Kontrak produksi STEP01 |
| B02 | FAST/SLOW, direction allowed, easing dan visual final tiap preset | ASTRA bersama pengguna | Registry specification dan sumber visual disetujui | STEP01 dan sertifikasi STEP08 |
| B03 | Exact build Premiere 24.x, CEP, locale dan mesin pengujian | Pengguna atau operator host, SOL merekam | Inventaris host dan akses pengujian nyata | Kesiapan G0 dan G3 serta semua host gate |
| B04 | Prompt UI, gambar final, approval, UI_REFERENCE_FINAL.docx | ASTRA bersama pengguna | G2 PASS dengan semua gambar dan approval hash | Seluruh coding |
| B05 | Dependency version/runtime, lisensi file reuse, build FFmpeg untuk distribusi | ASTRA merencanakan, SOL membuktikan | ADR dependency, notices, SBOM dan build flags final | Adopsi dependency dan G10 |
| B06 | Schema penuh V2, mapping catalog ID/preset key, unknown fields, rounding, ticks, transform, short clip policy, limits | ASTRA STEP01 | DOCX kontrak tanpa ambiguity; hal yang host-dependent punya prosedur probe dan runtime block | G1A dan implementasi kontrak |

Missing file proyek runtime berbeda dari missing referensi planning. Untuk proyek nyata: dua JSON, audio/SRT dan PNG yang diwajibkan, serta background required harus ada dan terbaca; jika tidak, hentikan proses sebelum mutasi Premiere. Fixture sintetis hanya untuk tes dan tidak menggantikan file pengguna.

Perencanaan dapat menjelaskan backlog meskipun sumber belum lengkap. Implementasi tidak boleh mengarang nilai yang belum ditetapkan. Tidak ada blocker yang ditutup dalam paket ini selain tersedianya Master V3 asli dan handoff STEP00.
