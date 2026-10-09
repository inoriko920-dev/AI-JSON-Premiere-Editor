# Rencana implementasi ASTRA untuk SOL

## 01 Rencana implementasi ASTRA untuk SOL

AI JSON Premiere Editor
Dokumen STEP00 • Revisi A1 • 9 Oktober 2026

Dokumen ini mengubah Master Plan V3 menjadi urutan kerja yang dapat dilanjutkan SOL atau AI lain. Sasaran akhirnya adalah panel Adobe Premiere Pro 2024 pada Windows 11 yang membaca dua JSON, menyusun sequence, memasang animasi BOTH, lalu menyerahkan hasil kepada pengguna untuk edit manual dan ekspor melalui Premiere.

Status paket ini adalah PLANNING COMPLETE WITH OPEN PREREQUISITES. Penulisan rencana selesai; izin coding, persetujuan UI, kompatibilitas host, dan kualitas 21 preset belum lulus. Tidak ada aplikasi, installer, atau uji Premiere yang diklaim selesai dalam handoff ini.

Keputusan yang tidak boleh berubah
- Host utama adalah Premiere Pro 2024 major 24. Panel menggunakan CEP dan ExtendScript; FFmpeg hanya untuk media alpha per aset yang membutuhkan prerender.
- EDIT_PLAN versi edit-plan-v2 dan ANIMATION_PLAN versi animation-plan-v1 tetap terpisah. Satu keputusan animasi untuk setiap pasangan scene_id dan asset_id; mode BOTH wajib.
- Preset IN dan OUT adalah preset yang sama. Durasi, perilaku keluar, dan arah berasal dari registry; SOL tidak memilih ulang animasi GPT.
- Timeline hasil harus aman untuk diedit. Gunakan sequence baru; jangan menimpa hasil manual pengguna.
- Tampilan panel menggunakan Bahasa Indonesia, putih dan biru. Timeline serta preview tetap milik Premiere; tidak ada AI chat atau renderer desktop pengganti.

Hasil yang diserahkan
Master V3 asli dan salinan teksnya; DOCX ini beserta versi Markdown; matriks AC01–AC30; daftar 21 preset; daftar blocker; status proyek; dan instruksi pembuka untuk SOL di 00_START_HERE.md. Tidak ada kode produk atau schema runtime yang dibuat pada STEP00.

Langkah berikutnya adalah STEP01 perencanaan kontrak. STEP02 membuat prompt UI lalu wajib berhenti sampai gambar final disetujui dan disatukan dalam DOCX referensi UI. Semua dokumen planning yang berlaku harus berada di repo sebelum SOL menulis kode.

## 02 Audit sumber dan keputusan menggunakan komponen lama

Baseline repository
Pada audit 9 Oktober 2026, API GitHub menyatakan AI-JSON-Premiere-Editor kosong dengan pesan Git Repository is empty. Belum ada commit sumber, AGENTS, branch implementasi, tes, atau hasil build yang dapat diperiksa. Pengguna secara eksplisit meminta rencana dimasukkan ke GitHub; otorisasi ini mencakup publikasi dokumen planning sekarang.

Sumber pengguna
Master V3 yang dilampirkan dibaca seluruh paragraf dan 28 tabelnya. Dokumen asli disalin tanpa perubahan ke docs/source. SHA-256 dicatat di SOURCE_AUDIT.md dan CHECKSUMS.sha256. Lampiran JSON pada V3 adalah contoh dengan placeholder hash, bukan fixture produksi yang sudah valid.

Sumber yang belum disediakan
Master V2, dokumen durasi 21 animasi, spesifikasi Layout Zoom dan Penempatan Gambar, spesifikasi Animation Engine General Reveal, Prompt 1 bersama Prompt_panel, dan Prompt 4 belum tersedia dalam input sesi atau repo kosong. Jangan menyatakan dokumen tersebut telah dibaca. Prioritas pengadaan: layout/crop dan perilaku serta durasi semua speed. Jika pengguna memilih menggantinya, ASTRA harus membuat spesifikasi pengganti dan meminta persetujuan eksplisit.

Keputusan reuse
Pencarian GitHub terbatas dengan kata Premiere CEP JSON timeline tidak menemukan produk yang dapat langsung diadopsi. Ini bukan bukti bahwa tidak ada produk lain. Kandidat dasar terkuat yang diperiksa adalah Adobe-CEP/Samples/PProPanel, dengan lisensi MIT pada root. Ambil hanya bridge, pola panel, dan contoh API yang diperlukan setelah audit file serta lisensi masing-masing; jangan fork seluruh demo beserta operasi contoh yang tidak relevan.

Snapshot referensi
Commit Adobe Samples yang diamati adalah e4946b73ac1e566dced8e95dba10811c31036927. README-nya sudah membahas 25.6; karena itu contoh terbaru tidak boleh dianggap tersertifikasi untuk 24.x. CEP-Resources menyediakan bahan runtime; kecocokan CSXS harus dideteksi dari host aktual. Belum ada kode pihak ketiga yang disalin ke repo ini.

Lisensi produk dan dependency
Jangan menetapkan lisensi seluruh proyek atas nama pengguna. Catat kandidat dependency beserta versi, URL, lisensi, hash, notices, dan keputusan distribusi. FFmpeg memerlukan pemeriksaan build flags dan lisensi binary yang benar-benar dipilih; keputusan bundling final berada di STEP10.

## 03 Arsitektur yang harus diimplementasikan

Batas modul
- panel adalah CEP HTML CSS JavaScript. Modul ini mengelola pilihan file, state, laporan, progress, dan pemanggilan bridge. Ia tidak menghitung ulang keputusan animasi atau memutasi timeline lewat jalur lain.
- core adalah validator dan compiler lokal. Rekomendasi ASTRA adalah Python terpaket sebagai helper Windows, dengan versi runtime serta dependency dikunci setelah pilot. Host JSX tetap ECMAScript 3. Node bawaan CEP, jika dipakai, hanya untuk bridge proses yang dibuktikan.
- host adalah adapter JSX dengan daftar operasi terbatas: inspectHost, importMedia, createManagedSequence, placeClips, applyNativePreset, readbackSequence, dan markIncomplete. Nama ini merupakan kontrak usulan, bukan klaim metode API Adobe tersedia langsung.
- worker menghasilkan overlay RGBA untuk satu asset instance. Media alpha harus siap dan diverifikasi sebelum mutasi timeline; core mencatat format, hash, dan jumlah frame.
- registry menyimpan identitas preset, speed, direction, kurva, backend tersertifikasi, dan referensi bukti. Registry kreatif dipisahkan dari capability mesin.

