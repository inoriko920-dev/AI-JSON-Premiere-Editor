const test=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const content=fs.readFileSync(path.join(__dirname,"..","host","track_placement_adapter.jsx"),"utf8");

const GUID="a11a1111-bbbb-4444-aaaa-111111111111";
const TB="8467200000",BIN="managed-bin-1",SOURCE="image_node_1";
const START=String(150*8467200000),END=String(330*8467200000);
function clips(){
 const items=[];
 Object.defineProperty(items,"numItems",{get(){return items.length;}});
 return items;
}
function track(options={},label){
 const items=clips();
 return {
  clips:items,
  overwriteClip(item,ticks){
   options.calls=(options.calls||0)+1;
   if(options.failOverwrite)return false;
   if(options.throwOverwrite)throw Error("host exception after write");
   const start=ticks, end=options.wrongEnd?
     String(329*8467200000):END;
   items.push({nodeId:"new-trackitem-1",projectItem:item,
     start:{ticks:start},end:{ticks:end},mediaType:"Video"});
   if(options.linkedAudio){
     options.a1.clips.push({nodeId:"unexpected-linked-audio",projectItem:item,
       start:{ticks:"0"},end:{ticks:END},mediaType:"Audio"});
   }
   return true;
  }
 };
}
function mock(options={}){
 const v1=track(),v2=track(),v3=track(options),a1=track();
 options.a1=a1;
 const v=[v1,v2,v3],a=[a1];
 Object.defineProperty(v,"numTracks",{get(){return v.length;}});
 Object.defineProperty(a,"numTracks",{get(){return a.length;}});
 const seq={name:"AIJSON_ManagedNew",sequenceID:GUID,timebase:TB,
   frameSizeHorizontal:1920,frameSizeVertical:1080,
   videoTracks:v,audioTracks:a};
 const sequences=[seq];
 Object.defineProperty(sequences,"numSequences",{get(){return sequences.length;}});
 const pngItem={nodeId:SOURCE,getMediaPath:()=> "C:\\Job\\A001.png"};
 const children=[pngItem];
 Object.defineProperty(children,"numItems",{get(){return children.length;}});
 const bin={nodeId:BIN,name:"AIJSON_MEDIA_DEMO_2026",children};
 const rootChildren=[bin];
 Object.defineProperty(rootChildren,"numItems",{get(){return rootChildren.length;}});
 const project={sequences,rootItem:{children:rootChildren}};
 const context=vm.createContext({$:{},app:{version:"24.4",project}});
 vm.runInContext(content,context,{timeout:1200});
 const api=context.$._AIJSON_STILL_PLACEMENT_V1;
 const op={sequenceId:GUID,assetId:"A001",sourceNodeId:SOURCE,binNodeId:BIN,
   media_item_id:"ASSET_A001",track:"V3",zero_based_track_index:2,
   start_ticks:START,end_ticks:END,expected_duration_ticks:String(180*8467200000),
   ticks_per_frame:TB,native_trim_verified:true,effect_backend_verified:true,
   snapshot_digest_sha256:"a".repeat(64),worklist_digest_sha256:"b".repeat(64)};
 const auth={kind:"HOST_REVIEWED_TRACK_PLACEMENT_V1",ownerConfirmed:true,
   preflightAllPass:true,hostCapabilityVerified:true,layoutVerified:true,
   fxBackendVerified:true,sourceTimingVerified:true,hostVersion:"24.4",
   snapshotDigest:op.snapshot_digest_sha256,operationDigest:op.worklist_digest_sha256};
 const prev={sequenceId:GUID,rows:JSON.parse(JSON.stringify(api.inspectManaged(seq)))};
 return {api,seq,op,auth,prev,options,v1,v2,v3,a1,project,
   place:()=>api.placeStill(op,prev,auth),calls:()=>options.calls||0};
}
test("guarded candidate creates precisely one still on V3 and verifies ticks",()=>{
 const h=mock();
 assert.equal(h.place(),"S7|1|PLACED_STILL|new-trackitem-1");
 assert.equal(h.v3.clips.length,1);
 assert.equal(h.v1.clips.length,0);
 assert.equal(h.v2.clips.length,0);
 assert.equal(h.a1.clips.length,0);
 assert.equal(h.v3.clips[0].start.ticks,START);
 assert.equal(h.calls(),1);
});
test("false or absent authorization cannot place a clip",()=>{
 for(const key of ["ownerConfirmed","preflightAllPass",
   "hostCapabilityVerified","layoutVerified","fxBackendVerified",
   "sourceTimingVerified"]){
  const h=mock();
  h.auth[key]=false;
  assert.equal(h.place(),"S7|1|BLOCKED|AUTHORIZATION_NOT_VERIFIED",key);
  assert.equal(h.calls(),0);
 }
});
test("forged JSON READY cannot override an operation with missing trim proof",()=>{
 const h=mock();
 h.op.native_trim_verified=false;
 h.op.validation={status:"READY"};
 assert.equal(h.place(),"S7|1|BLOCKED|STILL_OPERATION_INVALID");
 assert.equal(h.calls(),0);
});
test("source missing from managed bin blocks before track mutation",()=>{
 const h=mock();
 h.project.rootItem.children[0].children.splice(0,1);
 assert.equal(h.place(),"S7|1|BLOCKED|MANAGED_MEDIA_MISSING");
 assert.equal(h.calls(),0);
});
test("existing clip overlap cannot be overwritten",()=>{
 const h=mock();
 h.v3.clips.push({nodeId:"prior-edit",projectItem:{nodeId:"some-other-source"},
    start:{ticks:START},end:{ticks:END},mediaType:"Video"});
 h.prev.rows=JSON.parse(JSON.stringify(h.api.inspectManaged(h.seq)));
 assert.equal(h.place(),"S7|1|BLOCKED|WOULD_OVERWRITE_EXISTING_CLIP");
 assert.equal(h.calls(),0);
 assert.equal(h.v3.clips[0].nodeId,"prior-edit");
});
test("stale clip snapshot blocks if timeline changed since owner reviewed",()=>{
 const h=mock();
 h.v3.clips.push({nodeId:"user-clip",projectItem:{nodeId:"any"},
    start:{ticks:"0"},end:{ticks:START},mediaType:"Video"});
 assert.equal(h.place(),"S7|1|BLOCKED|TIMELINE_CHANGED");
 assert.equal(h.calls(),0);
});
test("actual Premiere may choose incorrect still duration; leave INCOMPLETE",()=>{
 const h=mock({wrongEnd:true});
 assert.equal(h.place(),"S7|1|INCOMPLETE|CLIP_TIMING_READBACK_MISMATCH");
 assert.equal(h.calls(),1);
 assert.equal(h.v3.clips.length,1,"No cleanup of partial operation");
});
test("surprise linked audio is detected after host call, with no delete",()=>{
 const h=mock({linkedAudio:true});
 assert.equal(h.place(),"S7|1|INCOMPLETE|OTHER_TRACK_MODIFIED");
 assert.equal(h.calls(),1);
 assert.equal(h.a1.clips.length,1);
});
test("host overwrite failure is INCOMPLETE and never retried",()=>{
 const h=mock({failOverwrite:true});
 assert.equal(h.place(),"S7|1|INCOMPLETE|HOST_OVERWRITE_FAILED");
 assert.equal(h.calls(),1);
});
test("host exception is INCOMPLETE and never retries or deletes",()=>{
 const h=mock({throwOverwrite:true});
 assert.equal(h.place(),"S7|1|INCOMPLETE|HOST_PLACE_EXCEPTION");
 assert.equal(h.calls(),1);
});
test("second invocation needs fresh exact readback rather than old expected state",()=>{
 const h=mock();
 assert.equal(h.place(),"S7|1|PLACED_STILL|new-trackitem-1");
 assert.equal(h.place(),"S7|1|BLOCKED|TIMELINE_CHANGED");
 assert.equal(h.calls(),1);
});
test("readback correct origin on V2 is preserved with fixed track index",()=>{
 const h=mock();
 h.op.track="V2";h.op.zero_based_track_index=1;
 // Inject a different target track writer in our mocked sequence.
 h.v2.overwriteClip=h.v3.overwriteClip.bind(h.v2);
 assert.equal(h.place(),"S7|1|PLACED_STILL|new-trackitem-1");
 assert.equal(h.v2.clips.length,1);
 assert.equal(h.v3.clips.length,0);
});
test("no live CEP script references this mutation adapter",()=>{
 const manifest=fs.readFileSync(path.join(__dirname,"..","CSXS","manifest.xml"),"utf8");
 assert.equal(manifest.includes("track_placement_adapter.jsx"),false);
 for(const forbidden of ["app.enableQE","insertClip(",".remove(",".deleteBin(","eval("]){
   assert.equal(content.includes(forbidden),false,forbidden);
 }
});
