/* STEP22: mocked ExtendScript ES3 read-only component inventory checks.
 * Synthetic host objects test logic only; this does not certify Premiere.
 */
const test=require("node:test");
const assert=require("node:assert/strict");
const vm=require("node:vm");
const fs=require("node:fs");
const path=require("node:path");
const script=fs.readFileSync(path.join(__dirname,"..","host",
                                      "native_opacity_inspector.jsx"),"utf8");
const ID="12345678-abcd-49ef-88ab-123456789abc";
const NODE="12345";
function collection(rows){
    const c={numItems:rows.length};
    rows.forEach((r,i)=>{c[i]=r;});
    return c;
}
function makeHost(){
    let forbidden=0;
    const param={displayName:"Opacity",
                 getValue(){forbidden++;throw Error("NO HOST METHOD");},
                 setValue(){forbidden++;throw Error("NO MUTATION");}};
    const components=collection([
        {matchName:"Mock.Component.Opacity",properties:collection([param])},
        {matchName:"Mock.Component.Motion",properties:collection([
            {displayName:"Motion Scale"}])}
    ]);
    const clip={start:{ticks:"9000"},end:{ticks:"24000"},
                projectItem:{nodeId:NODE},components,
                setValue(){forbidden++;throw Error("NO SET");}};
    const tracks=collection([]);
    tracks.numTracks=3;
    tracks[0]={clips:collection([])};
    tracks[1]={clips:collection([clip])};
    tracks[2]={clips:collection([])};
    const seq={sequenceID:ID,name:"AIJSON_MANAGED_Test",
               videoTracks:tracks};
    const app={version:"24.6.3",project:{activeSequence:seq}};
    return {app,seq,clip,components,param,get forbidden(){return forbidden;}};
}
function run(host,options={}){
    const ctx={$:{},app:host.app};
    vm.runInNewContext(script,ctx,{timeout:1500});
    const args=[
        options.id===undefined?ID:options.id,
        options.track===undefined?"V2":options.track,
        options.start===undefined?"9000":options.start,
        options.node===undefined?NODE:options.node,
        options.end===undefined?"24000":options.end
    ];
    const ret=ctx.$._AIJSON_NATIVE_OPACITY_INSPECT_V1.inspect(...args);
    return ret;
}
test("STEP22 returns untrusted component names only, without any setter or host method",()=>{
    const h=makeHost();
    const result=run(h);
    assert.equal(result,
        "S22|1|OBSERVED_UNCERTIFIED|24.6.3|2|"+
        "Mock.Component.Opacity:Opacity;Mock.Component.Motion:Motion%20Scale");
    assert.equal(h.forbidden,0);
    assert.doesNotMatch(result,/^S22\|1\|CERTIFIED\|/);
    assert.doesNotMatch(script,/\bsetValue\s*\(|\baddKey\s*\(|\.overwriteClip\s*\(|\.importFiles\s*\(|\.setTimeVarying\s*\(/);
});
test("STEP22 refuses unexpected Premiere version and missing project",()=>{
    for(const ver of ["23.5","25.0.0","24","24.1\nINJECTION",null]){
        const h=makeHost();h.app.version=ver;
        assert.equal(run(h),"S22|1|BLOCKED|HOST_VERSION_UNVERIFIED");
    }
    const h=makeHost();h.app.project=null;
    assert.equal(run(h),"S22|1|BLOCKED|NO_HOST_PROJECT");
});
test("STEP22 requires managed sequence and exact active id",()=>{
    let h=makeHost();h.seq.name="Personal Work";
    assert.equal(run(h),"S22|1|BLOCKED|MANAGED_SEQUENCE_MISMATCH");
    h=makeHost();h.seq.sequenceID="87654321-abcd-49ef-88ab-123456789abc";
    assert.equal(run(h),"S22|1|BLOCKED|MANAGED_SEQUENCE_MISMATCH");
    h=makeHost();h.app.project.activeSequence=null;
    assert.equal(run(h),"S22|1|BLOCKED|MANAGED_SEQUENCE_MISMATCH");
});
test("STEP22 validates selectors and denies traversal/unintended tracks",()=>{
    for(const opts of [{track:"V1"},{track:"A1"},{track:"__proto__"},
                       {node:"../../passwd"},{node:""},{id:"bad"},
                       {start:"-1"},{start:"00009000"},{start:9000},
                       {end:"9000"},{end:"8000"},{end:"024000"},{end:24000},
                       {end:"-1"}]){
        const h=makeHost();
        assert.equal(run(h,opts),"S22|1|BLOCKED|SELECTOR_INVALID");
    }
});
test("STEP23 requires clip end tick readback to match exact placement",()=>{
    let h=makeHost();
    assert.equal(run(h,{end:"30000"}),"S22|1|BLOCKED|CLIP_END_MISMATCH");
    assert.equal(h.forbidden,0);
    h=makeHost();h.clip.end.ticks="23999";
    assert.equal(run(h),"S22|1|BLOCKED|CLIP_END_MISMATCH");
    h=makeHost();h.clip.end=null;
    assert.equal(run(h),"S22|1|BLOCKED|CLIP_END_MISMATCH");
    h=makeHost();
    assert.match(run(h),/^S22\|1\|OBSERVED_UNCERTIFIED\|/);
});
test("STEP22 cannot inspect missing or ambiguous clip",()=>{
    let h=makeHost();
    assert.equal(run(h,{node:"Unknown"}),"S22|1|BLOCKED|CLIP_NOT_FOUND");
    h=makeHost();h.seq.videoTracks[1].clips=collection([h.clip,h.clip]);
    assert.equal(run(h),"S22|1|BLOCKED|CLIP_AMBIGUOUS");
    h=makeHost();h.seq.videoTracks[1].clips=collection([null]);
    assert.equal(run(h),"S22|1|BLOCKED|CLIP_READBACK_FAILED");
});
test("STEP22 rejects duplicate or malformed component metadata",()=>{
    let h=makeHost();h.components[1].matchName="Mock.Component.Opacity";
    assert.equal(run(h),"S22|1|BLOCKED|COMPONENT_DUPLICATE_OR_UNSAFE");
    h=makeHost();h.components[0].matchName="X\nLOGS";
    assert.equal(run(h),"S22|1|BLOCKED|COMPONENT_ID_UNVERIFIED");
    h=makeHost();h.components[0].properties[0].displayName="";
    assert.equal(run(h),"S22|1|BLOCKED|PROPERTY_LABEL_UNVERIFIED");
    h=makeHost();h.components.numItems=3000;
    assert.equal(run(h),"S22|1|BLOCKED|COMPONENTS_UNAVAILABLE");
    h=makeHost();h.components[0].properties.numItems=1000;
    assert.equal(run(h),"S22|1|BLOCKED|PROPERTIES_UNAVAILABLE");
});
test("STEP22 never trusts fake host capability or methods",()=>{
    const h=makeHost();
    h.components[0].properties[0].getValue=()=>{throw Error("getter called");};
    assert.match(run(h),/^S22\|1\|OBSERVED_UNCERTIFIED\|/);
    assert.equal(h.forbidden,0);
    assert.doesNotMatch(script,/eval\s*\(|\$\.evalFile|new\s+Time\s*\(/);
});