Aliran data
Panel memilih dua JSON dan root media. Core menghasilkan snapshot input, validasi, dan rencana operasi deterministik. Worker menyiapkan cache yang diperlukan. Preflight READY hanya diberikan setelah seluruh dependency tersedia. Adapter membangun sequence baru lalu membaca hasil kembali. Laporan akhir menghubungkan setiap clip dengan scene dan asset asal.

Kontrak komunikasi
Gunakan envelope version, request_id, job_id, operation, manifest_path, expected_manifest_hash. Respons berisi request_id, status, result atau error dengan code, message, scene_id, asset_id, dan retryable. Satu job mutasi aktif per proyek. Callback dengan ID lama dibuang. Timeout tidak boleh ditafsirkan sebagai operasi pasti gagal: inspeksi jurnal dan host sebelum retry.

Keamanan bridge
JSON selalu data. Hindari eval terhadap JSON dan interpolasi nama file menjadi kode. Panel hanya memanggil wrapper JSX tetap, dengan path yang di-escape dan divalidasi ulang. JSX membaca manifest lokal dalam folder kerja yang diizinkan. Pilih parser JSON yang kompatibel ES3 dan audit lisensinya. Helper memakai executable tetap dan argument list tanpa shell. Tidak ada remote script, unduhan executable diam-diam, atau layanan publik.

Struktur target setelah coding dibuka
CSXS untuk manifest; panel untuk UI; host untuk adapter; core/schema dan core/registry untuk kontrak; worker untuk preflight, compiler dan FX; tests untuk fixture dan tes; packaging untuk paket; docs/evidence untuk bukti. Struktur ini belum dibuat sebagai implementasi pada STEP00.

## 04 Kontrak input dan hasil compiler

Validasi schema
EDIT_PLAN mempertahankan project_id, revision, canvas, sources, profiles, assets, scenes, dan field kompatibilitas V2. ANIMATION_PLAN mempertahankan project_id, edit_plan_revision, revision, mode, animation_profile, project_seed, decisions, dan provenance. Implementasikan schema hanya setelah membaca kontrak V2 atau spesifikasi pengganti yang disetujui; jangan memperketat field lama secara sembarang berdasarkan satu contoh V3.

Invarian yang sudah final
project_id harus sama dan edit_plan_revision harus cocok. Semua scene_id unik, referensi asset harus ada, dan set pasangan scene/asset sama persis dengan set keputusan animasi. Duplikat, missing, dan extra ditolak. Dalam satu scene asset_id tidak boleh ambigu. SINGLE satu slot SINGLE; DOUBLE tepat LEFT dan RIGHT dengan dua asset_id berbeda.

mode harus BOTH. Tolak field enter_effect, exit_effect, enter_direction, exit_direction, in_ms, out_ms pada keputusan animasi. Speed hanya SLOW, MEDIUM, FAST dengan angka registry yang sudah ditetapkan. Direction harus ada dalam daftar allowed untuk preset tersebut. locked dan provenance tidak boleh diubah plugin; requirement nilai true perlu dibekukan di STEP01 sesuai kontrak asli. project_seed bukan izin untuk random ulang preset.

Identitas dan hash
V3 memakai R01 atau G01 pada tabel dan BRUSH atau PAN pada JSON. Rekomendasi kontrak: R01/G01 sebagai catalog_id; BRUSH/PAN sebagai preset key di JSON. STEP01 membekukan mapping tanpa mengganti input. Hash profile memverifikasi byte artefak profile yang disimpan. Hash compiler memakai serialisasi kanonis yang spesifikasinya dibekukan di STEP01; jangan mencampur hash byte mentah dengan hash semantik tanpa label.

Manifest internal usulan
Simpan manifest_version, input_hashes, revisions, layout_hash, registry_hash, capability_profile_hash, compiler_version, job_id, sequence_profile, ordered_operations, dan expected_readback. Tiap instance memuat instance_key, scene_id, asset_id, source_path/hash, track, timeline start/end, source in/out, base transform, preset, speed, direction, phase frames, backend, dan cache_path/hash bila ada.

Kompatibilitas dan hasil
render pada EDIT_PLAN adalah legacy output hint; tampilkan INFO/DEPRECATED_RENDER_HINT dan jangan menjalankan encoding final. validation.status dari JSON tidak mengalahkan validasi aktual. Output normal meliputi preflight-report, compiled-manifest, journal, clip-map dan assembly-report. Dokumen ini merencanakan format; versi schema formal disahkan pada STEP01 dan dites pada STEP04.

## 05 Timing layout media dan urutan komposit

Waktu
Profil awal dibatasi 1920×1080 dengan fps_num 30 dan fps_den 1. Seluruh interval adalah [start_frame,end_frame). Audio tidak dipotong atau di-retime per scene. Usulan pembulatan timestamp nonnegatif adalah nearest frame dengan tie menuju atas, dihitung memakai bilangan rasional; contoh 1000 ms menjadi 30 frame. Bekukan kebijakan ini di STEP01 dan uji batas setengah frame.

Konversi host
Pisahkan frame sequence, source in/out, dan waktu keyframe. Premiere ticks disimpan sebagai string desimal pada bridge jika melebihi integer aman JavaScript. Nilai tick per detik serta ruang koordinat waktu keyframe harus dibuktikan melalui pilot pada build host, bukan disimpulkan dari display timecode. Readback clip idealnya tepat frame; selisih lebih dari satu frame pasti FAIL menurut V3. Selisih sampai satu frame tetap dicatat dan hanya diterima untuk alasan decoder yang tersertifikasi, bukan dibulatkan diam-diam.

