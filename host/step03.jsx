/* STEP03 P0 — ExtendScript ES3. No import, timeline mutation, filesystem write or eval. */
$._AIJSON_P0 = {
    probe: function () {
        try {
            if (typeof app === "undefined" || !app) {
                return "P0|1|ERROR|NO_APP";
            }
            var version = String(app.version || "");
            if (!/^[0-9]+(\.[0-9]+){1,3}$/.test(version)) {
                return "P0|1|ERROR|HOST_VERSION_UNKNOWN";
            }
            return "P0|1|OK|" + version;
        } catch (e) {
            return "P0|1|ERROR|HOST_PROBE_EXCEPTION";
        }
    }
};
