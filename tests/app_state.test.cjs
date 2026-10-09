const test=require("node:test");
const assert=require("node:assert/strict");
const vm=require("node:vm");
const fs=require("node:fs");
const path=require("node:path");
const bridge=fs.readFileSync(path.join(__dirname,"..","panel","bridge.js"),"utf8");
const helper=fs.readFileSync(path.join(__dirname,"..","panel","helper_bridge.js"),"utf8");
const app=fs.readFileSync(path.join(__dirname,"..","panel","app.js"),"utf8");
function boot(nativeResponse, extra={}) {
    const elements=new Map();
    for(const id of ["btn-host","host-status","host-detail","log-entry",
                     "btn-preflight","btn-assemble","btn-helper",
                     "helper-status","helper-detail","btn-report","p0-report"]){
        elements.set(id,{id,disabled:id==="btn-helper"||id==="btn-preflight"||id==="btn-assemble",
            textContent:"",value:"",className:"status",events:{},
            addEventListener(event,cb){this.events[event]=cb;}});
    }
    let evalCalls=[];
    const lifecycle={};
    const doc={readyState:"complete",getElementById:id=>elements.get(id)};
    const context={document:doc,setTimeout:()=>1,clearTimeout:()=>{},console,module:{exports:{}},
        addEventListener(event,cb){lifecycle[event]=cb;}};
    if(nativeResponse!==null){
        context.__adobe_cep__={evalScript:(src,cb)=>{evalCalls.push(src);cb(nativeResponse);},
                                  getSystemPath:()=>"file:///C:/User/AIJSON"};
    }
    Object.assign(context,extra);
    vm.runInNewContext(bridge,context,{timeout:1000});
    vm.runInNewContext(helper,context,{timeout:1000});
    vm.runInNewContext(app,context,{timeout:1000});
    return {el:id=>elements.get(id),evalCalls,
            clickHost(){elements.get("btn-host").events.click();},
            clickHelper(){elements.get("btn-helper").events.click();},
            clickReport(){elements.get("btn-report").events.click();},
            unload(){if(lifecycle.unload) lifecycle.unload();},
            pagehide(){if(lifecycle.pagehide) lifecycle.pagehide();}};
}
test("Browser fallback never enables helper/assembly without CEP",()=>{
 const p=boot(null);
 assert.match(p.el("host-status").textContent,/CEP BELUM/);
 assert.equal(p.el("btn-helper").disabled,true);
 assert.equal(p.el("btn-assemble").disabled,true);
 assert.equal(p.el("btn-preflight").disabled,true);
 p.clickHost();p.clickHelper();
 assert.equal(p.evalCalls.length,0);
});
test("24.x probe shows version but assembly remains blocked",()=>{
 const p=boot("P0|1|OK|24.4.2");
 p.clickHost();
 assert.match(p.el("host-status").textContent,/24\.4\.2/);
 assert.equal(p.el("btn-host").disabled,false);
 assert.equal(p.el("btn-helper").disabled,false);
 assert.equal(p.el("btn-assemble").disabled,true);
 assert.equal(p.el("btn-preflight").disabled,true);
 assert.deepEqual(p.evalCalls,["$._AIJSON_P0.probe()"]);
});
test("Unsupported host rejects helper and assembly",()=>{
 const p=boot("P0|1|OK|25.2");
 p.clickHost();p.clickHelper();
 assert.match(p.el("host-status").textContent,/TIDAK DIDUKUNG/);
 assert.equal(p.el("btn-helper").disabled,true);
 assert.equal(p.el("btn-assemble").disabled,true);
});
test("CEP host supported but Node absent shows helper blocker",()=>{
 const p=boot("P0|1|OK|24.2");
 p.clickHost();p.clickHelper();
 assert.match(p.el("helper-detail").textContent,/HELPER_NODE_UNAVAILABLE/);
 assert.equal(p.el("btn-assemble").disabled,true);
});
test("CEP mixed context publishes bridge browser global",()=>{
 const p=boot("P0|1|OK|24.0");
 p.clickHost();
 assert.match(p.el("host-status").textContent,/24\.0/);
});

