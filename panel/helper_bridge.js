/* P0 local helper process handshake. No shell, no JSON arguments, no media operations. */
(function (root, factory) {
    "use strict";
    var api = factory();
    if (root && root.document) { root.AIJSONP0Helper = api; }
    if (typeof module === "object" && module.exports) { module.exports = api; }
}(this, function () {
    "use strict";
    var MAX_STDOUT = 8192;
    function parseResponse(raw) {
        if (typeof raw !== "string" || raw.length > MAX_STDOUT) {
            return {status:"error",code:"HELPER_BAD_RESPONSE"};
        }
        var data;
        try { data = JSON.parse(raw); }
        catch (e) { return {status:"error",code:"HELPER_BAD_RESPONSE"}; }
        if (!data || typeof data !== "object" || Array.isArray(data) ||
            data.protocol !== "AIJSON_STEP03_P0" || data.status !== "OK" ||
            data.helper_version !== "0.0.3" ||
            !/^\d+\.\d+\.\d+$/.test(data.python_version || "") ||
            !data.capabilities || typeof data.capabilities !== "object") {
            return {status:"error",code:"HELPER_BAD_RESPONSE"};
        }
        var expected=["schema_validation","media_probe","ffmpeg_prerender","premiere_mutation"];
        if (Object.keys(data.capabilities).length !== expected.length) {
            return {status:"error",code:"HELPER_UNEXPECTED_CAPABILITIES"};
        }
        for (var i=0;i<expected.length;i++) {
            if (data.capabilities[expected[i]] !== false) {
                return {status:"error",code:"HELPER_UNEXPECTED_CAPABILITIES"};
            }
        }
        return {status:"supported",code:"HELPER_P0_OK",version:data.helper_version,
                pythonVersion:data.python_version};
    }
    function decodeExtensionPath(raw, path) {
        if (typeof raw !== "string") { return null; }
        var decoded;
        try { decoded = decodeURIComponent(raw); } catch (e) { return null; }
        if (/^file:\/\/\/[A-Za-z]:\//i.test(decoded)) { decoded=decoded.slice(8); }
        if (!/^[A-Za-z]:[\/\\]/.test(decoded)) { return null; }
        return path.win32.resolve(decoded);
    }
    function createProbe(deps) {
        var active = false, counter = 0, child = null;
        function cancel() {
            counter++;
            active = false;
            if (child && typeof child.kill === "function") {
                try { child.kill(); } catch (ignored) {}
            }
            child = null;
        }
        function probe(cb) {
            if (typeof cb !== "function") { throw new TypeError("callback wajib"); }
            if (active) { return false; }
            if (!deps || deps.platform !== "win32") {
                cb({status:"error",code:"HELPER_WINDOWS_ONLY"}); return false;
            }
            var fs=deps.fs, path=deps.path, execFile=deps.execFile;
            if (!fs || !path || typeof execFile !== "function") {
                cb({status:"error",code:"HELPER_NODE_UNAVAILABLE"}); return false;
            }
            var root=decodeExtensionPath(deps.extensionPath,path);
            var py=deps.pythonExe;
            if (!root || typeof py !== "string" || !path.win32.isAbsolute(py) ||
                path.win32.basename(py).toLowerCase() !== "python.exe") {
                cb({status:"error",code:!py?"HELPER_PYTHON_NOT_CONFIGURED":"HELPER_PATH_INVALID"});
                return false;
            }
            var script, realRoot;
            try {
                realRoot=fs.realpathSync(root);
                script=fs.realpathSync(path.win32.join(realRoot,"helper","handshake.py"));
                var prefix=realRoot.replace(/[\\\/]+$/,"").toLowerCase()+"\\";
                if (script.toLowerCase().indexOf(prefix)!==0 ||
                    !fs.statSync(script).isFile() || !fs.statSync(py).isFile()) {
                    cb({status:"error",code:"HELPER_PATH_INVALID"}); return false;
                }
            } catch (e) {
                cb({status:"error",code:"HELPER_FILES_MISSING"}); return false;
            }
            var id=++counter;
            active=true;
            function finish(result) {
                if (!active || id!==counter) { return; }
                active=false; child=null;
                cb(result);
            }
            try {
                // The Python interpreter path is explicitly set via environment
                // for DEVELOPMENT ONLY, never sourced from either user JSON.
                child=execFile(py,["-I","-B",script,"--probe"],{
                    cwd:realRoot,windowsHide:true,shell:false,timeout:15000,
                    maxBuffer:MAX_STDOUT,encoding:"utf8"
                },function(err,stdout) {
                    if (err) { finish({status:"error",code:err.killed?"HELPER_TIMEOUT":"HELPER_EXEC_FAILED"}); }
                    else { finish(parseResponse(stdout)); }
                });
            } catch (e) { finish({status:"error",code:"HELPER_EXEC_FAILED"}); }
            return true;
        }
        return {probe:probe,cancel:cancel,isBusy:function(){return active;},
                parseResponse:parseResponse};
    }
    return {createProbe:createProbe,parseResponse:parseResponse,
            decodeExtensionPath:decodeExtensionPath};
}));
