const test=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const source=fs.readFileSync(path.join(__dirname,"..","host","track_placement_adapter.jsx"),"utf8");
const TPF=8467200000;
const guid="aaaa1111-bbbb-2222-cccc-333333333333";
function operation(key,track,item,start,end,slot,sourceIn=0){
 const tick=f=>String(f*TPF);
 return {key,track,item_id:item,slot,start_frame:start,end_frame:end,
  source_in_frame:sourceIn,source_out_frame:sourceIn+end-start,
  source_in_ticks:tick(sourceIn),source_out_ticks:tick(sourceIn+end-start),
  start_ticks:tick(start),end_ticks:tick(end),duration_ticks:tick(end-start),
  readback_verified:false};
}
function mock(options={}){
 const ops=[
  operation("BG_00000","V1","SOURCE_BACKGROUND",0,120,"BACKGROUND"),
  operation("BG_00001","V1","SOURCE_BACKGROUND",120,330,"BACKGROUND",0),
  operation("V001/A001","V2","ASSET_A001",0,150,"VISUAL"),
  operation("V002/A002","V2","ASSET_A002",150,330,"VISUAL"),
  operation("V002/A003","V3","ASSET_A003",192,330,"VISUAL"),
  operation("NARRATION","A1","SOURCE_AUDIO",0,330,"AUDIO")
 ];
 const manifest={schema_version:"timeline-placement-candidate-v1",
  status:"CANDIDATE_NOT_EXECUTABLE",can_assemble:false,
  operation_sha256:"a".repeat(64),snapshot_sha256:"b".repeat(64),
  ticks_per_frame:String(TPF),total_frames:330,
  operation_count:ops.length,operations:ops};
 let inserts=0, changed=0;
 function Time(){this.ticks="0";}
 function tracks(count,isAudio){
  const a=[];
  for(let i=0;i<count;i++){
   const c=[];
   Object.defineProperty(c,"numItems",{get(){return this.length;}});
   a.push({clips:c,overwriteClip(item,start){
     inserts++;
     if(options.failInsertAt===inserts)return false;
     if(options.throwAt===inserts)throw Error("insertion failed");
     const clip={projectItem:item,start:{ticks:start},end:{ticks:"999"},
       inPoint:{ticks:"0"},outPoint:{ticks:"999"}};
     if(options.ignoreOutPoint){
       Object.defineProperty(clip,"outPoint",{get(){return {ticks:"0"};},
         set(_){}});
     }
     c.push(clip);
     if(options.linkedAudioAt===inserts && !isAudio){
       seq.audioTracks[0].clips.push({projectItem:item});
     }
     return true;
   }});
  }
  Object.defineProperty(a,"numTracks",{get(){return a.length;}});
  return a;
 }
 const seq={sequenceID:guid,name:"AIJSON_My Managed Sequence",
    timebase:String(TPF),videoTracks:null,audioTracks:null};
 seq.videoTracks=tracks(3,false);seq.audioTracks=tracks(1,true);
 const sourceMap={};
 for(const [id,kind] of [
  ["SOURCE_BACKGROUND","background"],["SOURCE_AUDIO","audio"],
  ["ASSET_A001","png"],["ASSET_A002","png"],["ASSET_A003","png"]]){
   const projectItem={nodeId:id,getMediaPath(){return "C:\\Fixture\\"+id;}};
   sourceMap[id]={kind,nodeId:id,projectItem};
 }
 const auth={kind:"HOST_REVIEWED_TIMELINE_V1",ownerConfirmed:true,
   finalMediaHashesVerified:true,hostCapabilityVerified:true,
   layoutAndAllFxVerified:true,sourceIsolationVerified:true,
   preflightAllPass:true,hostVersion:"24.4",sequenceId:guid,
   operationDigest:manifest.operation_sha256,snapshotDigest:manifest.snapshot_sha256};
 const context={$:{},app:{version:options.hostVersion||"24.4"},Time};
 vm.runInNewContext(source,context,{timeout:2000});
 return {manifest,sourceMap,auth,seq,
   adapter:context.$._AIJSON_TRACK_PLACER_V1,
   inserts:()=>inserts,run(){return this.adapter.placeCandidate(this.manifest,this.seq,
      this.sourceMap,this.auth);}};
}
test("all V1/V2/V3/A1 clips placed into empty managed sequence and trimmed",()=>{
 const o=mock();
 assert.equal(o.run(),"S7|1|PLACED_CANDIDATE|6");
 assert.equal(o.inserts(),6);
 assert.equal(o.seq.videoTracks[0].clips.length,2);
 assert.equal(o.seq.videoTracks[1].clips.length,2);
 assert.equal(o.seq.videoTracks[2].clips.length,1);
 assert.equal(o.seq.audioTracks[0].clips.length,1);
 const last=o.seq.videoTracks[0].clips[1];
 assert.equal(last.start.ticks,String(120*TPF));
 assert.equal(last.end.ticks,String(330*TPF));
 assert.equal(last.outPoint.ticks,String(210*TPF));
});
test("no host or owner/codec/FX authorization always blocks before mutation",()=>{
 for(const changed of ["ownerConfirmed","finalMediaHashesVerified",
    "hostCapabilityVerified","layoutAndAllFxVerified",
    "sourceIsolationVerified","preflightAllPass"]){
   const o=mock();o.auth[changed]=false;
   assert.equal(o.run(),"S7|1|BLOCKED|AUTHORIZATION_NOT_VERIFIED",changed);
   assert.equal(o.inserts(),0);
 }
 const o=mock({hostVersion:"25.1"});
 assert.equal(o.run(),"S7|1|BLOCKED|HOST_UNSUPPORTED");
});
test("existing manual timeline edits cannot be overwritten",()=>{
 const o=mock();
 o.seq.videoTracks[1].clips.push({projectItem:{nodeId:"user-content"}});
 assert.equal(o.run(),"S7|1|BLOCKED|TARGET_NOT_EMPTY");
 assert.equal(o.inserts(),0);
 assert.equal(o.seq.videoTracks[1].clips.length,1);
});
test("manifest changed or mismatched digest blocks",()=>{
 const a=mock();a.auth.operationDigest="c".repeat(64);
 assert.equal(a.run(),"S7|1|BLOCKED|AUTHORIZATION_NOT_VERIFIED");
 const b=mock();b.manifest.operations[0].item_id="ASSET_A001";
 assert.equal(b.run(),"S7|1|BLOCKED|PLACEMENT_MANIFEST_INVALID");
 const c=mock();c.manifest.operations[0].source_out_ticks="NAN";
 assert.equal(c.run(),"S7|1|BLOCKED|PLACEMENT_MANIFEST_INVALID");
});
test("imported ProjectItem identity mismatch blocks without insertion",()=>{
 const o=mock();o.sourceMap.SOURCE_BACKGROUND.nodeId="wrong";
 assert.equal(o.run(),"S7|1|BLOCKED|SOURCE_OR_TRACK_UNVERIFIED");
 assert.equal(o.inserts(),0);
});
test("linked video audio added to A1 triggers INCOMPLETE, never continues",()=>{
 const o=mock({linkedAudioAt:1});
 assert.equal(o.run(),"S7|1|INCOMPLETE|SIDE_EFFECT_TRACK_CHANGED");
 assert.equal(o.inserts(),1);
 assert.equal(o.seq.audioTracks[0].clips.length,1);
});
test("malformed clip end readback stops after one mutation",()=>{
 const o=mock({ignoreOutPoint:true});
 assert.equal(o.run(),"S7|1|INCOMPLETE|CLIP_TIMING_READBACK_FAILED");
 assert.equal(o.inserts(),1);
});
test("overwrite API failing never deletes or retries",()=>{
 const o=mock({failInsertAt:3});
 assert.equal(o.run(),"S7|1|INCOMPLETE|OVERWRITE_API_FAILED");
 assert.equal(o.inserts(),3);
 assert.equal(o.seq.videoTracks[0].clips.length,2);
});
test("host exception after partial placement is INCOMPLETE",()=>{
 const o=mock({throwAt:2});
 assert.equal(o.run(),"S7|1|INCOMPLETE|HOST_EXCEPTION");
 assert.equal(o.inserts(),2);
 assert.equal(o.seq.videoTracks[0].clips.length,1);
});
test("duplicate placement keys and overlapping same-track spans are refused",()=>{
 const a=mock();a.manifest.operations[1].key=a.manifest.operations[0].key;
 assert.equal(a.run(),"S7|1|BLOCKED|PLACEMENT_MANIFEST_INVALID");
 const b=mock();b.manifest.operations[1].start_frame=110;
 assert.equal(b.run(),"S7|1|BLOCKED|PLACEMENT_MANIFEST_INVALID");
});
test("adapter never modifies master media, deletes timeline, or exports",()=>{
 for(const forbidden of ["setInPoint(", "setOutPoint(", "deleteSequence(",
   "remove(", "exportAsMediaDirect(", "app.enableQE", "eval("]){
  assert.equal(source.includes(forbidden),false,forbidden);
 }
});