test("panel unload cancels pending host response and blocks late callback",()=>{
 let onHost;
 const cep={
  evalScript:(_src,cb)=>{onHost=cb;},
  getSystemPath:()=>"file:///C:/User/AIJSON"
 };
 const p=boot(null,{__adobe_cep__:cep});
 p.clickHost();
 assert.equal(typeof onHost,"function");
 p.unload();
 onHost("P0|1|OK|24.3");
 assert.equal(p.el("btn-host").disabled,true);
 assert.equal(p.el("btn-helper").disabled,true);
 assert.equal(p.el("btn-assemble").disabled,true);
 p.clickHost();
 assert.equal(p.evalCalls.length,0);
});
test("panel pagehide kills running Python helper; stale result does not update UI",()=>{
 const nodePath=require("node:path");
 let complete,killCount=0,spawnCount=0;
 const cepNode={
  process:{platform:"win32",env:{AIJSON_P0_PYTHON_EXE:"C:\\Python311\\python.exe"}},
  require(name){
    if(name==="path")return nodePath;
    if(name==="fs")return {realpathSync:p=>p,statSync:()=>({isFile:()=>true})};
    if(name==="child_process")return {execFile:(_exe,_args,_opts,cb)=>{
      spawnCount++;
      complete=cb;
      return {kill(){killCount++;}};
    }};
    throw new Error("unexpected node module");
  }
 };
 const p=boot("P0|1|OK|24.2",{cep_node:cepNode});
 p.clickHost();
 assert.equal(p.el("btn-helper").disabled,false);
 p.clickHelper();
 assert.equal(spawnCount,1);
 assert.equal(p.el("helper-status").textContent,"Memeriksa helper…");
 p.pagehide();
 p.unload();
 assert.equal(killCount,1,"teardown must be idempotent");
 const valid=JSON.stringify({protocol:"AIJSON_STEP03_P0",status:"OK",
   helper_version:"0.0.3",python_version:"3.11.9",
   capabilities:{schema_validation:false,media_probe:false,
     ffmpeg_prerender:false,premiere_mutation:false}});
 complete(null,valid);
 assert.equal(p.el("btn-helper").disabled,true);
 assert.equal(p.el("btn-assemble").disabled,true);
 assert.notEqual(p.el("helper-status").textContent,"HELPER P0 • HANDSHAKE OK");
 p.clickHelper();
 assert.equal(spawnCount,1);
});

test("P0 report shows sanitized host version without personal paths or G3 PASS",()=>{
 const p=boot("P0|1|OK|24.3");
 p.clickHost();p.clickReport();
 const r=p.el("p0-report").value;
 assert.match(r,/AI_JSON_PREMIERE_P0_DIAGNOSTIK_V1/);
 assert.match(r,/HOST_STATUS=SUPPORTED/);
 assert.match(r,/HOST_CODE=HOST_24/);
 assert.match(r,/HOST_VERSION=24.3/);
 assert.match(r,/HELPER_STATUS=NOT_CHECKED/);
 assert.match(r,/G3=BLOCKED_HOST/);
 assert.doesNotMatch(r,/C:\\|\/Users\/|python\.exe|AIJSON_P0_PYTHON_EXE/);
 assert.equal(p.el("btn-assemble").disabled,true);
});
test("P0 report preserves unsupported host and browser fallback",()=>{
 const p=boot("P0|1|OK|25.2");
 p.clickHost();p.clickReport();
 assert.match(p.el("p0-report").value,/HOST_STATUS=UNSUPPORTED/);
 assert.match(p.el("p0-report").value,/HOST_CODE=E_HOST_UNSUPPORTED/);
 const browser=boot(null);
 browser.clickReport();
 assert.match(browser.el("p0-report").value,/HOST_CODE=CEP_NOT_AVAILABLE/);
 assert.match(browser.el("p0-report").value,/HOST_STATUS=ERROR/);
});
test("Diagnostic report button is disabled when panel is unloaded",()=>{
 const p=boot("P0|1|OK|24.4");
 p.clickHost();p.clickReport();
 const before=p.el("p0-report").value;
 p.unload();
 assert.equal(p.el("btn-report").disabled,true);
 p.clickReport();
 assert.equal(p.el("p0-report").value,before);
});
