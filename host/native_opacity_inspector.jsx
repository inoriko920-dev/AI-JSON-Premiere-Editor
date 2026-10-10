/* STEP22 Premiere Pro 2024 (ES3) read-only Opacity capability inventory.
 *
 * This script IS NOT loaded by the CEP panel. It never sets keyframes,
 * calls setValue, modifies a sequence, selects clips, imports media or calls
 * the QE DOM. Inspect exactly one clip inside the caller-identified existing
 * AIJSON-managed sequence. No component/parameter name is assumed to mean
 * Opacity until independently verified in a real Premiere 24.x host.
 *
 * Mock host tests prove control flow, NOT actual Premiere compatibility.
 */
if (typeof $ === "undefined") { var $ = {}; }
$._AIJSON_NATIVE_OPACITY_INSPECT_V1=(function () {
    function finiteInteger(n,lower,upper){
        return typeof n==="number" && isFinite(n) && Math.floor(n)===n &&
               n>=lower && n<=upper;
    }
    function ticks(s){
        return typeof s==="string" && /^(0|[1-9][0-9]{0,25})$/.test(s);
    }
    function earlier(a,b){
        return a.length<b.length || (a.length===b.length && a<b);
    }
    function safeName(s){
        return typeof s==="string" && s.length>0 && s.length<=80 &&
               !/[\u0000-\u001f\u007f]/.test(s);
    }
    function collection(c,limit){
        if(!c || !finiteInteger(c.numItems,0,limit)){return -1;}
        return c.numItems;
    }
    function tracks(c){
        if(!c || !finiteInteger(c.numTracks,1,32)){return -1;}
        return c.numTracks;
    }
    function inspect(sequenceId, trackName, startTicks, sourceNodeId, endTicks){
        try {
            if (typeof app==="undefined" || !app || !app.project) {
                return "S22|1|BLOCKED|NO_HOST_PROJECT";
            }
            var version=String(app.version||"");
            if(!/^24\.[0-9]+(\.[0-9]+){0,2}$/.test(version)){
                return "S22|1|BLOCKED|HOST_VERSION_UNVERIFIED";
            }
            if(typeof sequenceId!=="string" ||
               !/^[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$/.test(sequenceId) ||
               (trackName!=="V2" && trackName!=="V3") ||
               !ticks(startTicks) || !ticks(endTicks) ||
               !earlier(startTicks,endTicks) ||
               !safeName(sourceNodeId) ||
               !/^[A-Za-z0-9_.-]+$/.test(sourceNodeId)){
                return "S22|1|BLOCKED|SELECTOR_INVALID";
            }
            var seq=app.project.activeSequence;
            if(!seq ||
               typeof seq.name!=="string" ||
               !/^AIJSON_MANAGED_[A-Za-z0-9_-]{4,64}$/.test(seq.name) ||
               String(seq.sequenceID||"").toLowerCase()!==sequenceId.toLowerCase()){
                return "S22|1|BLOCKED|MANAGED_SEQUENCE_MISMATCH";
            }
            if(!seq.videoTracks || tracks(seq.videoTracks)<3){
                return "S22|1|BLOCKED|TRACKS_UNAVAILABLE";
            }
            var t=seq.videoTracks[trackName==="V2"?1:2];
            if(!t || !t.clips){return "S22|1|BLOCKED|TRACKS_UNAVAILABLE";}
            var n=collection(t.clips,10000);
            if(n<0){return "S22|1|BLOCKED|CLIPS_UNAVAILABLE";}
            var selected=null,hits=0,i,clip;
            for(i=0;i<n;i++){
                clip=t.clips[i];
                if(!clip || !clip.start || !clip.projectItem){
                    return "S22|1|BLOCKED|CLIP_READBACK_FAILED";
                }
                if(String(clip.start.ticks||"")===startTicks &&
                   String(clip.projectItem.nodeId||"")===sourceNodeId){
                    selected=clip;hits++;
                }
            }
            if(hits!==1){
                return hits===0?"S22|1|BLOCKED|CLIP_NOT_FOUND":
                                "S22|1|BLOCKED|CLIP_AMBIGUOUS";
            }
            // Source+start can match a clip that was shortened, extended
            // or manually trimmed. Reject changed duration before returning
            // any component inventory; do not modify the user timeline.
            if(!selected.end || String(selected.end.ticks||"")!==endTicks){
                return "S22|1|BLOCKED|CLIP_END_MISMATCH";
            }
            // Candidate output only: the host's Opacity effect/component
            // matchName, locale-specific labels, numeric units and time
            // coordinate conventions are NOT known or authorized here.
            var cs=selected.components,count=collection(cs,20);
            if(count<1){return "S22|1|BLOCKED|COMPONENTS_UNAVAILABLE";}
            var output=[],comp,p,properties,m,j,seen={};
            for(i=0;i<count;i++){
                comp=cs[i];
                if(!comp || !safeName(comp.matchName)){
                    return "S22|1|BLOCKED|COMPONENT_ID_UNVERIFIED";
                }
                m=encodeURIComponent(comp.matchName);
                if(m.length>180 || seen[m]){
                    return "S22|1|BLOCKED|COMPONENT_DUPLICATE_OR_UNSAFE";
                }
                seen[m]=true;
                properties=comp.properties;
                var plen=collection(properties,32);
                if(plen<0){return "S22|1|BLOCKED|PROPERTIES_UNAVAILABLE";}
                var labels=[];
                for(j=0;j<plen;j++){
                    p=properties[j];
                    if(!p || !safeName(p.displayName)){
                        return "S22|1|BLOCKED|PROPERTY_LABEL_UNVERIFIED";
                    }
                    var enc=encodeURIComponent(p.displayName);
                    if(enc.length>180){
                        return "S22|1|BLOCKED|PROPERTY_LABEL_UNVERIFIED";
                    }
                    // No setters, no host method invocation for parameters:
                    // this is strictly a structural, read-only inventory.
                    labels.push(enc);
                }
                output.push(m+":"+labels.join(","));
            }
            var report="S22|1|OBSERVED_UNCERTIFIED|"+version+"|"+
                       String(count)+"|"+output.join(";");
            if(report.length>8192){
                return "S22|1|BLOCKED|REPORT_RESOURCE_LIMIT";
            }
            return report;
        } catch(e) {
            return "S22|1|BLOCKED|HOST_INSPECTION_EXCEPTION";
        }
    }
    return {inspect:inspect};
}());
