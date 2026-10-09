const test=require("node:test");
const assert=require("node:assert/strict");
const path=require("node:path");
const vm=require("node:vm");
const fs=require("node:fs");
const helper=require("../panel/helper_bridge.js");
const api=require("../panel/validation_bridge.js");

const VALID={
    schema_version:"structure-validation-report-v1",status:"NEEDS_REVIEW",
    can_assemble:false,error_count:0,review_count:1,
    issues:[{code:"E_HOST_UNVERIFIED",severity:"REVIEW",
        pointer:"/host",message:"Test fixture. C:\\Private\\secret"}]
};
function fake(deps={}){
  const calls=[],control={calls};
  const io={realpathSync:x=>x,statSync:x=>({
    isFile:()=>!/media(\/|\\)?$/.test(x),
    isDirectory:()=>/media(\/|\\)?$/.test(x)
  })};
  const opts={
    platform:"win32",fs:io,path,pythonExe:"C:\\Python311\\python.exe",
    extensionPath:"file:///C:/Adobe/CEP/Panel",
    decodeExtensionPath:helper.decodeExtensionPath,
    execFile:(exe,args,options,done)=>{
      calls.push({exe,args,options});
      control.done=done;
      return {kill(){control.killCount=(control.killCount||0)+1;}};
    },
    ...deps
  };
  control.validator=api.createValidator(opts);
  return control;
}
const selected={
  edit:"C:\\Project\\EDIT_PLAN.json",
  animation:"C:\\Project\\ANIMATION_PLAN.json",
  media:"C:\\Project\\media"
};
test("native CEP picker file and folder signatures match Adobe CEP API",()=>{
 let argv;
 const picker={showOpenDialogEx:(...args)=>{
   argv=args;return {err:0,data:["C:\\Project\\EDIT_PLAN.json"]};
 }};
 let item=api.selectNative(picker,"edit",path);
 assert.equal(item.status,"selected");
 assert.deepEqual(argv,[false,false,"Pilih EDIT_PLAN.json","","json".split(","),
                        "File JSON","Pilih"]);
 const folder={showOpenDialogEx:(...args)=>{
   argv=args;return {err:0,data:["C:\\Project\\media"]};
 }};
 item=api.selectNative(folder,"media",path);
 assert.equal(item.status,"selected");
 assert.equal(argv[1],true);
 assert.deepEqual(argv[4],[]);
});
test("picker cancellation and malicious/incorrect filename fail closed",()=>{
 const picker=x=>({showOpenDialogEx:()=>({err:0,data:x})});
 assert.equal(api.selectNative(picker([]),"edit",path).status,"cancelled");
 for(const item of ["C:\\Temp\\notes.json","\\\\server\\share\\EDIT_PLAN.json",
   "C:EDIT_PLAN.json","C:\\private\\edit_plan.json\nbad"]){
  assert.equal(api.selectNative(picker([item]),"edit",path).status,"error",item);
 }
 assert.equal(api.selectNative(picker(["C:\\foo\\EDIT_PLAN.json","C:\\bar\\EDIT_PLAN.json"]),"edit",path).status,"error");
 assert.equal(api.selectNative(null,"edit",path).code,"CEP_DIALOG_UNAVAILABLE");
});
test("raw malicious report cannot mark assembly READY or leak paths",()=>{
 for(const candidate of [
  JSON.stringify({...VALID,can_assemble:true}),
  JSON.stringify({...VALID,status:"READY"}),
  JSON.stringify({...VALID,review_count:2}),
  JSON.stringify({...VALID,issues:[{code:"malicious",severity:"REVIEW"}]}),
  "NOT_JSON",null,"x".repeat(524289)
 ]){
  assert.equal(api.parseReport(candidate).status,"error");
 }
 const good=api.parseReport(JSON.stringify(VALID));
 assert.equal(good.status,"NEEDS_REVIEW");
 assert.equal(good.can_assemble,false);
 assert.deepEqual(good.issues,[{code:"E_HOST_UNVERIFIED",severity:"REVIEW"}]);
 assert.equal(JSON.stringify(good).includes("Private"),false);
});
test("Windows launches isolated Python with fixed script and bounded no-shell args",()=>{
 const o=fake();let outcome=null;
 assert.equal(o.validator.run(selected,r=>outcome=r),true);
 assert.equal(o.calls.length,1);
 const call=o.calls[0];
 assert.equal(call.exe,"C:\\Python311\\python.exe");
 assert.equal(call.options.shell,false);
 assert.equal(call.options.windowsHide,true);
 assert.equal(call.options.timeout,30000);
 assert.equal(call.options.maxBuffer,524288);
 assert.equal(call.args[0],"-I");
 assert.equal(call.args[1],"-B");
 assert.equal(call.args[2],"C:\\Adobe\\CEP\\Panel\\helper\\validate_request.py");
 assert.deepEqual(call.args.slice(3,7),[
   "--edit",selected.edit,"--animation",selected.animation]);
 assert.equal(call.args.includes("--media-root"),true);
 o.done({code:3},JSON.stringify(VALID));
 assert.equal(outcome.status,"NEEDS_REVIEW");
 assert.equal(outcome.can_assemble,false);
 assert.equal(o.validator.isBusy(),false);
});
test("invalid CLI report exit/status combinations fail closed",()=>{
 let o=fake();let result;
 o.validator.run(selected,r=>result=r);
 o.done(null,JSON.stringify(VALID));
 assert.equal(result.code,"VALIDATOR_EXIT_MISMATCH");
 o=fake();o.validator.run(selected,r=>result=r);
 o.done({code:2},JSON.stringify(VALID));
 assert.equal(result.code,"VALIDATOR_EXIT_MISMATCH");
 o=fake();o.validator.run(selected,r=>result=r);
 o.done({code:"ENOENT"},"");
 assert.equal(result.code,"VALIDATOR_EXEC_FAILED");
});
test("bad path, missing files and no Python never spawn",()=>{
 for(const [overrides,choice,code] of [
  [{pythonExe:null},selected,"VALIDATOR_PYTHON_NOT_CONFIGURED"],
  [{pythonExe:"cmd.exe"},selected,"VALIDATOR_PATH_INVALID"],
  [{platform:"linux"},selected,"VALIDATOR_WINDOWS_ONLY"],
  [{fs:{realpathSync(){throw Error("not found")}}},selected,"VALIDATOR_INPUT_MISSING"],
  [{}, {...selected,edit:"C:\\Temp\\virus.txt"},"VALIDATOR_INPUT_MISSING"]
 ]){
   const o=fake(overrides);let result;
   assert.equal(o.validator.run(choice,r=>result=r),false);
   assert.equal(result.code,code);
   assert.equal(o.calls.length,0);
 }
});
test("cancel kills subprocess and stale completion cannot succeed",()=>{
 const o=fake();let results=[];
 assert.equal(o.validator.run(selected,r=>results.push(r)),true);
 assert.equal(o.validator.run(selected,r=>results.push(r)),false);
 const stale=o.done;
 o.validator.cancel();
 assert.equal(o.killCount,1);
 assert.equal(o.validator.run(selected,r=>results.push(r)),true);
 stale({code:3},JSON.stringify(VALID));
 assert.equal(results.length,0);
 o.done({code:3},JSON.stringify(VALID));
 assert.equal(results.length,1);
 assert.equal(results[0].status,"NEEDS_REVIEW");
});
test("bridge exports to both window and CommonJS under CEP mixed Node",()=>{
 const content=fs.readFileSync(path.join(__dirname,"..","panel","validation_bridge.js"),"utf8");
 const context={document:{},module:{exports:{}}};
 vm.runInNewContext(content,context,{timeout:1000});
 assert.equal(typeof context.AIJSONValidationBridge.createValidator,"function");
 assert.equal(typeof context.module.exports.createValidator,"function");
});

