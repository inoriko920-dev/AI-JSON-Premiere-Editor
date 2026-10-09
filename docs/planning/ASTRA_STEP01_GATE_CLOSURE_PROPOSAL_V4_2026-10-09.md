# ASTRA STEP01 — Gate Closure Proposal V4

> 9 Oktober 2026 WIB | planning only | G1A BLOCKED | G2 NOT_STARTED | coding dilarang

Tujuan: menyelesaikan substansi kontrak yang didukung Master V2/V3 dan mengonsolidasikan keputusan tersisa, bukan menambah tahapan tanpa batas. Dokumen ini tidak mengubah input pengguna atau mengklaim uji Premiere.

## A. Sudah ditetapkan sumber (bukan bukti produk berjalan)

| Aturan | Detail | Dasar |
| --- | --- | --- |
| **EDIT_PLAN root** | 11 field wajib: schema_version, project_id, revision, canvas, sources, profiles, assets, scenes, render, validation, provenance. | V2 §5.2 tabel 10 |
| **Scene plan** | scene_id, source_segment_ids, narration_quote, layout_type, start/end, assets[], transition_policy; metadata audit kompatibel. | V2 §5.3 tabel 11 |
| **Asset occurrence** | asset_id, slot, start/end, entry_evidence; stagger_frames/timing_lock metadata eksplisit; TANPA efek di EDIT_PLAN. | V2 §5.4 tabel 12 |
| **ANIMATION_PLAN root** | 9 field wajib: schema_version, project_id, edit_plan_revision, revision, mode, animation_profile, project_seed, decisions, provenance. | V2 §5.6 |
| **Decision BOTH** | scene_id, asset_id, preset, speed, direction, locked; global mode BOTH; set (scene,asset) sama persis. | V2 §5.8; V3 §4.2 |
| **Parser aman** | UTF-8 strict, no comment/trailing comma, reject duplicate object keys termasuk nested; no exec or shell injection. | V2 §6.1; V3 §10.3 |
| **Timing frame** | [start,end), integer 30/1 fps awal; ms->frame satu kali round_half_up; ticks hanya setelah host probe. | V2 §4.4 |
| **Clip min** | Jika durasi D < in_frames+out_frames preflight FAIL sebelum mutasi; tak boleh mengganti efek/Enter-only. | V2 §8.4 |
| **SRT confidence** | EXACT_WORD memerlukan word alignment; EXACT_CUE hanya batas cue; ambigu wajib review/FAIL. | V2 §4.3 |
| **Legacy render** | render pada EDIT_PLAN tetap diterima sebagai hint usang; final MP4 diekspor oleh Premiere. | V3 §4.1 |
| **Safety sequence** | CREATE_NEW_SEQUENCE, journaling, no destructive retry; tidak overwrite manual edits/cache linked. | V3 §5.5 & §10.4 |

## B. Sepuluh keputusan tersisa

