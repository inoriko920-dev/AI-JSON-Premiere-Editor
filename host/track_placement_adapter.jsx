/* STEP07 — guarded ES3 V2/V3 still placement candidate.
 * NOT LOADED by CEP ScriptPath. NOT production-ready. Only intended for
 * reviewed new managed sequence AND managed bin, with exact caller-supplied
 * full track readback. No automatic source trimming and NO V1/A1 insertion.
 * A mismatched post-mutation result is INCOMPLETE and never auto-deleted.
 */
if (typeof $ === "undefined") { var $ = {}; }
$._AIJSON_STILL_PLACEMENT_V1 = (function(){
    function guid(v){return typeof v==="string" && /^[0-9a-f-]{36}$/i.test(v);}
    function ticks(v){return typeof v==="string" && /^(0|[1-9][0-9]{0,34})$/.test(v);}
    function hash(v){return typeof v==="string" && /^[a-f0-9]{64}$/.test(v);}
    function id(v){return typeof v==="string" && /^[A-Za-z0-9_.-]{1,90}$/.test(v);}
    function arr(v){return Object.prototype.toString.call(v)==="[object Array]";}
    function children(bin){
        if(!bin || !bin.children || typeof bin.children.numItems!=="number" ||
           bin.children.numItems<0 || bin.children.numItems>10000) {return -1;}
        return bin.children.numItems;
    }
    function sequence(p,sequenceId){
        if(!p || !p.sequences || typeof p.sequences.numSequences!=="number" ||
            p.sequences.numSequences>10000){return null;}
        var found=null;
        for(var i=0;i<p.sequences.numSequences;i++){
            var s=p.sequences[i];
            if(s && String(s.sequenceID||"").toLowerCase()===sequenceId.toLowerCase()){
                if(found){return null;}
                found=s;
            }
        }
        return found;
    }
    function getClips(track){
        if(!track || !track.clips || typeof track.clips.numItems!=="number" ||
            track.clips.numItems<0 || track.clips.numItems>10000 ||
            Math.floor(track.clips.numItems)!==track.clips.numItems){return null;}
        var result=[];
        for(var j=0;j<track.clips.numItems;j++){
            var clip=track.clips[j];
            if(!clip || typeof clip.nodeId!=="string" || !clip.nodeId ||
                !clip.projectItem || typeof clip.projectItem.nodeId!=="string" ||
                !clip.start || !clip.end){return null;}
            var start=String(clip.start.ticks),end=String(clip.end.ticks);
            if(!ticks(start)||!ticks(end)){return null;}
            result.push({nodeId:clip.nodeId,
                projectItemNodeId:clip.projectItem.nodeId,
                startTicks:start,endTicks:end,
                mediaType:String(clip.mediaType||"")});
        }
        return result;
    }
    function fullState(s){
        if(!s || !s.videoTracks || !s.audioTracks ||
            s.videoTracks.numTracks<3 || s.audioTracks.numTracks<1 ||
            s.videoTracks.numTracks>32 || s.audioTracks.numTracks>32){return null;}
        var rows=[];
        for(var kind=0;kind<2;kind++){
            var tracks=kind===0?s.videoTracks:s.audioTracks;
            for(var n=0;n<tracks.numTracks;n++){
                var clips=getClips(tracks[n]);
                if(!clips){return null;}
                rows.push({track:(kind===0?"V":"A")+(n+1),clips:clips});
            }
        }
        return rows;
    }
    function same(a,b){
        if(!arr(a)||!arr(b)||a.length!==b.length){return false;}
        for(var i=0;i<a.length;i++){
            if(!a[i] || !b[i] || a[i].track!==b[i].track ||
                !arr(a[i].clips)||!arr(b[i].clips)||
                a[i].clips.length!==b[i].clips.length){return false;}
            for(var j=0;j<a[i].clips.length;j++){
                var x=a[i].clips[j],y=b[i].clips[j];
                if(!x||!y||x.nodeId!==y.nodeId||
                    x.projectItemNodeId!==y.projectItemNodeId||
                    x.startTicks!==y.startTicks||x.endTicks!==y.endTicks||
                    x.mediaType!==y.mediaType){return false;}
            }
        }
        return true;
    }
    function importItem(p,binId,sourceNodeId){
        if(!p.rootItem || children(p.rootItem)<0){return null;}
        var bin=null;
        for(var i=0;i<p.rootItem.children.numItems;i++){
            var x=p.rootItem.children[i];
            if(x && x.nodeId===binId){if(bin){return null;}bin=x;}
        }
        if(!bin || typeof bin.name!=="string" ||
            !/^AIJSON_MEDIA_[A-Za-z0-9_-]{8,54}$/.test(bin.name) ||
            children(bin)<0){return null;}
        var item=null;
        for(var j=0;j<bin.children.numItems;j++){
            var child=bin.children[j];
            if(child && child.nodeId===sourceNodeId){
                if(item){return null;}item=child;
            }
        }
        if(!item || typeof item.getMediaPath!=="function" ||
            !/\.png$/i.test(String(item.getMediaPath()||""))){return null;}
        return item;
    }
    function placeStill(operation,previousState,authorization){
        try{
            if(typeof app==="undefined" || !app || !app.project ||
               !/^24\./.test(String(app.version||""))) {
                return "S7|1|BLOCKED|HOST_UNAVAILABLE";
            }
            if(!operation || !authorization || !previousState ||
                authorization.kind!=="HOST_REVIEWED_TRACK_PLACEMENT_V1" ||
                authorization.ownerConfirmed!==true ||
                authorization.preflightAllPass!==true ||
                authorization.hostCapabilityVerified!==true ||
                authorization.layoutVerified!==true ||
                authorization.fxBackendVerified!==true ||
                authorization.sourceTimingVerified!==true ||
                authorization.hostVersion!==String(app.version) ||
                !hash(authorization.operationDigest) ||
                authorization.operationDigest!==operation.worklist_digest_sha256 ||
                !hash(operation.snapshot_digest_sha256) ||
                authorization.snapshotDigest!==operation.snapshot_digest_sha256) {
                return "S7|1|BLOCKED|AUTHORIZATION_NOT_VERIFIED";
            }
            if(!guid(operation.sequenceId)||!id(operation.assetId) ||
               !id(operation.sourceNodeId)||!id(operation.binNodeId) ||
               operation.media_item_id!=="ASSET_"+operation.assetId ||
               (operation.track!=="V2"&&operation.track!=="V3") ||
               operation.zero_based_track_index!==(operation.track==="V2"?1:2) ||
               !ticks(operation.start_ticks)||!ticks(operation.end_ticks) ||
               !ticks(operation.expected_duration_ticks)||
               operation.native_trim_verified!==true ||
               operation.effect_backend_verified!==true){
                return "S7|1|BLOCKED|STILL_OPERATION_INVALID";
            }
            var seq=sequence(app.project,operation.sequenceId);
            if(!seq || typeof seq.name!=="string" ||
               !/^AIJSON[_ ]/.test(seq.name) ||
               String(seq.timebase||"")!==operation.ticks_per_frame ||
               seq.frameSizeHorizontal!==1920 ||
               seq.frameSizeVertical!==1080){
                return "S7|1|BLOCKED|MANAGED_SEQUENCE_MISSING";
            }
            var before=fullState(seq);
            if(!before || !arr(previousState.rows) ||
               !same(before,previousState.rows) ||
               previousState.sequenceId!==operation.sequenceId) {
                return "S7|1|BLOCKED|TIMELINE_CHANGED";
            }
            var item=importItem(app.project,operation.binNodeId,
                               operation.sourceNodeId);
            if(!item){return "S7|1|BLOCKED|MANAGED_MEDIA_MISSING";}
            var target=seq.videoTracks[operation.zero_based_track_index];
            if(!target || typeof target.overwriteClip!=="function"){
                return "S7|1|BLOCKED|HOST_OVERWRITE_API_MISSING";
            }
            var onTrack=getClips(target);
            if(!onTrack){return "S7|1|BLOCKED|TIMELINE_UNREADABLE";}
            // No clip may be overwritten even if it belongs to our bin.
            // Tick strings are compared lexically by length rather than Number.
            function cmp(a,b){
                return a.length===b.length?(a<b?-1:a>b?1:0):
                    a.length<b.length?-1:1;
            }
            if(cmp(operation.start_ticks,operation.end_ticks)>=0){return "S7|1|BLOCKED|TIMING_INVALID";}
            for(var i=0;i<onTrack.length;i++){
                if(cmp(operation.start_ticks,onTrack[i].endTicks)<0 &&
                   cmp(operation.end_ticks,onTrack[i].startTicks)>0){
                    return "S7|1|BLOCKED|WOULD_OVERWRITE_EXISTING_CLIP";
                }
            }
            // First and ONLY host mutation; never retry on ambiguous outcomes.
            var result=target.overwriteClip(item,operation.start_ticks);
            if(result!==true){return "S7|1|INCOMPLETE|HOST_OVERWRITE_FAILED";}
            var after=fullState(seq);
            if(!after || after.length!==before.length) {
                return "S7|1|INCOMPLETE|TRACK_READBACK_FAILED";
            }
            var targetName=operation.track,oldRow=null,newRow=null;
            for(var k=0;k<before.length;k++){
                if(before[k].track===targetName){
                    oldRow=before[k];newRow=after[k];
                } else if(!same([before[k]],[after[k]])){
                    return "S7|1|INCOMPLETE|OTHER_TRACK_MODIFIED";
                }
            }
            if(!oldRow || !newRow ||
                newRow.clips.length!==oldRow.clips.length+1){
                return "S7|1|INCOMPLETE|CLIP_COUNT_MISMATCH";
            }
            var newClip=null,novel=0;
            for(var a=0;a<newRow.clips.length;a++){
                var existed=false;
                for(var b=0;b<oldRow.clips.length;b++){
                    if(newRow.clips[a].nodeId===oldRow.clips[b].nodeId){
                        if(newRow.clips[a].startTicks!==oldRow.clips[b].startTicks ||
                            newRow.clips[a].endTicks!==oldRow.clips[b].endTicks ||
                            newRow.clips[a].projectItemNodeId!==
                                oldRow.clips[b].projectItemNodeId){
                            return "S7|1|INCOMPLETE|PRIOR_CLIP_MUTATED";
                        }
                        existed=true;break;
                    }
                }
                if(!existed){novel++;newClip=newRow.clips[a];}
            }
            if(novel!==1 || !newClip ||
                newClip.projectItemNodeId!==operation.sourceNodeId ||
                newClip.startTicks!==operation.start_ticks ||
                newClip.endTicks!==operation.end_ticks ||
                newClip.mediaType!=="Video"){
                return "S7|1|INCOMPLETE|CLIP_TIMING_READBACK_MISMATCH";
            }
            return "S7|1|PLACED_STILL|"+newClip.nodeId;
        }catch(e){return "S7|1|INCOMPLETE|HOST_PLACE_EXCEPTION";}
    }
    return {placeStill:placeStill,inspectManaged:function(s){
        try{return fullState(s);}catch(e){return null;}
    }};
}());