test("sanitized read-only draft summary is accepted; executable draft is refused",()=>{
 const draft={status:"DRAFT_NOT_EXECUTABLE",can_assemble:false,
   scene_count:2,asset_instance_count:3,total_frames:330,
   operation_digest_sha256:"a".repeat(64)};
 let data=api.parseReport(JSON.stringify({...VALID,draft}));
 assert.equal(data.status,"NEEDS_REVIEW");
 assert.equal(data.draft.total_frames,330);
 assert.equal(data.draft.digest,"a".repeat(64));
 data=api.parseReport(JSON.stringify({...VALID,draft:{...draft,can_assemble:true}}));
 assert.equal(data.code,"VALIDATOR_RESPONSE_INVALID");
});

test("optional FFprobe executable is fixed environment configuration, not user JSON",()=>{
 let o=fake({ffprobeExe:"C:\\FFmpeg\\bin\\ffprobe.exe"}),result;
 assert.equal(o.validator.run(selected,r=>result=r),true);
 assert.deepEqual(o.calls[0].args.slice(-2),
   ["--ffprobe-exe","C:\\FFmpeg\\bin\\ffprobe.exe"]);
 o.done({code:3},JSON.stringify(VALID));
 assert.equal(result.status,"NEEDS_REVIEW");
 o=fake({ffprobeExe:"ffprobe.exe"});
 assert.equal(o.validator.run(selected,r=>result=r),false);
 assert.equal(result.code,"VALIDATOR_FFPROBE_PATH_INVALID");
 assert.equal(o.calls.length,0);
});

