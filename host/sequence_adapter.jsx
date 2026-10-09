/* STEP05: Premiere Pro 2024 ExtendScript (ECMAScript 3).
 * Host tests still UNVERIFIED. No sequence modification, asset import or
 * FX from CEP panel. The create function is NOT WIRED to the panel and
 * requires an explicit internal verified authorization; no JSON READY bypass.
 * This file is intentionally separate from P0's loaded ScriptPath until
 * later host-capability evidence and a reviewed preflight/approval gate exist.
 */
if (typeof $ === "undefined") { var $ = {}; }
$._AIJSON_SEQUENCE_V1 = (function () {
    function project() {
        if (typeof app === "undefined" || !app || !app.project) { return null; }
        return app.project;
    }
    function hostVersion() {
        if (typeof app === "undefined" || !app) { return ""; }
        var v = String(app.version || "");
        return /^[0-9]+(\.[0-9]+){1,3}$/.test(v) ? v : "";
    }
    function supported() {
        return /^24\./.test(hostVersion());
    }
    function digits(s) {
        return typeof s === "string" && /^[1-9][0-9]{0,25}$/.test(s);
    }
    function countTracks(trackCollection) {
        if (!trackCollection || typeof trackCollection.numTracks !== "number") { return -1; }
        var n = trackCollection.numTracks;
        return n >= 0 && n <= 256 && Math.floor(n) === n ? n : -1;
    }
    function identifier(text) {
        return typeof text === "string" && /^[a-zA-Z0-9_ -]{1,72}$/.test(text);
    }
    function guid(text) {
        return typeof text === "string" &&
            /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/.test(text);
    }
    function countSequences(p) {
        var c = p.sequences;
        if (!c || typeof c.numSequences !== "number" || c.numSequences < 0 ||
            c.numSequences > 100000 || Math.floor(c.numSequences) !== c.numSequences) {
            return -1;
        }
        return c.numSequences;
    }
    function sequenceAt(p,i) { return p.sequences[i]; }
    function sequenceIdentity(s) {
        if (!s) { return null; }
        var id = String(s.sequenceID || "");
        if (!guid(id)) { return null; }
        return id.toLowerCase();
    }
    function snapshot(p) {
        var n = countSequences(p);
        if (n < 0) { return null; }
        var old = [];
        for (var i=0;i<n;i++) {
            var item = sequenceAt(p,i);
            if (!item || typeof item.name !== "string" || item.name.length === 0) { return null; }
            var id = sequenceIdentity(item);
            if (!id) { return null; }
            old.push({id:id,name:String(item.name)});
        }
        return old;
    }
    function inspect() {
        try {
            var p=project(), ver=hostVersion();
            if (!p) { return "S5|1|ERROR|NO_PROJECT"; }
            if (!supported()) { return "S5|1|ERROR|HOST_UNSUPPORTED"; }
            var active=p.activeSequence;
            if (!active) { return "S5|1|NO_ACTIVE_SEQUENCE|"+ver; }
            var tb=String(active.timebase || "");
            var v=countTracks(active.videoTracks), a=countTracks(active.audioTracks);
            var w=active.frameSizeHorizontal,h=active.frameSizeVertical;
            if (!digits(tb) || v<0 || a<0 || typeof w!=="number" ||
                typeof h!=="number" || w<1 || h<1 ||
                Math.floor(w)!==w || Math.floor(h)!==h) {
                return "S5|1|ERROR|HOST_TIMEBASE_OR_TRACKS_UNKNOWN";
            }
            return "S5|1|OBSERVED|"+ver+"|"+tb+"|"+v+"|"+a+"|"+w+"|"+h;
        } catch(e) { return "S5|1|ERROR|HOST_INSPECT_EXCEPTION"; }
    }
    function createNewEmpty(name, requestedGUID, requirements, authorization) {
        /* This API is for a future reviewed dispatcher, not exposed in CEP UI.
         * input validation.READY and mock tests do NOT authorize host writes.
         * Post-create mismatches leave the NEW sequence intact and INCOMPLETE.
         * No delete, retry, modification of older sequences, or QE DOM.
         */
        try {
            var p=project();
            if (!p) { return "S5|1|BLOCKED|NO_PROJECT"; }
            if (!supported()) { return "S5|1|BLOCKED|HOST_UNSUPPORTED"; }
            if (!authorization || authorization.kind !== "HOST_REVIEWED_OPERATION_V1" ||
                authorization.ownerConfirmed !== true ||
                authorization.hostCapabilityVerified !== true ||
                authorization.layoutVerified !== true ||
                authorization.fxBackendVerified !== true ||
                authorization.preflightAllPass !== true ||
                !requirements || requirements.canvasWidth !== 1920 ||
                requirements.canvasHeight !== 1080 ||
                requirements.fpsNum !== 30 || requirements.fpsDen !== 1 ||
                !digits(requirements.expectedTicksPerFrame) ||
                authorization.hostVersion !== hostVersion()) {
                return "S5|1|BLOCKED|AUTHORIZATION_NOT_VERIFIED";
            }
            if (!identifier(name) || !guid(requestedGUID)) {
                return "S5|1|BLOCKED|SEQUENCE_ID_INVALID";
            }
            var existing=snapshot(p);
            if (!existing) { return "S5|1|BLOCKED|SEQUENCE_REGISTRY_UNAVAILABLE"; }
            for(var i=0;i<existing.length;i++){
                if (existing[i].name.toLowerCase() === name.toLowerCase() ||
                    existing[i].id === requestedGUID.toLowerCase()) {
                    return "S5|1|BLOCKED|SEQUENCE_ALREADY_EXISTS";
                }
            }
            if (typeof p.createNewSequence!=="function") {
                return "S5|1|BLOCKED|CREATE_API_UNAVAILABLE";
            }
            /* This is the first host mutation; all safety checks precede it. */
            var seq=p.createNewSequence(name, requestedGUID);
            if (!seq) { return "S5|1|INCOMPLETE|CREATE_RETURNED_EMPTY"; }
            var after=snapshot(p),actualId=sequenceIdentity(seq);
            if (!after || after.length!==existing.length+1 || !actualId) {
                return "S5|1|INCOMPLETE|READBACK_FAILED";
            }
            var newCount=0;
            for(var j=0;j<after.length;j++){
                var found=false;
                for(var k=0;k<existing.length;k++){
                    if (existing[k].id===after[j].id &&
                        existing[k].name===after[j].name) { found=true;break; }
                }
                if(!found){newCount++;if(after[j].id!==actualId ||
                    after[j].name!==name) {
                    return "S5|1|INCOMPLETE|READBACK_IDENTITY_CHANGED";
                }}
            }
            if (newCount!==1) { return "S5|1|INCOMPLETE|READBACK_NOT_UNIQUE"; }
            if (seq.frameSizeHorizontal!==1920 || seq.frameSizeVertical!==1080 ||
                String(seq.timebase || "")!==requirements.expectedTicksPerFrame ||
                countTracks(seq.videoTracks)<3 || countTracks(seq.audioTracks)<1) {
                return "S5|1|INCOMPLETE|SEQUENCE_PROFILE_MISMATCH";
            }
            /* Empty only! No import, clip insertion, FX, or export here. */
            return "S5|1|CREATED_EMPTY|"+actualId;
        } catch(e) {
            /* Cannot know if mutation occurred before exception: never delete. */
            return "S5|1|INCOMPLETE|HOST_CREATE_EXCEPTION";
        }
    }
    return {inspect:inspect,createNewEmpty:createNewEmpty};
}());
