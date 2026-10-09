# ASTRA STEP01 — Kontrak teknis dan arsitektur V1 (DRAFT WITH BLOCKERS)

> 9 Oktober 2026 WIB · Authoring ASTRA · Planning only · G1A BLOCKED · Belum boleh coding

## STEP01 — Kontrak teknis dan arsitektur (ASTRA)

Dokumen kerja V1, 9 Oktober 2026 WIB. Produk: AI-JSON-Premiere-Editor, Adobe Premiere Pro 2024 Windows 11. Status: DRAFT_WITH_BLOCKERS, bukan spesifikasi yang telah disahkan.

Tujuan dokumen: menyusun kontrak input, keluaran, aturan keselamatan, keputusan arsitektur dan katalog fixture agar SOL dapat bekerja tanpa menafsirkan instruksi kreatif. Ini pekerjaan perencanaan saja. Belum ada parser, schema executable, plugin, worker atau pengujian Premiere.

Otoritas: instruksi pengguna terbaru; docs/source/MASTER_PLAN_V3_PLUGIN_ADOBE_PREMIERE_PRO_2024_JSON_BOTH.docx; docs/planning/ASTRA_STEP00_RENCANA_IMPLEMENTASI_SOL_V3_A1_2026-10-09.docx; AGENTS.md. Bila bertentangan, jangan menetapkan keputusan sepihak: buat ADR dan minta penutupan blocker.

### 01 — Lingkup, baseline, dan hasil yang tidak boleh diklaim

Target arsitektur adalah panel CEP + host ExtendScript JSX + helper lokal terkontrol + FFmpeg untuk subset efek baked. Bukan plugin UXP dan bukan video renderer mandiri; sequence Premiere tetap hasil utama dan ekspor MP4 dilakukan lewat Premiere.

Main pada baseline e28e08f818d92f01996ce6a6ca6db52606728bfb memuat hanya dokumen; implementasi belum ada, pull request belum ada saat audit dimulai. Semua tes host P0–P6 NOT_TESTED, registry 21 preset UNVERIFIED.

Perubahan perencanaan dikerjakan pada branch ASTRA STEP01 dan diserahkan lewat draft PR. Tidak ada merge main dan tidak mengaktifkan gate UI atau coding.

### 02 — Inventaris sumber dan tingkat kepastian

TERSEDIA: Master V3 asli, transkrip Master V3, rencana ASTRA STEP00, matriks 30 acceptance criteria, matriks 21 preset dan audit B01–B06.

BELUM TERSEDIA: Master V2 kontrak asli; dokumen Layout Zoom/Crop; Animation Engine General Reveal; durasi terverifikasi 21 efek; Prompt 1, Prompt_panel, Prompt 4; gambar final UI; exact build Premiere 24.x pada host uji.

Status PROVISIONAL berlaku untuk field dictionary yang disimpulkan dari contoh V3. Contoh V3 berisi placeholder SHA, dan tidak boleh diubah statusnya menjadi fixture produksi valid hanya dengan mengganti label.

Sumber master menyatakan dukungan versi edit-plan-v2 dan animation-plan-v1 wajib dijaga. Pemblokiran G1A tidak dapat ditutup sampai sumber lama atau penggantinya disetujui eksplisit.

### 03 — Kontrak identitas dan korelasi kedua JSON (NORMATIF V3)

EDIT_PLAN.schema_version harus edit-plan-v2 dan ANIMATION_PLAN.schema_version harus animation-plan-v1. Dokumen yang versinya lain ditolak tanpa migrasi otomatis.

EDIT_PLAN.project_id harus sama dengan ANIMATION_PLAN.project_id; ANIMATION_PLAN.edit_plan_revision harus sama dengan EDIT_PLAN.revision. revision animasi terpisah dari revision edit.

ANIMATION_PLAN.mode harus persis BOTH. Tidak ada field pemisah pilihan IN dan OUT: enter_effect, exit_effect, enter_direction, exit_direction, in_ms, out_ms pada decision adalah kesalahan. OUT diturunkan dari preset yang sama.

Set semua pasangan (scene_id, asset_id) pada seluruh kemunculan asset EDIT_PLAN harus sama persis dengan set pasangan pada ANIMATION_PLAN.decisions. Duplikat, missing atau ekstra ditolak. Asset identik di scene berbeda tetap merupakan dua kemunculan dan dua keputusan.

Pemilihan preset oleh GPT sudah final dan locked; plugin tidak boleh mengacak ulang, diam-diam mengganti, atau memilih alternatif jika backend tidak mendukung. project_seed bukan pemicu re-roll.

