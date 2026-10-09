/* STEP03 only: panel state stays NO_PROJECT; no assembly or preflight functionality. */
(function (root) {
    "use strict";
    var document = root.document;
    if (!document) { return; }
    function init() {
        var btn = document.getElementById("btn-host");
        var status = document.getElementById("host-status");
        var detail = document.getElementById("host-detail");
        var log = document.getElementById("log-entry");
        var cep = root.__adobe_cep__;
        var evalScript = cep && typeof cep.evalScript === "function" ?
            function (script, callback) { cep.evalScript(script,callback); } : null;
        var bridge = root.AIJSONP0Bridge.createBridge(evalScript,root.setTimeout.bind(root),root.clearTimeout.bind(root),8000);
        function render(result) {
            var label="Gagal memeriksa host",message="Pemeriksaan host tidak berhasil.";
            status.className="status bad";
            if (result.status === "supported") {
                label="Premiere Pro 2024 • "+result.version+" (terdeteksi)";
                message="Host 24.x cocok. Ini baru pemeriksaan versi; kemampuan plugin dan operasi timeline BELUM teruji.";
                status.className="status good";
            } else if (result.status === "unsupported") {
                label="HOST TIDAK DIDUKUNG";
                message="E_HOST_UNSUPPORTED: ditemukan "+result.version+", dibutuhkan Premiere Pro 2024 versi 24.x.";
            } else if (result.code === "CEP_NOT_AVAILABLE") {
                label="CEP BELUM TERHUBUNG";
                message="Panel harus dibuka di Premiere Pro 2024, bukan melalui browser biasa.";
            } else {
                message="Kode: "+result.code+". Periksa log CEP dan uji ulang pada Premiere 24.x.";
            }
            status.textContent=label;
            detail.textContent=message;
            log.textContent=message;
        }
        btn.addEventListener("click",function () {
            if (bridge.isBusy()) { return; }
            btn.disabled=true;
            status.className="status wait";
            status.textContent="Memeriksa versi host…";
            detail.textContent="Menunggu jawaban ExtendScript.";
            bridge.probe(function (result) {
                btn.disabled=false;
                render(result);
            });
            if (!bridge.isBusy()) { btn.disabled=false; }
        });
        if (!evalScript) {
            render({status:"error",code:"CEP_NOT_AVAILABLE"});
        }
    }
    if (document.readyState==="loading") {
        document.addEventListener("DOMContentLoaded",init);
    } else { init(); }
}(this));
