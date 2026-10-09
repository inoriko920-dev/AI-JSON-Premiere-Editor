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
        var reportBtn = document.getElementById("btn-report");
        var reportBox = document.getElementById("p0-report");
        var cep = root.__adobe_cep__;
        var evalScript = cep && typeof cep.evalScript === "function" ?
            function (script, callback) { cep.evalScript(script,callback); } : null;
        var bridge = root.AIJSONP0Bridge.createBridge(
            evalScript,root.setTimeout.bind(root),root.clearTimeout.bind(root),8000);
        var helperBridge = null;
        var hostSupported = false;
        var closed = false;
        var lastHost = {status:"not_checked",code:"HOST_NOT_CHECKED"};
        var lastHelper = {status:"not_checked",code:"HELPER_NOT_CHECKED"};
        function safeCode(input, fallback) {
            return typeof input === "string" && /^[A-Z][A-Z0-9_]{0,48}$/.test(input) ?
                input : fallback;
        }
        function safeVersion(input) {
            return typeof input === "string" && /^[0-9]+(?:\.[0-9]+){1,3}$/.test(input) ?
                input : "TIDAK_TERSEDIA";
        }
        function makeReport() {
            var hs = lastHost.status === "supported" ? "SUPPORTED" :
                lastHost.status === "unsupported" ? "UNSUPPORTED" :
                lastHost.status === "not_checked" ? "NOT_CHECKED" : "ERROR";
            var hp = lastHelper.status === "supported" ? "SUPPORTED" :
                lastHelper.status === "not_checked" ? "NOT_CHECKED" : "ERROR";
            return [
                "AI_JSON_PREMIERE_P0_DIAGNOSTIK_V1",
                "JENIS=LAPORAN_LOKAL_BELUM_DIVERIFIKASI",
                "HOST_STATUS="+hs,
                "HOST_CODE="+safeCode(lastHost.code,"HOST_UNKNOWN"),
                "HOST_VERSION="+safeVersion(lastHost.version),
                "HELPER_STATUS="+hp,
                "HELPER_CODE="+safeCode(lastHelper.code,"HELPER_UNKNOWN"),
                "HELPER_VERSION="+safeVersion(lastHelper.version),
                "G3=BLOCKED_HOST_SAMPAI_UJI_PREMIERE_ASLI",
                "UI_IMPORT_PREFLIGHT_ASSEMBLY=DINONAKTIFKAN",
                "BUKTI_DOCKING_REOPEN=PERLU_PEMERIKSAAN_MANUAL"
            ].join("\n");
        }

        function teardown() {
            if (closed) { return; }
            closed = true;
            hostSupported = false;
            bridge.cancel();
            if (helperBridge) { helperBridge.cancel(); }
            btn.disabled = true;
            helperBtn.disabled = true;
            reportBtn.disabled = true;
        }
        if (typeof root.addEventListener === "function") {
            root.addEventListener("pagehide", teardown);
            root.addEventListener("unload", teardown);
        }

        function reportHelper(result) {
            if (closed) { return; }
            lastHelper = result;
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
            if (closed) { return; }
            lastHost = result;
            lastHelper = {status:"not_checked",code:"HELPER_NOT_CHECKED"};
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
            if (closed) { return; }
            if (bridge.isBusy()) { return; }
            hostSupported=false;
            lastHost={status:"error",code:"HOST_CHECK_PENDING"};
            lastHelper={status:"not_checked",code:"HELPER_NOT_CHECKED"};
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
            if (closed) { return; }
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
                lastHelper={status:"error",code:"HELPER_CHECK_PENDING"};
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
        reportBtn.addEventListener("click",function () {
            if (!closed) { reportBox.value = makeReport(); }
        });
        if (!evalScript) { renderHost({status:"error",code:"CEP_NOT_AVAILABLE"}); }
    }
    if (document.readyState==="loading") {
        document.addEventListener("DOMContentLoaded",init);
    } else { init(); }
}(this));
