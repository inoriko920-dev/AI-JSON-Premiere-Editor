# SOL STEP07 — empat track V1/V2/V3/A1 (10 Oktober 2026)

**Aturan pemilik:** SOL terus mengerjakan seluruh coding dan CI tanpa meminta pemilik mengetes build sekarang; uji host Premiere Pro 2024 pada Windows 11 dilakukan paling akhir. **G3 tetap BLOCKED_HOST / UNVERIFIED**, tidak boleh dianggap PASS dari mock.

## Kode yang telah dibuat

- `core/track_plan.py` menerima dua JSON yang disahkan secara struktural oleh compiler, snapshot media dengan SHA-256, durasi aktual narasi dan background dalam milidetik, serta timebase Premiere dalam string desimal. Menghasilkan jadwal **V1 background berulang, V2 gambar SINGLE/LEFT, V3 gambar RIGHT, dan A1 narasi** dalam interval half-open [start,end) 30fps.
- Background diulang dengan durasi media yang **dibulatkan ke bawah** ke frame utuh (menghindari pemotongan melewati akhir sumber). Narasi wajib mencakup keseluruhan durasi; tidak membuat audio dummy, menggeser posisi, memilih ulang preset, atau menebak durasi tidak tersedia.
- Contoh 330 frame: V1 [0,180) + [180,330), V2 A001 [0,150) + A002 [150,330), V3 A003 [192,330), A1 [0,330). Semua ticks menggunakan aritmetika integer Python dan string.
- Manifest menghasilkan status **CANDIDATE_NOT_EXECUTABLE**, `can_import=false`, `can_assemble=false` dan operation_sha256; hasil bukan instruksi host yang siap dijalankan. Perlu proof terpisah untuk decoder, audio isolation dari background, source trim, layout/crop, animasi BOTH dan host.
- `host/track_placement_adapter.jsx`: *kandidat* ExtendScript ES3 memakai `Track.overwriteClip` **hanya pada sequence baru dengan nama AIJSON_MANAGED dan seluruh track kosong**, ID sequence unik dan bin media hasil impor yang tepat. Host API memeriksa hasil satu per satu berdasarkan nodeId sumber, start/end ticks, trimming Time.end, jumlah klip, dan audio bocor ke A1.
- Kandidat menolak data yang tidak lengkap/diubah, missing import item, host 24.x salah, authorization/preflight false, klip manual di track, atau cap waktu tidak cocok. Semua operasi separuh jalan menghasilkan **INCOMPLETE**, tidak menghapus, retry, atau mengubah sequence lama. Tidak menggunakan `insertClip` yang meripple timeline pengguna, tidak menyimpan proyek, tidak menghapus file.
- Presisi: `ticksAtFrame` menggandakan string digit ticks tanpa mengubah ticks besar menjadi Number JS dan menolak rencana timing manipulatif.
- **Adapter mutasi TIDAK ada pada CEP live ScriptPath atau ZIP unsigned P0**. Uji JavaScript host memakai mock, belum Premiere nyata.

## Batasan dan pekerjaan berikutnya

Pada sumber saat ini, penerapan `TrackItem.end` pada host dan source in/out yang tepat masih **wajib dibuktikan di Premiere Pro 2024 asli**, audio background bisa menciptakan linked-audio side effect sehingga adapter berhenti jika terdeteksi, dan dukungan preset 21 BOTH serta layout crop final belum tersambung. Belum ada eksekusi FFmpeg prerender, MP4 final, atau installer.

STEP07 kandidat sudah dikode; status tes mutakhir berada di [workflow STEP07](../../actions/workflows/step07-track-mock.yml) dan harus diperiksa pada HEAD terbaru. STEP berikutnya: integrasikan metadata FFprobe + snapshot dengan compiler track secara read-only, kemudian resolver frame source + adapter FX/crop, lanjut uji host final.