SRT dan evidence
Uji UTF-8 BOM, Unicode, multiline, cue berulang, format rusak, occurrence, serta source_span. EXACT_CUE hanya membuktikan batas cue yang direferensikan. EXACT_WORD memerlukan data kata yang benar-benar diverifikasi. Estimasi memerlukan review yang tercatat dengan hash input; UNRESOLVED tidak boleh READY. Perubahan JSON atau SRT membatalkan hasil review sebelumnya. Waktu dialog tidak boleh ditebak atau digeser untuk mengakomodasi efek.

Layout
Ukuran SINGLE, posisi LEFT/RIGHT, anchor, crop, safe area, label baked, dan aturan zoom menunggu dokumen layout. Jangan mengisi angka berdasarkan selera SOL. Compiler nantinya menghasilkan transform absolut yang deterministik dan diuji dengan golden image. Untuk prerender, tentukan apakah overlay lokal atau full canvas; jangan menerapkan transform layout dua kali. Pilot memilih satu konvensi yang terdokumentasi sebelum produksi.

Media dan track
V1 background, V2 SINGLE atau LEFT, V3 RIGHT, A1 narasi. V4 label dan V5 subtitle serta A2 musik hanya bila kebijakan input memintanya. Latar required harus ada dan dapat didekode. Audio background dibisukan, termasuk audio linked saat insert. Loop background memakai durasi source nyata dan trim klip terakhir tanpa celah. Audio asli dan panjang sequence dicocokkan; mismatch yang belum memiliki policy masuk NEEDS_REVIEW.

Urutan operasi
Gunakan strategi penempatan yang terbukti tidak menimbulkan ripple. Template sequence dengan track yang cukup menjadi kandidat bila official DOM tidak dapat menambah track. Gagal menyediakan track atau timebase harus menghentikan build; QE DOM bukan jalan pintas produksi.

## 06 Registry dan pembuktian 21 preset BOTH

Registry adalah kontrak visual
Preset bukan sekadar nama. Setiap entri perlu catalog_id, preset key, versi, definisi IN/HOLD/OUT, duration per speed, allowed directions, easing, opacity/mask, reference hash, serta batas durasi minimum. Angka MEDIUM dari V3 disalin ke PRESET_MATRIX.csv sebagai REFERENCE_UNCALIBRATED. FAST dan SLOW belum memiliki nilai; jangan membuat multiplier sementara lalu menyebutnya final.

Pemilihan backend
Native dan prerender memiliki status terpisah UNVERIFIED, VERIFIED, atau UNSUPPORTED per build host dan versi algoritma. Backend resolver hanya memilih dari capability yang sudah dibuktikan, dengan prioritas native. Resolusi ini tidak boleh mengganti preset yang dipilih GPT. Profil sertifikasi mencakup exact host build, locale, effect matchName, worker hash, codec, pixel format, dan bukti visual. Pembaruan salah satu komponen membatalkan sertifikasi yang relevan.

Kandidat awal
Fade, Pan, Rise, Pop, Breathe, dan Drift diuji dengan Motion/Opacity. Wipe, Blur, Baseline, dan Succession memerlukan pembuktian parameter/effect; bila native tidak dapat dibuktikan, gunakan prerender yang dinyatakan eksplisit. Tectonic, Tumble, Scrapbook, dan Stomp menguji transform kompleks. Brush, Ink, Spray Paint, dan Sketch adalah kandidat mask prerender. Digital, Gradient, dan Neon diputuskan setelah percobaan. Semua masih UNVERIFIED.

Pembagian fase
Untuk instance dengan N frame, hitung IN, HOLD, OUT dari registry dan batas instance; N harus cukup untuk fase wajib. Detail apakah endpoint dihitung sebagai sample inklusif dibekukan dalam kontrak efek agar tidak terjadi off-by-one. Frame terakhir yang ditampilkan adalah end_frame minus satu. BOTH tidak berarti OUT selalu pembalikan IN. Klip pendek harus FAIL dengan pesan konflik durasi, bukan efek dipercepat diam-diam.

Galeri dan toleransi
Minimal setiap preset memiliki galeri MEDIUM dengan latar checkerboard, latar terang, dan latar gelap. Namun 21 klip saja tidak menyertifikasi semua pilihan: tiap kombinasi speed/direction yang advertised harus diuji atau ditandai tidak didukung. Capture awal, puncak IN, HOLD, awal OUT, dan frame akhir; periksa clipping, alpha fringe, label dan overlap DOUBLE. Pembandingan visual merujuk sumber pengguna; V3 tidak menuntut replika pixel-identik Canva.

Aturan PASS
Simpan proof native keyframe readback atau proof alpha import, hasil lihat manusia, hash media, dan kemampuan manual edit. Wipe boleh memakai prerender pada pilot P3; laporkan native Fade/Pan terpisah dan Wipe backend sebenarnya. Jangan memberi G6 NATIVE PASS untuk Wipe baked.

## 07 State keselamatan transaksi dan pemulihan

State panel
NO_PROJECT → FILES_SELECTED → PREFLIGHT_RUNNING → READY atau NEEDS_REVIEW atau PREFLIGHT_FAIL. Dari READY masuk ASSEMBLING lalu ASSEMBLED atau INCOMPLETE. Perubahan file, profile atau host membatalkan READY. Tombol SUSUN TIMELINE OTOMATIS hanya aktif pada READY, project tersimpan, dan snapshot masih sama. Klik ganda, panel reload dan callback lama tidak boleh membuat job kedua.

Tahapan transaksi
Validasi dan hash semua input; dry run; siapkan cache; cek snapshot sekali lagi; pastikan project tersimpan dan konfirmasi tindakan build di panel; buat job journal; buat sequence baru bernama AI_JSON dengan project, revision dan job ID; impor media; susun layer; pasang efek; readback; tulis laporan. Project tidak diasumsikan memiliki transaksi atomik atau undo sempurna.

