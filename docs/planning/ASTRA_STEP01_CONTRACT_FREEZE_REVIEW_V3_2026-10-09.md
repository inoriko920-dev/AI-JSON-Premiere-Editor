# ASTRA STEP01 — Addendum pembekuan kontrak (usulan ditandai)

> 9 Oktober 2026 WIB · Draft Review V3 · No product code · G1A BLOCKED · G2 NOT_STARTED

## Ringkasan

- STEP01 dapat dilanjutkan secara aman sebagai perencanaan. Berkas Master V2/layout/animation engine/duration/prompt sudah ditemukan, sehingga B01 bagian pencarian SOURCE_LOCATED; tetapi dokumen mentah tidak diunggah publik, dan persetujuan scope sumber masih harus ditutup.

- Addendum ini menyelesaikan bagian aturan yang langsung didukung sumber, menyediakan 21 kandidat arah untuk ditinjau, 20 keputusan/status serta tujuh contoh rounding. Tidak memalsukan registry, tes atau keputusan pengguna.

- G1A SPEC BLOCKED karena B02 (FAST/SLOW dan arah kanonis) dan B06 (allowlist/limits/alias/edge policy); B03 host, B04 UI, B05 dependency tetap OPEN. SOL coding dilarang.

## Kebijakan parsing dan kompatibilitas yang didukung dokumen

- EDIT_PLAN v2 top-level dari sumber S01: schema_version, project_id, revision, canvas, sources, profiles, assets, scenes, render, validation, provenance. Field render dan validation tetap dibaca secara kompatibel namun render adalah legacy hint dan validation input bukan runtime PASS.

- ANIMATION_PLAN v1 top-level: schema_version, project_id, edit_plan_revision, revision, mode, animation_profile, project_seed, decisions, provenance. Tiap keputusan punya scene_id, asset_id, preset, speed, direction, locked; mode BOTH tunggal wajib.

- JSON harus UTF-8 strict, tanpa komentar/trailing comma, dan duplikasi key pada objek bersarang ditolak. Simpan kedua file raw SHA-256; hash profil layout/registry harus cocok versi yang dipakai.

- Set pasangan scene_id/asset_id yang tampil dalam EDIT_PLAN harus tepat sama dengan decision pada ANIMATION_PLAN. Dua appearance asset yang sama pada scene yang sama tanpa ID kemunculan berbeda dilarang—pecah scene/beat sebelum import.

- Periksa ID scene dan asset, slot SINGLE atau pasangan LEFT+RIGHT pada DOUBLE, integer nonnegatif start/end dan [start,end); tidak boleh ada field efek atau speed terselip di EDIT_PLAN scene/assets.

- Kebijakan unknown fields perlu menjaga kompatibilitas V2: larang field yang secara eksplisit dilarang termasuk enter_effect/exit_effect dan direction/speed di EDIT_PLAN. Untuk nested atau vendor metadata lainnya jangan putuskan additionalProperties:false global dari contoh JSON semata tanpa menyusun allowlist dari source.

## Frame math yang dapat disahkan tanpa host

- Keputusan V2: frame = round_half_up(milliseconds * fps_num / (1000 * fps_den)). Untuk integer ms>=0 dan fps_num/fps_den positif, implementasi integer: floor((2*milliseconds*fps_num + 1000*fps_den) / (2000*fps_den)). Jangan konversi frame input yang sudah integer berulang kali.

- Pada 30/1fps: 16 ms→0 frame; 17 ms→1 frame; tepat 50 ms (1.5 frame)→2 frame; 1000 ms→30 frame. Gunakan integer besar atau overflow guard, bukan floats yang menumpuk.

- Validasi asset clip D=end-start. Jika D < IN+OUT, fail E_TIME_006/E_ANIM_PRESET sesuai taxonomy; tidak random ulang, menghapus OUT, masuk Enter-only, mengganti Fade atau mengubah speed. D==IN+OUT lolos formula minimum Master V2 namun kebijakan minimum HOLD visual tetap menjadi catatan QA.

- Frame sequence tidak sama dengan keyframe host/ticks. Premiere bridge harus mengukur timebase yang sebenarnya pada exact build 24.x; bila belum verified, host build tidak boleh berjalan.

## Source-based mapping arah dan speed

