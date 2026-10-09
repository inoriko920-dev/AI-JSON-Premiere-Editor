/* STEP06 Premiere Pro 2024 CEP/ExtendScript ES3 guarded import candidate.
 * NOT loaded in CSXS ScriptPath and NOT called by the user-facing panel.
 * The input must come from the Python media snapshot and an independent
 * verified preflight + owner consent. A snapshot's SHA alone grants NOTHING.
 * Failed post-mutation operations are preserved as INCOMPLETE; no deletes.
 */
if (typeof $ === "undefined") { var $ = {}; }
$._AIJSON_MEDIA_IMPORT_V1 = (function () {
    function project() {
        return (typeof app !== "undefined" && app && app.project) ?
            app.project : null;
    }
    function hostVersion() { return typeof app !== "undefined" && app ?
        String(app.version || "") : ""; }
    function validBinName(v) {
        return typeof v === "string" && /^AIJSON_MEDIA_[A-Za-z0-9_-]{8,54}$/.test(v);
    }
    function hash(v) { return typeof v === "string" && /^[a-f0-9]{64}$/.test(v); }
    function validPath(v) {
        if (typeof v !== "string" || v.length > 1024 ||
            !/^[A-Za-z]:[\\\/]/.test(v) ||
            /[\x00-\x1f|<>"?*]/.test(v)) { return false; }
        var elements = v.replace(/\//g,"\\").split("\\");
        for (var j=0;j<elements.length;j++) {
            if (elements[j] === "." || elements[j] === ".." || elements[j] === "") {
                if (j!==0) { return false; }
            }
        }
        return true;
    }
    function pathKey(p) {return p.replace(/\//g,"\\").toLowerCase();}
    function children(bin) {
        return bin && bin.children && typeof bin.children.numItems === "number" &&
            bin.children.numItems >= 0 && bin.children.numItems < 100000 &&
            Math.floor(bin.children.numItems) === bin.children.numItems ?
            bin.children.numItems : -1;
    }
    function validateEntries(snapshot) {
        if (!snapshot || snapshot.schema_version!=="verified-media-snapshot-v1" ||
            snapshot.status!=="CANDIDATE_NOT_AUTHORIZED" ||
            snapshot.can_import!==false || snapshot.can_assemble!==false ||
            !hash(snapshot.inventory_sha256) ||
            Object.prototype.toString.call(snapshot.items)!=="[object Array]" || snapshot.items.length < 4 ||
            snapshot.items.length > 2000 ||
            snapshot.item_count!==snapshot.items.length) {return null;}
        var ids={},paths={},importCount=0,kindCounts={srt:0,audio:0,background:0,png:0};
        for(var i=0;i<snapshot.items.length;i++) {
            var x=snapshot.items[i];
            if (!x || typeof x.item_id!=="string" ||
                !/^(SOURCE_(SRT|AUDIO|BACKGROUND)|ASSET_[A-Za-z0-9_-]{1,90})$/.test(x.item_id) ||
                ids[x.item_id] ||
                !validPath(x.absolute_path) ||
                !hash(x.sha256) || !hash(snapshot.inventory_sha256) ||
                typeof x.byte_size!=="number" || x.byte_size < 1 ||
                Math.floor(x.byte_size)!==x.byte_size ||
                x.byte_size > 9007199254740991 ||
                typeof x.mtime_ns!=="number" || x.mtime_ns < 0 ||
                !kindCounts.hasOwnProperty(x.kind)) {return null;}
            if (x.item_id==="SOURCE_SRT" && (x.kind!=="srt"||x.import_to_premiere!==false)) {return null;}
            if (x.item_id==="SOURCE_AUDIO" && (x.kind!=="audio"||x.import_to_premiere!==true)) {return null;}
            if (x.item_id==="SOURCE_BACKGROUND" && (x.kind!=="background"||x.import_to_premiere!==true)) {return null;}
            if (x.item_id.indexOf("ASSET_")===0 && (x.kind!=="png"||x.import_to_premiere!==true)) {return null;}
            var extensions={
                srt:/\.srt$/i,audio:/\.(mp3|wav)$/i,
                background:/\.mp4$/i,png:/\.png$/i
            };
            if (!extensions[x.kind].test(x.absolute_path)) {return null;}
            ids[x.item_id]=true;
            var key=pathKey(x.absolute_path);
            if(paths[key]){return null;}
            paths[key]=true;
            kindCounts[x.kind]++;
            if(x.import_to_premiere){importCount++;}
        }
        if (kindCounts.srt!==1 || kindCounts.audio!==1 ||
            kindCounts.background!==1 || kindCounts.png<1 ||
            snapshot.import_count!==importCount) {return null;}
        return true;
    }
    function validateDisk(snapshot) {
        if(typeof File!=="function"){return false;}
        for(var i=0;i<snapshot.items.length;i++){
            var item=snapshot.items[i], f;
            try { f=new File(item.absolute_path); } catch(ex) {return false;}
            if(!f || f.exists!==true ||
                typeof f.length!=="number" || f.length!==item.byte_size ||
                !validPath(String(f.fsName||"")) ||
                pathKey(String(f.fsName))!==pathKey(item.absolute_path)) {
                return false;
            }
        }
        return true;
    }
    function existingRoot(root,targetName) {
        var count=children(root);
        if(count<0){return null;}
        var ids={},names={};
        for(var i=0;i<count;i++){
            var child=root.children[i];
            if(!child || typeof child.nodeId!=="string" ||
                !child.nodeId.length || typeof child.name!=="string"){return null;}
            if(ids[child.nodeId]){return null;}
            ids[child.nodeId]=true;
            names[child.name.toLowerCase()]=true;
        }
        return {count:count,ids:ids,names:names};
    }
    function importFresh(snapshot,targetName,authorization) {
        /* Called only by a future reviewed internal host dispatcher.
         * A forged truthy status in either JSON is NOT authorization.
         * No source byte SHA is calculated in ExtendScript: external Python
         * must rehash immediately before a host operation is explicitly approved.
         */
        try {
            var p=project(),version=hostVersion();
            if(!p){return "S6|1|BLOCKED|NO_PROJECT";}
            if(!/^24\./.test(version)){return "S6|1|BLOCKED|HOST_UNSUPPORTED";}
            if(!authorization ||
                authorization.kind!=="HOST_REVIEWED_IMPORT_V1" ||
                authorization.ownerConfirmed!==true ||
                authorization.hostCapabilityVerified!==true ||
                authorization.mediaHashesFresh!==true ||
                authorization.preflightAllPass!==true ||
                authorization.hostVersion!==version ||
                !snapshot || authorization.snapshotDigest!==snapshot.inventory_sha256) {
                return "S6|1|BLOCKED|AUTHORIZATION_NOT_VERIFIED";
            }
            if(!validBinName(targetName) || !validateEntries(snapshot)) {
                return "S6|1|BLOCKED|IMPORT_MANIFEST_INVALID";
            }
            if(!validateDisk(snapshot)){
                return "S6|1|BLOCKED|SOURCE_CHANGED_OR_MISSING";
            }
            var root=p.rootItem,pre=existingRoot(root,targetName);
            if(!pre){return "S6|1|BLOCKED|PROJECT_REGISTRY_UNAVAILABLE";}
            if(pre.names[targetName.toLowerCase()]){
                return "S6|1|BLOCKED|MANAGED_BIN_ALREADY_EXISTS";
            }
            if(typeof root.findItemsMatchingMediaPath!=="function" ||
                typeof root.createBin!=="function" ||
                typeof p.importFiles!=="function"){
                return "S6|1|BLOCKED|IMPORT_API_UNAVAILABLE";
            }
            for(var i=0;i<snapshot.items.length;i++){
                var path=snapshot.items[i].absolute_path,match;
                if(!snapshot.items[i].import_to_premiere){continue;}
                match=root.findItemsMatchingMediaPath(path,1);
                if(match!==0 && !(Object.prototype.toString.call(match)==="[object Array]" && match.length===0)){
                    return "S6|1|BLOCKED|MEDIA_ALREADY_IN_PROJECT";
                }
            }
            /* FIRST host mutation: new, unique, empty managed bin. */
            var bin=root.createBin(targetName),after=existingRoot(root,targetName);
            if(!bin || !after || after.count!==pre.count+1 ||
                !bin.nodeId || pre.ids[String(bin.nodeId)] ||
                children(bin)!==0) {
                return "S6|1|INCOMPLETE|BIN_READBACK_FAILED";
            }
            var imported=0;
            for(var j=0;j<snapshot.items.length;j++){
                var entry=snapshot.items[j];
                if(!entry.import_to_premiere){continue;}
                var beforeCount=children(bin);
                if(beforeCount!==imported){
                    return "S6|1|INCOMPLETE|BIN_CHANGED_DURING_IMPORT";
                }
                if(!validateDisk(snapshot)){
                    return "S6|1|INCOMPLETE|SOURCE_CHANGED_AFTER_BIN_CREATE";
                }
                var ok=p.importFiles([entry.absolute_path],true,bin,false);
                if(ok!==true){return "S6|1|INCOMPLETE|IMPORT_API_FAILED";}
                if(children(bin)!==beforeCount+1){
                    return "S6|1|INCOMPLETE|IMPORT_COUNT_MISMATCH";
                }
                var child=bin.children[beforeCount],actual;
                if(!child || typeof child.getMediaPath!=="function" ||
                    typeof child.nodeId!=="string" || !child.nodeId.length) {
                    return "S6|1|INCOMPLETE|MEDIA_READBACK_FAILED";
                }
                actual=String(child.getMediaPath()||"");
                if(!validPath(actual)||pathKey(actual)!==pathKey(entry.absolute_path)){
                    return "S6|1|INCOMPLETE|MEDIA_PATH_MISMATCH";
                }
                imported++;
            }
            if(imported!==snapshot.import_count){
                return "S6|1|INCOMPLETE|FINAL_COUNT_MISMATCH";
            }
            /* No project save; no user file deletion, re-link or clip placement. */
            return "S6|1|IMPORTED_TO_NEW_BIN|"+String(imported);
        } catch(e){
            /* Exception may happen after createBin/importFiles: DO NOT retry. */
            return "S6|1|INCOMPLETE|HOST_IMPORT_EXCEPTION";
        }
    }
    return {importFresh:importFresh};
}());