Proteksi hasil manual
Tidak ada UPDATE_EXISTING pada rilis awal. Retry yang diminta pengguna membuat sequence baru; tidak menambah klip ke target yang sama. Simpan ownership berdasarkan ID yang stabil dan jurnal, bukan nama track saja. Jangan menghapus sequence lama, media, atau bin pengguna. Clip yang bergeser manual dianggap diverged. Cancel menghentikan operasi berikut pada batas aman dan melaporkan sequence parsial tanpa cleanup destruktif.

Jurnal dan crash
Tulis niat operasi sebelum mutasi dan hasil setelah readback. Setelah crash, gunakan job_id serta inspeksi host untuk menentukan apa yang benar-benar terjadi. Status UNKNOWN bukan izin mengulang insert. Report memuat expected dan actual counts, per-clip frame delta, host exact build, input hashes, registry, timestamps, warnings, dan error. Sukses UI tidak boleh mendahului verifikasi host.

Cache
Cache berada di folder proyek dan tidak dihapus saat uninstall. Key memasukkan asset hash, revision, preset, speed, direction, frame span, profile alpha, layout bila dirender, seed bila relevan, registry dan worker version. Tulis file sementara lalu rename atomik setelah validasi frame/alpha/hash. Disk penuh, timeout dan cancel tidak boleh menghasilkan cache berstatus valid. Hindari dua worker menulis key sama secara bersamaan.

Path dan repair
Normalisasi path tanpa menghilangkan Unicode. Tolak traversal, junction/symlink yang keluar root tanpa otorisasi, karakter kontrol, dan input berukuran di luar limit yang dibekukan STEP01. File luar root hanya jika dipilih pengguna dan tercatat. Relink memerlukan hash cocok. Rebuild cache menampilkan affected clips, meminta konfirmasi, dan tidak menimpa cache lama yang masih linked. Missing required file menghentikan proses sebelum mutasi timeline.

## 08 Rencana UI dan gerbang persetujuan

Tujuan desain
Panel dockable harus membantu pengguna awam memilih input, memahami kesalahan, dan menyusun timeline. Tampilan putih-biru, label Bahasa Indonesia, font ringkas yang terbaca. Ukuran kerja kandidat untuk review adalah panel 420×760 dan 760×900; ukuran minimum final ditetapkan setelah gambar dan pilot docking. Timeline dan playback tidak dibuat ulang di dalam panel.

Layar yang harus dirancang pada STEP02
- UI01 Import dan host: exact versi Premiere, status dukungan, dua pemilih JSON, folder media, ringkasan sumber, tombol Periksa Proyek.
- UI02 Preflight gagal atau perlu review: daftar error dengan file, scene/asset, waktu, penyebab dan tindakan. Filter tidak boleh menyembunyikan blocking error dari ringkasan.
- UI03 Ready dan Scene Inspector: scene SINGLE/DOUBLE, instance, frame, preset BOTH, speed, direction, backend, dan confidence. Tampilkan perbedaan Native editable dan Prerender baked.
- UI04 Assembly: progress per fase, current scene, job ID pendek, cancel aman, tombol susun nonaktif. Progress perkiraan tidak boleh disebut selesai sebelum readback.
- UI05 Hasil dan recovery: jumlah expected/actual, sequence baru, status ASSEMBLED atau INCOMPLETE, buka laporan, relink/repair dan rebuild sequence baru.
- DLG01 Konfirmasi build dan DLG02 Repair: tunjukkan dampak, lokasi cache, sequence baru, serta pembatasan edit gerakan baked.

State tambahan
Gambar harus mencakup host unsupported, file kosong, daftar scene panjang, error Unicode, narrow panel, disk kurang, dan disabled controls. Pesan tidak hanya mengandalkan warna. Keyboard focus, tab order, scroll dan tooltip panjang diuji saat implementasi; gambar hanya membuktikan desain visual.

STOP wajib
Halaman ini adalah brief kebutuhan UI, bukan prompt imagegen dan bukan gambar final. Pada STEP02 ASTRA menulis prompt visual, menyimpannya sebagai DOCX dan teks, lalu berhenti. Perintah lanjutkan saja tidak membuka coding. Pengguna perlu menyediakan atau meminta gambar, meninjau/revisi, lalu menyetujui seluruh UI final secara eksplisit.

Bukti yang membuka G2
docs/ui berisi seluruh gambar final bernama stabil, approval record dengan tanggal dan cakupan layar, hash gambar, serta satu UI_REFERENCE_FINAL.docx yang memasukkan seluruh gambar dan catatan perilakunya. Setiap gambar diganti berarti approval terkait diperiksa ulang. UI dianggap siap coding hanya jika dokumen planning lengkap, konflik kontrak selesai, dan G2 benar-benar PASS.

## 09 STEP00 sampai STEP02 perencanaan sebelum kode

STEP00 Audit dan handoff
Input: Master V3 asli dan repo target. Tugas ASTRA: audit baseline, identifikasi sumber hilang, pilih reuse, kunci lingkup, tulis backlog, acceptance dan gate. Output: paket dokumen ini. Pemeriksaan: hash source asli sama; seluruh AC dan preset tercakup; repo memuat file lengkap. Status sekarang: paket planning selesai dengan prasyarat terbuka. G0 kesiapan penuh tetap BLOCKED sampai sumber kontrak dan jalur host nyata tersedia. Tidak ada klaim HOST PASS.

STEP01 Spesifikasi kontrak dan arsitektur
Pemilik: ASTRA. Input wajib: V3 serta dokumen lama yang diperlukan, atau penggantinya yang disetujui. Tugas: field dictionary dua JSON, mapping ID preset, policy unknown fields, rounding, ruang waktu keyframe, layout transform, speed/direction, hash canonicalization, manifest, error taxonomy, limits, dan rencana fixture. Pilih helper/runtime dan catat ADR. Setiap ketidakpastian menjadi blocker spesifik dengan owner dan bukti penutupan.

Output STEP01: DOCX detail, contract Markdown, fixture catalog dan keputusan arsitektur. Fixture catalog berisi kasus dan hasil yang diharapkan, bukan hasil tes yang diklaim sudah jalan. G1A SPEC PASS berarti spesifikasi lengkap dan dapat ditinjau. G1B SCHEMA TEST PASS baru diuji SOL pada STEP04. Pemisahan ini menyelesaikan benturan V3 antara schema test di awal dan larangan coding sebelum UI. Belum boleh membuat executable validator, test harness, panel, atau schema implementasi.

