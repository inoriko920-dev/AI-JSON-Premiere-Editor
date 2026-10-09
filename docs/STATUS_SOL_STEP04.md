# SOL — Status implementasi aktif, 10 Oktober 2026

Pemilik menginstruksikan developer untuk **menyelesaikan seluruh coding yang memungkinkan dahulu, uji Premiere manual pada tahap terakhir**. Pekerjaan tidak lagi berhenti hanya karena G3 host belum diuji; status G3 tetap unverified. Tidak boleh menganggap semua fungsi atau 21 preset bekerja karena CI.

## Telah dikerjakan

- STEP03 branch `sol/step03-cep-p0-20261009`: P0 CEP panel, version guard, helper Python read-only, laporan diagnostik, staging test aman; CI Windows/Linux PASS.
- **STEP04 [PR #4](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/pull/4)**: parser JSON dengan duplicate-key reject; pasangan edit-plan-v2 dan animation-plan-v1, BOTH, timing frame, slot scene, registry 21 key arah kandidat, lock and unknown nested review.
- **STEP04 media**: resolver path aman dari traversal/symlink luar root, SHA-256 sumber, header PNG/WAV/MP3/MP4, SRT UTF-8 BOM, cue multiline, cue evidence; tidak mengarang timestamps atau file dummy.
- CLI `python -m core.validate_cli --edit EDIT_PLAN.json --animation ANIMATION_PLAN.json --max-json-bytes 1000000 --media-root MEDIA_ROOT --max-media-bytes 100000000 --max-srt-cues 10000`: nilai numerik hanya contoh batas **debug yang dipasok pemanggil**, bukan limit produksi resmi. Hasil error exit 2, butuh review exit 3; **tidak pernah READY** dan tidak memanggil Premiere.
- Tes unit lintas Windows+Linux untuk schema, path, SHA, SRT, CLI dan input tidak valid. Bukti CI harus selalu merujuk commit terbaru setelah lulus.

## Belum selesai dan harus terus dicoding otomatis

Integrasi panel untuk memilih dua JSON + folder media → helper validasi nyata; snapshot/hash dan preflight resource/codec; manifest compiler deterministik dengan timing frame serta V1/V2/V3/A1; adapter host CEP/ExtendScript create new sequence safe; import assets/background/audio; registry efek native/prerender, 21 preset BOTH dan jalur FFmpeg alpha; readback/jurnal/recovery; testing edge, panjang, Windows builds serta packaging akhir. **Jangan mengklaim satu pun fitur tersebut sudah jadi sebelum kodenya ada dan tesnya lulus.**

Batas bukti: G1A SPEC PASS, G2 UI PASS, G3 pending uji Premiere asli pada fase akhir. G1B adalah uji validator yang sedang berjalan, bukan sertifikasi host. No merge main/installer/release.