Scene berjenis SINGLE memiliki satu instance slot SINGLE; DOUBLE memiliki dua instance ID berbeda dengan slot LEFT dan RIGHT masing-masing tepat satu.

### 04 — Kamus field EDIT_PLAN v2 (contoh V3, belum mengganti V2)

Top-level yang dicontohkan: schema_version:string; project_id:string; revision:integer; canvas:object; sources:object; profiles:object; assets:map; scenes:array; render:legacy object; validation:legacy metadata; provenance:object.

canvas: width=1920, height=1080, fps_num=30, fps_den=1 pada profil awal yang dibatasi; boleh menolak profil lain sampai spesifikasi tambahan disahkan, bukan melakukan resize otomatis.

sources.srt.path/sha256; sources.audio.path/sha256; sources.background.path/required/audio_policy. Required source file harus ada, dapat dibaca, cocok hash jika dideklarasikan, dan dapat diprobe sebelum mutasi host. Audio narasi wajib untuk proyek bernarasi.

profiles.layout_id dan layout_hash mengikat dokumen transform yang digunakan. Hash placeholder atau profil tidak tersedia: preflight BLOCKED; tidak memakai layout default buatan SOL.

assets adalah peta asset_id ke path PNG. Metadata alpha, dimensi, hash, source provenance dan aturan penyediaannya menunggu kontrak V2. Semua path melalui resolver yang tidak menerima traversal di luar root tanpa persetujuan.

scenes adalah array berurutan; setiap scene berisi scene_id, layout_type, start_frame, end_frame, transition_policy, daftar assets. Field source_segment_ids dan narration_quote menjadi bukti referensi narasi, bukan izin mencipta timestamp kata.

Setiap scene.assets item berisi asset_id, slot, start_frame, end_frame, entry_evidence. Untuk DOUBLE tiap item punya start independen; scene V002 contoh A003 dimulai frame 192 ketika scene sudah mulai di 150.

render pada EDIT_PLAN merupakan legacy export hint: boleh dibaca sebagai informasi INFO/DEPRECATED_RENDER_HINT, tidak dieksekusi menjadi FFmpeg output final. validation.status=READY yang ada di file input tidak membuktikan hasil preflight plugin.

### 05 — Kamus field ANIMATION_PLAN v1 (contoh V3, belum mengganti V2)

Top-level contoh: schema_version, project_id, edit_plan_revision, revision, mode, animation_profile, project_seed, decisions, provenance.

animation_profile.id dan sha256 harus merujuk versi registry yang persis cocok dengan hash artefak saat build. Tidak boleh menggunakan registry versi lain secara diam-diam.

Setiap decision contoh: scene_id, asset_id, preset, speed, direction, locked. Preset adalah key semantik, bukan catalog display ID; speed dipilih dari SLOW, MEDIUM, FAST; direction harus salah satu yang diizinkan per preset registry.

locked wajib tidak dimutasi oleh plugin. Apakah locked=false dapat divalidasi sebagai input yang salah harus dipastikan dari Master V2; dalam rancangan produksi awal BLOKIR bila bukan true, tetapi belum boleh menyebutnya syarat V2 final.

provenance tidak boleh dipalsukan. Data eksternal diabaikan sebagai instruksi executable: jangan eval/menjalankan JS atau shell dari JSON.

### 06 — Peta ID 21 preset dan status registry

21 catalog_id terdokumentasi sebagai R01–R06 dan G01–G15. JSON contoh memakai key BRUSH, INK, DIGITAL, SPRAY_PAINT, SKETCH, GRADIENT, RISE, PAN, FADE, POP, WIPE, BLUR, SUCCESSION, BREATHE, BASELINE, DRIFT, TECTONIC, TUMBLE, NEON, SCRAPBOOK, STOMP.

Keputusan usulan: catalog_id hanya ID referensi matriks, sedangkan keputusan JSON memakai preset_key sesuai daftar pada PRESET_MATRIX.csv. Validasi harus mendukung key kanonis tanpa konversi lossy. Status PENDING_SOURCE_APPROVAL.

Entri registry wajib menjelaskan preset_key, catalog_id, versi, definisi IN/HOLD/OUT, allowed direction, parameter easing, mode transform/mask, durasi per speed dan batas clip minimum, serta proof native atau proof prerender.

Angka MEDIUM existing hanya REFERENCE_UNCALIBRATED; durasi FAST/SLOW, direction, keyframe curve, anchor mask dan parameter visual seluruhnya UNKNOWN. Tidak boleh menciptakan multiplier atau preset tiruan.