STEP02 Prompt gambar dan referensi UI
Pemilik: ASTRA dengan persetujuan pengguna. Input: G1A PASS, brief UI, daftar state dan teks error. Tugas awal hanya menulis prompt UI setiap layar dalam DOCX dan TXT/Markdown yang konsisten; setelah prompt selesai wajib STOP. Sesudah gambar selesai dan disetujui, konsolidasikan satu DOCX referensi UI, gambar asli, approval record, dan hash ke repo. G2 PASS memerlukan semua layar serta state yang disepakati dan seluruh planning.

Perintah kerja berikut untuk AI penerus
Mulai dengan membaca 00_START_HERE, STATUS, V3, plan A1, dan BLOCKERS. Selesaikan inventaris sumber STEP01 terlebih dahulu. Bila layout atau definisi efek masih hilang, nyatakan blocker dan bahan yang diperlukan. Jangan mengisi ukuran, durasi FAST/SLOW, bentuk Brush atau easing dari tebakan. Rencana detail tahap lanjutan pada halaman berikut adalah backlog bersyarat, bukan izin menjalankannya sekarang.

## 10 STEP03 dan STEP04 fondasi dan validasi

STEP03 Panel minimal dan pilot P0
Entry: G1A dan G2 PASS; semua DOCX dan gambar final di repo; mesin Windows 11 dengan Premiere 24.x yang bisa diuji tersedia. SOL membuat shell CEP minimal, manifest host terbatas 24.x, CSInterface yang diaudit, bridge JSX, host discovery, dan helper handshake. Terapkan UI yang disetujui tanpa fungsi susun aktif sebelum preflight siap. Batasi fitur dengan capability matrix.

Uji: panel muncul, close/reopen, docking, ukuran sempit, Unicode path, versi host dideteksi, callback/error/timeout, dan host unsupported ditolak. Rekam exact build, OS, locale, CEP version, project test, video atau screenshot panel asli. Tidak boleh mengganti bukti ini dengan screenshot browser atau mock host. Output docs/evidence/STEP03 dengan commit SHA, instructions reproduksi, log dan bukti. G3 PASS hanya dari Premiere nyata. Jika tidak ada host, status BLOCKED_HOST dan jangan lanjut STEP04 sebagai selesai.

STEP04 Validator compiler dan dry run
Entry: G3 PASS dan kontrak STEP01 dibekukan. SOL membuat schema dua JSON, parser aman, cross validation, SRT evidence, path resolver, probe media, registry resolver, manifest deterministik, state panel dan laporan Bahasa Indonesia. Pembacaan metadata native-only tidak perlu mewajibkan binary FFmpeg; gunakan probe alternatif yang dikunci. ffmpeg/ffprobe diwajibkan hanya jika backend terpilih memerlukannya.

Uji unit: JSON rusak, duplicate keys sesuai policy, version mismatch, pair missing/extra, split IN/OUT, unsupported direction, scene overlap, klip pendek, hash berbeda, alpha PNG rusak, SRT berulang, traversal dan input limit. Uji determinisme: dua compile input sama menghasilkan operation manifest sama setelah field volatil job/timestamp dikeluarkan dari pembandingan. Missing required asset menghasilkan FAIL sebelum satu pun operasi mutasi host.

Output dan batas gate
G1B menutup schema+fixture tests; G4 menutup kontrak compiler dan UI preflight. Capability produksi preset masih boleh UNVERIFIED; validitas input dan READY untuk assembly harus dibedakan. Tes unit boleh memakai fake capability profile yang jelas TEST_ONLY; profile itu tidak masuk paket produksi dan tidak membuka tombol build nyata. Pilot internal berikutnya memakai fixture terkendali dan izin fase, tidak memalsukan status preset pengguna.

Bukti minimum
Commit, perintah tes, hasil dan exit code, fixture hashes, contoh laporan positif/negatif, expected manifest, serta screenshot state validasi panel asli. CI lint/unit tidak menggantikan G3 dan tidak membuktikan 21 efek.

## 11 STEP05 dan STEP06 timeline dan efek awal

STEP05 Assembly dasar dan pilot P1 serta P2
Entry: G4 PASS dan fixture media sintetis teridentifikasi. SOL membuat sequence dari preset/template yang disertifikasi, track plan, import dedup per path/hash, penempatan background mute, narasi dan PNG SINGLE/DOUBLE, marker, jurnal, readback dan mode sequence baru. Capability diagnostik untuk pilot boleh terbatas pada assembly dasar; hasil ini bukan proyek pengguna yang memenuhi BOTH sebelum STEP06.

Fixture P2 mengacu contoh V3: V001 [0,150) dengan A001; V002 [150,330) dengan A002 kiri dan A003 kanan mulai frame 192. Harus tampak 3 visual instance independen, posisi layout sesuai sumber resmi, sequence berakhir sesuai policy audio, dan tanpa ripple. Background, narasi, dan optional clip dihitung terpisah dari 3 instance gambar.

Uji: readback start/end/source offsets, frame boundary, count, V1/V2/V3/A1, background loop terakhir, audio background tidak terdengar, PNG alpha dan label, save/reopen. Paksa gagal sesudah beberapa insert; sequence manual pembanding tetap identik. Klik ganda dan retry tidak menggandakan item di sequence target yang sama. G5 TIMELINE PASS memerlukan .prproj yang dapat dibuka dan bukti timeline nyata. Jangan menyebut ini produk lengkap.

STEP06 Pilot P3 Fade Pan Wipe BOTH
Entry: G5 PASS dan registry pilot dengan definisi visual/durasi yang disetujui. SOL mengimplementasikan native Fade/Pan, pemisahan base transform dari offset animasi, dan probe Wipe. Gunakan parameter stabil bila tersedia, periksa dukungan keyframe lalu baca nilainya kembali. Simpan native_status per preset dan build, bukan satu flag global.