test("manifest tick strings must equal exact frame arithmetic",()=>{
 const one=mock();
 one.manifest.operations[0].end_ticks=String(120*TPF+1);
 assert.equal(one.run(),"S7|1|BLOCKED|PLACEMENT_MANIFEST_INVALID");
 const two=mock();
 two.manifest.operations[0].source_out_frame=121;
 assert.equal(two.run(),"S7|1|BLOCKED|PLACEMENT_MANIFEST_INVALID");
 const three=mock();
 three.manifest.operations[2].duration_ticks="999999999999999999999";
 assert.equal(three.run(),"S7|1|BLOCKED|PLACEMENT_MANIFEST_INVALID");
});
test("background gap and incomplete narration are rejected",()=>{
 const a=mock();
 a.manifest.operations[1].start_frame=121;
 a.manifest.operations[1].start_ticks=String(121*TPF);
 assert.equal(a.run(),"S7|1|BLOCKED|PLACEMENT_MANIFEST_INVALID");
 const b=mock();
 const narration=b.manifest.operations[5];
 narration.end_frame=329;
 narration.end_ticks=String(329*TPF);
 narration.duration_ticks=String(329*TPF);
 narration.source_out_frame=329;
 narration.source_out_ticks=String(329*TPF);
 assert.equal(b.run(),"S7|1|BLOCKED|PLACEMENT_MANIFEST_INVALID");
});