- Dari 21 preset, hanya FADE direction=NONE disebut eksplisit oleh Master V2. Sumber Engine menjelaskan gerakan masing-masing, tetapi tidak menetapkan serialisasi token yang konsisten dengan tiga contoh Master V3.

- File STEP01_DIRECTION_CANDIDATES.csv merinci 21 families, opsi arah semantik menurut sumber, usulan token stabil, dan status. Tidak satu pun alias boleh otomatis dinyatakan production VERIFIED.

- MEDIUM memiliki 21 pasangan IN/OUT frame rujukan dari S04 dan sudah dicatat di STEP01 V2. Angka tersebut bukan konstanta Canva dan belum lolos QA visual Premiere. FAST/SLOW tidak punya matriks per preset yang disahkan.

- Opsi keputusan yang paling konservatif untuk MVP: hanya terima speed MEDIUM; jika input memilih FAST/SLOW, fail-closed dengan pesan koreksi dan tanpa perubahan JSON otomatis. Ini masih membutuhkan persetujuan eksplisit pengguna sebagai batas MVP.

## SRT dan keterlacakan

- Gunakan EXACT_WORD hanya untuk kata dengan timestamp verified, EXACT_CUE pada batas cue, APPROX_REVIEW sebagai preview/review only, UNRESOLVED memblokir assembly. Alias istilah V3 ESTIMATED_FROM_AUDIO perlu pemetaan yang disepakati tanpa meningkatkan tingkat kepastian.

- Frasa berulang mengharuskan occurrence/source_span agar pemetaan tidak melompat ke cue yang salah. Perubahan hash SRT/audio/JSON sesudah review wajib membatalkan READY.

- Gap antarscene tidak diisi dengan keputusan kreatif baru; gunakan transition_policy yang sah dari EDIT_PLAN. SRT/audio tetap menjadi sumber durasi, bukan jumlah frame gambar terakhir.

## Keselamatan project dan host

- CREATE_NEW_SEQUENCE adalah mode awal. Mutasi hanya sesudah seluruh input, registry, layout, media dan host capability lolos preflight; project tersimpan; operator menyetujui target sequence dan cache. Tidak menjalankan placeholder, overlay baked pengganti atau preset yang tidak lolos.

- Journal operasi dicatat sebelum host mutation dan diverifikasi melalui readback. Sequence parsial tidak dihapus, tidak di-retry otomatis dan tidak menimpa edit manual. Cache linked hanya direlink setelah hash cocok.

- Pengujian unit atas formula dan rencana fixture tidak membuktikan Premiere. G3–G9 memerlukan exact host build, foto/video/repro, native keyframe readback, alpha proof, timing dan ekspor Premiere nyata.

## Kondisi penutupan STEP01

- G1A bisa diajukan PASS hanya setelah user/reviewer menyetujui arah kanonis per preset, opsi MEDIUM-only atau matriks FAST/SLOW, unknown-field/alias/limits, sumber turunan vs archival raw, dan kelengkapan kontrak STEP01 DOCX.

- Jika keputusan ditunda, pertahankan BLOCKED dan catat siapa pemilik keputusan. Jangan mengarang DEFAULT dari contoh; jangan beralih STEP02 hanya karena dokumen ini selesai.

- Setelah G1A PASS dan perintah lanjut sesuai workflow, STEP02 membuat prompt gambar UI lalu STOP; seluruh gambar final disetujui, diarsipkan ke UI_REFERENCE_FINAL.docx sebelum SOL membuat kode.

## Matriks keputusan

