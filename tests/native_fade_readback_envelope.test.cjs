/* STEP24 ES3 readback envelope mock host: exact selectors and no writes. */
const test=require("node:test");
const assert=require("node:assert/strict");
const vm=require("node:vm");
const fs=require("node:fs");
const path=require("node:path");
const root=path.join(__dirname,"..","host");
const step22=fs.readFileSync(path.join(root,"native_opacity_inspector.jsx"),"utf8");
const step24=fs.readFileSync(path.join(root,"native_fade_readback_envelope.jsx"),"utf8");
const id="12345678-abcd-49ef-88ab-123456789abc", name="AIJSON_MANAGED_Test";
const nonce="0123456789abcdef0123456789abcdef", digest="a".repeat(64);
const node="Node1";
function collection(list){const v={numItems:list.length};
    list.forEach((x,i)=>{v[i]=x;}); return v;}
function fixture(){
    let calls=0;
    const param={displayName:"Opacity",
                 setValue(){calls++;throw Error("MUTATION");},
                 getValue(){calls++;throw Error("GETTER");}};
    const clip={start:{ticks:"9000"},end:{ticks:"24000"},
                projectItem:{nodeId:node},
                components:collection([{matchName:"TestOpacity",
                                        properties:collection([param])}]),
                setValue(){calls++;throw Error("MUTATION");}};
    const video={numTracks:3};
    video[0]={clips:collection([])};
    video[1]={clips:collection([clip])};
    video[2]={clips:collection([])};
    const seq={sequenceID:id,name,videoTracks:video};
    const app={version:"24.6.3",project:{activeSequence:seq}};
    return {app,clip,seq,get calls(){return calls;}};
}
function run(h,overrides={},include22=true){
    const ctx={$:{},app:h.app};
    if(include22)vm.runInNewContext(step22,ctx,{timeout:1000});
    vm.runInNewContext(step24,ctx,{timeout:1000});
    const args=[nonce,digest,id,name,"V2","9000","24000",node];
    Object.entries(overrides).forEach(([index,value])=>args[Number(index)]=value);
    return ctx.$._AIJSON_FADE_READBACK_V1.inspect(...args);
}
test("S24 returns nonce and exact selector echo, with encoded S22 inventory",()=>{
    const h=fixture(),result=run(h);
    const parts=result.split("|");
    assert.equal(parts.length,12);
    assert.equal(parts.slice(0,3).join("|"),"S24|1|OBSERVED_UNCERTIFIED");
    assert.deepEqual(parts.slice(3,11),
                     [nonce,digest,id,name,"V2","9000","24000",node]);
    assert.equal(decodeURIComponent(parts[11]),
                 "S22|1|OBSERVED_UNCERTIFIED|24.6.3|1|TestOpacity:Opacity");
    assert.equal(h.calls,0);
    assert.doesNotMatch(step24,/\bsetValue\s*\(|\baddKey\s*\(|\.overwriteClip\s*\(|\.importFiles\s*\(/);
});
test("S24 refuses mismatched sequence name, target node, stale clip end",()=>{
    let h=fixture();h.seq.name="AIJSON_MANAGED_Changed";
    assert.equal(run(h),"S24|1|BLOCKED|SEQUENCE_NAME_MISMATCH");
    h=fixture();h.clip.end.ticks="24001";
    assert.equal(run(h),"S24|1|BLOCKED|CLIP_INSPECTION_FAILED");
    h=fixture();h.clip.projectItem.nodeId="OtherNode";
    assert.equal(run(h),"S24|1|BLOCKED|CLIP_INSPECTION_FAILED");
    h=fixture();h.seq.sequenceID="87654321-abcd-49ef-88ab-123456789abc";
    assert.equal(run(h),"S24|1|BLOCKED|CLIP_INSPECTION_FAILED");
    assert.equal(h.calls,0);
});
test("S24 blocks missing S22 inspector, missing host and incorrect version",()=>{
    let h=fixture();
    assert.equal(run(h,{},false),"S24|1|BLOCKED|INSPECTOR_UNAVAILABLE");
    h=fixture();h.app.version="25.0";
    assert.equal(run(h),"S24|1|BLOCKED|CLIP_INSPECTION_FAILED");
    h=fixture();h.app.project=null;
    assert.equal(run(h),"S24|1|BLOCKED|SEQUENCE_NAME_MISMATCH");
});
test("S24 strict nonce, digest, source and decimal ticks inputs",()=>{
    for(const [index,bad] of [[0,"0"],[0,"g".repeat(32)],[1,"z".repeat(64)],
        [2,"BAD"],[2,id.toUpperCase()],[3,"Personal"],[4,"V1"],
        [5,"0009000"],[5,"-1"],[6,"9000"],[6,"9001"],[6,"024000"],
        [7,"..\\private"],[7,"A|B"],[7,""]]){
        const h=fixture();
        assert.equal(run(h,{[index]:bad}),"S24|1|BLOCKED|SELECTOR_INVALID",
                     String(index)+"/"+String(bad));
        assert.equal(h.calls,0);
    }
});
test("S24 rejects inspector error status, fake certified and exceptions",()=>{
    const h=fixture(),ctx={$:{},app:h.app};
    vm.runInNewContext(step24,ctx,{timeout:1000});
    ctx.$._AIJSON_NATIVE_OPACITY_INSPECT_V1={inspect(){
        return "S22|1|CERTIFIED|24.6.3|1|TestOpacity:Opacity";}};
    assert.equal(ctx.$._AIJSON_FADE_READBACK_V1.inspect(
        nonce,digest,id,name,"V2","9000","24000",node),
        "S24|1|BLOCKED|CLIP_INSPECTION_FAILED");
    ctx.$._AIJSON_NATIVE_OPACITY_INSPECT_V1.inspect=()=>{
        throw Error("host failure");};
    assert.equal(ctx.$._AIJSON_FADE_READBACK_V1.inspect(
        nonce,digest,id,name,"V2","9000","24000",node),
        "S24|1|BLOCKED|INSPECTION_EXCEPTION");
    assert.equal(h.calls,0);
});