test("sanitized import snapshot is not host approval and rejects forged readiness",()=>{
 const snap={status:"CANDIDATE_NOT_AUTHORIZED",can_import:false,
   item_count:6,import_count:5,inventory_sha256:"b".repeat(64),
   items:[{absolute_path:"C:\\Private\\secret"}]};
 const safe=api.parseReport(JSON.stringify({...VALID,import_snapshot:snap}));
 assert.equal(safe.status,"NEEDS_REVIEW");
 assert.equal(safe.import_snapshot.import_count,5);
 assert.equal(safe.import_snapshot.can_import,false);
 assert.equal(JSON.stringify(safe).includes("Private"),false);
 const changed=api.parseReport(JSON.stringify({
   ...VALID,import_snapshot:{...snap,can_import:true}
 }));
 assert.equal(changed.code,"VALIDATOR_RESPONSE_INVALID");
});

test("read-only 4-track candidate parser drops paths and refuses fabricated READY",()=>{
 const counts={V1:2,V2:2,V3:1,A1:1};
 const track={status:"CANDIDATE_NOT_EXECUTABLE",can_assemble:false,
   total_frames:330,track_counts:counts,
   operation_sha256:"a".repeat(64),private_path:"C:\\Users\\secret"};
 const parsed=api.parseReport(JSON.stringify({...VALID,track_candidate:track}));
 assert.equal(parsed.status,"NEEDS_REVIEW");
 assert.equal(parsed.track_candidate.counts.V1,2);
 assert.equal(parsed.track_candidate.can_assemble,false);
 assert.equal(JSON.stringify(parsed).includes("secret"),false);
 for(const changed of [
   {...track,can_assemble:true},
   {...track,status:"READY"},
   {...track,track_counts:{...counts,V1:-1}},
   {...track,operation_sha256:"malformed"},
 ]) {
   assert.equal(api.parseReport(JSON.stringify({...VALID,track_candidate:changed})).code,
     "VALIDATOR_RESPONSE_INVALID");
 }
});

test("BOTH phases display is only sanitized reference, never render or host write",()=>{
 const fx={status:"REFERENCE_SCHEDULE_ONLY",can_render:false,can_assemble:false,
   instance_count:3,zero_hold_count:1,operation_sha256:"a".repeat(64),
   private_asset_path:"C:\\Users\\Personal\\secret.png"};
 const good=api.parseReport(JSON.stringify({...VALID,animation_phases:fx}));
 assert.equal(good.status,"NEEDS_REVIEW");
 assert.equal(good.animation_phases.instance_count,3);
 assert.equal(good.animation_phases.can_render,false);
 assert.equal(JSON.stringify(good).includes("Personal"),false);
 for(const bad of [
   {...fx,can_render:true}, {...fx,can_assemble:true},
   {...fx,status:"READY"}, {...fx,zero_hold_count:999}
 ]){
   const result=api.parseReport(JSON.stringify({...VALID,animation_phases:bad}));
   assert.equal(result.code,"VALIDATOR_RESPONSE_INVALID");
 }
});
