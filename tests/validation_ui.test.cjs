const test=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const vm=require("node:vm");
const path=require("node:path");
const helperSource=fs.readFileSync(path.join(__dirname,"..","panel","helper_bridge.js"),"utf8");
const bridgeSource=fs.readFileSync(path.join(__dirname,"..","panel","validation_bridge.js"),"utf8");
const uiSource=fs.readFileSync(path.join(__dirname,"..","panel","validation_ui.js"),"utf8");

function boot(opts={}){
 const e=new Map(),lifecycle={},pending={},nativeCalls=[];
 const elementIds=["choose-edit","choose-animation","choose-media",
   "selected-edit","selected-animation","selected-media","btn-validate-offline",
   "validation-summary","btn-assemble","btn-preflight"];
 for(const id of elementIds){
   e.set(id,{id,disabled:true,events:{},textContent:"",
     className:"detail",addEventListener(name,cb){this.events[name]=cb;}});
 }
 const selection={edit:"C:\\Job\\EDIT_PLAN.json",
   animation:"C:\\Job\\ANIMATION_PLAN.json",media:"C:\\Job\\MEDIA"};
 const fakeFS={
   realpathSync:x=>x,
   statSync:x=>({isFile:()=>x!=="C:\\Job\\MEDIA",
     isDirectory:()=>x==="C:\\Job\\MEDIA"})
 };
 const cepfs={
   showOpenDialogEx:(multi,folder,title,start,types)=>{
     nativeCalls.push({multi,folder,title,start,types});
     if(opts.cancel&&title===opts.cancel){return {err:0,data:[]};}
     const result=folder?selection.media:title.includes("EDIT_PLAN")?
       selection.edit:selection.animation;
     return {err:0,data:[result]};
   }
 };
 const node={
  process:{platform:"win32",env:{AIJSON_P0_PYTHON_EXE:"C:\\Python311\\python.exe"}},
  require(name){
   if(name==="path")return path;
   if(name==="fs")return fakeFS;
   if(name==="child_process")return {
    execFile:(_exe,_argv,_options,callback)=>{
      pending.callback=callback;
      pending.count=(pending.count||0)+1;
      return {kill(){pending.killed=(pending.killed||0)+1;}};
    }};
   throw Error("unexpected dependency");
  }
 };
 const ctx={document:{readyState:"complete",getElementById:id=>e.get(id)},
   module:{exports:{}},
   __adobe_cep__:{getSystemPath:()=>"file:///C:/CEP/Panel"},
   cep:{fs:cepfs},cep_node:node,
   addEventListener:(name,fn)=>{lifecycle[name]=fn;}};
 vm.runInNewContext(helperSource,ctx,{timeout:1000});
 vm.runInNewContext(bridgeSource,ctx,{timeout:1000});
 vm.runInNewContext(uiSource,ctx,{timeout:1000});
 return {el:id=>e.get(id),nativeCalls,pending,
   click:id=>e.get(id).events.click(),
   unload:()=>{if(lifecycle.unload)lifecycle.unload();},
   pagehide:()=>{if(lifecycle.pagehide)lifecycle.pagehide();}};
}
test("panel enables file pickers and requires all three real selections",()=>{
 const p=boot();
 assert.equal(p.el("choose-edit").disabled,false);
 assert.equal(p.el("btn-validate-offline").disabled,true);
 p.click("choose-edit");
 p.click("choose-animation");
 assert.equal(p.el("btn-validate-offline").disabled,true);
 p.click("choose-media");
 assert.equal(p.el("btn-validate-offline").disabled,false);
 assert.equal(p.el("selected-media").textContent,"Folder terpilih");
 assert.equal(p.el("btn-assemble").disabled,true);
 assert.equal(p.el("btn-preflight").disabled,true);
});
test("validation invokes only read-only backend and sanitized status",()=>{
 const p=boot();
 for(const k of ["choose-edit","choose-animation","choose-media"]){p.click(k);}
 p.click("btn-validate-offline");
 assert.equal(p.pending.count,1);
 assert.equal(p.el("btn-validate-offline").disabled,true);
 p.pending.callback({code:3},JSON.stringify({
   schema_version:"structure-validation-report-v1",status:"NEEDS_REVIEW",
   can_assemble:false,error_count:0,review_count:1,
   issues:[{code:"E_HOST_UNVERIFIED",severity:"REVIEW",
      pointer:"/secret",message:"C:\\Users\\secret\\username"}]
 }));
 assert.match(p.el("validation-summary").textContent,/NEEDS_REVIEW/);
 assert.match(p.el("validation-summary").textContent,/E_HOST_UNVERIFIED/);
 assert.doesNotMatch(p.el("validation-summary").textContent,/C:\\Users/);
 assert.equal(p.el("btn-assemble").disabled,true);
});
test("file selection while validator busy invalidates previous callback",()=>{
 const p=boot();
 for(const k of ["choose-edit","choose-animation","choose-media"]){p.click(k);}
 p.click("btn-validate-offline");
 const old=p.pending.callback;
 p.click("choose-edit");
 assert.equal(p.pending.killed,1);
 old({code:3},JSON.stringify({
   schema_version:"structure-validation-report-v1",status:"NEEDS_REVIEW",
   can_assemble:false,error_count:0,review_count:0,issues:[]
 }));
 assert.match(p.el("validation-summary").textContent,/hasil pemeriksaan lama dibatalkan/);
 assert.equal(p.el("btn-validate-offline").disabled,false);
});
test("panel unload aborts Python and disables selectors forever",()=>{
 const p=boot();
 for(const k of ["choose-edit","choose-animation","choose-media"]){p.click(k);}
 p.click("btn-validate-offline");
 p.pagehide();p.unload();
 assert.equal(p.pending.killed,1);
 assert.equal(p.el("choose-edit").disabled,true);
 assert.equal(p.el("btn-validate-offline").disabled,true);
 p.click("choose-edit");
 assert.equal(p.nativeCalls.length,3);
});
test("CEP/Node absent never enables pickers or validation",()=>{
 const e=new Map();
 for(const id of ["choose-edit","choose-animation","choose-media",
   "selected-edit","selected-animation","selected-media",
   "btn-validate-offline","validation-summary"]){
   e.set(id,{disabled:true,textContent:"",events:{},
     addEventListener(event,callback){this.events[event]=callback;}});
 }
 const ctx={document:{readyState:"complete",getElementById:id=>e.get(id)},
   module:{exports:{}},addEventListener(){}};
 vm.runInNewContext(helperSource,ctx,{timeout:1000});
 vm.runInNewContext(bridgeSource,ctx,{timeout:1000});
 vm.runInNewContext(uiSource,ctx,{timeout:1000});
 assert.equal(e.get("btn-validate-offline").disabled,true);
 assert.match(e.get("validation-summary").textContent,/CEP\/Node tidak tersedia/);
});
