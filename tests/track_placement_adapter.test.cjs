const test=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const code=fs.readFileSync(path.join(__dirname,"..","host","track_placement_adapter.jsx"),"utf8");
const TB="8467200000", SEQ="aaaa1111-bbbb-2222-cccc-333333333333",BIN="AIJSON_MEDIA_DEMO_2026";
function plan(){
 const rows=[
  ["BG_0","SOURCE_BACKGROUND","V1",0,180],
  ["V001/A001","ASSET_A001","V2",0,150],
  ["NARRATION_0","SOURCE_AUDIO","A1",0,330],
  ["V002/A002","ASSET_A002","V2",150,330],
  ["BG_1","SOURCE_BACKGROUND","V1",180,330],
  ["V002/A003","ASSET_A003","V3",192,330]
 ];
 return {schema_version:"track-placement-candidate-v1",
  status:"CANDIDATE_NOT_EXECUTABLE",can_import:false,can_assemble:false,
  operation_sha256:"a".repeat(64),source_digest:"b".repeat(64),
  media_digest:"c".repeat(64),ticks_per_frame:TB,total_frames:330,
  placements:rows.map(([id,item,track,start,end])=>({
   instance_key:id,item_id:item,target_track:track,
   zero_based_track_index:track==="V3"?2:track==="V2"?1:0,
   start_frame:start,end_frame:end,start_ticks:String(start*Number(TB)),
   end_ticks:String(end*Number(TB)),
   source_in_frame:0,source_out_frame:end-start,
   media_readback:"NOT_TESTED"
  }))};
}
function setup(options={}){
 const p=plan(),imports=["SOURCE_AUDIO","SOURCE_BACKGROUND","ASSET_A001","ASSET_A002","ASSET_A003"];
 const media=imports.map((id,i)=>({nodeId:"node_"+id,name:id}));
 Object.defineProperty(media,"numItems",{get(){return this.length;}});
 const bin={name:BIN,children:media,nodeId:"managed-bin-id"};
 const userBin={name:"User Originals",nodeId:"user-owned",children:[]};
 const rootChildren=[userBin,bin];
 Object.defineProperty(rootChildren,"numItems",{get(){return this.length;}});
 let writes=0,trims=0,sourceTrims=0;
 const track=(name)=>{
  const clips=[];
  Object.defineProperty(clips,"numItems",{get(){return this.length;}});
  const t={name,clips,overwriteClip(item,stamp){
    writes++;
    if(options.failAt===writes){return false;}
    if(options.throwAt===writes){throw Error("simulated Adobe throw after host mutation");}
    const value={projectItem:item,start:{ticks:options.mismatchStart&&writes===1?"1":stamp},
      end:{ticks:"999"}};
    Object.defineProperty(value,"end",{
      get(){return this._end;},
      set(v){trims++;this._end=options.badTrim?{ticks:"999"}:v;}
    });
    Object.defineProperty(value,"inPoint",{
      get(){return this._in;},
      set(v){sourceTrims++;this._in=options.badSourceIn?{ticks:"999"}:v;}
    });
    Object.defineProperty(value,"outPoint",{
      get(){return this._out;},
      set(v){sourceTrims++;this._out=options.badSourceOut?{ticks:"999"}:v;}
    });
    value._in=options.missingSourceTrim?null:{ticks:"0"};
    value._out=options.missingSourceTrim?null:{ticks:"999"};
    value._end={ticks:"999"};
    clips.push(value);
    if(options.linkedAudio&&name==="V1"){
      a[0].clips.push({projectItem:item,start:{ticks:stamp},end:{ticks:"999"}});
    }
    if(options.linkedVideo&&name==="A1"){
      v[0].clips.push({projectItem:item,start:{ticks:stamp},end:{ticks:"999"}});
    }
    return true;
  }};
  return t;
 };
 const v=[track("V1"),track("V2"),track("V3")],a=[track("A1")];
 if(options.userClip){v[1].clips.push({projectItem:{nodeId:"manual"},start:{ticks:"0"},end:{ticks:"30"}});}
 Object.defineProperty(v,"numTracks",{get(){return this.length;}});
 Object.defineProperty(a,"numTracks",{get(){return this.length;}});
 const seq={sequenceID:SEQ,name:options.badSequenceName||"AIJSON_MANAGED_Project_001",
   timebase:options.badTimebase||TB,videoTracks:v,audioTracks:a};
 const sequences=[{sequenceID:"00000000-2222-3333-4444-555555555555",name:"User timeline",
    videoTracks:{},audioTracks:{}},seq];
 Object.defineProperty(sequences,"numSequences",{get(){return this.length;}});
 const context={$:{},app:{version:options.version||"24.4",
   project:{sequences,rootItem:{children:rootChildren}}}};
 if(!options.noTime){
   context.Time=function(){this.ticks="0";};
 }
 vm.runInNewContext(code,context,{timeout:3000});
 const auth={kind:"HOST_REVIEWED_PLACEMENT_V1",ownerConfirmed:true,
   hostCapabilitiesVerified:true,hashSnapshotFresh:true,
   fxAndLayoutVerified:true,mediaAudioIsolationVerified:true,
   preflightAllPass:true,hostVersion:"24.4",
   operationDigest:p.operation_sha256,managedSequenceId:SEQ};
 return {adapter:context.$._AIJSON_PLACEMENT_V1,plan:p,seq,v,a,auth,media,
   refs:imports.map((id,i)=>({item_id:id,node_id:media[i].nodeId})),
   writes:()=>writes,trims:()=>trims,sourceTrims:()=>sourceTrims,run(){
     return this.adapter.commitCandidate(this.plan,this.refs,SEQ,BIN,this.auth);
   },userBin};
}
test("writes 6 planned placements only onto EMPTY managed sequence; trims each by exact ticks",()=>{
 const x=setup();
 assert.equal(x.run(),"S7|1|PLACED_IN_NEW_SEQUENCE|6");
 assert.deepEqual(x.v.map(t=>t.clips.length),[2,2,1]);
 assert.equal(x.a[0].clips.length,1);
 assert.equal(x.v[0].clips[1].start.ticks,String(180*Number(TB)));
 assert.equal(x.v[1].clips[1].end.ticks,String(330*Number(TB)));
 assert.equal(x.writes(),6);
 assert.equal(x.trims(),6);
 assert.equal(x.sourceTrims(),12);
 assert.equal(x.v[0].clips[0].inPoint.ticks,"0");
 assert.equal(x.v[0].clips[0].outPoint.ticks,String(180*Number(TB)));
 assert.equal(x.v[0].clips[1].inPoint.ticks,"0");
 assert.equal(x.v[0].clips[1].outPoint.ticks,String(150*Number(TB)));
 assert.equal(x.a[0].clips[0].outPoint.ticks,String(330*Number(TB)));
 assert.equal(x.userBin.name,"User Originals");
});
test("no owner approval or verified host/profile can write",()=>{
 const x=setup();
 for(const overrides of [{ownerConfirmed:false},{hostCapabilitiesVerified:false},
   {hashSnapshotFresh:false},{fxAndLayoutVerified:false},
   {mediaAudioIsolationVerified:false},{preflightAllPass:false},
   {hostVersion:"24.5"},{operationDigest:"0".repeat(64)}]){
    const previous=x.auth;x.auth={...previous,...overrides};
    assert.equal(x.run(),"S7|1|BLOCKED|AUTHORIZATION_NOT_VERIFIED");
    x.auth=previous;
 }
 assert.equal(x.writes(),0);
});
test("existing manual edits and unrecognized sequence refuse BEFORE first write",()=>{
 const x=setup({userClip:true});
 assert.equal(x.run(),"S7|1|BLOCKED|TARGET_NOT_EMPTY");
 assert.equal(x.writes(),0);
 const bad=setup({badSequenceName:"Manually Edited Sequence"});
 assert.equal(bad.run(),"S7|1|BLOCKED|NOT_MANAGED_SEQUENCE");
 assert.equal(bad.writes(),0);
});
test("invalid plan, wrong track, duplicate instance, and fake READY are blocked",()=>{
 for(const corrupt of [
  x=>x.plan.can_assemble=true,
  x=>x.plan.status="READY",
  x=>x.plan.placements[0].target_track="V2",
  x=>x.plan.placements[0].start_ticks="001",
  x=>x.plan.placements[1].instance_key="BG_0",
  x=>x.plan.placements[0].item_id="ASSET_A001",
  x=>x.plan.placements[0].start_frame=100,
  x=>x.plan.placements[1].end_ticks=String(151*Number(TB)),
  x=>x.plan.placements[0].source_out_frame=181,
  x=>x.plan.ticks_per_frame="999",
 ]){
   const x=setup();corrupt(x);
   assert.equal(x.run(),"S7|1|BLOCKED|PLAN_INVALID");
   assert.equal(x.writes(),0);
 }
});
test("absence of imported item nodeId is blocked, no placeholder source",()=>{
 const x=setup();
 x.refs[4].node_id="not-found";
 assert.equal(x.run(),"S7|1|BLOCKED|MEDIA_BIN_READBACK_FAILED");
 assert.equal(x.writes(),0);
});
test("unknown host version and missing Time constructor block without writes",()=>{
 const x=setup({version:"25.0"});
 assert.equal(x.run(),"S7|1|BLOCKED|HOST_UNSUPPORTED");
 const y=setup({noTime:true});
 assert.equal(y.run(),"S7|1|BLOCKED|HOST_TIME_API_UNAVAILABLE");
 assert.equal(y.writes(),0);
});
test("partial failed overwrite does not delete or automatically retry",()=>{
 const x=setup({failAt:4});
 assert.equal(x.run(),"S7|1|INCOMPLETE|OVERWRITE_FAILED");
 assert.equal(x.writes(),4);
 assert.equal(x.userBin.name,"User Originals");
 assert.equal(x.v[0].clips.length,1);
 assert.equal(x.run(),"S7|1|BLOCKED|TARGET_NOT_EMPTY");
 assert.equal(x.writes(),4);
});
test("incorrect clip start or trim readback is INCOMPLETE, not success",()=>{
 const x=setup({mismatchStart:true});
 assert.equal(x.run(),"S7|1|INCOMPLETE|PLACEMENT_READBACK_FAILED");
 assert.equal(x.writes(),1);
 const y=setup({badTrim:true});
 assert.equal(y.run(),"S7|1|INCOMPLETE|TRIM_READBACK_FAILED");
 assert.equal(y.writes(),1);
});
test("unexpected linked audio from background video stops fail-closed",()=>{
 const x=setup({linkedAudio:true});
 assert.equal(x.run(),"S7|1|INCOMPLETE|UNEXPECTED_LINKED_AUDIO");
 assert.equal(x.writes(),1);
 assert.equal(x.a[0].clips.length,1);
});
test("host exception returns INCOMPLETE while preserving every existing project",()=>{
 const x=setup({throwAt:2});
 assert.equal(x.run(),"S7|1|INCOMPLETE|HOST_PLACEMENT_EXCEPTION");
 assert.equal(x.writes(),2);
 assert.equal(x.userBin.name,"User Originals");
});
test("static safety check: no ripple insert, remove, save, export or project mutation route",()=>{
 for(const forbidden of [".insertClip(", "deleteBin(", ".remove(", ".save(",
   "exportAsMediaDirect(", "app.enableQE", "eval("]){
   assert.equal(code.includes(forbidden),false,forbidden);
 }
});

