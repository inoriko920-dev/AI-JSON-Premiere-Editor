/* STEP04 read-only file selection and validation: never READY or Premiere mutation. */
(function(root){
    "use strict";
    var doc=root.document;
    if(!doc){return;}
    function init(){
        var kinds=["edit","animation","media"];
        var buttons={
            edit:doc.getElementById("choose-edit"),
            animation:doc.getElementById("choose-animation"),
            media:doc.getElementById("choose-media")
        };
        var labels={
            edit:doc.getElementById("selected-edit"),
            animation:doc.getElementById("selected-animation"),
            media:doc.getElementById("selected-media")
        };
        var runButton=doc.getElementById("btn-validate-offline");
        var status=doc.getElementById("validation-summary");
        var paths={edit:null,animation:null,media:null};
        var closed=false;
        var nativeFs=root.cep && root.cep.fs;
        var nodeReq=root.cep_node && typeof root.cep_node.require==="function"?
            root.cep_node.require:(typeof root.require==="function"?root.require:null);
        var nodeProc=root.cep_node && root.cep_node.process?
            root.cep_node.process:root.process;
        var cep=root.__adobe_cep__;
        var nodePath=null,client=null,hasPicker=false;

        if(nodeReq && nodeProc && cep && typeof cep.getSystemPath==="function" &&
           nativeFs && typeof nativeFs.showOpenDialogEx==="function" &&
           root.AIJSONValidationBridge && root.AIJSONP0Helper) {
            try {
                nodePath=nodeReq("path");
                var nodeFS=nodeReq("fs");
                var processAPI=nodeReq("child_process");
                client=root.AIJSONValidationBridge.createValidator({
                    path:nodePath,fs:nodeFS,execFile:processAPI.execFile,
                    platform:nodeProc.platform,
                    pythonExe:nodeProc.env && nodeProc.env.AIJSON_P0_PYTHON_EXE,
                    ffprobeExe:nodeProc.env && nodeProc.env.AIJSON_P0_FFPROBE_EXE,
                    extensionPath:cep.getSystemPath("extension"),
                    decodeExtensionPath:root.AIJSONP0Helper.decodeExtensionPath
                });
                hasPicker=true;
            } catch(e){hasPicker=false;}
        }
        function resetResult(){
            status.className="detail";
            status.textContent="Input berubah; hasil pemeriksaan lama dibatalkan. Belum READY.";
        }
        function refresh(){
            var valid=!!(paths.edit&&paths.animation&&paths.media);
            for(var i=0;i<kinds.length;i++){
                buttons[kinds[i]].disabled=closed||!hasPicker;
            }
            runButton.disabled=closed||!hasPicker||!valid||client.isBusy();
        }
        function onPick(kind){
            if(closed||!hasPicker){return;}
            var result=root.AIJSONValidationBridge.selectNative(nativeFs,kind,nodePath);
            if(result.status==="cancelled"){return;}
            if(result.status!=="selected"){
                status.className="status bad";
                status.textContent="Gagal memilih input: "+result.code+".";
                return;
            }
            if(client){client.cancel();}
            paths[kind]=result.path;
            // Only show the basename, never disclose the selected folder hierarchy.
            labels[kind].textContent=kind==="media"?
                "Folder terpilih":nodePath.win32.basename(result.path);
            resetResult();refresh();
        }
        for(var i=0;i<kinds.length;i++){
            (function(kind){
                buttons[kind].addEventListener("click",function(){onPick(kind);});
            }(kinds[i]));
        }
        runButton.addEventListener("click",function(){
            if(closed||!hasPicker||runButton.disabled||client.isBusy()||
                !paths.edit||!paths.animation||!paths.media){return;}
            status.className="status wait";
            status.textContent="Memeriksa file secara offline…";
            runButton.disabled=true;
            var started=client.run({
                edit:paths.edit,animation:paths.animation,media:paths.media
            },function(result){
                if(closed){return;}
                refresh();
                status.className="status bad";
                if(result.status==="error"){
                    status.textContent="Validasi tidak dapat berjalan: "+result.code+
                        ". Tidak ada perubahan proyek.";
                    return;
                }
                var codes=[];
                for(var j=0;j<result.issues.length && codes.length<6;j++){
                    codes.push(result.issues[j].code);
                }
                status.className=result.status==="PREFLIGHT_FAIL"?"status bad":"status wait";
                var draftLine=result.draft ?
                    " · draft "+result.draft.scene_count+" scene / "+
                        result.draft.asset_instance_count+" visual / "+
                        result.draft.total_frames+" frame (belum dapat dieksekusi)" : "";
                var importLine=result.import_snapshot ?
                    " · "+result.import_snapshot.import_count+
                    " media tercatat (HANYA KANDIDAT, belum izin impor)" : "";
                var trackLine=result.track_candidate ?
                    " · V1:"+result.track_candidate.counts.V1+
                    " V2:"+result.track_candidate.counts.V2+
                    " V3:"+result.track_candidate.counts.V3+
                    " A1:"+result.track_candidate.counts.A1+
                    " (KANDIDAT BELUM DAPAT DIEKSEKUSI)" : "";
                var phaseLine=result.animation_phases ?
                    " · BOTH "+result.animation_phases.instance_count+
                    " visual (fase referensi, 0 efek dibuat)" +
                    (result.animation_phases.zero_hold_count ?
                     ", "+result.animation_phases.zero_hold_count+" tanpa HOLD" : "") :
                    "";
                status.textContent="Validasi offline "+result.status+
                    " · error "+result.error_count+" · review "+result.review_count+
                    " · kode: "+(codes.join(", ")||"—")+draftLine+importLine+
                    trackLine+phaseLine+". Timeline tetap terkunci.";
            });
            if(!started){refresh();}
        });
        function teardown(){
            if(closed){return;}
            closed=true;
            if(client){client.cancel();}
            refresh();
        }
        if(typeof root.addEventListener==="function"){
            root.addEventListener("pagehide",teardown);
            root.addEventListener("unload",teardown);
        }
        if(!hasPicker){
            status.textContent="Dialog CEP/Node tidak tersedia. Jalankan di Premiere Pro 2024 dengan helper lokal.";
        }
        refresh();
    }
    if(doc.readyState==="loading"){doc.addEventListener("DOMContentLoaded",init);}
    else{init();}
}(this));