Prefer NATIVE yang diverifikasi terhadap build, tetapi fallback PRERENDER hanya jika merupakan implementasi preset yang sama dan secara eksplisit ditandai baked. Jika keduanya tidak VERIFIED, preflight gagal E_FX_BACKEND.

### 07 — Aturan timing dan pembulatan (pilihan usulan)

Semua scene/asset berada dalam interval half-open [start_frame,end_frame) dengan integer frame dan start<end. Profil awal adalah tepat 30/1 FPS. [0,150) berarti 150 frame; [150,330) berarti 180 frame.

Aturan usulan ketika sumber memakai milidetik: frame= floor((milliseconds*fps_num + 500*fps_den) / (1000*fps_den)) untuk nilai nonnegatif, tetapi rumus ini harus dikaji kembali untuk tie-to-upper berbasis rasional penuh sebelum disahkan. Prioritas utama adalah frame integer dari EDIT_PLAN: jangan konversi ulang jika sudah ada.

Asset tidak boleh melewati scene kecuali policy overlap/crossing-scope disahkan dan eksplisit di input. Dua item DOUBLE mempunyai timer sendiri. Tidak memotong narasi audio agar efek muat.

Host ticks tidak boleh diturunkan dari display timecode; query API host nyata. Angka ticks besar ditransfer sebagai decimal string melalui bridge bila melewati integer aman JS.

Readback posisi/durasi setiap klip dibandingkan expected frame. Delta lebih dari satu frame FAIL; delta 1 frame harus dicatat dan perlu bukti decoder/host khusus untuk penerimaan. Jitter keyframe OUT harus diuji pada nonzero start dan source trim.

### 08 — SRT evidence dan ketidakpastian timing

EXACT_WORD hanya bila ada timestamp kata terverifikasi. EXACT_CUE hanya memberikan batas cue. ESTIMATED_FROM_AUDIO memerlukan review manual terikat hash sumber bila material. UNRESOLVED/ambiguous adalah blocking error.

Occurrence dan source_span diperlukan untuk kutipan berulang; jangan menautkan dua frasa identik ke cue yang salah. Harus mendukung UTF-8, BOM, multiline dan Unicode. Cue rusak dan durasi negatif harus gagal.

Jika SRT dinyatakan wajib, file hilang atau hash tidak cocok maka E_MEDIA_MISSING sebelum mutasi. Perubahan sumber setelah review membatalkan READY.

### 09 — Layout, compositing, dan track plan

Track kandidat dari V3: V1 background (audio background MUTE), V2 visual SINGLE atau LEFT, V3 visual RIGHT, A1 narasi. V4 label, V5 subtitle, A2 musik hanya jika profil memintanya.

Koordinat atau crop SINGLE/DOUBLE, anchor, safe area, prioritas layer label dan aturan zoom belum terkonfirmasi. Semua angka ditahan menunggu dokumen Layout Zoom/Crop atau approved replacement.

Backend prerender harus merekam apakah overlay lokal atau full-canvas; transform layout tidak boleh diterapkan dua kali. Alpha import harus diperiksa terhadap latar terang/gelap dan saat reopening.

Background loop disusun sampai durasi sequence yang bersumber resmi dan trim segmen terakhir tanpa celah, tidak mengaktifkan audio background secara implisit.

Jika template sequence yang aman untuk 1080p 30fps, jumlah track atau insert tanpa ripple tidak bisa dibuktikan via DOM resmi, assembly ditolak; QE DOM bukan dependensi tersembunyi.

### 10 — Output compiler dan kesepakatan determinisme

Output usulan: preflight-report-v1.json; compiled-manifest-v1.json; job-journal-v1.jsonl; clip-map-v1.json; premiere-assembly-report-v1.json. Semua output skemanya diselesaikan sebelum SOL STEP04.

Manifest operation minimum: instance_key unik; scene_id; asset_id; source_path dan hash; sequence start/end frames; source in/out; designated track; base transform; preset; speed; direction; frames IN/HOLD/OUT; backend; cache relink bila baked; expected readback.

Hash INPUT_RAW_SHA256 menghitung byte file asli. CANONICAL_SHA256 (jika digunakan) butuh aturan serialisasi resmi, termasuk urutan key, Unicode, numbers dan excluded volatility. Tidak boleh mengklaim ekuivalensi dua hash tanpa definisi.

operation_digest harus stabil untuk input, registry, layout dan capability sama; job_id, waktu, lokasi log volatile dapat berbeda tetapi dipisah dari operation_digest.

Laporan hasil memuat host version/build, OS, locale, registry/layout/capability hash, job_id, managed sequence, expected dan actual counts, per-clip frame deltas, backend counts, alpha probe, warnings, errors, status dan evidence refs.