Uji: IN/HOLD/OUT, BOTH satu ID, speed/direction yang didukung, nonzero clip start, trimmed source, DOUBLE stagger, rotasi/scale yang tidak menggeser anchor tanpa sengaja, native keyframe dapat diedit manual. Uji di locale yang dipakai pengguna dan hindari displayName sebagai satu-satunya identitas parameter.

Wipe dan exit gate
Jika penambahan native Wipe tidak tersedia lewat jalur yang diterima, tandai UNSUPPORTED_NATIVE, siapkan fallback eksplisit pada STEP07, dan tandai bagian P3 Wipe pending. G6 boleh ditutup untuk subset native yang benar-benar terbukti, sementara P3 lengkap menunggu Wipe. G8 tidak dapat PASS selama P3 belum selesai. Tidak menurunkan Wipe menjadi Fade atau memakai QE DOM tersembunyi. Screenshot keyframe, readback JSON, preview video dan edit manual menjadi evidence G6.

## 12 STEP07 dan STEP08 alpha serta galeri lengkap

STEP07 Prerender dan pilot P4
Entry: G6 subset native PASS; kontrak Brush dan cache tersedia. SOL membuat worker yang merender satu overlay per instance, cache content-addressed, timeout/cancel, progress, disk budget, atomic finalize, dan relink hash. Tentukan candidate MOV alpha dan PNG sequence berdasarkan kemampuan impor host; jangan menetapkan codec final sebelum hasil pilot.

Prosedur alpha
Gunakan PNG dengan area transparan, tepi semi-transparan, label tipis dan warna jenuh. Render Brush dengan frame count tepat. Probe output untuk alpha dan decode frame awal/tengah/akhir. Impor ke Premiere dengan 30 FPS yang diverifikasi; image sequence perlu cara import serta interpret footage yang benar-benar diuji. Tampilkan di atas latar gelap, terang dan checkerboard. Periksa straight/premultiplied alpha, halo, black matte dan framing.

Uji lifecycle
Geser dan trim clip hasil, save, tutup, reopen, pindah salinan folder proyek lalu relink. Buktikan perubahan internal gerak memerlukan regenerasi; UI wajib menunjukkan baked. Uji worker crash, cancel, disk penuh, cache corrupt, job bersamaan, cache hilang dan mismatch algoritma. Hash yang tidak cocok tidak boleh auto-relink. Jika Wipe membutuhkan fallback, tutup P3 dengan proof yang sama dan backend sebenarnya.

G7 ALPHA PASS
Minimal satu format alpha tersertifikasi pada host target, output per instance tepat frame, repair terbukti dan cache tetap online setelah reopen. Jika semua format gagal, preset prerender UNSUPPORTED dan G7 FAIL. Jangan mengganti background hitam memakai chroma key sebagai default.

STEP08 Lengkapi 21 preset dan pilot P5
Entry: G7 PASS, sumber perilaku/durasi dan layout lengkap. Implementasikan bertahap keluarga Motion/Opacity, masking, transform kompleks, lalu reveal/glow. Untuk tiap preset, tambahkan bukti native atau alpha, expected frame, registry immutable/versioned dan tests untuk tiap kombinasi speed/direction yang advertised. Tidak wajib semua preset native.

G8 21 dari 21
PRESET_MATRIX tidak lagi berisi UNVERIFIED pada backend yang ditawarkan. Semua 21 preset menampilkan IN/HOLD/OUT sesuai referensi yang disetujui, pairing BOTH utuh, tidak ada silent fallback, P3 lengkap, dan G7 tetap PASS. Galeri 21 MEDIUM adalah ringkasan; full certification matrix tetap wajib. Perubahan algoritma memerlukan registry version baru dan revalidation. Simpan screenshot frame kritis, video galeri, host report, serta keputusan review visual.

## 13 STEP09 dan STEP10 pengujian akhir serta distribusi

STEP09 End to end dan pilot P6
Entry: G8 PASS. SOL menjalankan proyek 50, 100 dan 300 atau lebih scene dengan aset besar, aset yang berulang, SRT Unicode, background loop, SINGLE/DOUBLE stagger, semua preset dan durasi panjang. Catat spesifikasi mesin, elapsed time, peak memory, disk, ukuran cache, responsiveness dan frame drift. Jangan menjanjikan angka performa sebelum baseline diukur.

Pengujian pengguna
Jalankan preflight → build → preview → edit manual posisi/durasi dan native keyframe → simpan .prproj → tutup Premiere → buka ulang → pastikan media online → ekspor MP4 melalui Premiere. Periksa beberapa boundary termasuk scene akhir serta sinkron audio. Hasil ekspor harus nyata dan dapat diputar; FFmpeg output terpisah tidak memenuhi pembuktian ekspor Premiere.

Recovery akhir
Cancel tiap fase, reload panel, restart setelah partial job, missing audio/PNG/background required, cache korup, folder read-only, path Unicode/spasi, disk penuh, JSON berubah setelah preflight, dan sequence pengguna yang sudah diedit. Periksa tidak ada mutasi destruktif dan tidak ada status sukses palsu. Laporkan bug dengan reproduksi, input hash, expected/actual dan commit fix. G9 PASS hanya bila AC01–AC30 memiliki bukti yang cocok dengan commit kandidat rilis dan tidak ada blocker kritis.

STEP10 Paket plugin dan pilot pemasangan
Entry: G9 PASS. Output adalah paket extension Premiere beserta optional worker, bukan portable EXE renderer. Pengembangan boleh memakai folder source untuk pilot; paket distribusi dan installer dibuat di akhir. Audit CSXS manifest, versi helper, dependency lock, SBOM/notices, FFmpeg build flags, checksum, dan panduan Bahasa Indonesia.

Instalasi
Pilih jalur pemasangan per-user atau ZXP yang benar-benar dibuktikan pada host target. Dokumentasikan syarat signing dan langkah debug pengembangan terpisah. Jangan meninggalkan PlayerDebugMode aktif secara diam-diam atau mengubah registry tanpa tindakan/izin yang jelas. Uji install, upgrade, repair dan uninstall pada akun Windows bersih; data proyek serta cache yang linked tetap dipertahankan. Jangan membundel installer Adobe atau lisensi Premiere.

