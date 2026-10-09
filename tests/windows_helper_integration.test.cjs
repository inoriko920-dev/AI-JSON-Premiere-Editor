const test=require("node:test");
const assert=require("node:assert/strict");
const path=require("node:path");
const fs=require("node:fs");
const childProcess=require("node:child_process");
const helper=require("../panel/helper_bridge.js");

test("Windows runner actually runs the P0 helper using a safe subprocess",{
    skip:process.platform!=="win32"
},async()=>{
    const pythonRoot=process.env.pythonLocation;
    assert.ok(pythonRoot,"Windows CI requires setup-python and pythonLocation");
    const pythonExe=path.win32.join(pythonRoot,"python.exe");
    assert.ok(fs.statSync(pythonExe).isFile());
    const extensionUri="file:///"+process.cwd().replace(/\\/g,"/");
    const bridge=helper.createProbe({
        fs,path,execFile:childProcess.execFile,platform:"win32",
        pythonExe,extensionPath:extensionUri
    });
    const response=await new Promise((resolve,reject)=>{
        const started=bridge.probe(result=>resolve(result));
        if(!started)reject(new Error("P0 helper launch blocked by configuration"));
    });
    assert.equal(response.code,"HELPER_P0_OK");
    assert.equal(response.status,"supported");
    assert.equal(response.version,"0.0.3");
    assert.match(response.pythonVersion,/^3\.\d+\.\d+$/);
    assert.equal(bridge.isBusy(),false);
});
