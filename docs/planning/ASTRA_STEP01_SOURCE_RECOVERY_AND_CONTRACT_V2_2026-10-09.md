# ASTRA STEP01 — Pemulihan 7 sumber dan kontrak V2

Status 9 Oktober 2026 WIB: SOURCE_RECOVERED / CONTRACT_PARTIAL; G1A BLOCKED; G2 NOT_STARTED; CODING PROHIBITED.

Master V3 Premiere dan instruksi user terbaru mengatasi kontrak lama yang bertentangan. Sumber mentah dari Library pengguna **tidak otomatis dipublikasikan** ke repo publik.

## Inventaris sumber terverifikasi SHA-256

| ID | File | SHA-256 |
| --- | --- | --- |
| S01 | MASTER_PLAN_APP_RENDERER_JSON_ANIMATION_BOTH_V2.docx | c7532ffe4ae71ad4602ef0cf7165569db106d3fdcbbf5d72bfadef3524bdedd9 |
| S02 | Spesifikasi_Layout_Zoom_dan_Penempatan_Gambar_Canva.docx | 036cba26f4b1dfe0c42101fcf7f5edc7603673b504ddb241d9f08af911ebea9b |
| S03 | Spesifikasi_Animation_Engine_Canva_General_Reveal_Auto_Random.docx | d624d42aae6fb17a9e10e894596e4abe8789262c430ba409537e3a5f1ae868fd |
| S04 | MASTER_DURASI_IN_OUT_21_ANIMASI_CANVA_V2.docx | ef0977812c8e67a576648572a7c0cbc8f361a0c775e3cf5685d73fad17079327 |
| S05 | 01_Prompt_GPT_Visual_Planner_Scene_Asset_v2.txt | 1cc49fb2490d4274f3659188ea51210e65e1998204fa323d805f8943422d3c23 |
| S06 | 04_Prompt_GPT_Animation_Director_v2.txt | 73d2f05c481631cc3287c4348130c76be104e58b5f9916e96fcac164995b4d90 |
| S07 | Prompt_panel.txt | 6a7481623d24b6e22d0d88895e2f1948d3f721257dae7ea50f48fa66d29c7058 |

## 1. Ringkasan kemajuan

- Berhasil menemukan 7 dokumen lama di Library pengguna. Hash SHA-256 setiap sumber telah diverifikasi. File mentah tidak dipublikasikan otomatis ke GitHub publik; ringkasan yang diturunkan dan checksum disimpan untuk handoff SOL.

- STEP01 masih kontrak sebagian. G1A = BLOCKED karena allowed directions/FAST-SLOW/schema/persetujuan akses sumber belum sepenuhnya final. Tidak ada kode produk dan Premiere host tidak dites.

## 2. Kontrak dua JSON

- Master V2 menyebut EDIT_PLAN field top-level wajib: schema_version, project_id, revision, canvas, sources, profiles, assets, scenes, render, validation, provenance. edit-plan-v2 harus dipertahankan untuk kompatibilitas.

- ANIMATION_PLAN top-level wajib: schema_version, project_id, edit_plan_revision, revision, mode, animation_profile, project_seed, decisions, provenance. animation-plan-v1 dengan mode BOTH saja. Tiap decision: scene_id, asset_id, preset, speed, direction, locked.

- EDIT_PLAN tidak boleh berisi enter_effect, exit_effect, speed/direction atau duration override. Ada tepat satu pasangan (scene_id, asset_id) per kemunculan. Duplikasi/missing/extra semuanya error.

- Render field EDIT_PLAN tetap boleh ada sebagai hint ekspor legacy, tetapi plugin Premiere tidak meluncurkan export MP4 final dengan FFmpeg. Hasil utama adalah sequence/project Premiere.

- Asset D frame dengan D < IN+OUT wajib FAIL. Audio/SRT/PNG/background required hilang atau tidak terbaca harus STOP sebelum mutasi host. SRT cue-level tidak dipalsukan sebagai timestamp kata.

## 3. S02: angka sumber layout

- SINGLE target height 0.830H, hard cap width 0.720W, center X 0.500W, top anchor 0.052H; scale=min(0.83H/crop_h,0.72W/crop_w); preserve aspect ratio.

- DOUBLE width pair target 0.972W, center pair X 0.500W dan Y sekitar 0.500H, gap 0.015W, height hard max 0.705H. Dua aset harus tetap layer dan timing independen.

- Crop sheet 3x2 mengikuti coarse cells dan tight alpha trim, padding default 2%, label guard. Subtitle bottom safe default 10%; hindari stretch/overlap.

- Parameter ini berasal dari observasi screenshot yang terdokumentasi dalam S02, bukan hasil uji transform native di Premiere. Profile perlu ID/hash, golden visual tests serta penentuan crop alpha di backend.

## 4. S03/S04: 21 preset dan direction

- Rujukan IN/OUT MEDIUM frame untuk 21 preset tercantum di bagian daftar berikut. Semua angka adalah target replica (REFERENCE_UNCALIBRATED), bukan konstanta Canva atau proof backend.

- Engine lama memiliki direction generik LEFT, RIGHT, UP, DOWN, DIAG_TL/TR/BL/BR, RADIAL, NONE. Master V3 memberi contoh LEFT_TO_RIGHT, FROM_LEFT, RIGHT_TO_LEFT. Jangan diam-diam menormalisasi tanpa kontrak yang disetujui.

- Speed FAST/SLOW hanya memiliki rentang umum pada Engine lama, belum durasi IN/OUT individual 21 preset. Resolver wajib fail-closed untuk kombinasi yang belum punya registry verified.

