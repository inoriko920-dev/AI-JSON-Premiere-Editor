# Transkrip Master Plan V3

Salinan baca dari DOCX asli; DOCX asli tetap otoritatif. Urutan paragraf dan tabel dipertahankan.


DOKUMEN INDUK - REVISI ARSITEKTUR

MASTER PLAN V3

AI JSON VIDEO EDITOR  |  PLUGIN ADOBE PREMIERE PRO 2024

CEP + ExtendScript + FFmpeg (Hybrid)   •   Windows 11   •   9 Oktober 2026

Satu preset per kemunculan aset. Mode BOTH wajib. Dua JSON terpisah. Timeline Premiere dapat disunting sebelum ekspor.

STATUS: MASTER PLAN / SPECIFICATION ONLY - TIDAK ADA CODE, PLUGIN TERPASANG, ATAU HASIL UJI PREMIERE

KONTRAK DIKUNCI | KEPUTUSAN V3
Target pengguna | Premiere Pro 2024 (host 24.x), Windows 11
Output utama | Project/sequence di Premiere, bukan MP4 hasil renderer mandiri
Dua sumber perintah | EDIT_PLAN.json v2 dan ANIMATION_PLAN.json v1
Animasi | Pilihan GPT: satu preset yang sama untuk masuk + keluar; mode BOTH wajib
Teknologi | Panel CEP + ExtendScript; worker FFmpeg hanya saat diperlukan
Edit manual | Native clip/edit/keyframe bila didukung; prerender overlay terbatas pengeditannya
Batas tahap ini | Dokumen diserahkan; coding dan GitHub tidak dikerjakan

Perubahan dari MASTER PLAN V2

V2 memusatkan hasil pada render MP4 oleh aplikasi tersendiri. V3 memusatkan hasil pada timeline Premiere Pro 2024 yang dapat ditinjau, diedit, dan diekspor sendiri oleh pengguna. Kontrak data V2 tentang scene dan animasi tetap menjadi sumber kebenaran, tetapi semua komponen penyusun timeline dan preset harus melewati uji kompatibilitas host 24.x.

Dokumen ini merupakan rencana pembangunan dan matriks pembuktian. Ketersediaan sebuah API dalam dokumentasi tidak sama dengan jaminan setiap efek 21 preset sudah berjalan di Premiere 2024.

Daftar isi

01. Ringkasan eksekutif dan keputusan final

02. Delta V2 → V3 dan prioritas kompatibilitas

03. Tujuan produk, cakupan, definisi selesai

04. Alur pengguna dan struktur paket

05. Kontrak data dua JSON dan mapping SRT

06. Arsitektur plugin CEP/ExtendScript/worker

07. Membuat sequence, track, aset dan kontrol proyek

08. Animation Engine 21 preset, BOTH wajib

09. Strategi native vs prerender FFmpeg

10. Desain panel UI Premiere 2024

11. Validasi, keamanan, error, rollback, audit

12. Uji otomatis, pilot host nyata dan acceptance

13. Roadmap kerja, gate, risiko dan handoff

14. Lampiran contoh JSON, folder, bukti dan rujukan

Navigasi dibuat sebagai daftar isi statis berdasarkan struktur dokumen; halaman dapat berubah apabila dokumen disunting.

0. Ringkasan eksekutif dan keputusan final

Produk yang dibuat adalah ekstensi berbentuk panel di Adobe Premiere Pro 2024. GPT menyiapkan rencana scene/timing dan JSON pilihan animasi. Ekstensi memvalidasi semuanya, menyusun aset ke timeline Premiere, menerapkan animasi BOTH per gambar, kemudian menyerahkan proyek kepada pengguna untuk penyuntingan manual dan ekspor akhir melalui Premiere. Tidak ada kebutuhan koneksi API AI dalam plugin versi awal.

ASPEK | KEPUTUSAN FINAL | KONSEKUENSI TEKNIS
Host | Premiere Pro 2024 / PPRO 24.x | CEP/ExtendScript; tidak bergantung UXP 25.6+
Kontrak scene | edit-plan-v2 (tetap) | Waktu dan asset instances dalam bilangan frame
Kontrak animasi | animation-plan-v1 (tetap) | BOTH wajib; tepat satu preset per (scene_id,asset_id)
Media | PNG alpha, audio, SRT, background jika required | Missing atau tidak terbaca → FAIL, tidak susun timeline
Penempatan | Dokumen Layout/Crop terdahulu | Transform awal ditentukan plugin, bukan GPT
Efek | Native-first; FFmpeg untuk efek kompleks | Hasil native editable; prerender hanya klip/manipulasi luar
Output | Premiere Sequence + manifest/diagnostic | Export MP4 oleh pengguna melalui Premiere
Distribusi | Pengembangan ZIP, rilis paket plugin setelah bukti host | Installer tidak dibuat sebelum gate pass

0.1 Batas kepastian dan pembuktian

TERBUKTI DOKUMEN: CEP klasik dan ExtendScript adalah jalur relevan untuk Premiere 2024; project item, sequence, track, component/parameter mempunyai API scripting yang terdokumentasi.

BELUM TERBUKTI DI MESIN PENGGUNA: pembuatan semua layer otomatis, keyframe per parameter dengan build 24.x yang dimiliki, 21 efek per preset, impor alpha MOV/PNG sequence dan installer. Semua memerlukan pilot pada Premiere 2024 asli.

DILARANG menganggap API UXP, feature Premiere 25.x/26.x, QE DOM tersembunyi, atau hasil rendering FFmpeg sebagai bukti fitur native Premiere 2024.

1. Delta V2 → V3 dan prioritas kompatibilitas

KOMPONEN V2 | STATUS V3 | TINDAKAN
Render MP4 aplikasi terpisah | DIGANTI | Generate sequence/project di Premiere; ekspor via Premiere
UI desktop Windows terpisah | DIGANTI | Dockable CEP panel di workspace Premiere
Komposisi video FFmpeg final | DIPERSEMPIT | FFmpeg hanya menghasilkan intermediate RGBA untuk preset yang perlu
EDIT_PLAN v2 | DIPERTAHANKAN | Scene, asset placement, SRT frame tetap authoritative; render block legacy
ANIMATION_PLAN v1 BOTH | DIPERTAHANKAN | Tidak ada enter_effect vs exit_effect
21 registry/durasi | DIPERTAHANKAN | Bukti implementasi backend per effect diwajibkan
SINGLE/DOUBLE/crop | DIPERTAHANKAN | Terjemahkan ke Motion base transform dan track Premiere
Portable EXE renderer | DIBATALKAN | Paket extension installer Windows + optional worker

1.1 Referensi pengguna yang harus tetap dibaca