### 11 — ADR arsitektur untuk SOL (usulan belum dikunci)

ADR01 ACCEPTED_BY_MASTER: panel CEP dockable; CSInterface bridge ke JSX ExtendScript ECMAScript 3; helper lokal untuk parser, SRT, path, hash, FFprobe/FFmpeg dan manifest. Tidak memanggil APIs unsupported tanpa probe.

ADR02 CONDITIONAL: helper Python terpaket direkomendasikan agar JSON Schema, hashing dan FFmpeg arg list dapat diuji offline. Final runtime versi, packaging, license dan Windows signing masih B05; Node terkontrol tetap kandidat sampai ADR dependency.

ADR03 ACCEPTED_BY_MASTER: keluaran Premiere sequence editable, bukan MP4 standalone; efek native editable, prerender adalah baked dan dapat digeser/trim saja.

ADR04 ACCEPTED_BY_MASTER: create NEW sequence adalah default; tidak ada UPDATE_EXISTING pada rilis awal. Retry tidak boleh mengulang ke sequence parsial.

ADR05 PENDING_HOST: host capability profile adalah versi aktual build Premiere 24.x + locale + fitur tersedia + parameter keyframe + alpha/codec. Runner CI Windows tanpa Premiere tidak boleh menandai host gates PASS.

### 12 — State machine, keselamatan, dan pemulihan

State: NO_PROJECT → FILES_SELECTED → PREFLIGHT_RUNNING → READY atau NEEDS_REVIEW/PREFLIGHT_FAIL; READY → ASSEMBLING → ASSEMBLED/INCOMPLETE. File/profile/host berubah → READY invalid.

READY hanya apabila semua media wajib ada, parser+semantic+registry+capability lulus, proyek host tersimpan, dan sumber tidak berubah sejak snapshot. Tombol SUSUN TIMELINE OTOMATIS harus disabled bila tidak READY.

Build memerlukan konfirmasi dan transaction journal: intent dicatat sebelum host call, hasil setelah readback. Klik ganda/reload callback usang tidak membuat job kedua.

Setelah crash UNKNOWN berarti inspeksi manual, bukan izin mengulang operasi. Failure tidak menghapus sequence lama, media, cache linked maupun edit manual. Recovery menyarankan Rebuild New Sequence atau Repair Cache berbasis hash dan konfirmasi.

Cache baked keyed oleh asset hash, preset, speed, direction, source/time span, registry, alpha profile, layout, worker version dan seed jika relevan. Penulisan temporary → verifikasi frame/alpha/hash → atomic rename; disk penuh/cancel tidak memproduksi cache valid.

### 13 — Error codes, preflight, dan pesan Bahasa Indonesia

E_JSON_SCHEMA: field/type/versi tidak sesuai. E_PLAN_PAIR: project/revision/asset pair tidak cocok. E_ANIM_MODE: bukan BOTH atau ada pemisah IN/OUT. E_ANIM_PRESET: key/speed/direction tidak didukung. E_MEDIA_MISSING: media wajib tidak tersedia/terbaca.

E_SRT_AMBIGUOUS: bukti cue/occurrence tidak jelas. E_HOST_UNSUPPORTED: Premiere bukan 24.x atau API belum tersertifikasi. E_HOST_SEQUENCE: gagal membuat sequence/track. E_FX_BACKEND: tidak ada backend terverifikasi untuk preset. E_ALPHA_IMPORT: alpha tidak benar. E_CACHE_MISSING: linked cache hilang. E_HOST_PARTIAL: host gagal setelah mutasi parsial.

Setiap error harus memuat file, scene atau asset ID yang relevan, expected vs actual bila mungkin, penyebab singkat, dan langkah perbaikan. Stack trace khusus log developer.

Fatal preflight mencegah satu pun mutasi timeline. Needs review berbeda dari PASS dan tidak mengaktifkan build.

### 14 — Batas keamanan dan kebijakan file

File JSON input tidak dipercaya: batasi ukuran, scene count, asset count dan path panjang; angka final limit masih PENDING_SOURCE_APPROVAL, jangan masukkan angka spekulatif dalam schema final.

Path UTF-8 Unicode, spasi dan kutip harus ditangani. Tolak traversal; symlink/junction escape root tanpa izin harus ditolak. File luar root hanya dengan pilihan eksplisit pengguna dan audit path. Tidak menjalankan string path sebagai command.

FFmpeg selalu dipanggil memakai argv terpisah setelah verifikasi binary/hash dan capability, tidak lewat concat shell string dari JSON. Dilarang eval JSON, download executable tersembunyi, PlayerDebugMode permanen atau mencatat credential.