| ID | Topik | Rekomendasi | Status | Sumber |
| --- | --- | --- | --- | --- |
| Q01 | Speed versi awal | MVP MEDIUM-only; FAST/SLOW ditolak sampai nilai per-preset disahkan. | PENDING_USER_APPROVAL | V2 §5.6 memberi prioritas MEDIUM. |
| Q02 | Token direction | Bekukan 21 allowlist sesuai visual source; jangan otomatis ubah LEFT menjadi FROM_LEFT. | PENDING_REVIEW | V3 examples versus legacy engine tokens. |
| Q03 | Unknown field schema | Pertahankan 11 EDIT_PLAN dan 9 ANIMATION_PLAN root required; reject split fields; unknown nested NEEDS_REVIEW sampai allowlist tuntas. | PENDING_TECH_SIGNOFF | V2 strict dan V3 kompatibilitas. |
| Q04 | locked=false | Input tidak boleh dimutasi; locked=false NEEDS_REVIEW, bukan berubah diam-diam ke true. | PENDING_TECH_SIGNOFF | V2 mewajibkan field, bukan nilai true. |
| Q05 | SRT APPROX_REVIEW vs ESTIMATED_FROM_AUDIO | Keduanya tetap NEEDS_REVIEW sampai review manual terikat hash; tidak dinaikkan menjadi EXACT_WORD. | SOURCE_DERIVED_PROPOSAL | V2 §4.3, V3 §4.3. |
| Q06 | Minimum HOLD | D==IN+OUT bukan otomatis gagal; verifikasi visual tanpa menciptakan kebijakan random engine lama. | SOURCE_DERIVED_PROPOSAL | V2 §8.4 mensyaratkan D>=IN+OUT. |
| Q07 | Scene gap | Gap hanya mengikuti CUT/EXIT_TO_BG/CONTINUE_LAST dari EDIT_PLAN; unknown gap BLOCK. | SOURCE_SUPPORTED | V2 §4.4, §5.3. |
| Q08 | Batas resource | Tetapkan caps JSON/scenes/media/path dengan ADR threat-model dan tes, bukan nilai karangan. | PENDING_TECH_SIGNOFF | V3 §10.3. |
| Q09 | Premiere host capability | Probe 24.x actual: ticks, alpha, native keyframe; unknown BLOCK. | SOURCE_SUPPORTED_HOST_PENDING | V3 host gate P0/P1. |
| Q10 | Sumber historis mentah | Tetap privat di Library; ringkasan + SHA cukup untuk handoff sementara; unggah raw hanya dengan izin. | PENDING_USER_APPROVAL | Repo publik; 7 dokumen pengguna. |

**Prioritas utama Q01:** Master V2 mendukung MEDIUM terlebih dahulu, sedangkan FAST/SLOW menunggu matriks kalibrasi per preset. Rekomendasi MVP adalah MEDIUM-only; status masih menunggu persetujuan pengguna, jangan diam-diam menetapkan PASS.

## C. Verifikasi frame yang bisa dibuat sebagai fixture setelah UI gate

Formula integer untuk ms nonnegatif: `floor((2*ms*fps_num + 1000*fps_den) / (2000*fps_den))` menghasilkan round-half-up. Untuk 30 FPS: 0ms→0; 16ms→0; 17ms→1; 50ms→2; 1000ms→30. Jangan lakukan serial conversion via floating point per scene.

Jika D=end-start kurang dari IN+OUT: fail-closed. Jika D tepat IN+OUT: source V2 memenuhi syarat durasi tetapi visual zero-HOLD perlu review pada fase efek.

## D. Blokir dan gate

| ID | Status | Bukti/penutupan |
| --- | --- | --- |
| B01 | SOURCE_LOCATED / HANDOFF_DECISION_PENDING | 7 dokumen pribadi ditemukan dan hash tercatat; sumber mentah belum diunggah publik. |
| B02 | REVIEW_PENDING | MEDIUM-only opsi Q01; 21 allowlist direction belum disahkan, FAST/SLOW belum calibrated. |
| B03 | HOST_PENDING | PPRO 24.x exact build, locale/CEP/ticks/alpha belum diuji. |
| B04 | UI_NOT_STARTED | STEP02 prompts -> STOP -> approved PNG -> one UI_REFERENCE_FINAL.docx. |
| B05 | DEPENDENCIES_PENDING | Worker version, FFmpeg licensing, SBOM dan packaging. |
| B06 | REVIEW_PENDING | Unknown fields, locked=false, parser limits, SRT alias dan edge policy. |

**G1A BLOCKED; G1B NOT_STARTED; G2 NOT_STARTED.** Semua fitur host G3–G10, tes P0–P6, AC01–AC30 dan 21 efek masih NOT_TESTED. DOCX adalah dokumen rencana, bukan hasil test.

## E. Next action singkat

1. Tentukan Q01 MEDIUM-only atau nilai FAST/SLOW 21 preset; serta Q02 arah.
2. Review Q03/Q04/Q08 schema safety tanpa mematahkan kompatibilitas V2, dan Q10 handoff sumber.
3. Setelah G1A PASS dengan catatan reviewer/evidence, lanjut STEP02 prompt UI lalu **WAJIB STOP**. Coding SOL baru setelah seluruh gambar UI final disetujui dan 1 DOCX UI disimpan di GitHub.

Repo `main` tidak diubah. PR #1 tetap Draft.
