/* STEP04 CEP native picker + safe Python read-only validation boundary. */
(function (root, factory) {
    "use strict";
    var api=factory();
    if (root && root.document) { root.AIJSONValidationBridge=api; }
    if (typeof module==="object" && module.exports) { module.exports=api; }
}(this,function () {
    "use strict";
    var MAX_OUTPUT=512*1024;
    var READ_BUDGETS=Object.freeze({
        json:"1048576", media:"1073741824", cues:"10000"
    }); // Temporary explicit DEV limits, NOT production approved resource caps.

    function windowsPath(value,path,kind) {
        if (typeof value!=="string" || !/^[A-Za-z]:[\\/]/.test(value) ||
            value.length>1024 || /[\0-\x1f]/.test(value) ||
            !path || !path.win32 || !path.win32.isAbsolute(value)) { return null; }
        var canonical=path.win32.normalize(value);
        if (kind==="edit" && path.win32.basename(canonical).toLowerCase()!=="edit_plan.json") { return null; }
        if (kind==="animation" && path.win32.basename(canonical).toLowerCase()!=="animation_plan.json") { return null; }
        if ((kind==="edit" || kind==="animation") && path.win32.extname(canonical).toLowerCase()!==".json") { return null; }
        return canonical;
    }
    function selectNative(cepFs,kind,path) {
        if (!cepFs || typeof cepFs.showOpenDialogEx!=="function" ||
            ["edit","animation","media"].indexOf(kind)===-1) {
            return {status:"error",code:"CEP_DIALOG_UNAVAILABLE"};
        }
        var folders=kind==="media";
        var title=kind==="edit"?"Pilih EDIT_PLAN.json":kind==="animation"?
            "Pilih ANIMATION_PLAN.json":"Pilih folder media proyek";
        try {
            var chosen=cepFs.showOpenDialogEx(false,folders,title,"",
                folders?[]:["json"],"File JSON","Pilih");
            if (!chosen || chosen.err!==0) { return {status:"error",code:"CEP_DIALOG_ERROR"}; }
            if (!Array.isArray(chosen.data) || chosen.data.length===0) {
                return {status:"cancelled",code:"SELECTION_CANCELLED"};
            }
            if (chosen.data.length!==1) { return {status:"error",code:"SELECTION_COUNT_INVALID"}; }
            var value=windowsPath(chosen.data[0],path,kind);
            return value ? {status:"selected",path:value} :
                {status:"error",code:"SELECTION_PATH_INVALID"};
        } catch(e) { return {status:"error",code:"CEP_DIALOG_ERROR"}; }
    }
    function parseReport(raw) {
        if(typeof raw!=="string" || raw.length>MAX_OUTPUT){
            return {status:"error",code:"VALIDATOR_RESPONSE_INVALID"};
        }
        var obj;
        try { obj=JSON.parse(raw); } catch(e) {
            return {status:"error",code:"VALIDATOR_RESPONSE_INVALID"};
        }
        if(!obj || typeof obj!=="object" || Array.isArray(obj) ||
            obj.schema_version!=="structure-validation-report-v1" ||
            ["PREFLIGHT_FAIL","NEEDS_REVIEW"].indexOf(obj.status)===-1 ||
            obj.can_assemble!==false ||
            !Number.isSafeInteger(obj.error_count) || obj.error_count<0 ||
            !Number.isSafeInteger(obj.review_count) || obj.review_count<0 ||
            !Array.isArray(obj.issues) || obj.issues.length>5000 ||
            obj.error_count+obj.review_count!==obj.issues.length) {
            return {status:"error",code:"VALIDATOR_RESPONSE_INVALID"};
        }
        var sanitized=[];
        for(var i=0;i<obj.issues.length;i++){
            var item=obj.issues[i];
            if(!item || typeof item!=="object" ||
                !/^[A-Z][A-Z0-9_]{1,60}$/.test(item.code||"") ||
                ["ERROR","REVIEW"].indexOf(item.severity)===-1) {
                return {status:"error",code:"VALIDATOR_RESPONSE_INVALID"};
            }
            sanitized.push({code:item.code,severity:item.severity});
        }
        // No untrusted path/message or arbitrary JSON is forwarded to the UI.
        return {status:obj.status,can_assemble:false,
            error_count:obj.error_count,review_count:obj.review_count,
            issues:sanitized};
    }
    function createValidator(deps){
        var active=false,generation=0,child=null;
        function cancel(){
            generation++;active=false;
            if(child&&typeof child.kill==="function"){
                try {child.kill();}catch(ignored){}
            }
            child=null;
        }
        function run(selection,callback){
            if(typeof callback!=="function"){throw new TypeError("callback wajib");}
            if(active){return false;}
            if(!deps || deps.platform!=="win32"){
                callback({status:"error",code:"VALIDATOR_WINDOWS_ONLY"});return false;
            }
            var fs=deps.fs,path=deps.path,execFile=deps.execFile;
            if(!fs||!path||typeof execFile!=="function"){
                callback({status:"error",code:"VALIDATOR_NODE_UNAVAILABLE"});return false;
            }
            var py=deps.pythonExe;
            var base=deps.decodeExtensionPath &&
                deps.decodeExtensionPath(deps.extensionPath,path);
            if(!base || !windowsPath(py,path,"python") ||
                path.win32.basename(py).toLowerCase()!=="python.exe"){
                callback({status:"error",code:!py?
                    "VALIDATOR_PYTHON_NOT_CONFIGURED":"VALIDATOR_PATH_INVALID"});
                return false;
            }
            if(!selection || typeof selection!=="object"){
                callback({status:"error",code:"VALIDATOR_INPUT_MISSING"});return false;
            }
            var edit=windowsPath(selection.edit,path,"edit"),
                animation=windowsPath(selection.animation,path,"animation"),
                media=windowsPath(selection.media,path,"media");
            if(!edit||!animation||!media){
                callback({status:"error",code:"VALIDATOR_INPUT_MISSING"});return false;
            }
            var script,realRoot;
            try{
                realRoot=fs.realpathSync(base);
                script=fs.realpathSync(path.win32.join(realRoot,"helper","validate_request.py"));
                var rootPrefix=realRoot.replace(/[\\/]+$/,"").toLowerCase()+"\\";
                if(script.toLowerCase().indexOf(rootPrefix)!==0 ||
                    !fs.statSync(script).isFile()||!fs.statSync(py).isFile()||
                    !fs.statSync(edit).isFile()||!fs.statSync(animation).isFile()||
                    !fs.statSync(media).isDirectory()){
                    callback({status:"error",code:"VALIDATOR_INPUT_MISSING"});return false;
                }
            }catch(e){
                callback({status:"error",code:"VALIDATOR_INPUT_MISSING"});return false;
            }
            active=true;
            var id=++generation;
            function finish(result){
                if(!active||id!==generation){return;}
                active=false;child=null;
                callback(result);
            }
            try{
                var args=["-I","-B",script,
                    "--edit",edit,"--animation",animation,
                    "--max-json-bytes",READ_BUDGETS.json,
                    "--media-root",media,
                    "--max-media-bytes",READ_BUDGETS.media,
                    "--max-srt-cues",READ_BUDGETS.cues];
                child=execFile(py,args,{
                    cwd:realRoot,shell:false,windowsHide:true,timeout:30000,
                    maxBuffer:MAX_OUTPUT,encoding:"utf8"
                },function(error,stdout){
                    if(error && error.killed){
                        finish({status:"error",code:"VALIDATOR_TIMEOUT"});return;
                    }
                    if(error && error.code!==2 && error.code!==3 &&
                        error.code!=="2" && error.code!=="3"){
                        finish({status:"error",code:"VALIDATOR_EXEC_FAILED"});return;
                    }
                    var report=parseReport(stdout);
                    if(report.status!=="error" && (
                        (error && (error.code===2||error.code==="2") &&
                            report.status!=="PREFLIGHT_FAIL") ||
                        (error && (error.code===3||error.code==="3") &&
                            report.status!=="NEEDS_REVIEW") ||
                        (!error))) {
                        // CLI must exit 2 for INVALID or 3 for REVIEW. Any 0 exit
                        // is suspicious; no implicit PASS/READY from this bridge.
                        finish({status:"error",code:"VALIDATOR_EXIT_MISMATCH"});return;
                    }
                    finish(report);
                });
            }catch(e){finish({status:"error",code:"VALIDATOR_EXEC_FAILED"});}
            return true;
        }
        return {run:run,cancel:cancel,isBusy:function(){return active;}};
    }
    return {selectNative:selectNative,createValidator:createValidator,
        parseReport:parseReport,windowsPath:windowsPath};
}));
