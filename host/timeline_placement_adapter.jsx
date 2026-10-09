/* STEP07 Premiere Pro 2024 ExtendScript ES3 candidate.
 * Single-clip append-by-overwrite on an exclusively NEW, managed sequence.
 * NOT LOADED by the CEP manifest and no public panel API invokes it.
 * Track.overwriteClip(projectItem, tickString) is used only with verified
 * disjoint destination; never use insertClip (would ripple other clips).
 *
 * A single operation may mutate the host before readback fails. On ANY such
 * uncertainty return INCOMPLETE without cleanup/retry, preserving user work.
 * Source trims, animation, transforms and background looping remain separate.
 */
if (typeof $ === "undefined") { var $ = {}; }
$._AIJSON_PLACEMENT_V1 = (function () {
    function validUUID(x) {
        return typeof x === "string" &&
            /^[a-fA-F0-9]{8}(-[a-fA-F0-9]{4}){3}-[a-fA-F0-9]{12}$/.test(x);
    }
    function ticks(x) {
        return typeof x === "string" && /^(0|[1-9][0-9]{0,32})$/.test(x);
    }
    function validName(x) {
        return typeof x === "string" && /^AIJSON_[a-zA-Z0-9_ -]{1,70}$/.test(x);
    }
    function isInteger(x,min,max) {
        return typeof x === "number" && x >= min && x <= max && Math.floor(x)===x;
    }
    function tracks(collection) {
        return collection && isInteger(collection.numTracks,0,256)?
            collection.numTracks:-1;
    }
    function safeItemId(id) {
        return typeof id === "string" && id.length > 0 && id.length <= 200 &&
            /^[A-Za-z0-9_.:-]+$/.test(id);
    }
    function getItemSequence(p, guid) {
        if(!p || !p.sequences || !isInteger(p.sequences.numSequences,0,100000)) {
            return null;
        }
        var item=null;
        for(var i=0;i<p.sequences.numSequences;i++){
            var s=p.sequences[i];
            if(!s || !validUUID(String(s.sequenceID || ""))){return null;}
            if(String(s.sequenceID).toLowerCase()===guid.toLowerCase()){
                if(item){return null;} // identical GUID would be ambiguous
                item=s;
            }
        }
        return item;
    }
    function findProjectItem(bin, nodeId) {
        if(!bin || !bin.children ||
            !isInteger(bin.children.numItems,1,100000)){return null;}
        var item=null;
        for(var i=0;i<bin.children.numItems;i++){
            var c=bin.children[i];
            if(!c || !safeItemId(c.nodeId)){return null;}
            if(c.nodeId === nodeId){
                if(item){return null;}
                item=c;
            }
        }
        return item;
    }
    function clipState(track) {
        if(!track || !track.clips ||
           !isInteger(track.clips.numItems,0,10000)) {return null;}
        var list=[],seen={};
        for(var i=0;i<track.clips.numItems;i++) {
            var c=track.clips[i];
            if(!c || !safeItemId(c.nodeId) ||
                !c.projectItem || !safeItemId(c.projectItem.nodeId) ||
                !c.start || !c.end ||
                !ticks(String(c.start.ticks)) || !ticks(String(c.end.ticks)) ||
                seen[c.nodeId]) {return null;}
            seen[c.nodeId]=true;
            list.push({
                id:c.nodeId,source_id:c.projectItem.nodeId,
                start:String(c.start.ticks),end:String(c.end.ticks)
            });
        }
        return list;
    }
    function allState(sequence) {
        if(!sequence || tracks(sequence.videoTracks)<3 ||
            tracks(sequence.audioTracks)<1){return null;}
        var out={};
        var i,clips;
        for(i=0;i<tracks(sequence.videoTracks);i++){
            clips=clipState(sequence.videoTracks[i]);
            if(!clips){return null;}
            out["V"+String(i+1)]=clips;
        }
        for(i=0;i<tracks(sequence.audioTracks);i++){
            clips=clipState(sequence.audioTracks[i]);
            if(!clips){return null;}
            out["A"+String(i+1)]=clips;
        }
        return out;
    }
    function stateMatches(actual, expected) {
        if(!actual || !expected ||
           Object.prototype.toString.call(expected)!=="[object Object]"){return false;}
        var count=0,key,j,k, a,b;
        for(key in actual) {
            if(!actual.hasOwnProperty(key)){continue;}
            count++;
            if(!expected.hasOwnProperty(key) ||
               Object.prototype.toString.call(expected[key])!=="[object Array]" ||
               actual[key].length!==expected[key].length){return false;}
            a=actual[key];b=expected[key];
            for(j=0;j<a.length;j++){
                if(!b[j] || a[j].id!==b[j].id ||
                   a[j].source_id!==b[j].source_id ||
                   a[j].start!==b[j].start || a[j].end!==b[j].end){
                    return false;
                }
            }
        }
        k=0;for(key in expected){if(expected.hasOwnProperty(key)){k++;}}
        return count===k;
    }
    function inspectSequence(sequenceId) {
        try{
            if(typeof app==="undefined" || !app || !app.project ||
               !/^24\./.test(String(app.version || "")) ||
               !validUUID(sequenceId)){return null;}
            var s=getItemSequence(app.project,sequenceId);
            return s?allState(s):null;
        } catch(error){return null;}
    }
    function placeOne(request, auth) {
        try{
            var p=typeof app!=="undefined" && app?app.project:null;
            if(!p || !/^24\./.test(String(app.version || ""))) {
                return "S7|1|BLOCKED|HOST_UNAVAILABLE";
            }
            if(!auth || auth.kind!=="HOST_REVIEWED_PLACEMENT_V1" ||
               auth.ownerConfirmed!==true || auth.hostCapabilityVerified!==true ||
               auth.projectIdentityVerified!==true || auth.mediaHashesFresh!==true ||
               auth.layoutVerified!==true || auth.fxBackendVerified!==true ||
               auth.preflightAllPass!==true || auth.sourceDurationVerified!==true ||
               auth.hostVersion!==String(app.version||"") ||
               !request || auth.sequenceId!==request.sequenceId ||
               auth.snapshotDigest!==request.snapshotDigest ||
               typeof request.snapshotDigest!=="string" ||
               !/^[a-f0-9]{64}$/.test(request.snapshotDigest)) {
                return "S7|1|BLOCKED|AUTHORIZATION_NOT_VERIFIED";
            }
            if(!validUUID(request.sequenceId) || !validName(request.sequenceName) ||
               !safeItemId(request.projectItemNodeId) ||
               !ticks(request.startTicks) || !ticks(request.endTicks) ||
               !ticks(request.sourceDurationTicks) ||
               !request.expectedBefore ||
               ["V1","V2","V3","A1"].indexOf(request.track)===-1 ||
               request.expectedType!==(request.track==="A1"?"Audio":"Video") ||
               request.sourceDurationTicks==="0" ||
               request.startTicks===request.endTicks) {
                return "S7|1|BLOCKED|PLACEMENT_INVALID";
            }
            /* ES3 host has no native BigInt. Exact duration/interval equality
               is verified on the Python side; host compares decimal strings
               after the edit. Do not convert ticks to Number. */
            var seq=getItemSequence(p,request.sequenceId);
            if(!seq || seq.name!==request.sequenceName ||
               tracks(seq.videoTracks)<3 || tracks(seq.audioTracks)<1) {
                return "S7|1|BLOCKED|MANAGED_SEQUENCE_UNAVAILABLE";
            }
            var state=allState(seq);
            if(!state || !stateMatches(state,request.expectedBefore)){
                return "S7|1|BLOCKED|TRACK_BASELINE_CHANGED";
            }
            var track=request.track==="A1"?seq.audioTracks[0]:
                seq.videoTracks[Number(request.track.slice(1))-1];
            if(!track || typeof track.overwriteClip!=="function") {
                return "S7|1|BLOCKED|TRACK_API_UNAVAILABLE";
            }
            var dest=state[request.track];
            /* No overlap or even nonempty track: do not overwrite, move, or
               ripple anything. Later append-on-track requires proof upgrade. */
            if(dest.length!==0) {return "S7|1|BLOCKED|TRACK_NOT_EMPTY";}
            if(!p.rootItem || !p.rootItem.children ||
                !isInteger(p.rootItem.children.numItems,0,100000)){
                return "S7|1|BLOCKED|MEDIA_BIN_UNAVAILABLE";
            }
            var bin=null,i;
            for(i=0;i<p.rootItem.children.numItems;i++){
                var child=p.rootItem.children[i];
                if(child && child.name===request.mediaBinName){
                    if(bin){return "S7|1|BLOCKED|MEDIA_BIN_AMBIGUOUS";}
                    bin=child;
                }
            }
            if(!bin || !/^AIJSON_MEDIA_[A-Za-z0-9_-]{8,54}$/.test(
                String(request.mediaBinName||""))) {
                return "S7|1|BLOCKED|MEDIA_BIN_UNAVAILABLE";
            }
            var item=findProjectItem(bin,request.projectItemNodeId);
            if(!item || typeof item.getMediaPath!=="function") {
                return "S7|1|BLOCKED|PROJECT_ITEM_NOT_FOUND";
            }
            /* No ProjectItem.setInPoint()/setOutPoint(), as those mutate master
               sources and could change a user's other timeline clips. Source
               must already be exactly pretrimmed to expected duration. */
            if(auth.sourceItemNodeId!==request.projectItemNodeId ||
               auth.expectedSourceDurationTicks!==request.sourceDurationTicks) {
                return "S7|1|BLOCKED|SOURCE_DURATION_UNVERIFIED";
            }
            if(typeof item.getMediaPath()!=="string" ||
                item.getMediaPath().length===0){
                return "S7|1|BLOCKED|MEDIA_READBACK_FAILED";
            }
            /* FIRST HOST MUTATION; track was proven completely empty. */
            var ok=track.overwriteClip(item,request.startTicks);
            if(ok!==true){
                return "S7|1|INCOMPLETE|OVERWRITE_API_FAILED";
            }
            var after=allState(seq);
            if(!after || !after[request.track] ||
               after[request.track].length!==1){
                return "S7|1|INCOMPLETE|CLIP_READBACK_FAILED";
            }
            var expectedStart=request.startTicks,expectedEnd=request.endTicks;
            var inserted=after[request.track][0];
            if(inserted.source_id!==request.projectItemNodeId ||
               inserted.start!==expectedStart || inserted.end!==expectedEnd ||
               !safeItemId(inserted.id)){
                return "S7|1|INCOMPLETE|CLIP_TIMING_OR_ID_MISMATCH";
            }
            /* Verify ALL OTHER tracks and their clip IDs/positions unchanged.
               Linked audio/video side effects are flagged INCOMPLETE. */
            var other={},key;
            for(key in after){
                if(after.hasOwnProperty(key) && key!==request.track){
                    other[key]=after[key];
                }
            }
            var expectedOther={};
            for(key in state){
                if(state.hasOwnProperty(key)&&key!==request.track){
                    expectedOther[key]=state[key];
                }
            }
            if(!stateMatches(other,expectedOther)){
                return "S7|1|INCOMPLETE|UNEXPECTED_TRACK_MUTATION";
            }
            return "S7|1|PLACED_ONE|"+request.track+"|"+inserted.id;
        }catch(error) {
            /* Unknown point of failure: no retries/undo/destructive cleanup. */
            return "S7|1|INCOMPLETE|HOST_PLACEMENT_EXCEPTION";
        }
    }
    return {inspectSequence:inspectSequence,placeOne:placeOne};
}());