Output, log dan bukti video bisa memuat konten pengguna; repo publik hanya fixture sintetis dan evidence yang telah disanitasi/diizinkan.

### 15 — Katalog fixture dan gate pengujian

Seluruh entri tercantum pada STEP01_FIXTURE_CATALOG.csv sebagai rencana uji, bukan file input siap jalan dan bukan hasil PASS. Fixture awal F001 memetakan DEMO_001 V001 SINGLE A001 [0,150) dan V002 DOUBLE A002 [150,330), A003 [192,330), dengan 3 decision BOTH, hanya setelah SHA media diganti dengan hash nyata.

Kelompok kontrak: valid positive, JSON syntax/types, version, pair match, duplicate, BOTH split, unknown preset, speed/direction, locked, timing, SRT evidence, media/path/hash, cache/capability, recovery.

Implementasi test dan executable schema baru pada STEP04 sesudah G2 dan host STEP03. Setiap kasus direncanakan memiliki expected code, before/after host mutation counts, dan bukti aktual untuk hasil nyata.

Acceptance AC01–AC30 dari Master V3 tetap berlaku; tidak ada AC dinyatakan PASS hanya karena katalog kasus lengkap.

### 16 — Keputusan terbuka dan bukti untuk menutupnya

B01: masukkan Master V2, Layout Zoom/Crop, Animation Engine General Reveal, durasi 21 animasi, Prompt 1/Prompt_panel/Prompt 4; atau setujui satu approved-replacement spec yang kompatibel.

B02: daftar lengkap allowed directions dan durasi SLOW/MEDIUM/FAST, easing, mask/opacity dan referensi visual untuk seluruh 21 efek.

B03: inventaris host uji yang sah: Windows 11, exact Premiere 24.x build, locale, CEP/CSXS version, FFmpeg alpha capability; bukti P0 pilot menyusul STEP03, tidak diklaim saat planning.

B04: STEP02 menulis prompt UI lalu STOP; gambar final, persetujuan eksplisit, source hashes dan satu UI_REFERENCE_FINAL.docx wajib di repo sebelum code.

B05: ADR dependency lengkap (versi, sumber dan izin pakai, binary notices, FFmpeg distribution terms dan rencana signing/packaging) sebelum dependency dipakai/distribusikan.

B06: normatif unresolved: unknown-field policy untuk kompatibilitas V2; duplicate JSON keys; locked=false policy; bounds/payload sizes; half-frame rational rounding; chronology scene gap/overlap; short-clip behavior; registry serialization; source in/out; tick-time coordinate; exact status transisi.

Penutupan blocker harus menyebut dokumen final, hash, peninjau, tanggal, dan keputusan. 'Sudah ada contoh dalam V3' tidak cukup untuk membekukan schema produksi.

### 17 — Gate keputusan akhir STEP01

STEP01 document deliverable: rencana field dictionary, invariants, arsitektur, security, preflight, fixture catalog, mapping awal tersedia dan disimpan pada branch. State dokumen COMPLETE_DRAFT_WITH_BLOCKERS.

G1A SPEC = BLOCKED, sebab B01/B02/B06 belum tertutup dan sebagian detail belum normatif. G1B SCHEMA TEST = NOT_STARTED (dialokasikan STEP04). G2 UI APPROVAL = NOT_STARTED. Coding = PROHIBITED.

Langkah kerja terdekat (masih STEP01): dapatkan dokumen lama atau persetujuan spesifikasi pengganti, bekukan registry/layout/policy, perbarui DOCX+MD, review lalu tandai G1A PASS dengan bukti. Baru setelah izin lanjut dan G1A PASS lakukan STEP02 prompt UI; sesudah prompt UI wajib STOP.

AI/SOL selanjutnya harus membaca AGENTS.md, docs/STATUS.md, Master V3, STEP00, STEP01, BLOCKERS dan matriks AC/preset. Jangan merge branch ASTRA atau mulai coding berdasarkan draft ini tanpa izin/gate.

### Lampiran katalog fixture

File pendamping: STEP01_FIXTURE_CATALOG.csv (48 kasus; bukan hasil uji).

### Source references

- docs/source/MASTER_PLAN_V3_TRANSCRIPT.md §§3–13, khususnya contoh 13.1–13.3.
- docs/planning/ASTRA_STEP00_RENCANA_IMPLEMENTASI_SOL_V3_A1_2026-10-09.md.
- docs/planning/BLOCKERS.md, PRESET_MATRIX.csv, ACCEPTANCE_MATRIX.csv.
