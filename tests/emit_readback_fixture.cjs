/* Cross-language QA fixture only: run the actual ES3 observer on a fake Premiere
 * object and emit its JSON. Do not execute scripts on a real Adobe host. */
const fs=require("node:fs"),path=require("node:path"),vm=require("node:vm");
const source=fs.readFileSync(path.join(__dirname,"..","host","readback_observer.jsx"),"utf8");
const SEQ="aaaa1111-bbbb-2222-cccc-333333333333",TB=8467200000;
const cols={V1:[],V2:[],V3:[],A1:[]};
for(const list of Object.values(cols)){
 Object.defineProperty(list,"numItems",{get(){return this.length;}});
}
const spans=[
 ["BG_0","V1","node-background",0,180],
 ["V001/A001","V2","node-001",0,150],
 ["NARRATION_0","A1","node-audio",0,330],
 ["V002/A002","V2","node-002",150,330],
 ["BG_1","V1","node-background",180,330],
 ["V002/A003","V3","node-003",192,330]
];
for(let i=0;i<spans.length;i++){
 const [key,track,item,start,end]=spans[i];
 cols[track].push({nodeId:"clip-"+(i+1),projectItem:{nodeId:item},
   start:{ticks:String(start*TB)},end:{ticks:String(end*TB)},
   inPoint:{ticks:"0"},outPoint:{ticks:String((end-start)*TB)}});
}
const v=[cols.V1,cols.V2,cols.V3],a=[cols.A1];
v.numTracks=3;a.numTracks=1;
const seqs=[{sequenceID:SEQ,timebase:String(TB),videoTracks:v,audioTracks:a}];
seqs.numSequences=1;
const ctx={$:{},app:{version:"24.4",project:{sequences:seqs}}};
vm.runInNewContext(source,ctx,{timeout:1500});
const result=ctx.$._AIJSON_READBACK_V1.capture(SEQ);
if(!result.startsWith('{"schema_version":'))throw Error("Unexpected observer error: "+result);
process.stdout.write(result);