G10 RELEASE PASS
Paket yang diunduh ulang sama checksum, berhasil dipasang dan menjalankan smoke E2E pada host tersertifikasi, manual menyatakan batas native/baked dengan jujur, dan seluruh gate serta izin publikasi rilis terpenuhi. Otorisasi sekarang hanya untuk upload planning; tidak otomatis mengizinkan merge perubahan implementasi, tag rilis atau publikasi installer.

## 14 Matriks bukti dan prosedur pilot host

Bukti per pilot
- P0 pada STEP03: panel dan bridge pada Premiere nyata. Rekam About/version, CEP/runtime, Windows, locale, commit dan log handshake.
- P1 pada STEP05: PNG alpha dan audio pada sequence 1080p 30 FPS. Rekam sequence settings, actual clip times dan saved project.
- P2 pada STEP05: satu SINGLE dan satu DOUBLE dengan tiga instance. Rekam track map, stagger frame 192 dan frame readback.
- P3 pada STEP06 sampai STEP07: Fade, Pan, Wipe BOTH selama 15–30 detik. Rekam backend masing-masing, keyframe untuk native dan alpha untuk baked.
- P4 pada STEP07: Brush dan alpha, reopen dan relink. Rekam media probe, pixel/visual check dan cache manifest.
- P5 pada STEP08: 21 preset plus seluruh kombinasi yang diiklankan. Rekam galeri dan certification matrix.
- P6 pada STEP09: 100 atau lebih scene, manual edit dan ekspor Premiere. Stress tambahan 300 atau lebih scene tetap termasuk pengujian akhir.

Format evidence index
Setiap gate mempunyai gate_id, status, tested_commit, host_build, OS, locale, runtime_versions, fixture_hashes, registry_hash, layout_hash, test_commands, expected_result, actual_result, reviewer, reviewed_at dan daftar artifact path/hash. Status yang diizinkan adalah NOT_STARTED, IN_PROGRESS, BLOCKED, FAIL, PASS. File template tidak boleh berisi PASS default atau reviewer fiktif.

Penyimpanan bukti
Simpan index dan report kecil di docs/evidence/STEPxx. .prproj dan video besar bisa berada pada lokasi artifact permanen yang dapat diakses penerus dengan checksum serta petunjuk unduh. Jangan hanya memakai artifact CI yang akan kedaluwarsa. Fixture sintetis diberi label jelas; file narasi/proyek pribadi tidak otomatis dipublikasikan ke repo public tanpa kebutuhan dan otorisasi.

CI dan host adalah bukti berbeda
Runner biasa menjalankan schema, compiler, security/path dan worker tests. Runner tersebut tidak dianggap memiliki Premiere berlisensi. Uji host memerlukan mesin nyata atau runner Windows terkontrol yang sudah menyediakan Premiere secara sah. Bila akses ini tidak tersedia, laporan berhenti pada BLOCKED_HOST; tidak membuat video simulasi yang menyerupai bukti host.

Kebijakan perubahan
Hasil PASS melekat pada commit dan konfigurasi yang diuji. Jika perubahan menyentuh timing, bridge, registry, codec atau packaging, jalankan ulang bukti terkait beserta smoke E2E. Tidak perlu mengulang semua tes untuk koreksi ejaan dokumen. Reviewer mencatat cakupan regresi dan alasan, bukan memindahkan status PASS dari commit lama tanpa pemeriksaan.

## 15 Cakupan acceptance dan katalog tes

Matriks lengkap
ACCEPTANCE_MATRIX.csv menyimpan seluruh teks AC01–AC30 dari Master V3 tanpa mengganti maknanya, tahap pemilik, ID tes usulan, evidence minimum, dan status NOT_TESTED. CSV ini menjadi daftar periksa SOL; DOCX merangkum hubungan kelompoknya di bawah. Semua test ID pada tahap planning adalah rencana, bukan test suite yang sudah tersedia.

Cakupan kontrak
AC03–AC12 dan AC24 ditangani terutama STEP04: schema/versi, pairing tepat, BOTH, enum/hash, speed/direction, timing dan SRT evidence, required media, serta larangan fallback. T-CONTRACT-VALID memakai dua JSON dengan media/hash nyata. Set negatif mengubah satu invarian per fixture agar kegagalan dan error code dapat diverifikasi. AC07 juga diperiksa di galeri karena validasi data saja tidak membuktikan render memakai preset sama.

Cakupan host dan layout
AC01–AC02 dibuktikan STEP03. AC13–AC18 serta AC25–AC26 dibuktikan STEP05 lalu regresi STEP09. T-HOST-PLACEMENT membandingkan manifest dengan readback untuk setiap clip. T-SAFETY-MANUAL mengambil snapshot sequence pengguna sebelum dan sesudah gagal, cancel serta retry. T-LAYOUT-ALPHA menggunakan target posisi/crop dari profile resmi dan frame komposit nyata.

Cakupan animasi
AC19 dan AC21 mencakup STEP06; AC22–AC23 STEP07; AC20 dan AC24 lengkap STEP08. T-FX-PRESET memeriksa 21 entry, fase, speed/direction, endpoint dan galeri. T-NATIVE-EDIT melakukan perubahan keyframe manual. T-ALPHA-IMPORT memeriksa latar checkerboard/terang/gelap serta kemampuan geser dan trim. Screenshot contoh tidak cukup bila tidak terkait source hash dan host build.

Cakupan ketahanan dan hasil akhir
AC27–AC30 ditutup STEP09 dengan lifecycle, path/disk/cancel, skala, manual edit dan MP4 yang diekspor Premiere. Catat setidaknya posisi audio awal, tengah dan akhir untuk drift. G10 menambah install/upgrade/uninstall dan checksum walaupun AC utama sudah ditutup G9. Tes keamanan mengirim nama path yang berisi tanda kutip, semicolon dan karakter Unicode untuk membuktikan data tidak menjadi perintah.

