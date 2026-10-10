/* STEP24 guarded, read-only native FADE clip probe envelope (ES3).
 *
 * Requires separately loaded STEP22 inspector; NOT wired into CEP production.
 * An echoed digest/nonce is ONLY a correlation check, not authentication,
 * and an OBSERVED record is NEVER Premiere host certification/permission
 * to write keyframes. No external code, eval or host timeline mutation.
 */
if (typeof $ === "undefined") { var $ = {}; }
$._AIJSON_FADE_READBACK_V1=(function(){
    function valid(s,re){return typeof s==="string" && re.test(s);}
    function guid(s){return valid(s,/^[a-f0-9]{8}(-[a-f0-9]{4}){3}-[a-f0-9]{12}$/);}
    function ticks(s){return valid(s,/^(0|[1-9][0-9]{0,25})$/);}
    function earlier(a,b){return a.length<b.length || a.length===b.length && a<b;}
    function inspect(nonce,digest,id,name,track,start,end,node){
        try{
            if(!valid(nonce,/^[a-f0-9]{32}$/) ||
               !valid(digest,/^[a-f0-9]{64}$/) ||
               !guid(id) ||
               !valid(name,/^AIJSON_MANAGED_[A-Za-z0-9_-]{4,64}$/) ||
               (track!=="V2" && track!=="V3") ||
               !ticks(start) || !ticks(end) || !earlier(start,end) ||
               !valid(node,/^[A-Za-z0-9_.-]{1,80}$/)){
                return "S24|1|BLOCKED|SELECTOR_INVALID";
            }
            if(typeof app==="undefined" || !app || !app.project ||
               !app.project.activeSequence ||
               app.project.activeSequence.name!==name){
                return "S24|1|BLOCKED|SEQUENCE_NAME_MISMATCH";
            }
            if(typeof $._AIJSON_NATIVE_OPACITY_INSPECT_V1!=="object" ||
               !$._AIJSON_NATIVE_OPACITY_INSPECT_V1 ||
               typeof $._AIJSON_NATIVE_OPACITY_INSPECT_V1.inspect!=="function"){
                return "S24|1|BLOCKED|INSPECTOR_UNAVAILABLE";
            }
            // Actual STEP22 read-only inspector compares the selected clip's
            // sequence ID, track, start/end ticks and imported media node ID.
            var reply=$._AIJSON_NATIVE_OPACITY_INSPECT_V1.inspect(
                id,track,start,node,end);
            if(typeof reply!=="string" ||
               reply.indexOf("S22|1|OBSERVED_UNCERTIFIED|")!==0){
                return "S24|1|BLOCKED|CLIP_INSPECTION_FAILED";
            }
            var encoded=encodeURIComponent(reply);
            if(encoded.length>24576){return "S24|1|BLOCKED|RESOURCE_LIMIT";}
            var envelope="S24|1|OBSERVED_UNCERTIFIED|"+
              nonce+"|"+digest+"|"+id+"|"+name+"|"+track+"|"+
              start+"|"+end+"|"+node+"|"+encoded;
            if(envelope.length>26000){return "S24|1|BLOCKED|RESOURCE_LIMIT";}
            return envelope;
        }catch(e){return "S24|1|BLOCKED|INSPECTION_EXCEPTION";}
    }
    return {inspect:inspect};
}());
