/* STEP07 guarded Premiere Pro 2024 ES3 four-track placement CANDIDATE.
 * Deliberately NOT loaded by CEP ScriptPath. Uses Track.overwriteClip only
 * on a verified EMPTY new managed sequence. Host API behavior NOT VERIFIED.
 * This module does not grant authorization or make a non-executable draft READY.
 */
if (typeof $ === "undefined") {var $={};}
$._AIJSON_PLACEMENT_V1=(function(){
    function isTick(s,zero){
        return typeof s==="string" &&
            (zero ? /^(0|[1-9][0-9]{0,25})$/ :
                    /^[1-9][0-9]{0,25}$/).test(s);
    }
    function eq(a,b){return String(a)===String(b);}
    // Multiply a decimal tick string by a bounded integer frame without
    // passing giant tick values through IEEE-754 floating point.
    function ticksAtFrame(tick,frame){
        if(!isTick(tick,false) || typeof frame!=="number" ||
           Math.floor(frame)!==frame || frame<0 || frame>10000000){return null;}
        var carry=0,out="",i,product;
        for(i=tick.length-1;i>=0;i--){
            product=(tick.charCodeAt(i)-48)*frame+carry;
            out=String(product%10)+out;
            carry=Math.floor(product/10);
        }
        while(carry>0){
            out=String(carry%10)+out;
            carry=Math.floor(carry/10);
        }
        out=out.replace(/^0+(?=[0-9])/,"");
        return isTick(out,true)?out:null;
    }
    function less(a,b){
        if(a.length!==b.length){return a.length<b.length;}
        return a<b;
    }
    function count(collection){
        if(!collection || typeof collection.numItems!=="number" ||
            collection.numItems<0 || collection.numItems>100000 ||
            Math.floor(collection.numItems)!==collection.numItems){return -1;}
        return collection.numItems;
    }
    function validatePlan(plan,tb){
        if(!plan || plan.schema_version!=="track-placement-candidate-v1" ||
            plan.status!=="CANDIDATE_NOT_EXECUTABLE" ||
            plan.can_assemble!==false || plan.can_import!==false ||
            !/^[a-f0-9]{64}$/.test(plan.operation_sha256||"") ||
            !eq(plan.ticks_per_frame,tb) ||
            !isTick(plan.ticks_per_frame,false) ||
            !/^[a-f0-9]{64}$/.test(plan.source_digest||"") ||
            !/^[a-f0-9]{64}$/.test(plan.media_digest||"") ||
            typeof plan.total_frames!=="number" ||
            Math.floor(plan.total_frames)!==plan.total_frames ||
            plan.total_frames<1 || plan.total_frames>10000000 ||
            !(Object.prototype.toString.call(plan.placements)==="[object Array]") ||
            plan.placements.length<4 || plan.placements.length>10000){
            return false;
        }
        var seen={},spans={V1:[],V2:[],V3:[],A1:[]},expected={V1:0,V2:1,V3:2,A1:0};
        for(var i=0;i<plan.placements.length;i++){
            var p=plan.placements[i];
            if(!p || typeof p.instance_key!=="string" ||
                !/^[A-Za-z0-9_./-]{1,150}$/.test(p.instance_key) ||
                seen[p.instance_key] ||
                typeof p.item_id!=="string" ||
                !/^(SOURCE_(AUDIO|BACKGROUND)|ASSET_[A-Za-z0-9][A-Za-z0-9_.-]*)$/.test(p.item_id) ||
                !spans.hasOwnProperty(p.target_track) ||
                p.zero_based_track_index!==expected[p.target_track] ||
                !isTick(p.start_ticks,true) || !isTick(p.end_ticks,false) ||
                !less(p.start_ticks,p.end_ticks) ||
                typeof p.start_frame!=="number" || Math.floor(p.start_frame)!==p.start_frame ||
                typeof p.end_frame!=="number" || Math.floor(p.end_frame)!==p.end_frame ||
                p.start_frame<0 || p.end_frame<=p.start_frame ||
                p.end_frame>plan.total_frames ||
                ticksAtFrame(plan.ticks_per_frame,p.start_frame)!==p.start_ticks ||
                ticksAtFrame(plan.ticks_per_frame,p.end_frame)!==p.end_ticks ||
                typeof p.source_in_frame!=="number" ||
                typeof p.source_out_frame!=="number" ||
                p.source_in_frame!==0 ||
                p.source_out_frame!==p.end_frame-p.start_frame ||
                p.media_readback!=="NOT_TESTED"){
                return false;
            }
            if(p.target_track==="A1" && p.item_id!=="SOURCE_AUDIO" ||
               p.target_track==="V1" && p.item_id!=="SOURCE_BACKGROUND" ||
               (p.target_track==="V2" || p.target_track==="V3") &&
                    p.item_id.indexOf("ASSET_")!==0){return false;}
            seen[p.instance_key]=true;
            spans[p.target_track].push(p);
        }
        for(var track in spans){
            if(!spans.hasOwnProperty(track)){continue;}
            var group=spans[track];
            if(group.length===0){return false;}
            group.sort(function(a,b){return a.start_frame-b.start_frame;});
            for(var j=1;j<group.length;j++){
                if(group[j].start_frame<group[j-1].end_frame){return false;}
            }
            if(track==="V1" || track==="A1"){
                if(group[0].start_frame!==0 || group[group.length-1].end_frame!==plan.total_frames){
                    return false;
                }
                for(var k=1;k<group.length;k++){
                    if(group[k-1].end_frame!==group[k].start_frame){return false;}
                }
            }
        }
        return true;
    }
    function mediaBin(p,name){
        if(!p || !p.rootItem || !p.rootItem.children){return null;}
        var list=p.rootItem.children, size=count(list);
        if(size<0){return null;}
        var target=null;
        for(var i=0;i<size;i++){
            var item=list[i];
            if(item && item.name===name){if(target){return null;}target=item;}
        }
        return target;
    }
    function itemMap(bin,refs){
        var result={},n=count(bin.children);
        if(n<0 || !refs || Object.prototype.toString.call(refs)!=="[object Array]"){return null;}
        for(var i=0;i<refs.length;i++){
            var ref=refs[i];
            if(!ref || typeof ref.item_id!=="string" ||
                typeof ref.node_id!=="string" || !ref.node_id ||
                result.hasOwnProperty(ref.item_id)){return null;}
            var hits=0,found=null;
            for(var j=0;j<n;j++){
                var item=bin.children[j];
                if(item && String(item.nodeId||"")===ref.node_id){hits++;found=item;}
            }
            if(hits!==1){return null;}
            result[ref.item_id]=found;
        }
        return result;
    }
    function clipTrack(sequence,name){
        return name==="A1" ? sequence.audioTracks[0] :
            sequence.videoTracks[name==="V1"?0:name==="V2"?1:2];
    }
    function allEmpty(seq){
        if(!seq || !seq.videoTracks || !seq.audioTracks ||
            seq.videoTracks.numTracks!==3 || seq.audioTracks.numTracks!==1){
            return false;
        }
        for(var i=0;i<3;i++){
            if(!seq.videoTracks[i] || count(seq.videoTracks[i].clips)!==0){return false;}
        }
        return !!seq.audioTracks[0] && count(seq.audioTracks[0].clips)===0;
    }
    function findSequence(p,id){
        var c=p.sequences;
        if(!c || typeof c.numSequences!=="number" || c.numSequences<1){return null;}
        var result=null;
        for(var i=0;i<c.numSequences;i++){
            var s=c[i];
            if(s && String(s.sequenceID||"").toLowerCase()===id.toLowerCase()){
                if(result){return null;}
                result=s;
            }
        }
        return result;
    }
    function commitCandidate(plan, mediaRefs, sequenceId, mediaBinName, authorization){
        try{
            var p=typeof app!=="undefined"&&app?app.project:null,
                ver=typeof app!=="undefined"&&app?String(app.version||""):"";
            if(!p){return "S7|1|BLOCKED|NO_PROJECT";}
            if(!/^24\./.test(ver)){return "S7|1|BLOCKED|HOST_UNSUPPORTED";}
            if(!authorization ||
                authorization.kind!=="HOST_REVIEWED_PLACEMENT_V1" ||
                authorization.ownerConfirmed!==true ||
                authorization.hostCapabilitiesVerified!==true ||
                authorization.hashSnapshotFresh!==true ||
                authorization.fxAndLayoutVerified!==true ||
                authorization.mediaAudioIsolationVerified!==true ||
                authorization.preflightAllPass!==true ||
                authorization.hostVersion!==ver ||
                authorization.operationDigest!==plan.operation_sha256 ||
                authorization.managedSequenceId!==sequenceId){
                return "S7|1|BLOCKED|AUTHORIZATION_NOT_VERIFIED";
            }
            if(typeof sequenceId!=="string" ||
                !/^[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$/.test(sequenceId) ||
                !/^AIJSON_MEDIA_[A-Za-z0-9_-]{8,54}$/.test(mediaBinName)){
                return "S7|1|BLOCKED|MANAGED_ID_INVALID";
            }
            var seq=findSequence(p,sequenceId);
            if(!seq || typeof seq.name!=="string" ||
                !/^AIJSON_MANAGED_[A-Za-z0-9_-]{4,64}$/.test(seq.name)){
                return "S7|1|BLOCKED|NOT_MANAGED_SEQUENCE";
            }
            if(!validatePlan(plan,String(seq.timebase||""))){
                return "S7|1|BLOCKED|PLAN_INVALID";
            }
            if(!allEmpty(seq)){return "S7|1|BLOCKED|TARGET_NOT_EMPTY";}
            var bin=mediaBin(p,mediaBinName),items=bin&&itemMap(bin,mediaRefs);
            if(!items){return "S7|1|BLOCKED|MEDIA_BIN_READBACK_FAILED";}
            for(var i=0;i<plan.placements.length;i++){
                if(!items.hasOwnProperty(plan.placements[i].item_id)){
                    return "S7|1|BLOCKED|SOURCE_NOT_IMPORTED";
                }
            }
            if(typeof Time!=="function"){
                return "S7|1|BLOCKED|HOST_TIME_API_UNAVAILABLE";
            }
            /* All preflight checks end here. The first host mutation follows.
             * Track.overwriteClip ONLY on a freshly EMPTY managed sequence.
             * Incomplete sequences are NOT retried or auto-deleted.
             */
            var touched=0;
            for(var j=0;j<plan.placements.length;j++){
                var row=plan.placements[j],track=clipTrack(seq,row.target_track),
                    before=count(track.clips),after,clip,newEnd,ok;
                if(before<0){return "S7|1|INCOMPLETE|TRACK_CHANGED";}
                ok=track.overwriteClip(items[row.item_id],row.start_ticks);
                if(ok!==true){return "S7|1|INCOMPLETE|OVERWRITE_FAILED";}
                touched++;
                after=count(track.clips);
                if(after!==before+1){return "S7|1|INCOMPLETE|TRACK_COUNT_MISMATCH";}
                clip=track.clips[after-1];
                if(!clip || !clip.projectItem ||
                    String(clip.projectItem.nodeId||"")!==String(items[row.item_id].nodeId) ||
                    !clip.start || !eq(clip.start.ticks,row.start_ticks)){
                    return "S7|1|INCOMPLETE|PLACEMENT_READBACK_FAILED";
                }
                if(!clip.end || !eq(clip.end.ticks,row.end_ticks)){
                    newEnd=new Time();
                    newEnd.ticks=row.end_ticks;
                    clip.end=newEnd;
                }
                if(!clip.end || !eq(clip.end.ticks,row.end_ticks)){
                    return "S7|1|INCOMPLETE|TRIM_READBACK_FAILED";
                }
                /* Any unexpected linked audio/audio spill => stop, preserve.
                 * No unlink, mute or delete operations will touch user media.
                 */
                var audio=count(seq.audioTracks[0].clips),expectedAudio=0;
                for(var a=0;a<=j;a++){
                    if(plan.placements[a].target_track==="A1"){expectedAudio++;}
                }
                if(audio!==expectedAudio){
                    return "S7|1|INCOMPLETE|UNEXPECTED_LINKED_AUDIO";
                }
            }
            return "S7|1|PLACED_IN_NEW_SEQUENCE|"+String(touched);
        }catch(e){
            return "S7|1|INCOMPLETE|HOST_PLACEMENT_EXCEPTION";
        }
    }
    return {commitCandidate:commitCandidate};
}());
