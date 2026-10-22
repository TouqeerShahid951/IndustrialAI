// A live API/worker journey complements the in-app-browser acceptance pass.
// Run against the local service started by scripts/start_mvp.sh.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile,mkdir,writeFile,mkdtemp,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {randomUUID} from 'node:crypto';

test('authenticated upload, all-five worker, review audit, three exports, cancel and retry',{timeout:240000},async()=>{
 const root=resolve('..'),base=process.env.MVP_E2E_URL||'http://127.0.0.1:8008';
 assert.ok(new URL(base).hostname==='127.0.0.1'||new URL(base).hostname==='localhost','E2E must target loopback');
 const password=(await readFile(join(root,'var/mvp/operator-password.txt'),'utf8')).trim();
 const sessionResponse=await fetch(base+'/api/session',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({password})});
 assert.equal(sessionResponse.status,200);
 const session=await sessionResponse.json(),cookie=sessionResponse.headers.getSetCookie()[0].split(';')[0];
 async function request(path,body,method=body?'POST':'GET'){
  const response=await fetch(base+'/api'+path,{method,headers:{Cookie:cookie,'X-CSRF-Token':session.csrf,'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined});
  assert.ok(response.ok,`${method} ${path}: ${response.status} ${await (!response.ok?response.text():Promise.resolve(''))}`);return response.json();
 }
 async function waitJob(id){let job;for(let n=0;n<1200;n++){job=await request('/jobs/'+id);if(['completed','partial','failed','cancelled','interrupted'].includes(job.status))return job;await new Promise(r=>setTimeout(r,100));}assert.fail('Worker timed out');}
 const directory=await mkdtemp(join(tmpdir(),'industrial-e2e-'));
 let uid;
 try{
  const fixture=join(directory,'fixture.mp4');
  execFileSync(join(root,'.venv/bin/python'),['-c',"import cv2,numpy as np,sys; w=cv2.VideoWriter(sys.argv[1],cv2.VideoWriter_fourcc(*'mp4v'),10,(160,120)); [w.write(np.full((120,160,3),i*5,np.uint8)) for i in range(15)]; w.release()",fixture]);
  const uploaded=await fetch(base+'/api/uploads',{method:'POST',headers:{Cookie:cookie,'X-CSRF-Token':session.csrf,'X-Upload-Name':'MVP%20journey%20fixture.mp4','Content-Type':'application/octet-stream'},body:await readFile(fixture)});
  assert.equal(uploaded.status,202);const upload=await uploaded.json();uid=upload.upload_id;
  assert.equal((await waitJob(upload.preparation_job_id)).status,'completed');
  const config={request_id:randomUUID(),capabilities:['fire','smoke','smoking','no_helmet','intrusion'],device:process.env.MVP_E2E_DEVICE||'mps',camera:'Automated development fixture',zones:[{name:'Test zone',points:[[.1,.1],[.9,.1],[.9,.9],[.1,.9]]}]};
  const queued=await request('/uploads/'+uid+'/jobs',config);
  assert.equal((await request('/uploads/'+uid+'/jobs',config)).id,queued.id,'job idempotency');
  const job=await waitJob(queued.id);assert.equal(job.status,'completed',JSON.stringify(job.result));
  for(const kind of config.capabilities)assert.equal(job.result.capabilities[kind].status,'completed');
  const incident=await request('/jobs/'+job.id+'/incidents',{request_id:randomUUID(),kind:'smoke',start:.1,end:.8,initial_review:{decision:'uncertain',note:'Synthetic application acceptance fixture; not a real event.'}});
  const review={request_id:randomUUID(),decision:'false_alarm',expected_version:1,note:'=application acceptance check'};
  const saved=await request('/incidents/'+incident.id+'/reviews',review);assert.equal(saved.version,2);
  assert.equal((await request('/incidents/'+incident.id+'/reviews',review)).version,2);
  assert.equal((await request('/jobs/'+job.id+'/incidents'))[0].decision,'false_alarm');
  const exports=[];
  for(const format of ['json','csv','mp4']){
   const task=await request('/jobs/'+job.id+'/exports',{request_id:randomUUID(),format,incident_id:incident.id});
   const done=await waitJob(task.id);assert.equal(done.status,'completed',done.error);
   const path=base+'/api/artifacts/'+done.result.artifact_id;
   const response=await fetch(path,{headers:{Cookie:cookie,Range:'bytes=0-31'}});assert.equal(response.status,206);
   assert.equal((await fetch(path)).status,401);
   if(format==='mp4')assert.ok(done.result.manifest_id);
   exports.push(format);
  }
  const cancelJob=await request('/uploads/'+uid+'/jobs',{...config,request_id:randomUUID()});
  await request('/jobs/'+cancelJob.id+'/cancel',{});assert.equal((await waitJob(cancelJob.id)).status,'cancelled');
  const retry=await request('/jobs/'+cancelJob.id+'/retry',{request_id:randomUUID()});assert.notEqual(retry.id,cancelJob.id);assert.equal((await waitJob(retry.id)).status,'completed');
  await mkdir('test-results',{recursive:true});await writeFile('test-results/api-journey.json',JSON.stringify({passed:true,date:new Date().toISOString(),capabilities:config.capabilities,exports,checks:['upload','preview','job-idempotency','full-worker','manual-observation','review-audit','review-idempotency','private-range-download','cancel','retry']},null,2));
 }finally{
  if(uid)await request('/uploads/'+uid,undefined,'DELETE');
  await rm(directory,{recursive:true,force:true});
 }
});
