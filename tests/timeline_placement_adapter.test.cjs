const test=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const source=fs.readFileSync(path.join(__dirname,"..","host","timeline_placement_adapter.jsx"),"utf8");
const GUID="11111111-2222-3333-4444-555555555555";
const digest="a".repeat(64);
const before={V1:[],V2:[],V3:[],A1:[]};
function ctx(opts={}){
 const clips={},errors=opts;
 let calls=0;
 function mkTrack(key){
  const entries=[];Object.defineProperty(entries,"numItems",{get(){return this.length;}});
  const track={clips:entries,overwriteClip(item,tick){
    calls++;
    if(opts.throwOnWrite){throw Error("Premiere host unavailable");}
    if(opts.failWrite){return false;}
    const end=opts.badEnd?"9999":"200";
    entries.push({nodeId:"clip-"+calls,projectItem:item,
      start:{ticks:tick},end:{ticks:end}});
    if(opts.linkedAudio && key==="V2"){
      clips.A1.clips.push({nodeId:"linked-"+calls,projectItem:item,
        start:{ticks:tick},end:{ticks:end}});
    }
    return true;
  }};
  return track;
 }
 ["V1","V2","V3","A1"].forEach(x=>clips[x]=mkTrack(x));
 const vids=[clips.V1,clips.V2,clips.V3],audios=[clips.A1];
 vids.numTracks=3;audios.numTracks=1;
 const children=[];
 Object.defineProperty(children,"numItems",{get(){return this.length;}});
 const item={nodeId:"png.001",getMediaPath(){return "C:\\JOB\\image.png";}};
 const bin={name:"AIJSON_MEDIA_BATCH_2026",nodeId:"bin-001",
   children:[item]};
 bin.children.numItems=1;
 children.push(bin);
 const sequences=[{sequenceID:GUID,name:"AIJSON_TEST_SEQUENCE",
   videoTracks:vids,audioTracks:audios}];
 sequences.numSequences=1;
 const project={rootItem:{children},sequences};
 const globals={$:{},app:{version:opts.version||"24.3",project}};
 vm.runInNewContext(source,globals,{timeout:2500});
 const adapter=globals.$._AIJSON_PLACEMENT_V1;
 const request={sequenceId:GUID,sequenceName:"AIJSON_TEST_SEQUENCE",
    mediaBinName:bin.name,projectItemNodeId:"png.001",
    track:"V2",startTicks:"100",endTicks:"200",
    sourceDurationTicks:"100",expectedType:"Video",
    snapshotDigest:digest,expectedBefore:JSON.parse(JSON.stringify(before))};
 const auth={kind:"HOST_REVIEWED_PLACEMENT_V1",ownerConfirmed:true,
   hostCapabilityVerified:true,projectIdentityVerified:true,
   mediaHashesFresh:true,layoutVerified:true,fxBackendVerified:true,
   preflightAllPass:true,sourceDurationVerified:true,
   hostVersion:"24.3",sequenceId:GUID,snapshotDigest:digest,
   sourceItemNodeId:"png.001",expectedSourceDurationTicks:"100"};
 return {adapter,request,auth,project,clips,calls:()=>calls,bin,item};
}
test("can place a single asset on empty managed V2 with exact tick-string readback",()=>{
 const h=ctx();
 assert.equal(h.adapter.placeOne(h.request,h.auth),"S7|1|PLACED_ONE|V2|clip-1");
 assert.equal(h.calls(),1);
 assert.equal(h.clips.V2.clips[0].start.ticks,"100");
 assert.equal(h.clips.V3.clips.length,0);
 assert.equal(h.clips.A1.clips.length,0);
});
test("cannot mutate when host, owner, media hash or FX proof missing",()=>{
 const h=ctx();
 for(const field of ["ownerConfirmed","hostCapabilityVerified",
   "projectIdentityVerified","mediaHashesFresh","layoutVerified",
   "fxBackendVerified","preflightAllPass","sourceDurationVerified"]){
   const auth={...h.auth,[field]:false};
   assert.equal(h.adapter.placeOne(h.request,auth),
     "S7|1|BLOCKED|AUTHORIZATION_NOT_VERIFIED",field);
 }
 assert.equal(h.calls(),0);
});
test("older sequence and existing clip baseline are immutable",()=>{
 const h=ctx();
 h.clips.V2.clips.push({nodeId:"manual",projectItem:h.item,
   start:{ticks:"0"},end:{ticks:"50"}});
 assert.equal(h.adapter.placeOne(h.request,h.auth),
   "S7|1|BLOCKED|TRACK_BASELINE_CHANGED");
 assert.equal(h.calls(),0);
 assert.equal(h.clips.V2.clips[0].nodeId,"manual");
});
test("no insertion on nonempty managed track even when baseline matches",()=>{
 const h=ctx();
 h.clips.V2.clips.push({nodeId:"managed",projectItem:h.item,
   start:{ticks:"0"},end:{ticks:"50"}});
 h.request.expectedBefore.V2=[{id:"managed",source_id:"png.001",
   start:"0",end:"50"}];
 assert.equal(h.adapter.placeOne(h.request,h.auth),
   "S7|1|BLOCKED|TRACK_NOT_EMPTY");
 assert.equal(h.calls(),0);
});
test("mismatched duration and source identity stop before any write",()=>{
 const h=ctx();
 h.auth.expectedSourceDurationTicks="101";
 assert.equal(h.adapter.placeOne(h.request,h.auth),
   "S7|1|BLOCKED|SOURCE_DURATION_UNVERIFIED");
 h.auth.expectedSourceDurationTicks="100";
 h.auth.sourceItemNodeId="another";
 assert.equal(h.adapter.placeOne(h.request,h.auth),
   "S7|1|BLOCKED|SOURCE_DURATION_UNVERIFIED");
 assert.equal(h.calls(),0);
});
test("wrong sequence UUID/name or wrong host version refuses",()=>{
 const h=ctx();
 h.request.sequenceId="22222222-2222-3333-4444-555555555555";
 h.auth.sequenceId=h.request.sequenceId;
 assert.equal(h.adapter.placeOne(h.request,h.auth),
   "S7|1|BLOCKED|MANAGED_SEQUENCE_UNAVAILABLE");
 const bad=ctx({version:"25.0"});
 assert.equal(bad.adapter.placeOne(bad.request,bad.auth),
   "S7|1|BLOCKED|HOST_UNAVAILABLE");
 assert.equal(bad.calls(),0);
});
test("on mismatched readback new clip remains and status is INCOMPLETE",()=>{
 const h=ctx({badEnd:true});
 assert.equal(h.adapter.placeOne(h.request,h.auth),
   "S7|1|INCOMPLETE|CLIP_TIMING_OR_ID_MISMATCH");
 assert.equal(h.calls(),1);
 assert.equal(h.clips.V2.clips.length,1);
});
test("linked audio side effect fails readback and preserves newly placed clip",()=>{
 const h=ctx({linkedAudio:true});
 assert.equal(h.adapter.placeOne(h.request,h.auth),
   "S7|1|INCOMPLETE|UNEXPECTED_TRACK_MUTATION");
 assert.equal(h.clips.A1.clips.length,1);
 assert.equal(h.clips.V2.clips.length,1);
});
test("host failure after attempt never retries or erases",()=>{
 const h=ctx({throwOnWrite:true});
 assert.equal(h.adapter.placeOne(h.request,h.auth),
   "S7|1|INCOMPLETE|HOST_PLACEMENT_EXCEPTION");
 assert.equal(h.calls(),1);
});
test("placing on A1 requires Audio media type and uses audio track 0",()=>{
 const h=ctx();
 h.request.track="A1";h.request.expectedType="Audio";
 assert.equal(h.adapter.placeOne(h.request,h.auth),
   "S7|1|PLACED_ONE|A1|clip-1");
 assert.equal(h.clips.A1.clips.length,1);
 assert.equal(h.clips.V2.clips.length,0);
});
test("reject preflight bypass, untrusted paths and missing project item",()=>{
 const h=ctx();
 h.request.snapshotDigest="x";
 assert.equal(h.adapter.placeOne(h.request,h.auth),
   "S7|1|BLOCKED|AUTHORIZATION_NOT_VERIFIED");
 h.request.snapshotDigest=digest;
 h.request.projectItemNodeId="bad/../../source";
 assert.equal(h.adapter.placeOne(h.request,h.auth),
   "S7|1|BLOCKED|PLACEMENT_INVALID");
 assert.equal(h.calls(),0);
});
test("read-only sequence snapshot is safe and detects malformed clip IDs",()=>{
 const h=ctx();const snapshot=h.adapter.inspectSequence(GUID);
 assert.deepEqual(JSON.parse(JSON.stringify(snapshot)),before);
 h.clips.V2.clips.push({nodeId:"bad id",projectItem:h.item,start:{ticks:"0"},end:{ticks:"1"}});
 assert.equal(h.adapter.inspectSequence(GUID),null);
});
test("candidate host code never exports, deletes, ripples or calls QE",()=>{
 for(const forbidden of ["insertClip(","app.enableQE","deleteSequence(","remove(",
   "setInPoint(","setOutPoint(","exportAsMediaDirect(","eval("]){
   assert.equal(source.includes(forbidden),false,forbidden);
 }
});
