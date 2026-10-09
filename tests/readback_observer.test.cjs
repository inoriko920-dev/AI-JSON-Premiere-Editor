const test=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const source=fs.readFileSync(path.join(__dirname,"..","host","readback_observer.jsx"),"utf8");
const SEQ="aaaa1111-bbbb-2222-cccc-333333333333";
const TB="8467200000";
function create(opts={}){
 const item={nodeId:"node-background"};
 const make=(name)=>{
   const clips=[];Object.defineProperty(clips,"numItems",{get(){return this.length;}});
   return {name,clips};
 };
 const v=[make("V1"),make("V2"),make("V3")],a=[make("A1")];
 Object.defineProperty(v,"numTracks",{get(){return v.length;}});
 Object.defineProperty(a,"numTracks",{get(){return a.length;}});
 const seq={sequenceID:SEQ,timebase:opts.tb||TB,videoTracks:v,audioTracks:a};
 const seqs=[seq];Object.defineProperty(seqs,"numSequences",{get(){return seqs.length;}});
 const context={$:{},app:{version:opts.version||"24.4",project:{sequences:seqs}}};
 vm.runInNewContext(source,context,{timeout:2000});
 function addClip(track,id,sourceId,start,end,sourceIn,sourceOut){
   track.clips.push({nodeId:id,projectItem:{nodeId:sourceId},
      start:{ticks:start},end:{ticks:end},inPoint:{ticks:sourceIn},
      outPoint:{ticks:sourceOut}});
 }
 return {api:context.$._AIJSON_READBACK_V1,context,seq,seqs,v,a,addClip};
}
test("unmodified managed four-track sequence yields valid JSON without project names",()=>{
 const x=create();
 x.addClip(x.v[0],"clip-1","node-background","0",TB,"0",TB);
 x.addClip(x.v[1],"clip-2","node-png","0",TB,"0",TB);
 const raw=x.api.capture(SEQ),r=JSON.parse(raw);
 assert.equal(r.schema_version,"premiere-track-readback-v1");
 assert.equal(r.status,"CAPTURED_UNVERIFIED");
 assert.equal(r.can_assemble,false);
 assert.equal(r.ticks_per_frame,TB);
 assert.equal(r.tracks.V1[0].item_node_id,"node-background");
 assert.equal(r.tracks.V2[0].clip_id,"clip-2");
 assert.equal(r.tracks.A1.length,0);
 assert.equal(raw.includes("C:\\Users"),false);
});
test("unexpected linked clips in extra video or audio track halt readback",()=>{
 const x=create();const make=()=>{
  const clips=[{nodeId:"leak"}];clips.numItems=1;return {clips};
 };
 x.v.push(make());
 assert.equal(x.api.capture(SEQ),"S14|1|ERROR|EXTRA_VIDEO_TRACK_CONTENT");
 const y=create();y.a.push(make());
 assert.equal(y.api.capture(SEQ),"S14|1|ERROR|EXTRA_AUDIO_TRACK_CONTENT");
});
test("unknown sequence, unknown host version and malformed timebase fail closed",()=>{
 const x=create();
 assert.equal(x.api.capture("bad"),"S14|1|ERROR|SEQUENCE_ID_INVALID");
 assert.equal(x.api.capture("aaaa1111-bbbb-2222-cccc-444444444444"),
  "S14|1|ERROR|SEQUENCE_NOT_UNIQUE");
 x.context.app.version="25.3";
 assert.equal(x.api.capture(SEQ),"S14|1|ERROR|HOST_UNSUPPORTED");
 x.context.app.version="24.4";x.seq.timebase="0";
 assert.equal(x.api.capture(SEQ),"S14|1|ERROR|TIMEBASE_INVALID");
});
test("untrusted clip ID, tick or duplicate readback is not serialized",()=>{
 const x=create();
 x.addClip(x.v[1],"bad/id","node-1","0",TB,"0",TB);
 assert.equal(x.api.capture(SEQ),"S14|1|ERROR|TRACK_READBACK_INVALID_V2");
 const y=create();
 y.addClip(y.v[0],"clip-1","node-1","0",TB,"0",TB);
 y.addClip(y.v[2],"clip-1","node-1","0",TB,"0",TB);
 assert.equal(y.api.capture(SEQ),"S14|1|ERROR|TRACK_READBACK_INVALID_V3");
 const z=create();
 z.addClip(z.a[0],"clip-1","node-1","1.0",TB,"0",TB);
 assert.equal(z.api.capture(SEQ),"S14|1|ERROR|TRACK_READBACK_INVALID_A1");
});
test("observer executes no mutation API, no file IO, no eval or user media read",()=>{
 for(const name of [".overwriteClip(",".insertClip(",".createBin(",
   ".importFiles(", "app.enableQE", "eval(", "File(", ".remove("]){
  assert.equal(source.includes(name),false,name);
 }
});
