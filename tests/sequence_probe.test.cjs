const test=require("node:test");
const assert=require("node:assert/strict");
const vm=require("node:vm");
const fs=require("node:fs");
const path=require("node:path");
const api=require("../panel/sequence_probe.js");

test("read-only sequence response retains large tick strings intact",()=>{
 const r=api.parse("S5|1|OBSERVED|24.5|254016000000|3|2|1920|1080");
 assert.equal(r.status,"observed_unverified");
 assert.equal(r.ticksPerFrame,"254016000000");
 assert.equal(r.videoTracks,3);
 assert.equal(r.audioTracks,2);
 assert.equal(r.canAssemble,false);
});
test("malicious and impossible host probes cannot authorize actions",()=>{
 for(const s of ["S5|1|CREATED_EMPTY|A", "S5|1|OBSERVED|25.5|12|3|1|1920|1080",
   "S5|1|OBSERVED|24.5|0|3|1|1920|1080",
   "S5|1|OBSERVED|24.5|123|999|1|1920|1080",
   "S5|1|OBSERVED|24.5|123|3|1|0|1080",
   "S5|1|OBSERVED|24.5|123|3|1|1920|20000",
   "S5|1|OBSERVED|24.5|123|3|1|1920|1080|inject",
   "S5|1|OBSERVED|24.5|123456789012345678901234567890|3|1|1920|1080",
   null,{}, "x".repeat(300)
 ]){
  const value=api.parse(s);
  assert.equal(value.status,"error");
  assert.equal(value.canAssemble,false);
 }
});
test("no active sequence remains unverified, never READY",()=>{
 const r=api.parse("S5|1|NO_ACTIVE_SEQUENCE|24.3");
 assert.equal(r.status,"no_active_sequence");
 assert.equal(r.canAssemble,false);
});
test("probe only evaluates fixed read-only ExtendScript expression",()=>{
 let callback,submitted;
 const adapter=api.createBridge((script,cb)=>{submitted=script;callback=cb;},
  ()=>1,()=>{});
 let result;
 assert.equal(adapter.probe(r=>{result=r;}),true);
 assert.equal(submitted,"$._AIJSON_SEQUENCE_V1.inspect()");
 callback("S5|1|OBSERVED|24.5|8467200000|3|1|1920|1080");
 assert.equal(result.ticksPerFrame,"8467200000");
 assert.equal(adapter.isBusy(),false);
});
test("cancel suppresses delayed probes, and timeout fails closed",()=>{
 let cb,timer,ticks=0;
 const adapter=api.createBridge((_,call)=>{cb=call;},
   fn=>{timer=fn;return ++ticks;},()=>{});
 let count=0;
 adapter.probe(()=>{count++;});adapter.cancel();
 cb("S5|1|OBSERVED|24.5|8467200000|3|1|1920|1080");
 assert.equal(count,0);
 let result;
 adapter.probe(r=>{result=r;});
 timer();
 assert.equal(result.code,"S5_PROBE_TIMEOUT");
 assert.equal(result.canAssemble,false);
});
test("both CEP global and CommonJS receive the diagnostic parser",()=>{
 const content=fs.readFileSync(path.join(__dirname,"..","panel","sequence_probe.js"),"utf8");
 const ctx={document:{},module:{exports:{}}};
 vm.runInNewContext(content,ctx,{timeout:1000});
 assert.equal(typeof ctx.AIJSONSequenceProbe.createBridge,"function");
 assert.equal(typeof ctx.module.exports.parse,"function");
});
