/* STEP14 Premiere Pro 2024 ExtendScript ES3 READ-ONLY readback capture.
 * NOT loaded from CEP ScriptPath. Never imports/inserts/crops/mutates.
 * The object is a local observation, NOT a signed/host-attested receipt.
 * No media path, sequence name, user clip name, or source JSON is returned.
 */
if (typeof $ === "undefined") { var $={}; }
$._AIJSON_READBACK_V1=(function(){
    function safeId(v) {
        return typeof v==="string" && /^[A-Za-z0-9_.:-]{1,200}$/.test(v);
    }
    function tick(v) {
        return typeof v==="string" && /^(0|[1-9][0-9]{0,35})$/.test(v);
    }
    function sequenceGuid(v) {
        return typeof v==="string" &&
            /^[a-fA-F0-9]{8}(-[a-fA-F0-9]{4}){3}-[a-fA-F0-9]{12}$/.test(v);
    }
    function integer(n,min,max) {
        return typeof n==="number" && n>=min && n<=max && Math.floor(n)===n;
    }
    function err(code) {return "S14|1|ERROR|"+code;}
    function sequenceFor(p,guid) {
        if(!p.sequences || !integer(p.sequences.numSequences,0,100000)){return null;}
        var found=null;
        for(var i=0;i<p.sequences.numSequences;i++){
            var x=p.sequences[i];
            if(!x || !sequenceGuid(String(x.sequenceID||""))){return null;}
            if(String(x.sequenceID).toLowerCase()===guid.toLowerCase()){
                if(found){return null;}
                found=x;
            }
        }
        return found;
    }
    function clips(track,seen) {
        if(!track || !track.clips ||
            !integer(track.clips.numItems,0,10000)){return null;}
        var data=[],v,c,id,source,field,start,end,sin,sout;
        for(var i=0;i<track.clips.numItems;i++){
            c=track.clips[i];
            id=String(c && c.nodeId || "");
            source=String(c && c.projectItem && c.projectItem.nodeId || "");
            if(!safeId(id)||!safeId(source)||seen[id] ||
                !c.start||!c.end||!c.inPoint||!c.outPoint){
                return null;
            }
            start=String(c.start.ticks);
            end=String(c.end.ticks);
            sin=String(c.inPoint.ticks);
            sout=String(c.outPoint.ticks);
            if(!tick(start)||!tick(end)||!tick(sin)||!tick(sout)){
                return null;
            }
            seen[id]=true;
            data.push({clip_id:id,item_node_id:source,start_ticks:start,
                end_ticks:end,source_in_ticks:sin,source_out_ticks:sout});
        }
        return data;
    }
    function encode(clip) {
        /* Values are constrained to safe decimal/id characters; do not rely
         * on JSON global being available in Premiere ExtendScript ES3. */
        return '{"clip_id":"'+clip.clip_id+'","item_node_id":"'+clip.item_node_id+
            '","start_ticks":"'+clip.start_ticks+'","end_ticks":"'+clip.end_ticks+
            '","source_in_ticks":"'+clip.source_in_ticks+
            '","source_out_ticks":"'+clip.source_out_ticks+'"}';
    }
    function asJson(clipsByTrack,guid,tb) {
        var order=["V1","V2","V3","A1"],parts=[];
        for(var i=0;i<order.length;i++){
            var list=clipsByTrack[order[i]],serialized=[];
            for(var j=0;j<list.length;j++){serialized.push(encode(list[j]));}
            parts.push('"'+order[i]+'":['+serialized.join(",")+']');
        }
        return '{"schema_version":"premiere-track-readback-v1",'+
            '"status":"CAPTURED_UNVERIFIED","can_assemble":false,'+
            '"sequence_id":"'+guid.toLowerCase()+'",'+
            '"ticks_per_frame":"'+tb+'",'+
            '"tracks":{'+parts.join(",")+'}}';
    }
    function capture(sequenceId) {
        try{
            if(typeof app==="undefined"||!app||!app.project){
                return err("NO_PROJECT");
            }
            if(!/^24\./.test(String(app.version||""))){
                return err("HOST_UNSUPPORTED");
            }
            if(!sequenceGuid(sequenceId)){return err("SEQUENCE_ID_INVALID");}
            var seq=sequenceFor(app.project,sequenceId);
            if(!seq){return err("SEQUENCE_NOT_UNIQUE");}
            var tb=String(seq.timebase||"");
            if(!/^[1-9][0-9]{0,25}$/.test(tb)){
                return err("TIMEBASE_INVALID");
            }
            var v=seq.videoTracks,a=seq.audioTracks;
            if(!v||!a||!integer(v.numTracks,3,256)||
                !integer(a.numTracks,1,256)){
                return err("TRACKS_INVALID");
            }
            var seen={},out={},order=["V1","V2","V3","A1"];
            for(var i=0;i<3;i++){
                var arr=clips(v[i],seen);
                if(!arr){return err("TRACK_READBACK_INVALID");}
                out[order[i]]=arr;
            }
            out.A1=clips(a[0],seen);
            if(!out.A1){return err("TRACK_READBACK_INVALID");}
            /* Extra tracks are permitted only when empty. This avoids
             * silently declaring a match while linked clips leaked to A2/V4.
             */
            for(var j=3;j<v.numTracks;j++){
                if(!v[j]||!v[j].clips||v[j].clips.numItems!==0){
                    return err("EXTRA_VIDEO_TRACK_CONTENT");
                }
            }
            for(var k=1;k<a.numTracks;k++){
                if(!a[k]||!a[k].clips||a[k].clips.numItems!==0){
                    return err("EXTRA_AUDIO_TRACK_CONTENT");
                }
            }
            var result=asJson(out,sequenceId,tb);
            return result.length<=524288?result:err("OBSERVATION_TOO_LARGE");
        }catch(e){return err("HOST_READBACK_EXCEPTION");}
    }
    return {capture:capture};
}());