| ID | Keputusan | Dasar | Status | Catatan |
| --- | --- | --- | --- | --- |
| D01 | Conserve source-compatible top-level EDIT_PLAN fields | V2 requires schema_version/project_id/revision/canvas/sources/profiles/assets/scenes/render/validation/provenance | SOURCE_SUPPORTED | Can disallow absence without changing V2 |
| D02 | Conserve source-compatible ANIMATION_PLAN fields | V2 requires schema_version/project_id/edit_plan_revision/revision/mode/animation_profile/project_seed/decisions/provenance | SOURCE_SUPPORTED | Preserve V1 schema |
| D03 | Use no split IN/OUT fields | V2 + V3 Both locked | SOURCE_SUPPORTED | E_ANIM_MODE on split fields |
| D04 | Half-open frame intervals | V2/V3 scene and asset frames | SOURCE_SUPPORTED | [start,end), start<end |
| D05 | SRT ms-to-frame round_half_up | V2 specified round_half_up(ms*fps/1000) | SOURCE_SUPPORTED | Integer rational formula in addendum |
| D06 | No HOLD required if D==IN+OUT | V2 D>=IN+OUT; equality not prohibited | SOURCE_DERIVED_PROPOSED | Confirm minimal visual HOLD policy separately |
| D07 | No automatic clip shorten/speed change | V2 master failure E_TIME_006 and V3 no fallback | SOURCE_SUPPORTED | Do not use legacy duration sheet exception |
| D08 | Strict duplicate JSON object key handling | V2 strict parser requirement | SOURCE_SUPPORTED | Reject any repeated object key, including nested |
| D09 | Unknown field allowlist schema | V2 strict extra fields but V3 compatibility priority | PROPOSAL_NEEDS_SIGNOFF | Forbid reserved animation fields; preserve documented optional V2 extension keys |
| D10 | Direction canonical tokens per preset | Engine family-level semantics; V3 uses mixed tokens | PROPOSAL_NEEDS_SIGNOFF | See 21-row direction candidates, no auto alias in production yet |
| D11 | Only MEDIUM while FAST/SLOW unresolved | MEDIUM frames from source S04 | OPTION_NEEDS_USER_APPROVAL | Restrict other speeds via explicit E_ANIM_PRESET until per-preset maps certified |
| D12 | Review-labeled ambiguous SRT mapping | EXACT_WORD/EXACT_CUE/APPROX_REVIEW/UNRESOLVED V2 | SOURCE_SUPPORTED | V3 ESTIMATED_FROM_AUDIO mapping requires explicit alias decision |
| D13 | Renderer output hint is legacy only | V3 supersedes MP4 standalone output in V2 | SOURCE_SUPPORTED | Premiere exports final MP4 |
| D14 | Never assume Premiere tick timebase | V3 demands actual host probe | SOURCE_SUPPORTED_HOST_PENDING | G3 host real proof remains OPEN |
| D15 | Numeric resource ceilings | No approved max JSON size/scene count/path cap values | PROPOSAL_NEEDS_SIGNOFF | Record protective constants only after ADR review |
| D16 | Maintain source raw docs private | Seven user-owned sources found in Library | PRIVACY_GUARD | Derived SHA and contract allowed; publishing raw source requires explicit authorization |
| D17 | CREATE_NEW_SEQUENCE default | V3 safety policy | SOURCE_SUPPORTED | No destructive update_existing |
| D18 | Empty/invalid required file blocks every host mutation | V2/V3 fail-closed | SOURCE_SUPPORTED | No dummy asset rescue |
| D19 | SRT/audio/scene gap policy | V2 explicit visual gap policy | SOURCE_SUPPORTED | No implicit hold/fade through unplanned gaps |
| D20 | Lock false policy for production | V2 decision locked expected but false compatibility not explicitly documented | PROPOSAL_NEEDS_SIGNOFF | Do not modify locked value; decide whether block or needs review |

## Contoh pembulatan deterministik 30 FPS

| Test | Kasus | ms | frame (half up) |
| --- | --- | ---: | ---: |
| T001 | SRT ms 0 at 30fps | 0 | 0 |
| T002 | SRT ms 16 at 30fps | 16 | 0 |
| T003 | SRT ms 17 at 30fps | 17 | 1 |
| T004 | SRT ms 50 at 30fps | 50 | 2 |
| T005 | SRT ms 1000 at 30fps | 1000 | 30 |
| T006 | SRT ms 1500 at 30fps | 1500 | 45 |
| T007 | SRT ms 33333 at 30fps | 33333 | 1000 |

**Catatan:** Ini katalog desain test, bukan test executed PASS. G1B baru dapat dikerjakan SOL STEP04 setelah G2/UI host gate.

## Berkas pendamping

- STEP01_DIRECTION_CANDIDATES.csv — 21 kandidat direction, status SOURCE_SEMANTIC_ONLY kecuali token NONE untuk FADE sumber V2.
- STEP01_CONTRACT_DECISIONS.csv — keputusan yang didukung sumber vs memerlukan persetujuan.
- STEP01 fixture catalog dari PR sebelumnya tetap rujukan testing.
- MASTER V3 dan sumber yang ditemukan tetap otoritas; dokumen user pribadi tidak dipublikasikan otomatis.
