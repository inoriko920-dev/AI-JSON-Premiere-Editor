> UPDATED 9 October 2026: ADR-001 is historical; [ADR-002](ADR_002_B06_SPEC_FREEZE_2026-10-09.md) is the active ASTRA B06 spec decision. Numeric host budgets remain deferred; G1A still blocked by B02.

# ADR-001 — Kontrak validator dua JSON dan preflight non-destruktif

**Proyek:** AI-JSON-Premiere-Editor · **Tahap:** ASTRA STEP01 · **Tanggal:** 9 Oktober 2026 · **Status:** TECHNICAL_POLICY_DOCUMENTED / B06 REVIEW_PENDING · **G1A BLOCKED, G2 NOT_STARTED**

## 0. Tujuan dan batasan

Ini adalah rujukan untuk SOL sesudah persetujuan UI, bukan JSON Schema executable, parser, unit test, plugin CEP, atau bukti Premiere 24.x. Data Master V2 dan V3 menjadi otoritas; catatan lama untuk standalone renderer tidak boleh membatalkan output native Premiere dan prinsip satu preset BOTH per asset occurrence.

**Yang benar-benar selesai:** pemeriksaan 17 area field/policy dari V2/V3, 4 grup field terlarang, 13 mapping error yang perlu diaudit, dan 12 keputusan/prosedur ASTRA. **Yang belum selesai:** sign-off untuk metadata nested/locked=false, cap numerik berdasar host, pemetaan arah 21 preset, dan scope FAST/SLOW.

## 1. Field dictionary berbasis sumber

Kamus yang lengkap untuk setiap path disimpan pada [STEP01_B06_FIELD_POLICY.csv](STEP01_B06_FIELD_POLICY.csv). Status berbeda:
- `REQUIRED_ROOT_V2`: seluruh field root wajib menurut Master V2 §5.2 dan §5.6, bukan hanya field yang kebetulan tampak dalam contoh.
- `SCENE_SEMANTIC_V2` / `ASSET_OCCURRENCE_V2`: tipe dan field penting scene/asset dibaca sesuai Master V2; `semantic_relation`, `locked` scene, `stagger_frames`, dan `timing_lock` tidak boleh terhapus hanya karena absen pada contoh Master V3.
- `EXPECTED_PROFILE_V3`, `REQUIRED_SOURCE_V3`, `REQUIRED_PROFILE_V2`: rincian konkret contoh dan integritas source.
- `LEGACY_HINT_V3`: `EDIT_PLAN.render` tetap diterima dan dapat dicatat sebagai INFO/DEPRECATED_RENDER_HINT; **dilarang mengeksekusi `output_path` untuk final export worker**.
- `EXAMPLE_INFO_ONLY`: provenance/validation sebagai metadata audit, tidak menjalankan shell/JS dan `validation.status=READY` bukan preflight yang terpercaya.
- `PROHIBITED`: field pemilihan IN/OUT terpisah, speed/direction/duration di posisi EDIT_PLAN, atau lokasi PNG/scene time yang bocor ke ANIMATION_PLAN.

### Root wajib, jangan diubah

`EDIT_PLAN.json` (`edit-plan-v2`) memiliki **11** nama root: `schema_version`, `project_id`, `revision`, `canvas`, `sources`, `profiles`, `assets`, `scenes`, `render`, `validation`, `provenance`.

`ANIMATION_PLAN.json` (`animation-plan-v1`) memiliki **9** nama root: `schema_version`, `project_id`, `edit_plan_revision`, `revision`, `mode`, `animation_profile`, `project_seed`, `decisions`, `provenance`.

Field yang dideklarasikan `integer` tidak boleh menerima JSON boolean, pecahan, negatif untuk frame, atau overflow host. `revision >=1`. Frame half-open `[start_frame,end_frame)` dengan `start<end` dan canvas pilot `1920×1080, fps_num=30, fps_den=1`.

### Format evidence dan hashing

Sumber SRT/audio harus tersedia dan dapat di-decode, hash SHA-256 riil cocok dengan input; `<SHA256_...>` adalah placeholder dan ERROR pada proyek nyata. `entry_evidence.accuracy=EXACT_WORD` hanya jika word alignment terverifikasi, `EXACT_CUE` hanya cue boundaries. `APPROX_REVIEW` V2 dan `ESTIMATED_FROM_AUDIO` V3 disimpan sebagai label **berbeda**, dengan outcome review, **tidak dipromosikan** menjadi EXACT_WORD. `UNRESOLVED` dan occurrence ambiguity memblokir assembly.

Path media relatif dinormalisasi terhadap project root; reject traversal, escape via symlink/reparse point, unsafe shell arguments atau absolute path di luar izin. Di bawah Windows path Unicode/spasi/quotes yang sah tidak boleh ditolak tanpa sebab. Worker dipanggil dengan argv array dan shell disabled.

## 2. Kebijakan unknown properties — usulan teknis B06

