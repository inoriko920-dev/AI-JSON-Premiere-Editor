/* STEP05 read-only diagnostic parser for later CEP <-> ExtendScript integration.
 * Separate from the P0 loaded panel. A probe result never authorizes editing.
 */
(function(root,factory){
    "use strict";
    var api=factory();
    if(root && root.document){root.AIJSONSequenceProbe=api;}
    if(typeof module==="object" && module.exports){module.exports=api;}
}(this,function(){
    "use strict";
    var SCRIPT='$._AIJSON_SEQUENCE_V1.inspect()';
    var ERROR_CODES={
      NO_PROJECT:true,HOST_UNSUPPORTED:true,
      HOST_TIMEBASE_OR_TRACKS_UNKNOWN:true,HOST_INSPECT_EXCEPTION:true
    };
    function bad(code){return {status:"error",code:code,canAssemble:false};}
    function parse(raw){
        if(typeof raw!=="string"||raw.length>256){return bad("S5_RESPONSE_INVALID");}
        var values=/^S5\|1\|OBSERVED\|(24\.[0-9]+(?:\.[0-9]+){0,2})\|([1-9][0-9]{0,25})\|([0-9]{1,3})\|([0-9]{1,3})\|([0-9]{1,5})\|([0-9]{1,5})$/.exec(raw);
        if(values){
            var video=Number(values[3]),audio=Number(values[4]),
                width=Number(values[5]),height=Number(values[6]);
            if(video>256||audio>256||width<1||height<1||
                width>16384||height>16384){
                return bad("S5_RESPONSE_INVALID");
            }
            return {status:"observed_unverified",canAssemble:false,
                hostVersion:values[1],ticksPerFrame:values[2],
                videoTracks:video,audioTracks:audio,width:width,height:height};
        }
        var missing=/^S5\|1\|NO_ACTIVE_SEQUENCE\|(24\.[0-9]+(?:\.[0-9]+){0,2})$/.exec(raw);
        if(missing){
            return {status:"no_active_sequence",hostVersion:missing[1],
                canAssemble:false};
        }
        var problem=/^S5\|1\|ERROR\|([A-Z][A-Z0-9_]{1,48})$/.exec(raw);
        return problem && ERROR_CODES[problem[1]] ? bad(problem[1]) :
            bad("S5_RESPONSE_INVALID");
    }
    function bridge(evalScript,setTimer,clearTimer){
        var invoke=typeof evalScript==="function"?evalScript:null,
            schedule=typeof setTimer==="function"?setTimer:setTimeout,
            clear=typeof clearTimer==="function"?clearTimer:clearTimeout;
        var active=false,sequence=0,timeout=null;
        function cancel(){
            sequence++;active=false;
            if(timeout!==null){clear(timeout);timeout=null;}
        }
        function probe(callback){
            if(typeof callback!=="function"){throw new TypeError("callback required");}
            if(active){return false;}
            if(!invoke){callback(bad("CEP_NOT_AVAILABLE"));return false;}
            active=true;var id=++sequence;
            function finish(result){
                if(!active||id!==sequence){return;}
                cancel();callback(result);
            }
            timeout=schedule(function(){finish(bad("S5_PROBE_TIMEOUT"));},8000);
            try{
                invoke(SCRIPT,function(raw){finish(parse(raw));});
            }catch(error){finish(bad("CEP_EVAL_FAILURE"));}
            return true;
        }
        return {probe:probe,cancel:cancel,isBusy:function(){return active;}};
    }
    return {parse:parse,createBridge:bridge,INSPECT_SCRIPT:SCRIPT};
}));
