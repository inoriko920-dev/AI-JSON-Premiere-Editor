const test=require("node:test");
const assert=require("node:assert/strict");
const vm=require("node:vm");
const fs=require("node:fs");
const path=require("node:path");
const script=fs.readFileSync(path.join(__dirname,"..","host","step03.jsx"),"utf8");
function probe(app) {
    const ctx={ $:{} };
    if(app!==undefined){ctx.app=app;}
    vm.runInNewContext(script,ctx,{timeout:1000});
    return ctx.$._AIJSON_P0.probe();
}
test("ExtendScript P0 probe produces strict host response",()=>{
    assert.equal(probe({version:"24.6.3"}),"P0|1|OK|24.6.3");
    assert.equal(probe({version:"25.0"}),"P0|1|OK|25.0");
    assert.equal(probe({version:"23.4"}),"P0|1|OK|23.4");
});
test("ExtendScript missing or malformed app version blocks response",()=>{
    assert.equal(probe(undefined),"P0|1|ERROR|NO_APP");
    assert.equal(probe({version:"24.1\nSCRIPT"}),"P0|1|ERROR|HOST_VERSION_UNKNOWN");
    assert.equal(probe({version:"24"}),"P0|1|ERROR|HOST_VERSION_UNKNOWN");
    assert.equal(probe({version:""}),"P0|1|ERROR|HOST_VERSION_UNKNOWN");
    const getter={get version(){throw new Error("test");}};
    assert.equal(probe(getter),"P0|1|ERROR|HOST_PROBE_EXCEPTION");
});
test("host JSX is read-only",()=>{
    assert.doesNotMatch(script,/createSequence|importFiles|app\.project\.\s*(delete|remove)|eval\s*\(/);
});
