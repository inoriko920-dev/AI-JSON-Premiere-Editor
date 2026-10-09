/* STEP03 P0. Read-only Premiere probe and dev-only helper probe; NO assembly. */
(function (root) {
    "use strict";
    var document = root.document;
    if (!document) { return; }
    function init() {
        var btn = document.getElementById("btn-host");
        var status = document.getElementById("host-status");
        var detail = document.getElementById("host-detail");
        var log = document.getElementById("log-entry");
        var helperBtn = document.getElementById("btn-helper");
        var helperStatus = document.getElementById("helper-status");
        var helperDetail = document.getElementById("helper-detail");
        var cep = root.__adobe_cep__;
        var evalScript = cep && typeof cep.evalScript === "function" ?
            function (script, callback) { cep.evalScript(script,callback); } : null;
        var bridge = root.AIJSONP0Bridge.createBridge(
            evalScript,root.setTimeout.bind(root),root.clearTimeout.bind(root),8000);
        var helperBridge = null;
        var hostSupported = false;

        function reportHelper(result) {
            helperStatus.className = "status bad";
            var text = "Helper belum dapat diperiksa.";
            if (result.status === "supported") {
                helperStatus.className = "status good";
                helperStatus.textContent = "HELPER P0 • HANDSHAKE OK";
                text = "Versi "+result.version+", Python "+result.pythonVersion+
                       ". Ini hanya probe lokal; validator dan media belum aktif.";
            } else {
                helperStatus.textContent = "HELPER BELUM SIAP";
                if (result.code === "HELPER_PYTHON_NOT_CONFIGURED") {
                    text = "Python development belum dikonfigurasi pada AIJSON_P0_PYTHON_EXE.";
                } else if (result.code === "HELPER_NODE_UNAVAILABLE") {
                    text = "HELPER_NODE_UNAVAILABLE: Node.js CEP belum tersedia; periksa CEFCommandLine dan runtime CEP.";
                } else {
                    text = "Kode: "+result.code+". Tidak ada perintah timeline dijalankan.";
                }
            }
            helperDetail.textContent = text;
            log.textContent = text;
        }
        function renderHost(result) {
            var label="Gagal memeriksa host",message="Pemeriksaan host tidak berhasil.";
            hostSupported = result.status === "supported";
            helperBtn.disabled = !hostSupported;
            if (helperBridge) { helperBridge.cancel(); }
            helperStatus.className = "status";
            helperStatus.textContent = "Belum diuji";
            helperDetail.textContent = hostSupported ?
                "Host versi 24.x terdeteksi. Jalankan pemeriksaan helper jika dikonfigurasi." :
                "Helper nonaktif sampai Premiere Pro 2024 terdeteksi.";
            status.className="status bad";
            if (hostSupported) {
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
            hostSupported=false;
            helperBtn.disabled=true;
            if (helperBridge) { helperBridge.cancel(); }
            btn.disabled=true;
            status.className="status wait";
            status.textContent="Memeriksa versi host…";
            detail.textContent="Menunggu jawaban ExtendScript.";
            bridge.probe(function (result) {
                btn.disabled=false;
                renderHost(result);
            });
            if (!bridge.isBusy()) { btn.disabled=false; }
        });
        helperBtn.addEventListener("click",function () {
            if (!hostSupported || helperBtn.disabled) { return; }
            var nodeRequire = root.cep_node && typeof root.cep_node.require === "function" ?
                root.cep_node.require : (typeof root.require === "function" ? root.require : null);
            var nodeProcess = root.cep_node && root.cep_node.process ?
                root.cep_node.process : root.process;
            if (!nodeRequire || !nodeProcess || !cep ||
                typeof cep.getSystemPath !== "function") {
                reportHelper({status:"error",code:"HELPER_NODE_UNAVAILABLE"}); return;
            }
            try {
                if (!helperBridge) {
                    var fs = nodeRequire("fs");
                    var path = nodeRequire("path");
                    var childProcess = nodeRequire("child_process");
                    helperBridge = root.AIJSONP0Helper.createProbe({
                        fs:fs,path:path,execFile:childProcess.execFile,platform:nodeProcess.platform,
                        extensionPath:cep.getSystemPath("extension"),
                        pythonExe:nodeProcess.env && nodeProcess.env.AIJSON_P0_PYTHON_EXE
                    });
                }
                if (helperBridge.isBusy()) { return; }
                helperBtn.disabled=true;
                helperStatus.className="status wait";
                helperStatus.textContent="Memeriksa helper…";
                helperDetail.textContent="Menunggu respons proses Python lokal yang dikonfigurasi.";
                var started=helperBridge.probe(function (result) {
                    helperBtn.disabled=!hostSupported;
                    reportHelper(result);
                });
                if (!started && !helperBridge.isBusy()) {
                    helperBtn.disabled=!hostSupported;
                }
            } catch(e) {
                helperBtn.disabled=!hostSupported;
                reportHelper({status:"error",code:"HELPER_NODE_UNAVAILABLE"});
            }
        });
        if (!evalScript) { renderHost({status:"error",code:"CEP_NOT_AVAILABLE"}); }
    }
    if (document.readyState==="loading") {
        document.addEventListener("DOMContentLoaded",init);
    } else { init(); }
}(this));