Kriteria gagal
Satu mandatory AC tanpa evidence tetap NOT_TESTED atau BLOCKED. Test skip karena host tidak ada bukan PASS. Registry belum terkalibrasi tidak boleh dianggap didukung. Fitur optional yang belum diminta dapat dinonaktifkan dengan policy eksplisit; jangan menghapus requirement inti 21 preset, dua JSON, alpha, BOTH atau edit manual untuk mempercepat rilis.

## 16 Handoff kerja SOL dan status yang jujur

Urutan membaca
Mulai dari README dan AGENTS, lalu docs/00_START_HERE.md, docs/STATUS.md, Master V3 asli atau transkrip lengkap, plan A1 ini, BLOCKERS, SOURCE_AUDIT, ACCEPTANCE_MATRIX dan PRESET_MATRIX. Sesudah tersedia, baca semua DOCX STEP01 dan UI_REFERENCE_FINAL beserta approval. Bila ada konflik, instruksi eksplisit pengguna paling baru mengalahkan dokumen lama; jangan memodifikasi keputusan diam-diam.

Disiplin tahap
Tiap giliran menjalankan satu STEP yang diizinkan. Rencana roadmap ini tidak mengubah semua tahap menjadi IN_PROGRESS. Untuk tahap planning buat DOCX detail sebelum handoff. Implementasi cukup commit, tes, bukti dan status ringkas; DOCX baru diperlukan bila keputusan kontrak atau arsitektur berubah. Setelah tahap selesai laporkan hasil, gate, blocker dan STEP berikut; tunggu lanjutkan sesuai workflow pengguna.

Aturan GitHub
Publikasi dokumen sekarang secara eksplisit diminta pengguna. Repo kosong boleh diinisialisasi pada main dengan paket planning yang koheren. Implementasi berikut menggunakan branch step bernama jelas dan PR yang menjelaskan masalah, perubahan, batas dan evidence. Tidak force-push, menghapus histori atau merge secara otomatis. Permintaan upload planning ini bukan izin merge kode atau release. Jangan mengubah repo lain.

Format laporan SOL
Cantumkan STEP dan task ID, commit/PR, apa yang berubah, tes yang benar-benar dijalankan, host build bila ada, artifact bukti dan hash, gate PASS/FAIL/BLOCKED, remaining work, dan tindakan berikut. Jangan menyebut source ZIP atau screenshot UI sebagai aplikasi jadi. Jangan membuat persentase kemajuan tanpa dasar acceptance yang dapat dihitung.

Blocker yang harus ditutup
B01 sumber V2/layout/efek/prompt; B02 angka FAST/SLOW dan direction/visual; B03 exact build host serta jalur pengujian; B04 UI final dan approval; B05 keputusan lisensi dependency serta runtime; B06 schema ambigu dan policy internal. B01/B02/B06 menghalangi kontrak produksi; B04 menghalangi seluruh coding; B03 menghalangi pilot host; B05 harus ditutup sebelum dependency didistribusikan.

Tindakan pertama AI penerus
Kerjakan STEP01 perencanaan saja setelah meninjau gate G0 dan sumber yang masuk. Jika bahan wajib belum ada, minta dokumen yang spesifik atau keputusan pengganti dari pengguna; jangan mengeksekusi contoh lampiran sebagai pekerjaan produksi. Sesudah kontrak lengkap, lanjutkan STEP02 hanya dengan instruksi pengguna. Status akhir tugas ASTRA saat ini adalah dokumentasi tersimpan, implementasi belum dimulai.

## 17 Sumber teknis dan batas kepastian

Sumber utama
Master Plan V3 yang diberikan pengguna adalah otoritas fitur. Salinan asli di docs/source dipertahankan byte-for-byte. Daftar referensi eksternal dalam V3 adalah petunjuk riset; keberadaannya tidak menggantikan uji kompatibilitas 24.x. Dokumen terdahulu yang belum tersedia dicatat sebagai missing, tidak diringkas berdasarkan judul saja.

Sumber resmi yang diperiksa pada audit ini
Adobe developer portal membedakan CEP classic panel dengan UXP yang ditujukan untuk Premiere 25.6 ke atas. Ini mendukung keputusan tetap CEP untuk target 2024, tanpa menganggap dukungan lintas versi otomatis.
https://developer.adobe.com/premiere-pro/

Adobe PProPanel menyediakan sample panel dan contoh ExtendScript. README terbaru telah berubah untuk era 25.6; hanya pola relevan yang menjadi kandidat reuse dan tiap operasi tetap harus diuji pada 24.x. Audit root LICENSE menunjukkan MIT, tetapi file dan dependency yang benar-benar diambil tetap diperiksa tersendiri.
https://github.com/Adobe-CEP/Samples/tree/e4946b73ac1e566dced8e95dba10811c31036927/PProPanel
https://github.com/Adobe-CEP/Samples/blob/e4946b73ac1e566dced8e95dba10811c31036927/LICENSE

Adobe CEP Resources menyediakan dokumentasi dan alat CEP. Versi runtime untuk paket proyek ini belum dinyatakan lulus pada mesin pengguna.
https://github.com/Adobe-CEP/CEP-Resources

Halaman lisensi FFmpeg menunjukkan kondisi lisensi dapat bergantung pada komponen build. Rencana ini tidak menyimpulkan semua binary bebas didistribusikan dengan cara yang sama; SOL harus merekam konfigurasi binary final dan obligations yang sesuai sebelum bundling.
https://ffmpeg.org/legal.html

Rujukan lanjutan dari V3
Scripting Guide di ppro-scripting.docsforadobe.dev dapat membantu riset Sequence, Track, TrackItem dan ComponentParam. Guide tersebut bukan bukti bahwa setiap metode berjalan sama pada host pengguna. Sebelum implementasi, baca metode yang benar-benar dipakai dan buat probe terbatas tanpa QE DOM produksi.

Batas hasil audit
Tidak ada Premiere 2024 yang dijalankan dalam tugas planning ini. Tidak ada alpha codec tersertifikasi, preset native yang terbukti, fixture produksi atau UI final. Keputusan teknis tambahan dalam dokumen diberi status rekomendasi atau kontrak usulan sampai dibekukan pada gate yang disebutkan. Seluruh status kemampuan di matriks awal adalah NOT_TESTED atau UNVERIFIED.
