const test=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const code=fs.readFileSync(path.join(__dirname,"..","host","media_import_adapter.jsx"),"utf8");
const target="AIJSON_MEDIA_DEMO_2026";
function input(){
 const items=[
  ["SOURCE_SRT","srt","C:\\Job\\narasi.srt",false],
  ["SOURCE_AUDIO","audio","C:\\Job\\narasi.wav",true],
  ["SOURCE_BACKGROUND","background","C:\\Job\\background.mp4",true],
  ["ASSET_A001","png","C:\\Job\\images\\A001.png",true],
  ["ASSET_A002","png","C:\\Job\\images\\A002.png",true]
 ].map((item,i)=>({
   item_id:item[0],kind:item[1],absolute_path:item[2],
   sha256:"a".repeat(64),byte_size:100+i,mtime_ns:111111,
   import_to_premiere:item[3],relative_path:"media-"+i
 }));
 return {schema_version:"verified-media-snapshot-v1",
  status:"CANDIDATE_NOT_AUTHORIZED",can_import:false,can_assemble:false,
  inventory_sha256:"b".repeat(64),item_count:items.length,
  import_count:4,items};
}
function host(options={}){
 const snap=input();
 const fileSizes=new Map(snap.items.map(x=>[x.absolute_path.toLowerCase(),x.byte_size]));
 let mutations=0,imports=0,created=null;
 const rootChildren=[{nodeId:"user-owned-1",name:"My edits",getMediaPath:()=>""}];
 Object.defineProperty(rootChildren,"numItems",{get(){return this.length;}});
 const project={
   rootItem:{
    children:rootChildren,
    findItemsMatchingMediaPath(path){
      return options.existsInProject===path ? [{nodeId:"prior"}] : 0;
    },
    createBin(name){
      mutations++;
      if(options.throwAfterCreate){throw Error("Host failed after create attempt");}
      const newChildren=[];
      Object.defineProperty(newChildren,"numItems",{get(){return this.length;}});
      created={nodeId:"new-managed-123",name,children:newChildren};
      rootChildren.push(created);
      if(options.badBin){created.children.push({nodeId:"unexpected"});}
      return created;
    }
   },
   importFiles(paths,suppressUI,bin,numbered){
      imports++;
      if(options.failImportAt===imports){return false;}
      if(options.throwImportAt===imports){throw Error("host throws after import");}
      if(!options.noInsertAt || options.noInsertAt!==imports){
        const media=options.wrongMediaAt===imports?
          "C:\\Job\\unknown.png":paths[0];
        bin.children.push({
          nodeId:"imported-"+imports,
          getMediaPath:()=>media
        });
      }
      assert.equal(suppressUI,true);
      assert.equal(numbered,false);
      assert.equal(paths.length,1);
      return true;
   }
 };
 const app={version:options.hostVersion||"24.4",project};
 function File(p){
   this.fsName=p;this.exists=fileSizes.has(p.toLowerCase());
   this.length=fileSizes.get(p.toLowerCase())||0;
 }
 const context=vm.createContext({$:{},app,File});
 vm.runInContext(code,context,{timeout:2000});
 const adapter=context.$._AIJSON_MEDIA_IMPORT_V1;
 const auth={kind:"HOST_REVIEWED_IMPORT_V1",ownerConfirmed:true,
   hostCapabilityVerified:true,mediaHashesFresh:true,preflightAllPass:true,
   hostVersion:"24.4",snapshotDigest:snap.inventory_sha256};
 return {snapshot:snap,auth,adapter,fileSizes,project,rootChildren,
   mutations:()=>mutations,imports:()=>imports,created:()=>created,
   run:()=>adapter.importFresh(snap,target,auth)};
}
test("imports only background, narration, and PNG into NEW private bin",()=>{
 const h=host();
 assert.equal(h.run(),"S6|1|IMPORTED_TO_NEW_BIN|4");
 assert.equal(h.mutations(),1);
 assert.equal(h.imports(),4);
 assert.equal(h.rootChildren.length,2);
 assert.equal(h.rootChildren[0].name,"My edits");
 assert.equal(h.created().children.length,4);
 assert.equal(h.created().name,target);
});
test("unapproved or forged JSON READY never causes import",()=>{
 const h=host();
 h.snapshot.validation={status:"READY"};
 h.auth.preflightAllPass=false;
 assert.equal(h.run(),"S6|1|BLOCKED|AUTHORIZATION_NOT_VERIFIED");
 h.auth.preflightAllPass=true;h.auth.snapshotDigest="c".repeat(64);
 assert.equal(h.run(),"S6|1|BLOCKED|AUTHORIZATION_NOT_VERIFIED");
 h.auth.snapshotDigest=h.snapshot.inventory_sha256;
 h.auth.ownerConfirmed=false;
 assert.equal(h.run(),"S6|1|BLOCKED|AUTHORIZATION_NOT_VERIFIED");
 assert.equal(h.imports(),0);
 assert.equal(h.mutations(),0);
});
test("existing managed bin name blocks repeat without touching anything",()=>{
 const h=host();
 assert.equal(h.run(),"S6|1|IMPORTED_TO_NEW_BIN|4");
 assert.equal(h.run(),"S6|1|BLOCKED|MANAGED_BIN_ALREADY_EXISTS");
 assert.equal(h.imports(),4);
 assert.equal(h.mutations(),1);
});
test("invalid manifest/duplicated paths/IDs and unexpected media type reject early",()=>{
 for(const corrupt of [
  s=>s.item_count=99,
  s=>s.items[4].absolute_path=s.items[3].absolute_path,
  s=>s.items[4].item_id=s.items[3].item_id,
  s=>s.items[2].kind="invalid",
  s=>s.items[2].absolute_path="..\\other.mp4",
  s=>s.items[2].absolute_path="\\\\server\\share\\bg.mp4",
  s=>s.items[2].sha256="UNKNOWN",
  s=>s.import_count=9,
  s=>s.items[0].import_to_premiere=true
 ]){
  const h=host();corrupt(h.snapshot);
  assert.equal(h.run(),"S6|1|BLOCKED|IMPORT_MANIFEST_INVALID");
  assert.equal(h.mutations(),0);
 }
});
test("file missing or size changed blocks BEFORE managed bin exists",()=>{
 const h=host();
 h.fileSizes.delete(h.snapshot.items[3].absolute_path.toLowerCase());
 assert.equal(h.run(),"S6|1|BLOCKED|SOURCE_CHANGED_OR_MISSING");
 assert.equal(h.imports(),0);
 assert.equal(h.mutations(),0);
});
test("previously imported same media blocks, no duplicates",()=>{
 const h=host({existsInProject:"C:\\Job\\narasi.wav"});
 assert.equal(h.run(),"S6|1|BLOCKED|MEDIA_ALREADY_IN_PROJECT");
 assert.equal(h.mutations(),0);
});
test("unsupported Premiere version blocks with no API calls",()=>{
 const h=host({hostVersion:"25.1"});
 assert.equal(h.run(),"S6|1|BLOCKED|HOST_UNSUPPORTED");
 assert.equal(h.mutations(),0);
});
test("no true imported child readback keeps INCOMPLETE bin for investigation",()=>{
 const h=host({noInsertAt:2});
 assert.equal(h.run(),"S6|1|INCOMPLETE|IMPORT_COUNT_MISMATCH");
 assert.equal(h.mutations(),1);
 assert.equal(h.imports(),2);
 assert.equal(h.rootChildren.length,2);
 assert.equal(h.created().children.length,1);
});
test("wrong imported path flags INCOMPLETE and never deletes existing edits",()=>{
 const h=host({wrongMediaAt:1});
 assert.equal(h.run(),"S6|1|INCOMPLETE|MEDIA_PATH_MISMATCH");
 assert.equal(h.rootChildren[0].name,"My edits");
 assert.equal(h.imports(),1);
});
test("native import failure preserves already imported media without retry",()=>{
 const h=host({failImportAt:3});
 assert.equal(h.run(),"S6|1|INCOMPLETE|IMPORT_API_FAILED");
 assert.equal(h.created().children.length,2);
 assert.equal(h.imports(),3);
 assert.equal(h.rootChildren[0].name,"My edits");
});
test("unexpected host exception after bin creation never auto-cleans",()=>{
 const h=host({throwImportAt:1});
 assert.equal(h.run(),"S6|1|INCOMPLETE|HOST_IMPORT_EXCEPTION");
 assert.equal(h.rootChildren.length,2);
 assert.equal(h.mutations(),1);
});
test("bin creation readback mismatch does not continue importing",()=>{
 const h=host({badBin:true});
 assert.equal(h.run(),"S6|1|INCOMPLETE|BIN_READBACK_FAILED");
 assert.equal(h.imports(),0);
 assert.equal(h.mutations(),1);
});
test("static adapter never deletes project media or exports",()=>{
 for(const forbidden of ["deleteBin(", "removeMedia(", "changeMediaPath(",
   "exportAsMediaDirect(", "app.enableQE", "eval("]){
   assert.equal(code.includes(forbidden),false,forbidden);
 }
});
