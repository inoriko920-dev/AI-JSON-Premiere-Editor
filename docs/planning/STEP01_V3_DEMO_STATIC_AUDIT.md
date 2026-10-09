# STEP01 — Audit statis pasangan JSON contoh Master V3

**Sumber:** `docs/source/MASTER_PLAN_V3_TRANSCRIPT.md` bagian 13.1 (EDIT_PLAN DEMO_001) dan 13.2 (ANIMATION_PLAN DEMO_001), dibaca pada branch `astra/step01-contract-spec-20261009`. Rujukan durasi animasi dari V3 §7.2 / MASTER DURASI V2. Audit dilakukan pada **JSON contoh yang tertanam di dokumen**, bukan media proyek nyata.

## Hasil

**18/18 pemeriksaan statis struktur = PASS.** Ini bukan contract test executable produk, bukan CI dan bukan pengesahan G1B. Tidak ada Premiere diakses, tidak ada media didecode, tidak ada alpha/keyframe atau kecepatan lain dibuktikan.

| ID | Pemeriksaan | Audit | Sumber |
| --- | --- | --- | --- |
| A01 | Both embedded JSON documents parse | PASS | V3 13.1 + 13.2 |
| A02 | Exact schema_versions edit-plan-v2 / animation-plan-v1 | PASS | V3 13.1 + 13.2 |
| A03 | project_id matches | PASS | V3 4.2 |
| A04 | edit_plan_revision equals edit revision | PASS | V3 4.2 |
| A05 | mode BOTH global | PASS | V3 4.2 |
| A06 | Exactly two scenes in sample | PASS | V3 13.1 |
| A07 | SINGLE one asset and DOUBLE two assets | PASS | V3 4.2 |
| A08 | DOUBLE LEFT and RIGHT independently represented | PASS | V3 13.1 |
| A09 | Three asset time spans are positive integer frames | PASS | V3 4.4 |
| A10 | Asset spans fit inside respective scenes | PASS | V3 4.2 |
| A11 | No duplicate (scene_id,asset_id) occurrences | PASS | V2 5.1 |
| A12 | Exactly three animation decisions | PASS | V3 13.2 |
| A13 | Exact bijection between occurrences and decisions | PASS | V3 4.2 |
| A14 | All three use known MEDIUM reference presets | PASS | V3 7.2 / 13.2 |
| A15 | All three decisions locked=true | PASS | V3 13.2 |
| A16 | No enter_effect/exit_effect or split direction/time fields | PASS | V3 4.2 |
| A17 | All three durations meet MEDIUM reference IN+OUT | PASS | V3 7.2; uncalibrated |
| A18 | Right asset start_frame=192 is explicit 42-frame delay | PASS | V3 13.1 |

## Trace per occurrence

Seluruh nilai waktu adalah **frame integer pada 30 FPS**. Minimum referensi = IN + OUT; `hold_candidate` adalah sisa durasi matematis, **bukan** hasil keyframe host Premiere.

| Scene | Asset | Preset | Direction contoh | start | end excl | D | IN | OUT | min BOTH | HOLD calon |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| V001 | A001 | BRUSH | LEFT_TO_RIGHT | 0 | 150 | 150 | 39 | 9 | 48 | 102 |
| V002 | A002 | PAN | FROM_LEFT | 150 | 330 | 180 | 21 | 8 | 29 | 151 |
| V002 | A003 | WIPE | RIGHT_TO_LEFT | 192 | 330 | 138 | 21 | 8 | 29 | 109 |

V002.RIGHT dimulai frame 192, sedangkan scene mulai 150, artinya **42 frame / 1,4 detik** lebih lambat; penundaan itu memang tertulis di JSON, bukan hasil engine menambah stagger otomatis.

## Batas bukti / gate

- Contoh memakai placeholder `<SHA256_SRT>`, `<SHA256_AUDIO>`, `<SHA256_LAYOUT>`, `<SHA256_ANIMATION_REGISTRY>`; literal itu tidak bisa menjadi hash produksi.
- Berkas `narasi.srt`, `narasi.wav`, `background.mp4`, dan PNG A001–A003 hanya tertulis sebagai path contoh, tidak diprobe atau didecode.
- Direction `LEFT_TO_RIGHT`, `FROM_LEFT`, `RIGHT_TO_LEFT` cocok bentuk contoh, **belum** dijamin allowed by tested registry. Alpha/NATIVE/PRERENDER semuanya UNVERIFIED.
- File `validation.status=READY` di input adalah klaim produsen data, **bukan** izin langsung merakit timeline. Runtime preflight wajib menolak placeholder, media hilang atau registry yang tidak certified.
- F026 pada katalog fixture lama menyebut `BLOCKED_POLICY` untuk half-frame tie. **Dikoreksi:** sumber V2 §4.4 eksplisit menetapkan `round_half_up`; pada 30 FPS, 50 ms = 1,5 frame → 2 frame. Fixture diubah ke G1B.
- Katalog fixture bertambah dari 48 menjadi **68 kasus terencana**, mencakup duplicate keys, field terlarang, error jenis frame, minimum BOTH, dan READY palsu. Ini rencana uji yang belum dijalankan.

## Status keputusan

- **B01** sumber ditemukan; izin menyalin raw source ke GitHub publik tidak otomatis ada.
- **B02** durasi MEDIUM masih referensi (belum kalibrasi), pilihan membatasi MVP ke MEDIUM belum disetujui pengguna, FAST/SLOW dan direction registry belum final.
- **B03** Premiere host 24.x belum diuji.
- **B04** desain UI final belum ada.
- **B06** beberapa allowlist/caps/policy masih perlu disahkan.

**G1A BLOCKED, G1B NOT_STARTED, G2 NOT_STARTED, coding dilarang.** Langkah berikut tetap menutup Q01/Q02/Q03/Q04/Q08/Q10 secara nyata. Setelah G1A PASS, STEP02 prompt UI wajib STOP menunggu gambar final dan 1 DOCX referensi UI.
