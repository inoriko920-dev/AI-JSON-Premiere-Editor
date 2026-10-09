const test=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const os=require("node:os");
const cp=require("node:child_process");
const crypto=require("node:crypto");
const helper=require("../panel/helper_bridge.js");
const api=require("../panel/validation_bridge.js");

test("Windows uses real isolated Python runner and real media to produce NEEDS_REVIEW",{
 skip:process.platform!=="win32"
},async()=>{
 const pythonRoot=process.env.pythonLocation;
 assert.ok(pythonRoot,"Windows runner must provision Python with setup-python");
 const py=path.join(pythonRoot,"python.exe");
 const home=fs.mkdtempSync(path.join(os.tmpdir(),"aijson-offline-"));
 try{
  const media=path.join(home,"media");
  fs.mkdirSync(media);
  const srt=Buffer.from("1\n00:00:00,000 --> 00:00:03,000\nHalo Dunia.\n","utf8");
  const wav=Buffer.concat([Buffer.from("RIFF"),Buffer.alloc(4),
    Buffer.from("WAVEfmt "),Buffer.alloc(16)]);
  const mp4=Buffer.concat([Buffer.from([0,0,0,24]),Buffer.from("ftypisom"),
    Buffer.alloc(20)]);
  const png=Buffer.concat([Buffer.from([137,80,78,71,13,10,26,10]),
    Buffer.from([0,0,0,13]),Buffer.from("IHDR"),Buffer.from([0,0,2,0,0,0,2,0]),
    Buffer.from([8,6,0,0,0])]);
  function write(name,data){
    fs.writeFileSync(path.join(media,name),data);
    return crypto.createHash("sha256").update(data).digest("hex");
  }
  const srtHash=write("narasi.srt",srt), wavHash=write("narasi.wav",wav);
  const mp4Hash=write("background.mp4",mp4), pngHash=write("A001.png",png);
  const profileHash="a".repeat(64);
  const edit={
    schema_version:"edit-plan-v2",project_id:"OFFLINE_TEST",revision:1,
    canvas:{width:1920,height:1080,fps_num:30,fps_den:1},
    sources:{srt:{path:"narasi.srt",sha256:srtHash},
      audio:{path:"narasi.wav",sha256:wavHash},
      background:{path:"background.mp4",sha256:mp4Hash,required:true,audio_policy:"MUTE"}},
    profiles:{layout_id:"OFFLINE_UNVERIFIED",layout_hash:profileHash},
    assets:{A001:{path:"A001.png",sha256:pngHash}},
    scenes:[{scene_id:"V001",source_segment_ids:["N0001"],
      narration_quote:"Halo Dunia.",layout_type:"SINGLE",start_frame:0,
      end_frame:90,transition_policy:"CUT",
      assets:[{asset_id:"A001",slot:"SINGLE",start_frame:0,end_frame:90,
        entry_evidence:{cue_id:1,accuracy:"EXACT_CUE"}}]}],
    render:{codec:"libx264",pixel_format:"yuv420p",audio_codec:"aac",
      audio_policy:"NARRATION_ONLY",subtitles:"NONE",output_path:"DO_NOT_RENDER.mp4"},
    validation:{status:"READY",issues:[]},provenance:{}
  };
  const animation={
    schema_version:"animation-plan-v1",project_id:"OFFLINE_TEST",
    edit_plan_revision:1,revision:1,mode:"BOTH",
    animation_profile:{id:"CANVA_BOTH_21_V1",sha256:profileHash},
    project_seed:12,decisions:[{scene_id:"V001",asset_id:"A001",
      preset:"FADE",speed:"MEDIUM",direction:"NONE",locked:true}],
    provenance:{}
  };
  const editPath=path.join(home,"EDIT_PLAN.json");
  const animationPath=path.join(home,"ANIMATION_PLAN.json");
  fs.writeFileSync(editPath,JSON.stringify(edit),"utf8");
  fs.writeFileSync(animationPath,JSON.stringify(animation),"utf8");
  const uri="file:///"+process.cwd().replace(/\\/g,"/");
  const v=api.createValidator({fs,path,execFile:cp.execFile,
    platform:"win32",pythonExe:py,extensionPath:uri,
    decodeExtensionPath:helper.decodeExtensionPath});
  const result=await new Promise((resolve,reject)=>{
    const ok=v.run({edit:editPath,animation:animationPath,media},
      resolve);
    if(!ok)reject(new Error("Validator did not start"));
  });
  assert.equal(result.status,"NEEDS_REVIEW",JSON.stringify(result));
  assert.equal(result.can_assemble,false);
  assert.equal(result.error_count,0);
  assert.ok(result.review_count>=3);
  assert.ok(result.draft);
  assert.equal(result.draft.scene_count,1);
  assert.equal(result.draft.asset_instance_count,1);
  assert.equal(result.draft.total_frames,90);
  assert.ok(result.animation_phases);
  assert.equal(result.animation_phases.instance_count,1);
  assert.equal(result.animation_phases.zero_hold_count,0);
  assert.equal(result.animation_phases.can_render,false);
  assert.ok(result.import_snapshot,"real Windows Python should yield local import inventory");
  assert.equal(result.import_snapshot.item_count,4);
  assert.equal(result.import_snapshot.import_count,3);
  assert.equal(result.import_snapshot.can_import,false);
  assert.ok(result.issues.some(x=>x.code==="E_HOST_UNVERIFIED"));
  assert.equal(fs.existsSync(path.join(home,"DO_NOT_RENDER.mp4")),false);
  assert.equal(v.isBusy(),false);
 }finally{fs.rmSync(home,{recursive:true,force:true});}
});