DOKUMEN TERDAHULU | FUNGSI DI V3
MASTER PLAN V2 - JSON ANIMATION BOTH | Sumber kontrak EDIT_PLAN v2, ANIMATION_PLAN v1, validasi dan durasi
MASTER DURASI IN OUT 21 ANIMASI CANVA V2 | Baseline lama IN/OUT frame; data estimasi/rekomendasi, bukan angka asli Canva
Spesifikasi Layout Zoom dan Penempatan Gambar Canva | Posisi SINGLE/DOUBLE, cropping, safe area dan base transform
Spesifikasi Animation Engine Canva General Reveal | Deskripsi visual 21 preset, easing/opacity/mask/keyframe
Prompt 1 Visual Planner + Prompt_panel | Scene/segment/asset IDs, source_span, occurrence dan asset plan
Prompt 4 Animation Director | Rasional semantik untuk memilih animasi; output dinormalisasi menjadi BOTH

1.2 Sumber kebenaran dan konflik

Hierarchy: (1) revisi keputusan eksplisit pengguna / dokumen V3; (2) dua JSON resmi yang valid; (3) preset registry bertanda hash; (4) dokumen Layout/Crop dan Animasi terdahulu; (5) metadata media nyata. Jika ada konflik, preflight memberi FAIL/NEEDS_REVIEW; tidak menebak. Tidak boleh mengambil contoh dalam lampiran sebagai file produksi.

2. Tujuan produk, cakupan dan definisi selesai

2.1 Tujuan pengguna akhir

Mengimpor dua JSON melalui satu panel Premiere; validasi proyek dan semua file sebelum perubahan timeline.

Menghasilkan sequence 1920×1080 pada 30 FPS sesuai profil atau membuat dari template sequence yang telah diuji; tidak mengubah sequence aktif secara destruktif.

Mengimpor PNG aset dan menempatkan layer SINGLE/DOUBLE sesuai scene dan SRT yang sudah diselesaikan dalam EDIT_PLAN.

Menerapkan satu preset yang sama untuk animasi masuk dan keluar (BOTH), native bila realistis, fallback prerender alpha bila disetujui di registry.

Menampilkan track background, visual A/B, narasi, subtitle menurut kebijakan, dan penanda scene.

Memungkinkan menyimpan .prproj dan mengedit secara manual serta ekspor melalui menu Premiere.

Menyediakan bukti import, log, pemetaan track, versi registry, status kegagalan, dan tombol preview/repair tanpa merusak hasil lama.

2.2 Di luar lingkup V3

Tidak membuat atau mengubah gambar, tidak memanggil Gemini/GPT dari plugin, tidak mengganti narasi asli, tidak melakukan diarization, tidak membuat subtitle baru otomatis jika SRT tidak ada, tidak mengkloning preset Canva secara pixel-identik, tidak memaksa 21 preset native, tidak membuat export MP4 menggunakan FFmpeg sebagai alur utama, dan tidak melakukan merge/push GitHub tanpa instruksi eksplisit.

2.3 Definition of Done yang terukur

Produk dinyatakan selesai hanya ketika pengguna dapat memasang panel pada Premiere 2024 aktual, memberi proyek valid, menjalankan preflight, membangun sequence tanpa missing media/track salah, melihat animasi BOTH yang sudah diuji, mengeditnya, menyimpan .prproj, dan mengekspor MP4 lewat Premiere. Tidak cukup dengan gambar UI, tes parser, ZIP source, atau pemeriksaan CI tanpa host Premiere.

3. Alur pengguna dan struktur paket

3.1 Alur harian

GPT membaca hasil Prompt 1/Prompt_panel dan SRT; menyiapkan EDIT_PLAN.json berisi scene/timing yang dibuktikan dari narasi.

GPT memilih satu preset untuk tiap kemunculan aset pada scene; menyiapkan ANIMATION_PLAN.json (mode BOTH).

Pengguna menyiapkan folder proyek berisi dua JSON, SRT, audio, background bila diperlukan, dan PNG individual.

Buka Premiere 2024 → panel AI JSON Video Editor → Pilih folder proyek → Impor kedua JSON.

Tekan PERIKSA PROYEK. Panel memvalidasi schema, versi, semua media, pemetaan, timing, registry, dukungan alpha dan host.

Jika semua PASS, simpan/cadangkan .prproj saat ini; tekan SUSUN TIMELINE OTOMATIS.

Plugin membuat sequence baru / managed namespace, mengisi track, memasang efek BOTH sesuai strategi yang tervalidasi.

Pengguna preview, mengoreksi manual di Premiere bila perlu, menyimpan proyek, lalu ekspor melalui Premiere/Media Encoder.

3.2 Struktur proyek dan artefak bukti

PROJECT_NAME/
  EDIT_PLAN.json
  ANIMATION_PLAN.json
  narasi.srt
  narasi.wav
  background.mp4                 # wajib bila sources.background.required=true
  assets/
    A001.png
    A002.png
    A003.png
  premiere/
    PROJECT_NAME.prproj          # dibuat/disimpan melalui Premiere
  .ai-json-editor/
    manifest.json                # penetapan media dan track
    preflight-report.json
    assembly-report.json
    cache/
      V002_A003_WIPE_BOTH_*.mov  # bila codec alpha lulus uji host
    logs/

Folder cache hanya boleh dihapus melalui housekeeping yang mengerti referensi klip Premiere; jangan memindahkan file intermediate setelah linked ke proyek. Lokasi path relatif terhadap proyek; file luar hanya setelah pengguna memilih manual dan tercatat di manifest.

3.3 Formulir input minimal