- Auto-random, strong-effect downgrade Fade, stagger acak, Enter-only dan Exit-only dari spesifikasi engine lama tidak sesuai kontrak GPT locked V3 dan dilarang.

## 5. Aturan keselamatan host dan gate

- PPRO major 24 CEP + ExtendScript + FFmpeg hybrid. Tidak ada native keyframe atau alpha baked dinyatakan VERIFIED sebelum uji host actual exact build/locale, readback dan video evidence.

- CREATE_NEW_SEQUENCE default; tidak menimpa sequence atau edit manual. Crash/cancel memberi INCOMPLETE; jangan menghapus linked cache maupun media secara otomatis.

- B01 = SOURCE_LOCATED / ARCHIVAL_PENDING. B02 = PARTIAL. B03 = OPEN_HOST. B04 = OPEN_UI. B05 = OPEN_DEPENDENCIES. B06 = PARTIAL.

- G1A SPEC BLOCKED; G1B NOT_STARTED; G2 UI NOT_STARTED; coding tetap PROHIBITED. STEP berikut masih STEP01 menutup allowed directions, FAST/SLOW/medium restriction, unknown keys, source archive approval dan host-dependent ADR.

## 21 preset MEDIUM: reference IN/OUT frame (30fps)

| ID | Preset | IN | OUT | Total minimal |
| --- | --- | ---: | ---: | ---: |
| R01 | Brush | 39 | 9 | 48 |
| R02 | Ink | 40 | 9 | 49 |
| R03 | Digital | 24 | 7 | 31 |
| R04 | Spray Paint | 42 | 9 | 51 |
| R05 | Sketch | 42 | 10 | 52 |
| R06 | Gradient | 33 | 8 | 41 |
| G01 | Rise | 21 | 8 | 29 |
| G02 | Pan | 21 | 8 | 29 |
| G03 | Fade | 15 | 7 | 22 |
| G04 | Pop | 16 | 7 | 23 |
| G05 | Wipe | 21 | 8 | 29 |
| G06 | Blur | 21 | 8 | 29 |
| G07 | Succession | 25 | 9 | 34 |
| G08 | Breathe | 30 | 9 | 39 |
| G09 | Baseline | 14 | 7 | 21 |
| G10 | Drift | 33 | 9 | 42 |
| G11 | Tectonic | 22 | 8 | 30 |
| G12 | Tumble | 24 | 9 | 33 |
| G13 | Neon | 20 | 7 | 27 |
| G14 | Scrapbook | 22 | 9 | 31 |
| G15 | Stomp | 17 | 7 | 24 |

## 15 konflik V2/V3

| ID | Aturan lama | Aturan V3 | Status |
| --- | --- | --- | --- |
| C01 | Standalone renderer V2 | Plugin CEP + JSX + FFmpeg Premiere 2024 adalah target V3 | CLOSED_BY_V3 |
| C02 | Engine auto-random/reroll | GPT memilih tepat satu preset locked per occurrence | CLOSED_BY_V3 |
| C03 | Enter-only/Exit-only pada engine lama | Mode BOTH wajib, preset IN dan OUT sama | CLOSED_BY_V3 |
| C04 | Durasi pendek boleh dipercepat otomatis | Jika clip lebih pendek dari IN+OUT: FAIL, tanpa autopatch | CLOSED_BY_V3 |
| C05 | DOUBLE downgrade strong effect ke Fade | Dilarang silent effect fallback, minta revisi eksplisit | CLOSED_BY_V3 |
| C06 | Stagger masuk otomatis 80-220ms | A/B mengikuti frame eksplisit EDIT_PLAN | CLOSED_BY_V3 |
| C07 | Enum arah LEFT/RIGHT pada engine lama | Contoh V3: LEFT_TO_RIGHT/FROM_LEFT/RIGHT_TO_LEFT | OPEN_B06 |
| C08 | Speed fast/slow memakai range umum | Butuh IN/OUT angka FAST/SLOW per preset, tidak interpolasi diam-diam | OPEN_B02 |
| C09 | MEDIUM 21 efek target replica, bukan Canva internal | REFERENCE_UNCALIBRATED dan 0/21 host certified | OPEN_B02 |
| C10 | APPROX_REVIEW SRT vs ESTIMATED_FROM_AUDIO | Definisikan alias resmi, tidak naikkan confidence | OPEN_B06 |
| C11 | V2 render final via FFmpeg | V3 EDIT_PLAN.render legacy hint, ekspor Premiere | CLOSED_BY_V3 |
| C12 | Layout source berdasar screenshot observasi | Bekukan profile/hash, uji golden visual host | PARTIAL_B06 |
| C13 | V2 strict unknown keys | Bekukan allowlist field legacy agar kompatibel | OPEN_B06 |
| C14 | Premiere ticks, keyframe, alpha belum host tested | Probe actual Premiere Pro major 24.x | OPEN_B03 |
| C15 | Contoh JSON V3 memakai arah yang tidak ada di enum engine | Jangan klaim valid sebelum mapping disetujui | OPEN_B06 |

## Handoff selanjutnya

Untuk AI/SOL: baca Master V3 asli, kontrak STEP01 V1, dokumen V2 ini, PRESET_MATRIX.csv, ACCEPTANCE_MATRIX.csv, STEP01_FIXTURE_CATALOG.csv, BLOCKERS.md, dan AGENTS.md. Jangan memulai executable schema/panel sebelum G1A/G2 PASS. Setelah STEP02 prompt UI, wajib STOP menunggu gambar UI final dan DOCX referensi.

Masih OPEN: direction alias/per preset, speed FAST/SLOW, unknown-field allowlist, duplicate keys, scene gap, SRT evidence alias, host ticks, profile hashes, reuse licensing dan raw source archival permission.
