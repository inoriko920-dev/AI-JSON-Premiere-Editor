const test = require("node:test");
const assert = require("node:assert/strict");
const {createBridge,parseProbe,PROBE_CALL}=require("../panel/bridge.js");

test("24.x is accepted, others rejected",()=>{
 assert.deepEqual(parseProbe("P0|1|OK|24.6.3"),{status:"supported",version:"24.6.3",code:"HOST_24"});
 assert.deepEqual(parseProbe("P0|1|OK|25.0"),{status:"unsupported",version:"25.0",code:"E_HOST_UNSUPPORTED"});
 assert.deepEqual(parseProbe("P0|1|OK|23.5"),{status:"unsupported",version:"23.5",code:"E_HOST_UNSUPPORTED"});
});
test("invalid, forged and unexpected results fail closed",()=>{
 for(const v of ["EvalScript error.","P0|1|OK|24x","P0|1|OK|24.1|extra","","P0|1|OK|0","P0|1|OK|24.1\nSCRIPT",null]) {
  assert.equal(parseProbe(v).status,"error");
 }
});
test("fixed JSX probe call has no user supplied content",()=>{
 let call;
 let got;
 const b=createBridge((x,cb)=>{call=x; cb("P0|1|OK|24.0");}, ()=>100,()=>{});
 b.probe(x=>{got=x;});
 assert.equal(call,PROBE_CALL);
 assert.equal(got.status,"supported");
});
test("missing CEP bridge is blocked",()=>{
 const b=createBridge(null);
 let res;
 assert.equal(b.probe(v=>{res=v;}),false);
 assert.equal(res.code,"CEP_NOT_AVAILABLE");
});
test("old callback cannot complete a second request",()=>{
 let callbacks=[],results=[];
 const b=createBridge((x,cb)=>callbacks.push(cb),()=>1,()=>{});
 assert.equal(b.probe(v=>results.push(v)),true);
 assert.equal(b.probe(v=>results.push(v)),false);
 b.cancel();
 assert.equal(b.probe(v=>results.push(v)),true);
 callbacks[0]("P0|1|OK|24.0");
 callbacks[1]("P0|1|OK|25.0");
 assert.equal(results.length,1);
 assert.equal(results[0].status,"unsupported");
});
test("timeout blocks host and ignores delayed result",()=>{
 let pending,cb,res=[];
 const b=createBridge((x,f)=>{cb=f;},fn=>{pending=fn; return 1;},()=>{},10);
 b.probe(v=>res.push(v));
 pending();
 cb("P0|1|OK|24.0");
 assert.deepEqual(res,[{status:"error",code:"HOST_TIMEOUT"}]);
});
test("CEP exception becomes actionable error",()=>{
 const b=createBridge(()=>{throw new Error("boom");},()=>1,()=>{});
 let got;
 b.probe(r=>got=r);
 assert.equal(got.code,"CEP_EVAL_FAILURE");
});
