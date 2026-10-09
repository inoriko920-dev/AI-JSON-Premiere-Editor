/* STEP07 Premiere Pro 2024 ES3 candidate track placement adapter.
 * DISCONNECTED from CEP ScriptPath and all live UI controls.
 * Never run against user sequence; only newly created/verified managed sequence.
 * Track.overwriteClip operates only on an initially empty destination.
 * Trim newly inserted TrackItem only, do not modify master ProjectItem In/Out.
 * Any API discrepancy/linked-audio changes cause INCOMPLETE, never auto-delete.
 */
if (typeof $ === "undefined") { var $ = {}; }
$._AIJSON_TRACK_PLACER_V1 = (function () {
    var trackNames=["V1","V2","V3","A1"];
    function guid(v) {
        return typeof v==="string" &&
          /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/.test(v);
    }
    function ticks(v,allowZero) {
        return typeof v==="string" &&
            (allowZero ? /^(0|[1-9][0-9]{0,25})$/ : /^[1-9][0-9]{0,25}$/).test(v);
    }
    function track(seq, name) {
        if(name==="A1"){return seq.audioTracks && seq.audioTracks[0];}
        var n=({V1:0,V2:1,V3:2})[name];
        return typeof n==="number" && seq.videoTracks?seq.videoTracks[n]:null;
    }
    function count(collection){
        return collection && typeof collection.numTracks==="number" &&
            collection.numTracks >= 0 && collection.numTracks < 257 ?
            collection.numTracks:-1;
    }
    function clipCount(t){
        return t && t.clips && typeof t.clips.numItems==="number" &&
            t.clips.numItems>=0 && t.clips.numItems<100000 ?t.clips.numItems:-1;
    }
    function timeObject(value){
        if(typeof Time!=="function"){return null;}
        var t=new Time();
        t.ticks=value;
        return String(t.ticks)===value?t:null;
    }
    function seqEmpty(seq){
        var n=count(seq.videoTracks),a=count(seq.audioTracks);
        if(n<3||a<1){return false;}
        for(var i=0;i<n;i++){if(clipCount(seq.videoTracks[i])!==0){return false;}}
        for(var j=0;j<a;j++){if(clipCount(seq.audioTracks[j])!==0){return false;}}
        return true;
    }
    function allClipCounts(seq){
        var n=count(seq.videoTracks),a=count(seq.audioTracks),result=[];
        if(n<3||a<1){return null;}
        for(var i=0;i<n;i++){
            var c=clipCount(seq.videoTracks[i]);if(c<0){return null;}
            result.push(c);
        }
        for(var j=0;j<a;j++){
            var x=clipCount(seq.audioTracks[j]);if(x<0){return null;}
            result.push(x);
        }
        return result;
    }
    function trackedCountIndex(seq,label){
        return label==="A1"?count(seq.videoTracks):({V1:0,V2:1,V3:2})[label];
    }
    function uniqueOperations(manifest,items) {
        if(!manifest || manifest.schema_version!=="timeline-placement-candidate-v1" ||
            manifest.status!=="CANDIDATE_NOT_EXECUTABLE" ||
            manifest.can_assemble!==false || !/^[a-f0-9]{64}$/.test(manifest.operation_sha256||"") ||
            !ticks(manifest.ticks_per_frame,false) ||
            !ticks(manifest.snapshot_sha256,false) && !/^[a-f0-9]{64}$/.test(manifest.snapshot_sha256||"") ||
            Object.prototype.toString.call(manifest.operations)!=="[object Array]" ||
            manifest.operations.length<3||manifest.operations.length>4096 ||
            manifest.operation_count!==manifest.operations.length){return false;}
        var keys={},last={},has={V1:0,V2:0,V3:0,A1:0};
        for(var i=0;i<manifest.operations.length;i++){
            var op=manifest.operations[i],id=op&&op.item_id;
            if(!op||typeof op.key!=="string"||!op.key||keys[op.key] ||
                !/^(V1|V2|V3|A1)$/.test(op.track||"") ||
                typeof id!=="string" || !items[id] ||
                !ticks(op.start_ticks,true)||!ticks(op.end_ticks,false) ||
                !ticks(op.source_in_ticks,true)||!ticks(op.source_out_ticks,false) ||
                !ticks(op.duration_ticks,false) ||
                op.readback_verified!==false){return false;}
            if(op.track==="V1" && (id!=="SOURCE_BACKGROUND"||op.slot!=="BACKGROUND")){return false;}
            if(op.track==="A1" && (id!=="SOURCE_AUDIO"||op.slot!=="AUDIO")){return false;}
            if((op.track==="V2"||op.track==="V3") &&
                (id.indexOf("ASSET_")!==0||op.slot!=="VISUAL")){return false;}
            if(last[op.track]!==undefined &&
                op.start_frame<last[op.track]){return false;}
            if(typeof op.start_frame!=="number" || typeof op.end_frame!=="number" ||
                op.start_frame<0||op.end_frame<=op.start_frame ||
                Math.floor(op.start_frame)!==op.start_frame ||
                Math.floor(op.end_frame)!==op.end_frame){return false;}
            last[op.track]=op.end_frame;
            keys[op.key]=true;has[op.track]++;
        }
        return has.V1>0&&has.V2>0&&has.A1===1;
    }
    function placeCandidate(manifest,seq,sourceMap,authorization){
        try{
            if(typeof app==="undefined"||!app||!/^24\./.test(String(app.version||""))){
                return "S7|1|BLOCKED|HOST_UNSUPPORTED";
            }
            if(!authorization||authorization.kind!=="HOST_REVIEWED_TIMELINE_V1" ||
                authorization.ownerConfirmed!==true ||
                authorization.finalMediaHashesVerified!==true ||
                authorization.hostCapabilityVerified!==true ||
                authorization.layoutAndAllFxVerified!==true ||
                authorization.sourceIsolationVerified!==true ||
                authorization.preflightAllPass!==true ||
                authorization.hostVersion!==String(app.version||"") ||
                !seq || !guid(String(seq.sequenceID||"")) ||
                !/^AIJSON_[A-Za-z0-9_ -]{4,70}$/.test(String(seq.name||"")) ||
                authorization.sequenceId!==String(seq.sequenceID).toLowerCase() ||
                !manifest || authorization.operationDigest!==manifest.operation_sha256 ||
                authorization.snapshotDigest!==manifest.snapshot_sha256 ||
                String(seq.timebase||"")!==manifest.ticks_per_frame ||
                !sourceMap || typeof sourceMap!=="object"){
                return "S7|1|BLOCKED|AUTHORIZATION_NOT_VERIFIED";
            }
            if(!uniqueOperations(manifest,sourceMap)){
                return "S7|1|BLOCKED|PLACEMENT_MANIFEST_INVALID";
            }
            if(!seqEmpty(seq)){
                return "S7|1|BLOCKED|TARGET_NOT_EMPTY";
            }
            var modified=0;
            for(var i=0;i<manifest.operations.length;i++){
                var op=manifest.operations[i],src=sourceMap[op.item_id],t=track(seq,op.track);
                var pre=allClipCounts(seq);
                var expected=trackedCountIndex(seq,op.track);
                if(!t||!pre||typeof t.overwriteClip!=="function" ||
                    !src||!src.projectItem||typeof src.nodeId!=="string"||
                    String(src.projectItem.nodeId||"")!==src.nodeId ||
                    typeof src.projectItem.getMediaPath!=="function"){
                    return "S7|1|"+(modified?"INCOMPLETE":"BLOCKED")+"|SOURCE_OR_TRACK_UNVERIFIED";
                }
                if(src.kind!==(op.track==="A1"?"audio":op.track==="V1"?"background":"png")){
                    return "S7|1|"+(modified?"INCOMPLETE":"BLOCKED")+"|SOURCE_ROLE_MISMATCH";
                }
                // The overwrite API is only safe when there is no media at this
                // specific time; any cross-track/linked-audio insertion fails readback.
                var result=t.overwriteClip(src.projectItem,op.start_ticks);
                modified++;
                if(result!==true){
                    return "S7|1|INCOMPLETE|OVERWRITE_API_FAILED";
                }
                var post=allClipCounts(seq);
                if(!post){return "S7|1|INCOMPLETE|TRACK_READBACK_FAILED";}
                for(var j=0;j<pre.length;j++){
                    if(post[j]!==pre[j]+(j===expected?1:0)){
                        return "S7|1|INCOMPLETE|SIDE_EFFECT_TRACK_CHANGED";
                    }
                }
                var clip=t.clips[pre[expected]];
                if(!clip||!clip.projectItem||
                    String(clip.projectItem.nodeId||"")!==src.nodeId){
                    return "S7|1|INCOMPLETE|PROJECT_ITEM_MISMATCH";
                }
                var inTime=timeObject(op.source_in_ticks),
                    outTime=timeObject(op.source_out_ticks),
                    endTime=timeObject(op.end_ticks);
                if(!inTime||!outTime||!endTime){
                    return "S7|1|INCOMPLETE|TIME_OBJECT_INVALID";
                }
                // Mutate only THIS newly inserted instance, never source master.
                clip.inPoint=inTime;
                clip.outPoint=outTime;
                clip.end=endTime;
                if(!clip.start||!clip.end||!clip.inPoint||!clip.outPoint ||
                    String(clip.start.ticks)!==op.start_ticks ||
                    String(clip.end.ticks)!==op.end_ticks ||
                    String(clip.inPoint.ticks)!==op.source_in_ticks ||
                    String(clip.outPoint.ticks)!==op.source_out_ticks){
                    return "S7|1|INCOMPLETE|CLIP_TIMING_READBACK_FAILED";
                }
            }
            return "S7|1|PLACED_CANDIDATE|"+String(modified);
        }catch(e){
            return "S7|1|INCOMPLETE|HOST_EXCEPTION";
        }
    }
    return {placeCandidate:placeCandidate};
}());
