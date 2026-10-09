const test=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const source=fs.readFileSync(path.join(__dirname,"..","host","sequence_adapter.jsx"),"utf8");
const OLD_GUID="11111111-2222-3333-4444-555555555555";
const NEW_GUID="aaaa1111-bbbb-2222-cccc-333333333333";
const TB="8467200000";
function sequence(name,id,options={}){
 return {name,sequenceID:id,timebase:options.timebase||TB,
   frameSizeHorizontal:options.width||1920,
   frameSizeVertical:options.height||1080,
   videoTracks:{numTracks:options.vTracks===undefined?3:options.vTracks},
   audioTracks:{numTracks:options.aTracks===undefined?1:options.aTracks}};
}
function host(options={}){
 const prior=sequence("Untouched",OLD_GUID);
 const seqs=[prior];let creates=0;
 // Premiere SequenceCollection supports numeric [] access and numSequences.
 Object.defineProperty(seqs,"numSequences",{get(){return seqs.length;}});
 const project={
   sequences:seqs,
   activeSequence:options.noActive?null:prior,
   createNewSequence(name,requestedGUID){
     creates++;
     if(options.throwCreate){throw Error("Host crashed after mutation");}
     if(options.emptyCreate){return 0;}
     const s=sequence(name,NEW_GUID,options);
     seqs.push(s);return s;
   }
 };
 const app=options.noProject?{version:options.version||"24.5"}:
   {version:options.version||"24.5",project};
 const context={$:{},app};vm.runInNewContext(source,context,{timeout:2000});
 const adapter=context.$._AIJSON_SEQUENCE_V1;
 function authorization(){
  return {kind:"HOST_REVIEWED_OPERATION_V1",ownerConfirmed:true,
    hostCapabilityVerified:true,layoutVerified:true,fxBackendVerified:true,
    preflightAllPass:true,hostVersion:"24.5"};
 }
 const requirements={canvasWidth:1920,canvasHeight:1080,fpsNum:30,
   fpsDen:1,expectedTicksPerFrame:TB};
 return {adapter,project,seqs,prior,creates:()=>creates,requirements,authorization};
}
test("ES3 host inspector reports exact ticks decimal as a string, no private project metadata",()=>{
 const h=host();
 assert.equal(h.adapter.inspect(),
  "S5|1|OBSERVED|24.5|8467200000|3|1|1920|1080");
 assert.equal(h.adapter.inspect().includes("Untouched"),false);
 const noActive=host({noActive:true});
 assert.equal(noActive.adapter.inspect(),"S5|1|NO_ACTIVE_SEQUENCE|24.5");
});
test("cannot probe or create without real 24.x project",()=>{
 const a=host({version:"25.6"});
 assert.equal(a.adapter.inspect(),"S5|1|ERROR|HOST_UNSUPPORTED");
 assert.equal(a.adapter.createNewEmpty("Managed",NEW_GUID,
   a.requirements,a.authorization()),
   "S5|1|BLOCKED|HOST_UNSUPPORTED");
 assert.equal(a.creates(),0);
 const b=host({noProject:true});
 assert.equal(b.adapter.inspect(),"S5|1|ERROR|NO_PROJECT");
});
test("unverified/absent approval and mismatched profile block before ANY create call",()=>{
 const h=host();
 const ok=h.authorization();
 for(const rejected of [undefined,{}, {...ok,preflightAllPass:false},
   {...ok,layoutVerified:false}, {...ok,fxBackendVerified:false},
   {...ok,hostVersion:"24.4"}, {...ok,ownerConfirmed:false}]){
  assert.equal(h.adapter.createNewEmpty("Managed",NEW_GUID,h.requirements,rejected),
   "S5|1|BLOCKED|AUTHORIZATION_NOT_VERIFIED");
 }
 assert.equal(h.adapter.createNewEmpty("Managed",NEW_GUID,
  {...h.requirements,fpsNum:2997},ok),
  "S5|1|BLOCKED|AUTHORIZATION_NOT_VERIFIED");
 assert.equal(h.creates(),0);
 assert.equal(h.seqs.length,1);
});
test("duplicate sequence name or identifier refuses without mutation",()=>{
 const h=host(),a=h.authorization();
 assert.equal(h.adapter.createNewEmpty("untouched",NEW_GUID,h.requirements,a),
 "S5|1|BLOCKED|SEQUENCE_ALREADY_EXISTS");
 assert.equal(h.adapter.createNewEmpty("Managed",OLD_GUID,h.requirements,a),
 "S5|1|BLOCKED|SEQUENCE_ALREADY_EXISTS");
 assert.equal(h.adapter.createNewEmpty("../bad",NEW_GUID,h.requirements,a),
 "S5|1|BLOCKED|SEQUENCE_ID_INVALID");
 assert.equal(h.creates(),0);
});
test("create-empty inserts exactly one NEW sequence and never alters previous",()=>{
 const h=host(),originalName=h.prior.name;
 const response=h.adapter.createNewEmpty("AIJSON Managed",NEW_GUID,
   h.requirements,h.authorization());
 assert.equal(response,"S5|1|CREATED_EMPTY|TRACKS_AND_TIMEBASE_READBACK_OK");
 assert.equal(h.creates(),1);
 assert.equal(h.seqs.length,2);
 assert.equal(h.prior.name,originalName);
 assert.equal(h.seqs[1].name,"AIJSON Managed");
});
test("post-mutation profile mismatch leaves new sequence intact and incomplete",()=>{
 const h=host({width:1280});
 assert.equal(h.adapter.createNewEmpty("Managed",NEW_GUID,
  h.requirements,h.authorization()),
  "S5|1|INCOMPLETE|SEQUENCE_PROFILE_MISMATCH");
 assert.equal(h.creates(),1);
 assert.equal(h.seqs.length,2,"Never delete a partially created sequence");
});
test("missing track in created sequence is incomplete, no cleanup/retry",()=>{
 const h=host({vTracks:2});
 assert.equal(h.adapter.createNewEmpty("Managed",NEW_GUID,
  h.requirements,h.authorization()),
  "S5|1|INCOMPLETE|SEQUENCE_PROFILE_MISMATCH");
 assert.equal(h.creates(),1);
});
test("host failure is not retried and prior sequence stays intact",()=>{
 const h=host({throwCreate:true});
 assert.equal(h.adapter.createNewEmpty("Managed",NEW_GUID,
  h.requirements,h.authorization()),
  "S5|1|INCOMPLETE|HOST_CREATE_EXCEPTION");
 assert.equal(h.creates(),1);
 assert.equal(h.prior.name,"Untouched");
});
test("host implementation does not use undocumented QE, deletes, imports, or exports",()=>{
 for(const forbidden of ["app.enableQE","removeSequence(","deleteSequence(",
   "importFiles(","insertClip(","exportAsMediaDirect(","eval("]){
   assert.equal(source.includes(forbidden),false,forbidden);
 }
});