Sumber V2 menuntut strict validation, tetapi tidak memberikan complete `additionalProperties` map untuk metadata nested. Master V3 secara eksplisit mempertahankan kompatibilitas V2. Maka proposal paling aman:
1. **Root:** wajib 11/9 nama di atas. Field root baru yang tidak dikenal `BLOCKED_SCHEMA`, bukan dihapus, bukan dipakai sebagai instruksi.
2. **Objek scene/asset/decision:** field yang normatif pada sumber dicek tipe/range. Field animasi yang salah lokasi **FAIL** walaupun nilai tampak valid. Jika ditemukan nama nested baru yang tidak termasuk documented metadata, tampilkan path + `NEEDS_REVIEW`, pertahankan berkas aslinya, jangan mutate Premiere. Jangan membuat allowlist permisif `additionalProperties:true` untuk semua objek.
3. **Blok audit legacy** `render`, `validation`, `provenance`: baca field yang dikenal; jika menemukan metadata audit tambahan, serialisasikan apa adanya dalam report (bounded as data), tanpa mengeksekusi `output_path`, `command`, `script`, atau `code`.
4. **Persetujuan final:** aturan nested unknown dan tambahan legacy masih `ADR_PROPOSAL`; SOL harus merekam fixture backward compatibility sebelum menetapkannya executable. Jangan memberi hasil PASS ketika ada ketidakpastian kontrak.

## 3. Status locked dan SRT

`ANIMATION_PLAN.decisions[].locked` wajib hadir bertipe boolean. **Proposal:** `locked=true` kandidat READY jika bukti lain lulus; `locked=false` => NEEDS_REVIEW, tidak diubah otomatis, tidak memilih preset lain. Pilihan ini konservatif tetapi bukan pernyataan bahwa Master V2 mewajibkan `true` sebagai tipe/enum.

Jika `D=end-start < in_frames+out_frames`, preflight mengeluarkan `E_TIME_006`; `D==minimum` melewati batas matematis tetapi QA visual nonzero HOLD memerlukan pemeriksaan setelah implementasi. Tidak ada random stagger, Enter-only, atau fade downgrade untuk menutup gap.

## 4. Error dictionary dan crosswalk

Lihat [STEP01_B06_ERROR_CROSSWALK.csv](STEP01_B06_ERROR_CROSSWALK.csv) untuk **13 kelas masalah**. Pilihan desain: UI menampilkan kode user-facing V3 (`E_JSON_SCHEMA`, `E_ANIM_MODE`, dst); log menyimpan `legacy_code_v2` untuk debugging kompatibilitas. Bila V2 punya kode spesifik yang tidak masuk daftar minimum V3 (`E_TIME_006`, `E_PROFILE_010`), **jangan hilangkan**: laporkan tetap jelas. Pengujian error taxonomy belum dijalankan.

Semua error yang mengancam bahan/proyek menyebabkan zero host mutations. State machine sah: `FILES_SELECTED → PREFLIGHT_RUNNING → NEEDS_REVIEW/FAIL/READY → ASSEMBLING → ASSEMBLED/INCOMPLETE`. Nilai `READY` hanya hasil preflight helper + verified registry/host, **bukan** nilai `validation.status` dari JSON.

## 5. Kebijakan batas sumber daya dan host-dependent values

Master V3 mewajibkan batas ukuran file, jumlah scene, total aset, disk dan memori tetapi **tidak memberikan angka produksi bersertifikasi**. ASTRA tidak mengarang limit numerik. Rekomendasi implementasi SOL setelah UI PASS:
- Pada STEP04, pilih cap konservatif yang terdokumentasi dalam ADR konfigurasi; ukur memory/throughput pada host Windows 11 nyata dan fixture stress 50/100/300+ scene, kemudian freeze angka + rationale + test.
- Jika limit belum tersedia atau resource tidak cukup, status `BLOCKED_CONFIG/LOW_DISK`; jangan mengabaikan risiko, jangan mulai host assembly.
- Nilai ticks/timebase, native keyframe support, alpha import dan codec hanya dinyatakan VERIFIED setelah Premiere Pro 2024 exact 24.x probe. Jangan menyatakan parser smoke sebagai host PASS.

## 6. Gate untuk handoff

| Kriteria | Hasil saat ini |
| --- | --- |
| Source field dictionary dan error crosswalk | **DIDOKUMENTASIKAN** |
| Rencana kompatibilitas V2 untuk unknown fields | **ADR PROPOSAL** |
| locked=false, SRT alias, resource budget | **REVIEW / HOST TEST PENDING** |
| Q01 MEDIUM-only MVP vs FAST/SLOW | **USER APPROVAL PENDING** |
| 21 full direction token allowlist | **B02 REVIEW PENDING** |
| G1A SPEC | **BLOCKED** |
| G1B executable schema/test | **NOT_STARTED** |
| G2 final UI | **NOT_STARTED** |

**Langkah lanjut:** ASTRA review ADR ini dan siapkan satu paket sign-off B02+B06. Perintah `lanjutkan` tidak otomatis menetapkan MEDIUM-only atau membuat UI final. Setelah G1A PASS, STEP02 prompt UI wajib STOP untuk gambar dan persetujuan; hanya setelah 1 DOCX referensi UI + planning ada di repo baru coding SOL diizinkan.