test("source trim readback failures stop immediately and preserve incomplete edits",()=>{
 for(const [option,codeExpected] of [
   [{badSourceIn:true},"SOURCE_TRIM_READBACK_FAILED"],
   [{badSourceOut:true},"SOURCE_TRIM_READBACK_FAILED"],
   [{missingSourceTrim:true},"SOURCE_TRIM_API_UNAVAILABLE"]
 ]){
   const x=setup(option);
   assert.equal(x.run(),"S7|1|INCOMPLETE|"+codeExpected);
   assert.equal(x.writes(),1);
   assert.equal(x.userBin.name,"User Originals");
   assert.equal(x.run(),"S7|1|BLOCKED|TARGET_NOT_EMPTY");
 }
});
test("source frame bounds are validated before first host write",()=>{
 for(const corrupt of [
   x=>x.plan.placements[0].source_in_frame=1,
   x=>x.plan.placements[0].source_out_frame=0,
   x=>x.plan.placements[0].source_out_frame=10000001,
   x=>x.plan.placements[0].source_out_frame="180",
 ]){
   const x=setup();corrupt(x);
   assert.equal(x.run(),"S7|1|BLOCKED|PLAN_INVALID");
   assert.equal(x.writes(),0);
 }
});

test("unexpected linked video from narration stops before further operations",()=>{
 const x=setup({linkedVideo:true});
 assert.equal(x.run(),"S7|1|INCOMPLETE|UNEXPECTED_LINKED_VIDEO");
 assert.equal(x.writes(),3);
 assert.equal(x.v[0].clips.length,2);
 assert.equal(x.userBin.name,"User Originals");
 assert.equal(x.run(),"S7|1|BLOCKED|TARGET_NOT_EMPTY");
});
