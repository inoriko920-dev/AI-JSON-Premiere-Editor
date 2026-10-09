const test=require("node:test");
const assert=require("node:assert/strict");
const vm=require("node:vm");
const fs=require("node:fs");
const path=require("node:path");
const bridge=fs.readFileSync(path.join(__dirname,"..","panel","bridge.js"),"utf8");
const app=fs.readFileSync(path.join(__dirname,"..","panel","app.js"),"utf8");
function boot(nativeResponse){
    const elements=new Map();
    for(const id of ["btn-host","host-status","host-detail","log-entry","btn-preflight","btn-assemble"]){
        elements.set(id,{id,disabled:id!=="btn-host",textContent:"",className:"status",events:{},
          addEventListener(event,cb){this.events[event]=cb;}});
    }
    let evalCalls=[];
    const doc={readyState:"complete",getElementById:id=>elements.get(id)};
    const context={document:doc,setTimeout:()=>1,clearTimeout:()=>{},console};
    if(nativeResponse!==null){
        context.__adobe_cep__={evalScript:(src,cb)=>{evalCalls.push(src);cb(nativeResponse);}};
    }
    vm.runInNewContext(bridge,context,{timeout:1000});
    vm.runInNewContext(app,context,{timeout:1000});
    return {el:id=>elements.get(id),evalCalls,click(){elements.get("btn-host").events.click();}};
}
test("Browser fallback never enables assembly without CEP",()=>{
    const p=boot(null);
    assert.match(p.el("host-status").textContent,/CEP BELUM/);
    assert.equal(p.el("btn-assemble").disabled,true);
    assert.equal(p.el("btn-preflight").disabled,true);
    p.click();
    assert.equal(p.evalCalls.length,0);
});
test("24.x probe shows version but still cannot assemble",()=>{
    const p=boot("P0|1|OK|24.4.2");
    p.click();
    assert.match(p.el("host-status").textContent,/24\.4\.2/);
    assert.equal(p.el("btn-host").disabled,false);
    assert.equal(p.el("btn-assemble").disabled,true);
    assert.equal(p.el("btn-preflight").disabled,true);
    assert.deepEqual(p.evalCalls,["$._AIJSON_P0.probe()"]);
});
test("Unsupported host remains blocked",()=>{
    const p=boot("P0|1|OK|25.2");
    p.click();
    assert.match(p.el("host-status").textContent,/TIDAK DIDUKUNG/);
    assert.equal(p.el("btn-assemble").disabled,true);
});
