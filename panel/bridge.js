/* Minimal audited CEP transport. Never interpolates file names or JSON in ExtendScript. */
(function (root, factory) {
    "use strict";
    if (typeof module === "object" && module.exports) {
        module.exports = factory();
    } else {
        root.AIJSONP0Bridge = factory();
    }
}(this, function () {
    "use strict";
    var PROBE_CALL = '$._AIJSON_P0.probe()';
    function parseProbe(raw) {
        if (typeof raw !== "string") { return {status:"error",code:"INVALID_HOST_RESPONSE"}; }
        var ok = /^P0\|1\|OK\|([0-9]+(?:\.[0-9]+){1,3})$/.exec(raw);
        if (ok) {
            var major = parseInt(ok[1].split(".")[0],10);
            return major === 24 ? {status:"supported",version:ok[1],code:"HOST_24"} :
              {status:"unsupported",version:ok[1],code:"E_HOST_UNSUPPORTED"};
        }
        var failure = /^P0\|1\|ERROR\|(NO_APP|HOST_VERSION_UNKNOWN|HOST_PROBE_EXCEPTION)$/.exec(raw);
        return failure ? {status:"error",code:failure[1]} :
           {status:"error",code:"INVALID_HOST_RESPONSE"};
    }
    function createBridge(evalScript, setTimer, clearTimer, duration) {
        var invoke = typeof evalScript === "function" ? evalScript : null;
        var schedule = typeof setTimer === "function" ? setTimer : setTimeout;
        var cancel = typeof clearTimer === "function" ? clearTimer : clearTimeout;
        var delay = typeof duration === "number" && duration > 0 ? duration : 8000;
        var generation = 0, busy = false, timeoutId = null;
        function stop() {
            generation += 1;
            busy = false;
            if (timeoutId !== null) { cancel(timeoutId); timeoutId = null; }
        }
        function probe(callback) {
            if (typeof callback !== "function") { throw new TypeError("callback wajib"); }
            if (busy) { return false; }
            if (!invoke) { callback({status:"error",code:"CEP_NOT_AVAILABLE"}); return false; }
            busy = true;
            var current = ++generation;
            function finish(value) {
                if (!busy || current !== generation) { return; }
                stop();
                callback(value);
            }
            timeoutId = schedule(function () {
                finish({status:"error",code:"HOST_TIMEOUT"});
            },delay);
            try {
                invoke(PROBE_CALL,function (raw) { finish(parseProbe(raw)); });
            } catch (e) {
                finish({status:"error",code:"CEP_EVAL_FAILURE"});
            }
            return true;
        }
        return {probe:probe,cancel:stop,isBusy:function(){return busy;},parseProbe:parseProbe};
    }
    return {createBridge:createBridge,parseProbe:parseProbe,PROBE_CALL:PROBE_CALL};
}));
