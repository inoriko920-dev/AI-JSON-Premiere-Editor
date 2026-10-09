const test=require("node:test");
const assert=require("node:assert/strict");
const vm=require("node:vm");
const path=require("node:path");
const fs=require("node:fs");
const helper=require("../panel/helper_bridge.js");
const response=JSON.stringify({
 protocol:"AIJSON_STEP03_P0",status:"OK",helper_version:"0.0.3",
 python_version:"3.11.9",
 capabilities:{schema_validation:false,media_probe:false,
               ffmpeg_prerender:false,premiere_mutation:false}
})+"\n";
function make(overrides={}) {
 const calls=[];
 const fsMock={realpathSync:p=>p,statSync:()=>({isFile:()=>true})};
 const out={calls};
 const deps={
  platform:"win32",fs:fsMock,path:path,
  extensionPath:"file:///C:/Users/Pengguna%20Uji/Adobe/CEP",
  pythonExe:"C:\\Python311\\python.exe",
  execFile:(executable,args,options,done)=>{
   calls.push({executable,args,options});
   out.complete=(error,data)=>done(error,data);
   return {kill(){out.killed=true;}};
  },...overrides};
 out.bridge=helper.createProbe(deps);
 return out;
}
test("strict response parser permits no operational capabilities",()=>{
 assert.equal(helper.parseResponse(response).status,"supported");
 for(const modified of [
   '{"protocol":"AIJSON_STEP03_P0","status":"OK"}',
   response.replace('"premiere_mutation":false','"premiere_mutation":true'),
   response.replace('"schema_validation":false','"schema_validation":"false"'),
   response.replace('"helper_version":"0.0.3"','"helper_version":"9.0"'),
   response.replace('"python_version":"3.11.9"','"python_version":"invalid"'),
   response.replace('"ffmpeg_prerender":false','"ffmpeg_prerender":false,"admin":false'),
   "NOT_JSON",null,"A".repeat(9000)]) {
  assert.equal(helper.parseResponse(modified).status,"error");
 }
});
test("fixed Python invocation uses no shell and no user JSON",()=>{
 const o=make();let result=null;
 assert.equal(o.bridge.probe(x=>result=x),true);
 assert.equal(o.calls.length,1);
 assert.equal(o.calls[0].executable,"C:\\Python311\\python.exe");
 assert.deepEqual(o.calls[0].args,[
   "-I","-B","C:\\Users\\Pengguna Uji\\Adobe\\CEP\\helper\\handshake.py","--probe"]);
 assert.equal(o.calls[0].options.shell,false);
 assert.equal(o.calls[0].options.windowsHide,true);
 assert.equal(o.calls[0].options.maxBuffer,8192);
 assert.equal(o.calls[0].options.timeout,5000);
 o.complete(null,response);
 assert.equal(result.status,"supported");
 assert.equal(o.bridge.isBusy(),false);
});
test("encoded Windows extension path preserves Unicode, spaces and hash characters",()=>{
 const url="file:///C:/Users/Jos%C3%A9%20A/%23Panel%20CEP";
 assert.equal(helper.decodeExtensionPath(url,path),"C:\\\\Users\\\\José A\\\\#Panel CEP");
});
test("helper refuses missing or malformed configuration without spawn",()=>{
 for(const [overrides,code] of [
  [{pythonExe:null},"HELPER_PYTHON_NOT_CONFIGURED"],
  [{pythonExe:"python.exe"},"HELPER_PATH_INVALID"],
  [{pythonExe:"C:\\Tools\\cmd.exe"},"HELPER_PATH_INVALID"],
  [{platform:"linux"},"HELPER_WINDOWS_ONLY"],
  [{extensionPath:"file://evil.example/share"},"HELPER_PATH_INVALID"],
  [{extensionPath:"C:\\..\\foo",fs:{realpathSync(){throw new Error("missing");}}},"HELPER_FILES_MISSING"]
 ]) {
  const o=make(overrides);let result;
  assert.equal(o.bridge.probe(x=>result=x),false);
  assert.equal(result.code,code);
  assert.equal(o.calls.length,0);
 }
});
test("symlink escape cannot launch an external script",()=>{
 const o=make({fs:{
  realpathSync:p=>p.endsWith("handshake.py")?"C:\\Outside\\handshake.py":p,
  statSync:()=>({isFile:()=>true})}});
 let got;
 assert.equal(o.bridge.probe(x=>got=x),false);
 assert.equal(got.code,"HELPER_PATH_INVALID");
 assert.equal(o.calls.length,0);
});
test("concurrent and cancelled subprocess callbacks are blocked",()=>{
 const o=make();let results=[];
 assert.equal(o.bridge.probe(x=>results.push(x)),true);
 assert.equal(o.bridge.probe(x=>results.push(x)),false);
 const old=o.complete;
 o.bridge.cancel();
 assert.equal(o.killed,true);
 assert.equal(o.bridge.probe(x=>results.push(x)),true);
 old(null,response);
 assert.equal(results.length,0);
 o.complete(null,response);
 assert.equal(results.length,1);
});
test("subprocess errors, timeouts and bad response stay blocked",()=>{
 let o=make();let got;
 o.bridge.probe(x=>got=x);
 o.complete(new Error("ENOENT"),"");
 assert.equal(got.code,"HELPER_EXEC_FAILED");
 o=make();o.bridge.probe(x=>got=x);
 o.complete({killed:true},"");
 assert.equal(got.code,"HELPER_TIMEOUT");
 o=make();o.bridge.probe(x=>got=x);
 o.complete(null,'{"wrong":true}');
 assert.equal(got.code,"HELPER_BAD_RESPONSE");
});
test("helper bridge exports browser global even in CEP mixed Node context",()=>{
 const source=fs.readFileSync(path.join(__dirname,"..","panel","helper_bridge.js"),"utf8");
 const ctx={document:{},module:{exports:{}}};
 vm.runInNewContext(source,ctx,{timeout:1000});
 assert.equal(typeof ctx.AIJSONP0Helper.createProbe,"function");
 assert.equal(typeof ctx.module.exports.createProbe,"function");
});