INPUT | DIPERLUKAN | JIKA TAK ADA / GAGAL
EDIT_PLAN.json | YA | Stop; tidak ada scene/timing yang dipercaya
ANIMATION_PLAN.json | YA | Stop; tidak boleh random animasi
narasi.srt | YA jika dinyatakan wajib di sources | Stop; jangan mengarang timestamp
audio.wav/mp3 | YA untuk proyek bernarasi | Stop; durasi tidak dapat diklaim sinkron
assets/*.png | YA untuk setiap asset yang tampil | Stop; jangan placeholder
background.mp4 | YA bila required:true | Stop; jangan background dummy
ffmpeg/ffprobe | Jika ada preset PRERENDER | Stop hanya bila preset yang dipilih memerlukan worker

4. Kontrak data dua JSON dan mapping SRT

4.1 Kontrak lama tetap valid: tidak mengubah JSON

Agar tidak mematahkan workflow GPT yang sudah dibuat, V3 menerima EDIT_PLAN.json dengan schema_version edit-plan-v2 dan ANIMATION_PLAN.json dengan schema_version animation-plan-v1, tanpa mengubah field animasi. Nilai render pada EDIT_PLAN v2 diperlakukan sebagai petunjuk eksport lama (legacy output hint) dan tidak dieksekusi oleh plugin; panel memberi INFO/DEPRECATED_RENDER_HINT, bukan menggunakan output_path untuk FFmpeg final. Jika V4 kelak diperlukan, harus memiliki schema terpisah dan migrator yang diuji.

JSON | FIELD PENTING | ROLE
EDIT_PLAN | project_id, revision, canvas, sources, profiles, assets, scenes | Authoritative untuk media, nama aset, scene, layout, frame, source evidence
ANIMATION_PLAN | project_id, edit_plan_revision, mode, animation_profile, decisions | Authoritative untuk satu preset, speed/direction dan locked per (scene,asset)
Plugin runtime profile | Premiere version, selected sequence preset, track policy, alpha capability, cache path | Konfigurasi mesin; BUKAN keputusan kreatif baru dari GPT

4.2 Aturan pencocokan wajib

project_id pada kedua JSON harus sama; edit_plan_revision di ANIMATION_PLAN sama dengan revision EDIT_PLAN.

Tepat satu decision animasi untuk setiap pasangan (scene_id, asset_id) yang tampil. Tidak ada extra, missing, atau duplikat.

mode harus persis BOTH; field terlarang enter_effect, exit_effect, enter_direction, exit_direction, in_ms, out_ms dalam keputusan animasi ditolak.

preset merupakan ID stabil dan didukung registry; speed SLOW/MEDIUM/FAST, direction hanya yang ditandai allowed oleh registry; OUT memakai perilaku keluarnya preset itu sendiri.

Bila asset yang sama muncul di dua scene, setiap kemunculan memakai lookup berbeda berdasarkan (scene_id,asset_id).

SINGLE tepat satu asset instance; DOUBLE tepat dua asset yang berbeda dan berada pada slot LEFT/RIGHT.

start_frame < end_frame, semua integer pada 30fps; start/end asset dalam batas scene kecuali policy yang sudah mendefinisikan overlap.

Jangan mengganti atau menafsirkan ulang pilihan semantik GPT pada tahap assembly.

4.3 Penyelarasan SRT: tidak mengarang timestamp kata

SRT menyediakan cue-level start/end. Jika pemetaan GPT menyebut kata di tengah cue, plugin tidak boleh mengaku tahu waktu persis kata dari subtitle cue-level saja. EDIT_PLAN harus menyimpan timing evidence: EXACT_WORD bila transcript berstempel kata terverifikasi, EXACT_CUE bila cocok satu cue, ESTIMATED_FROM_AUDIO bila diverifikasi manual, atau UNRESOLVED yang wajib review. Pemetaan occurrence dan source_span menjaga frasa berulang tidak salah tertaut.

EVIDENCE | STATUS | PERLAKUAN
EXACT_WORD | Lulus bila data timestamp kata tersedia | frame dibulatkan deterministik
EXACT_CUE | Lulus untuk batas cue | gunakan batas cue, bukan klaim presisi kata
ESTIMATED_FROM_AUDIO | Butuh review jika material | tampilkan confidence dan perlu konfirmasi
UNRESOLVED / ambiguous | FAIL | tidak membangun timeline dari tebakan

4.4 Frame/timebase dan overlap

Semua waktu disimpan sebagai frame integer dan menggunakan interval [start_frame,end_frame), pada fps_num/fps_den dari JSON. 30 FPS → satu frame = 33,333… ms. Ubah waktu ke frame dengan kebijakan pembulatan tunggal yang terdokumentasi; pada frame akhir sequence jangan menggeser audio karena rounding per scene. Setelah membangun timeline, baca kembali time/start/end Premiere dan bandingkan toleransi maksimum satu frame (untuk tipe media/sequence yang mendukung). Jika menyimpang lebih besar, laporkan FAIL.

Untuk DOUBLE, asset A dapat mulai di awal scene dan asset B menyusul: dua klip independen, masing-masing dengan start/end-nya. Overlap per track, crossing scene, dan transisi CUT/EXIT_TO_BG harus ditentukan dalam EDIT_PLAN dan tidak diputuskan acak oleh plugin.

5. Arsitektur plugin CEP/ExtendScript/worker

5.1 Lapisan sistem

LAPISAN | TEKNOLOGI | TUGAS | BATAS
Panel | CEP HTML/CSS/JS + CSInterface.js | Browse folder, tabel scene/effect, report, progress, tombol assembly | Tidak menulis operasi timeline langsung
Validator/Compiler | Helper lokal (Python packaged / Node terkontrol) | JSON Schema, SRT, path/hash, registry, layout, render manifest | Tidak mengubah keputusan animasi
Host adapter | ExtendScript .jsx ECMAScript 3 | Import media, sequence, track clip, base Motion, native keyframe | Hanya API yang terbukti pada Premiere 24.x
Effect registry | File deklaratif versioned | ID 21 preset, speeds, duration frames, direction, backend status | Tidak ada silent fallback
FX worker | FFmpeg + image-mask generator | Prerender alpha untuk kompleks; cachable dan reproducible | Tidak membuat MP4 final sebagai output utama
QA/audit | Log JSON + probes + screenshot evidence | Report: hasil, warning, media, clip map, file hash | Tidak mengklaim hasil host sebelum diuji

5.2 Peta komunikasi dan otoritas

GPT: EDIT_PLAN v2 + ANIMATION_PLAN v1
          |          |
          v          v
   [CEP UI -> Schema/Media/SRT/Registry Validator]
                     |
               Preflight PASS
                     |
      [Timeline Compiler -> deterministic manifest]
                /            \
      [ExtendScript]      [FFmpeg worker]
       native clips        alpha cache items
                \            /
        [Premiere Pro 2024 Sequence]
                     |
    [User manual edit + native Premiere export]

Bridge CSInterface.evalScript harus menggunakan metode host yang didefinisikan ketat. Jangan interpolasi bebas teks JSON menjadi kode ExtendScript. Panel menulis manifest sanitasi/escape ke file kerja; adapter JSX menerima path tervalidasi dan operasi kecil, bukan eksekusi string arbitrer. Nilai/response host harus bertipe dan dapat diserialisasi.

5.3 Struktur kode yang ditargetkan

ai-json-premiere-2024/
  CSXS/manifest.xml
  panel/index.html
  panel/css/app.css
  panel/js/app.js
  panel/js/CSInterface.js
  host/main.jsx
  host/lib/sequence.jsx
  host/lib/asset_placement.jsx
  host/lib/native_animation.jsx
  core/schema/edit-plan-v2.schema.json
  core/schema/animation-plan-v1.schema.json
  core/registry/canva-both-21-v1.json
  worker/preflight.py
  worker/timeline_compiler.py
  worker/fx_builder.py
  tests/fixtures/...
  tests/unit/...
  tests/integration/...
  docs/host_capability_matrix.md
  docs/README_ID.md
  packaging/...

5.4 Prasyarat minimum dan host guard

Target host Premiere Pro major 24; simpan build persis (24.x.y), sistem operasi, CEP runtime dan language UI dalam laporan startup. Fitur yang belum dibuktikan pada build tersebut berstatus BLOCKED/UNVERIFIED.

CEP manifest Host Name=PPRO dengan rentang versi yang sengaja membatasi 24.x; CSXS runtime harus dipastikan pada host nyata (laporan praktik 24.x menggunakan CEP 11).

Periksa project aktif dan sequence. Jika tidak aman mengubahnya, plugin membuat sequence baru dengan nama unik; jika host API create sequence/template gagal, tampilkan instruksi/manual gating - tidak memaksa setelan sequence default yang mungkin salah.

Perbedaan locale dan nama tampilan efek: gunakan stable matchName bila ada, bukan label UI bahasa tertentu; jika tidak tersedia, host capability discovery dan uji per-effect wajib.

5.5 Konektor project, status, dan operasi idempotent

Setiap assembly job memiliki job_id, project_id, edit_revision, animation_revision, assembly_hash dan target_sequence_name. Mode default CREATE_NEW_SEQUENCE; fitur UPDATE_EXISTING hanya dipertimbangkan setelah bukti idempotency. Tombol ulang bukan memasukkan duplikat ke timeline lama. Preflight menghasilkan rencana operasi yang bisa dibaca pengguna: n PNG, n native anim, n prerender, rentang track, estimasi cache dan semua warning.

6. Membuat sequence, track, aset dan kontrol proyek

6.1 Track plan dan prioritas komposit

TRACK | ISI | KONTRAK
V1 | Background MP4 loop | Audio background dimute kecuali eksplisit diizinkan
V2 | Gambar SINGLE atau slot kiri DOUBLE | Satu track managed, tidak menimpa item manual
V3 | Slot kanan DOUBLE | Terpisah; stagger sesuai JSON
V4 opsional | Graphic/label jika project memang mengatur | Tidak ditambahkan bila label sudah baked dalam PNG
V5 opsional | Subtitle dari SRT bila output meminta | Tidak otomatis bila NONE / overlay subtitle terpisah
A1 | Narasi asli | Source timing mengikuti project, tidak retime otomatis
A2 opsional | Musik/ambience bila source disetujui | Dilarang menambah lagu/efek suara sendiri

Urutan track V1–V5 adalah baseline rancangan, dapat berbeda setelah host pilot tetapi tetap deterministik dan direkam pada laporan. Di tiap sequence, track milik plugin ditandai prefix atau metadata; perubahan manual pada track selain milik plugin tidak boleh disentuh.

6.2 Algoritma assembly deterministik

Ambil ProjectContext dari dua JSON; validasi schema dan hash. Jika media kurang STOP sebelum memanggil Premiere API yang mengubah timeline.

Pastikan Premiere project tersedia dan pengguna menyetujui pembuatan sequence baru; minta penyimpanan project jika belum pernah disimpan.

Import file PNG, audio, background melalui API project; verifikasi ProjectItem dari path/ID dan decoder.

Buat sequence dengan resolusi/timebase yang diverifikasi; bila preset dibuat di Premiere, gunakan template preset yang sudah disertifikasi, jangan bergantung default.

Atur/cek jumlah track. Insert background dan audio; bedakan source in/out vs sequence start/end agar tidak menciptakan ripple.

Untuk tiap scene, masukkan klip aset tepat pada start_frame dan end_frame; pastikan layer kiri/kanan, base transform, alpha dan label sesuai profil layout.

Ambil satu preset BOTH dari ANIMATION_PLAN per pasangan scene/asset, resolusi durasi/speed/direction dari registry.

Jika backend NATIVE: apply transform/opacity/keyframe pada properti yang terbukti; jika PRERENDER: hasilkan RGBA clip transparan yang tetap dapat dipindah sebagai klip independen.

Masukkan marker scene dan import subtitle hanya jika kebijakan eksplisit meminta. Simpan laporan setiap operasi.

Baca kembali sequence track clips/start/end/effect properties; jika mismatch, tandai FAIL, jangan klaim PASS. Simpan project melalui tindakan pengguna/host bila tersedia.

6.3 Melindungi edit manual pengguna

Default non-destruktif: buat sequence baru bernama AI_JSON_<project>_<revision>_<job>. Jangan menghapus item pengguna dari timeline aktif. Bila assembly gagal setengah jalan, tandai sequence INCOMPLETE dan laporkan daftar item yang mungkin tertinggal; untuk retry buat sequence baru, bukan "cleanup" tanpa verifikasi. Auto relink hanya menggunakan hash/path yang cocok. Cache tidak boleh dihapus selama linked di project.

6.4 Native property proof dan batas API

Scripting Guide mendokumentasikan Track.insertClip(), Sequence.insertClip(), TrackItem.components serta ComponentParam.areKeyframesSupported(), setTimeVarying(), addKey() dan setValueAtKey(). Namun keberhasilan untuk param tertentu dan ketepatan waktu keyframe tetap harus dibuktikan per build 24.x. Pengaturan effects/transition baru yang tidak tersedia dalam official DOM tidak boleh diam-diam mengandalkan QE DOM sebagai dependency produksi; opsi alternatif adalah preset/MOGRT yang dapat dibuktikan, plugin effect SDK, atau PRERENDER.

7. Animation Engine - 21 preset, mode BOTH wajib

7.1 Aturan animasi yang dikunci

Setiap kemunculan gambar di setiap scene tepat satu pilihan preset. Pada fase IN dan OUT berlaku preset ID yang sama. "BOTH" bukan berarti IN dan OUT harus berupa frame identik terbalik; perilaku keluar mengikuti definisi EXIT dari preset yang sama di registry. GPT hanya memilih preset, speed, direction kompatibel; aplikasi menentukan durasi frame dan kurva. Tidak ada ENTER_EFFECT/EXIT_EFFECT dua pilihan.

7.2 Daftar preset yang harus didukung dan diuji

ID | PRESET | KELUARGA | IN 30FPS | OUT 30FPS | STATUS KELAYAKAN
R01 | Brush | Reveal | 39 | 9 | CALIBRATION REQUIRED
R02 | Ink | Reveal | 40 | 9 | CALIBRATION REQUIRED
R03 | Digital | Reveal | 24 | 7 | CALIBRATION REQUIRED
R04 | Spray Paint | Reveal | 42 | 9 | CALIBRATION REQUIRED
R05 | Sketch | Reveal | 42 | 10 | CALIBRATION REQUIRED
R06 | Gradient | Reveal | 33 | 8 | CALIBRATION REQUIRED
G01 | Rise | General | 21 | 8 | CALIBRATION REQUIRED
G02 | Pan | General | 21 | 8 | CALIBRATION REQUIRED
G03 | Fade | General | 15 | 7 | CALIBRATION REQUIRED
G04 | Pop | General | 16 | 7 | CALIBRATION REQUIRED
G05 | Wipe | General | 21 | 8 | CALIBRATION REQUIRED
G06 | Blur | General | 21 | 8 | CALIBRATION REQUIRED
G07 | Succession | General | 25 | 9 | CALIBRATION REQUIRED
G08 | Breathe | General | 30 | 9 | CALIBRATION REQUIRED
G09 | Baseline | General | 14 | 7 | CALIBRATION REQUIRED
G10 | Drift | General | 33 | 9 | CALIBRATION REQUIRED
G11 | Tectonic | General | 22 | 8 | CALIBRATION REQUIRED
G12 | Tumble | General | 24 | 9 | CALIBRATION REQUIRED
G13 | Neon | General | 20 | 7 | CALIBRATION REQUIRED
G14 | Scrapbook | General | 22 | 9 | CALIBRATION REQUIRED
G15 | Stomp | General | 17 | 7 | CALIBRATION REQUIRED

Durasi contoh di tabel adalah profil referensi pada dokumen V2 di speed MEDIUM, belum diverifikasi sebagai durasi asli Canva. Registry harus menautkan profile_id dan SHA-256, serta menyediakan nilai Speed FAST/SLOW yang eksplisit dan diuji. Jangan mengubah durasi jika klip terlalu singkat: laporkan konflik, minta keputusan revisi; bila policy tersertifikasi "fit-to-scene" disetujui pengguna, simpan audit per asset.

7.3 Registry runtime per preset

FIELD REGISTRY | WAJIB | KEGUNAAN
preset_id / display_name | YA | Enum stabil dan nama UI
in_frames/out_frames per speed | YA | Dua fase satu preset
direction_allowed | YA | Daftar arah yang betul-betul didukung
native_status | YA | VERIFIED / UNSUPPORTED / UNVERIFIED
prerender_status | YA | VERIFIED / UNSUPPORTED / UNVERIFIED
backend_selected | YA sebelum assembly | NATIVE atau PRERENDER saja
alpha_profile / cache_format | jika prerender | Format transparansi yang lulus tes Premiere
hash/version | YA | Reproduksibilitas dan mismatch detection
reference_diff | ketika diuji | Bukti visual vs video referensi

7.4 Pemilihan backend yang tidak merusak keputusan GPT

Backend dipilih oleh registry yang disertifikasi pada host, bukan GPT. Jika preset membutuhkan native tetapi native tidak terbukti, boleh menggunakan backend prerender hanya jika registry memiliki prerender VERIFIED dan fitur transparansi terbukti. Jika tidak ada backend yang terverifikasi, preflight FAIL; DILARANG mengganti preset, menurunkan intensitas tanpa izin, atau membuat black background.

7.5 Perilaku DOUBLE dan overlap animasi

Setiap aset pada DOUBLE mempunyai IN/HOLD/OUT sendiri yang dihitung dari start/end frame. Kedua animasi boleh punya preset berbeda, tetapi masing-masing tetap BOTH. Delay/stagger berasal dari EDIT_PLAN; tidak direkayasa oleh Animation Engine. Layer B tidak boleh mengubah base transform A. Hilangkan frame jitter ketika OUT dekat akhir scene dengan memastikan output frame dan alpha final; jangan memotong dialog audio.

8. Strategi native versus prerender FFmpeg

8.1 Matrik backend kandidat (belum klaim berhasil)

FAMILY/PRESET | PRIORITAS | PROOF OF CONCEPT
FADE / PAN / RISE / POP / BREATHE / DRIFT | Uji NATIVE dahulu | Motion/Opacity keyframe, timing IN dan OUT, hasil editable
WIPE / BLUR / BASELINE / SUCCESSION | NATIVE jika effect API dapat diakses; jika tidak PRERENDER | Kemampuan menambah komponen dan mempertahankan alpha
TECTONIC / TUMBLE / SCRAPBOOK / STOMP | Uji NATIVE Motion rotation dahulu | Rotation/position motion blur dan overlay jika dibutuhkan
BRUSH / INK / SKETCH / SPRAY_PAINT | PRERENDER kandidat awal | Mask RGBA alpha berurutan, fallback native jika terbukti
DIGITAL / GRADIENT / NEON | Tentukan via test | Mask/glow/flicker, alpha dan kualitas preview

8.2 Kontrak media prerender yang harus dibuktikan

FFmpeg worker menghasilkan overlay visual dengan alpha (transparan di luar gambar), resolusi, timebase, durasi frame persis sesuai instance aset. Jangan membuat video dengan background hitam yang kemudian di-key sebagai solusi default.

Pertama uji kandidat QuickTime MOV RGBA (codec/profile yang didukung Premiere Windows) dan PNG sequence dengan alpha. Pilihan final ditentukan dari tes impor, decoding, durasi dan alpha pada Premiere 24.x pengguna.

Jangan mengklaim semua alpha QuickTime codec didukung oleh Premiere 2024. Jika MOV alpha gagal, boleh memakai image sequence RGBA bila lulus uji. Jika keduanya gagal, efek PRERENDER berstatus UNSUPPORTED dan preflight tidak mengizinkan assembly.

Prerender boleh tetap berupa klip terpisah yang dapat dipindah, trim, crop luar atau diberi transform tambahan. Isi animasinya baked; untuk mengubah gerakan harus membuat ulang cache dari registry.

File cache dibuat per (project revision, asset SHA, preset, speed, direction, start/end frame, alpha profile, worker version, registry hash); penamaan deterministik dan checksum setelah selesai.

Seluruh proses worker berjalan lokal, dengan timeout, cancellation, isolation, safe command arguments tanpa shell string, dan ruang disk minimal yang dicek di awal.

8.3 Native editable vs prerender editable - kontrak UI

ATRIBUT | NATIVE | PRERENDER
Geser/trim klip | BISA | BISA, sebatas durasi media
Ubah base transform | BISA | BISA, tergantung overlay alignment
Ubah keyframe gerakan | BISA jika API/parameter terbukti | TIDAK; harus regenerate cache
Performa timeline | Tergantung efek host | Tergantung codec/cache
Bukti alpha | Periksa intrinsic opacity/effects | Preview dengan checkerboard + probe alpha
Simpan project portable | Butuh PNG/audio/source | Butuh seluruh media source + cache prerender

8.4 Siklus hidup cache dan relink

Cache disimpan dalam folder proyek untuk menjaga link media .prproj. Jika lokasi proyek berubah, plugin menyediakan repair relink berbasis manifest dan hash; jangan membuat ulang animasi secara diam-diam dengan versi algoritma yang berbeda. Fitur "Rebuild cache" harus menampilkan daftar affected clips dan meminta konfirmasi penggantian. Installer tidak menghapus cache proyek.

9. Rancangan panel UI Premiere 2024

9.1 Prinsip desain

Panel dockable bergaya sederhana, Bahasa Indonesia, putih-biru, font kecil yang terbaca; bukan replika Filmora. Jendela Premiere tetap tempat timeline dan preview utama. Tidak ada panel AI chat dalam versi awal. Validasi dan hasil pemetaan lebih penting daripada dekorasi.

AREA PANEL | ISI | TOMBOL/STATUS
Header | Nama aplikasi, status PPRO 24.x, mode BOTH | Pemeriksaan host
Impor | EDIT_PLAN.json, ANIMATION_PLAN.json, root media | Pilih/Impor
Ringkasan | Jumlah scene, SINGLE/DOUBLE, aset, durasi, 21 preset registry | Refresh ringkasan
Preflight | Valid/invalid media, preset, alpha, SRT evidence | PERIKSA PROYEK
Scene Inspector | Scene ID, aset, timestamp, preset, backend, confidence | Lihat rincian
Assembly | Target sequence baru dan mode safe build | SUSUN TIMELINE OTOMATIS
Log/Audit | Tahap, jumlah clip, error actionable, link folder report | Buka laporan
Repair | Relink missing cache, regenerate FX yang terotorisasi | Repair (confirmation)

9.2 State mesin dan tombol

STATE | PERILAKU | APAKAH ASSEMBLY BOLEH
NO_PROJECT | Belum ada proyek | TIDAK
FILES_SELECTED | Dipilih, belum valid | TIDAK
PREFLIGHT_RUNNING | Validasi berjalan | TIDAK
NEEDS_REVIEW | Ada timing ambigu atau konflik | TIDAK
PREFLIGHT_FAIL | Error wajib, file atau preset hilang | TIDAK
READY | Seluruh dependency terbukti | YA
ASSEMBLING | Perubahan Premiere berjalan | TIDAK (anti duplikat)
INCOMPLETE | Host gagal sebagian | TIDAK, sampai repair/rebuild
ASSEMBLED | Sequence diverifikasi | Tidak otomatis ulang tanpa mode baru

9.3 Pesan error yang dipahami pengguna

Contoh: "Gagal: A003.png belum tersedia (Scene V002, frame 192). Tambahkan gambar tersebut ke folder assets lalu klik Periksa Proyek." Hindari istilah stack trace sebagai satu-satunya informasi. Selalu jelaskan file, scene/asset, penyebab dan tindakan berikutnya. Stack trace hanya di log developer.

10. Validasi, keamanan, rollback dan audit

10.1 Validasi berlapis

Schema statis kedua JSON: type, enum, required, tambahan field yang dilarang, duplicate IDs.

Semantik silang: project/revision, exact set (scene,asset), layout counts, direction registry, clip duration, locks.

Path keamanan: normalize, unicode/spasi, disallow path traversal proyek yang tidak diberi izin; tidak mengeksekusi nama path sebagai kode.

Media probe: decode PNG alpha, durasi audio/SRT, background MP4 jika required, metadata framerate, availability cache disk.

Host capability: PPRO 24.x, panel aktif, createNewSequence, importFiles, track control, property keyframe, alpha clip support.

Dry-run compile: daftar operasi per track tanpa mutasi project.

Commit host: buat sequence baru dan verifikasi hasil setiap fase; tandai partial state jika gagal.

10.2 Error codes minimum

KODE | KONDISI | RESPONS
E_JSON_SCHEMA | JSON tidak sesuai | Tolak impor
E_PLAN_PAIR | project/revision/asset tidak cocok | Tolak assembly
E_ANIM_MODE | mode != BOTH atau ada enter/exit split | Tolak; jangan autofix
E_ANIM_PRESET | Preset/direction tidak didukung | Tolak; jangan ganti efek
E_MEDIA_MISSING | SRT/audio/PNG/MP4 required tidak ditemukan | Tolak; file wajib
E_SRT_AMBIGUOUS | source_quote/occurrence tidak teridentifikasi | Needs review
E_HOST_UNSUPPORTED | Premiere bukan 24.x / API tidak valid | Tolak
E_HOST_SEQUENCE | Create sequence/track gagal | Mark INCOMPLETE
E_FX_BACKEND | Native dan prerender belum VERIFIED | Tolak effect
E_ALPHA_IMPORT | RGBA cache tampil opaque/black | Tolak effect
E_CACHE_MISSING | Cache linked terhapus | Repair/relink
E_HOST_PARTIAL | Host gagal setelah sebagian item dipasang | Sequence diberi label INCOMPLETE

10.3 Keamanan plugin dan audit data

JSON input diperlakukan sebagai data tak tepercaya: schema, batas jumlah scene/aset, kapasitas file, normalisasi path dan izin folder. Hindari menjalankan arbitrary shell, eval JSON sebagai JavaScript, set PlayerDebugMode permanen setelah packaging, mengubah registry sistem tanpa petunjuk/izin pengguna, atau mengunduh executable tersembunyi. Semua perintah FFmpeg dibangun sebagai arg list sanitasi; log tidak menyimpan rahasia atau kredensial.

Report minimal: host_version, project_id, JSON revision/hash, registry version/hash, media path/hash, job_id, managed sequence, clip count, native count, prerender count, alpha probes, per-scene timing checks, timestamps, warnings, errors, status. Jangan menyatakan CI TEST PASS sebagai pengganti visual test Premiere host.

10.4 Recovery dan preservasi edit

Pada failure: jangan secara otomatis menghapus project/sequences, jangan menghapus file media atau mengganti preset. Operator memilih Rebuild New Sequence, Repair Cache, atau Cancel. Penggantian versi mustahil jika hash berubah tanpa acknowledgement. Manual user edits ditandai sebagai diverged; reimport tidak overwrite tanpa backup .prproj dan konfirmasi.

11. Uji otomatis, pilot host nyata, dan acceptance

11.1 Lapisan test

JENIS | TEST MINIMUM | BUKTI
Parser contract | Valid/invalid dua JSON, hash, BOTH, direction, duplicate | Test suite lulus
Timing | 30fps integer, cue repeated, negative/overlap, long timeline | Frame report
Effect unit | 21 IN + 21 OUT memakai preset ID sama | Effect gallery dan expected frame
Host integration | Panel visible, import, clip insert, transform/keyframe | Screenshot/video dari PPRO 24.x
Transparency | MOV alpha, PNG sequence fallback; black background rejected | Checkerboard dan pixel comparison
Project lifecycle | New sequence; cancel; restart; reopen .prproj; relink | Before/after timeline capture
Scale/stress | 50, 100, 300+ scenes, unicode/spaces, memory/disk/cache | Host logs & timing
End-to-end | SRT+PNG+MP4 BG+audio -> Premiere -> manual edit -> export | Actual .prproj and exported MP4

11.2 Acceptance criteria AC01–AC30

AC | SYARAT PASS YANG DAPAT DIBUKTIKAN
AC01 | Panel CEP muncul dan membuka UI di Premiere Pro 2024 24.x pengguna.
AC02 | UI menampilkan exact build host dan runtime; menolak versi tak disertifikasi.
AC03 | EDIT_PLAN edit-plan-v2 valid dibaca tanpa migrasi diam-diam.
AC04 | ANIMATION_PLAN animation-plan-v1 dibaca; mode BOTH wajib.
AC05 | Tepat satu preset per pasangan scene/asset; tidak ada missing/extra.
AC06 | Preset 21 nama valid dan registry hash cocok.
AC07 | Effect IN dan OUT tidak pernah dipilih berbeda untuk aset yang sama.
AC08 | Speed dan direction sesuai registry; durasi dari registry.
AC09 | Scene timestamp frame integer 30 FPS; mismatch >1 frame FAIL.
AC10 | SRT Unicode, multiline dan occurrence phrase berulang teruji.
AC11 | Timing ambigu tidak diluluskan sebagai kata yang pasti.
AC12 | File wajib audio/SRT/PNG/background tidak ada -> FAIL.
AC13 | PNG transparan tetap benar dan label tidak terpotong.
AC14 | SINGLE memiliki 1 aset di posisi sesuai spesifikasi layout.
AC15 | DOUBLE dua aset independen dengan timing stagger benar.
AC16 | Sequence profil 1920x1080, 30fps diverifikasi oleh host.
AC17 | Background + narration dimasukkan tanpa audio background liar.
AC18 | Setiap clip/source item dapat dirunut ke asset ID dan path.
AC19 | FADE/PAN/WIPE BOTH terbukti pada pilot di host 24.x.
AC20 | 21/21 preset BOTH menghasilkan IN/HOLD/OUT visual sesuai registry.
AC21 | Native keyframes bisa diedit manual untuk yang ditandai NATIVE.
AC22 | Prerender alpha tampil transparan di Premiere; no black matte.
AC23 | Prerender tetap bisa dipindah/trim pada timeline; internal motion baked.
AC24 | Tidak ada efek fallback diam-diam dari preset yang diminta GPT.
AC25 | Assembly gagal tidak menghapus sequence/item edit manual.
AC26 | Retry tidak membuat clip ganda di sequence target yang sama.
AC27 | Reopen .prproj tetap online dan cache tidak hilang.
AC28 | Manajemen path Unicode, folder kosong, disk penuh dan cancel lulus.
AC29 | Media/proyek panjang diproses tanpa drift atau memory leak kritis.
AC30 | Pengguna dapat melakukan edit manual lalu ekspor MP4 via Premiere.

11.3 Matriks pilot minimal

PILOT | BAHAN | GATE
P0 | Premiere 24.x + CEP Hello World + host version | Panel/CSInterface/ExtendScript READY
P1 | 1 PNG alpha + audio + template 1080p/30fps | Native sequence & accurate clip
P2 | 3 PNG (SINGLE lalu DOUBLE) + SRT + 2 JSON | Exact frame, track, pairing
P3 | Fade/Pan/Wipe BOTH di 15–30 detik | Editable native atau explicit backend
P4 | 1 kompleks (Brush) alpha test MOV/PNG sequence | Alpha host supported + cache stable
P5 | 21 effect clips gallery (IN & OUT) | 21/21 PASS
P6 | Long narration 100+ scene + user manual edit | Reopen/export PASS

12. Roadmap kerja, gate, risiko dan handoff

12.1 Tahap implementasi berurutan

TAHAP | PEKERJAAN | GATE
STEP00 | Audit V3, keputusan scope, lisensi open-source, kesiapan host | G0 PLANNING PASS
STEP01 | Arsitektur repo CEP + JSX + worker, schema dan fixtures | G1 SCHEMA PASS
STEP02 | Desain UI statis dan review gambar, satu DOCX referensi UI | STOP sampai user menyetujui UI
STEP03 | Panel CEP minimal yang terbuka di PPRO 2024 | G3 REAL HOST PASS
STEP04 | Validation/compile dua JSON, probe media, dry-run | G4 CONTRACT PASS
STEP05 | Sequence assembly SINGLE/DOUBLE 30fps, audio/bg | G5 TIMELINE PASS
STEP06 | Native Fade/Pan/Wipe BOTH, baca keyframe balik | G6 NATIVE PASS
STEP07 | RGBA prerender proof dan cache/relink | G7 ALPHA PASS
STEP08 | 21 preset lengkap, gallery per effect | G8 21/21 PASS
STEP09 | Stress/long project, manual edits, reopen/export | G9 END-TO-END PASS
STEP10 | Installer/paket plugin, instruksi per-user, checksum | G10 RELEASE PASS

12.2 Gate STOP wajib

Pengerjaan awal harus mendahulukan pembuktian pilot host dan desain UI. Tahap UI menghasilkan prompt visual kemudian STOP untuk persetujuan gambar final sebelum coding. Sesudah disetujui, berkas source-of-truth planning + referensi UI berada di repo sebelum implementasi. STEP selanjutnya hanya ketika semua gate masuk PASS; kemajuan simulasi/tes unit tidak menjadi pengganti host 24.x nyata. Portable/installer akhir, bukan di awal. Merge GitHub tidak otomatis.

12.3 Risiko kunci

RISIKO | DAMPAK | MITIGASI
CEP pada 2024 lama | Panel runtime/dll lama rentan perubahan | Kunci host 24.x; smoke real host; dokumentasi install
Scripting API effects terbatas | Preset tidak native | Proof per preset; verified FFmpeg alpha alternate
FFmpeg alpha codec tidak compatible | Overlay hitam/hilang | Premiere alpha host matrix; PNG sequence fallback
Timing SRT kalimat bukan kata | Gambar terlambat/cepat | Evidence serta review estimasi
JSON prompt mengandung efek split | BOTH rusak | Fail-closed schema
Host split timeline/perubahan manual | Hasil dobel atau menimpa edit | CREATE_NEW_SEQUENCE, audit clip map
Cache offline setelah pindah folder | Media missing | Manifest + relink + package project
FFmpeg lisensi/codec | Distribusi tak patuh | Audit LGPL/GPL build dan codec; jangan bundel sembarangan
Rilis tanpa Premiere host | Klaim sukses palsu | GATE real-host + screenshot .prproj + export

12.4 Handoff ASTRA (rencana) → SOL (implementasi)

ASTRA menjaga master DOCX ini, daftar kebutuhan/risiko, schema data, matriks efek, kriteria acceptance dan gate. SOL tidak mengubah semantik dari prompt: hanya mengimplementasikan adapter/manifests dan host plugin. Kode diperiksa dengan tes otomatis dan uji Premiere nyata; semua perubahan kontrak/arsitektur signifikan kembali ke DOCX keputusan. Setelah tiap tahap, laporkan PASS/FAIL, evidence, next step, dan pertanyaan blocking tanpa mengulang pekerjaan yang sudah selesai.

13. Lampiran implementasi dan kontrak uji

13.1 EDIT_PLAN.json v2 - contoh yang tetap diterima

Contoh diambil dari kontrak V2 sebagai alat tes. Field render tetap ada untuk kompatibilitas tetapi tidak digunakan plugin untuk encoding final. SHA placeholder harus diganti dengan hash media asli sebelum preflight. Bukan bukti source SRT produksi.

{
  "schema_version": "edit-plan-v2",
  "project_id": "DEMO_001",
  "revision": 2,
  "canvas": {
    "width": 1920,
    "height": 1080,
    "fps_num": 30,
    "fps_den": 1
  },
  "sources": {
    "srt": {
      "path": "narasi.srt",
      "sha256": "<SHA256_SRT>"
    },
    "audio": {
      "path": "narasi.wav",
      "sha256": "<SHA256_AUDIO>"
    },
    "background": {
      "path": "background.mp4",
      "required": true,
      "audio_policy": "MUTE"
    }
  },
  "profiles": {
    "layout_id": "CANVA_REFERENCE_V1",
    "layout_hash": "<SHA256_LAYOUT>"
  },
  "assets": {
    "A001": {
      "path": "assets/A001.png"
    },
    "A002": {
      "path": "assets/A002.png"
    },
    "A003": {
      "path": "assets/A003.png"
    }
  },
  "scenes": [
    {
      "scene_id": "V001",
      "source_segment_ids": [
        "N0001"
      ],
      "narration_quote": "Narasi pengantar topik.",
      "layout_type": "SINGLE",
      "start_frame": 0,
      "end_frame": 150,
      "transition_policy": "CUT",
      "assets": [
        {
          "asset_id": "A001",
          "slot": "SINGLE",
          "start_frame": 0,
          "end_frame": 150,
          "entry_evidence": {
            "cue_id": 1,
            "accuracy": "EXACT_CUE"
          }
        }
      ]
    },
    {
      "scene_id": "V002",
      "source_segment_ids": [
        "N0002",
        "N0003"
      ],
      "narration_quote": "Narasi membahas dua pihak.",
      "layout_type": "DOUBLE",
      "start_frame": 150,
      "end_frame": 330,
      "transition_policy": "CUT",
      "assets": [
        {
          "asset_id": "A002",
          "slot": "LEFT",
          "start_frame": 150,
          "end_frame": 330,
          "entry_evidence": {
            "cue_id": 2,
            "accuracy": "EXACT_CUE"
          }
        },
        {
          "asset_id": "A003",
          "slot": "RIGHT",
          "start_frame": 192,
          "end_frame": 330,
          "entry_evidence": {
            "cue_id": 3,
            "accuracy": "EXACT_CUE"
          }
        }
      ]
    }
  ],
  "render": {
    "codec": "libx264",
    "pixel_format": "yuv420p",
    "audio_codec": "aac",
    "audio_policy": "NARRATION_ONLY",
    "subtitles": "NONE",
    "output_path": "output/video_final.mp4"
  },
  "validation": {
    "status": "READY",
    "issues": []
  },
  "provenance": {
    "scene_plan_schema": "asset-scene-plan-v2",
    "timing_source": "SRT_EXACT_CUE",
    "ai_decision_mode": "A_JSON_ALL"
  }
}

13.2 ANIMATION_PLAN.json v1 - contoh BOTH wajib

Perhatikan hanya preset, speed, direction, locked; tidak terdapat enter_effect atau exit_effect. Prerender/native adalah keputusan registry host bukan field keputusan GPT.

{
  "schema_version": "animation-plan-v1",
  "project_id": "DEMO_001",
  "edit_plan_revision": 2,
  "revision": 1,
  "mode": "BOTH",
  "animation_profile": {
    "id": "CANVA_BOTH_21_V1",
    "sha256": "<SHA256_ANIMATION_REGISTRY>"
  },
  "project_seed": 827314,
  "decisions": [
    {
      "scene_id": "V001",
      "asset_id": "A001",
      "preset": "BRUSH",
      "speed": "MEDIUM",
      "direction": "LEFT_TO_RIGHT",
      "locked": true
    },
    {
      "scene_id": "V002",
      "asset_id": "A002",
      "preset": "PAN",
      "speed": "MEDIUM",
      "direction": "FROM_LEFT",
      "locked": true
    },
    {
      "scene_id": "V002",
      "asset_id": "A003",
      "preset": "WIPE",
      "speed": "MEDIUM",
      "direction": "RIGHT_TO_LEFT",
      "locked": true
    }
  ],
  "provenance": {
    "source": "GPT_ANIMATION_DIRECTOR",
    "registry": "GENERAL_15_REVEAL_6",
    "decisions_are_final": true
  }
}

13.3 Format assembly report usulan

{
  "schema_version": "premiere-assembly-report-v1",
  "project_id": "DEMO_001",
  "host": {
    "application": "PPRO",
    "version": "24.x (actual required)"
  },
  "mode": "CREATE_NEW_SEQUENCE",
  "edit_plan_revision": 2,
  "animation_plan_revision": 1,
  "scene_count": 2,
  "expected_asset_instances": 3,
  "assembled_asset_instances": 0,
  "native_effect_count": 0,
  "prerender_effect_count": 0,
  "status": "NOT_TESTED",
  "issues": [
    {
      "code": "E_HOST_UNTESTED",
      "message": "Contoh perencanaan; uji real Premiere 2024 belum dilaksanakan"
    }
  ]
}

13.4 Bukti wajib per gate

G0–G1: source specification, schema + fixtures yang lulus tes dan catatan lisensi worker.

G2: gambar UI final disetujui, referensi UI DOCX dan seluruh rencana tersedia sebelum coding.

G3: video/screenshot panel di Premiere 2024 yang menampilkan build/CSXS versi aktual.

G5: sequence Premiere minimal 3 PNG beserta report start/end frame dan saved .prproj.

G6–G8: galeri preset; pilihan backend per preset; hasil keyframe readback atau alpha proof.

G9: project panjang, reopened linked media, clip bisa diubah manual, Premiere export MP4.

G10: install/uninstall package dengan manifest/lisensi/checksum, versi dan panduan Bahasa Indonesia.

13.5 Sumber teknis publik yang digunakan (untuk audit developer)

REFERENSI | URL
Adobe Premiere developer portal CEP/UXP | https://developer.adobe.com/premiere-pro/
Adobe UXP 25.6 release | https://blog.developer.adobe.com/en/publish/2025/12/uxp-arrives-in-premiere-a-new-era-for-plugin-development
Adobe CEP Samples PProPanel | https://github.com/Adobe-CEP/Samples/tree/master/PProPanel
Adobe CEP 2024 runtime developer discussion | https://community.adobe.com/questions-729/html-extension-on-premiere-2024-1407199
Scripting Guide: Sequence | https://ppro-scripting.docsforadobe.dev/sequence/sequence/
Scripting Guide: Track | https://ppro-scripting.docsforadobe.dev/sequence/track/
Scripting Guide: TrackItem | https://ppro-scripting.docsforadobe.dev/item/trackitem/
Scripting Guide: ComponentParam | https://ppro-scripting.docsforadobe.dev/sequence/componentparam/
Adobe CEP to UXP 2026 schedule | https://helpx.adobe.com/creative-cloud/apps/integration-with-other-apps/manage-plugins/cep-uxp-plugin-transition.html

Catatan: beberapa API di Scripting Guide dan source sample mengikuti revisi terbaru; versi yang tercantum pada dokumentasi belum membuktikan perilaku yang identik di Premiere 24.x. Implementasi harus menyimpan hasil pembacaan dan verifikasi pada host aktual.

13.6 Checklist review final sebelum menulis kode

User mengonfirmasi Adobe Premiere Pro 2024 tetap target utama.

User menyetujui hybrid native-first + FFmpeg untuk efek kompleks dan keterbatasan edit internal prerender.

User mengonfirmasi animasi BOTH satu preset per kemunculan gambar, dua JSON terpisah.

Skema input EDIT_PLAN v2 + ANIMATION_PLAN v1, registry profile dan fail-closed disetujui.

Dokumen source lama lengkap, terutama layout/crop dan durasi 21 efek, disiapkan untuk handoff.

Pembuktian host 24.x dan alpha disusun sebelum janji 21/21 efek.

Tahap UI berhenti pada prompt sampai seluruh gambar disetujui; jangan coding prematur.

KESIMPULAN V3

Plugin Adobe Premiere 2024 menggantikan renderer mandiri sebagai jalur utama. Sistem GPT tetap menghasilkan dua JSON terpisah; setiap gambar menerima satu preset BOTH dari 21 efek. Plugin menyusun sequence native Premiere yang bisa diedit manual. Efek kompleks hanya boleh menjadi media RGBA prerender setelah alpha/codec kompatibilitas dan perilaku timeline benar-benar lulus uji Premiere 2024. Semua fitur yang belum diuji dinyatakan UNVERIFIED - bukan PASS.
