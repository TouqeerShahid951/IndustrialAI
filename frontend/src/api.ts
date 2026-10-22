import type {components} from './generated-api';
export type Upload = components['schemas']['UploadRecord'];
export type Job = components['schemas']['JobRecord'];
export type Incident = components['schemas']['IncidentRecord'];
export type Kind = components['schemas']['Capability'];
export type Point = [number,number];
export type Zone = {name:string;points:Point[]};
export const kinds:Kind[]=['fire','smoke','smoking','no_helmet','intrusion'];
export const labels:Record<Kind,string>={fire:'Fire',smoke:'Smoke',smoking:'Smoking behavior',no_helmet:'No helmet',intrusion:'Restricted-area intrusion'};
export const terminal=new Set(['completed','partial','failed','cancelled','interrupted']);
let csrf='';
export function setCSRF(value:string){csrf=value;}
export async function api<T>(path:string, options:RequestInit={}):Promise<T>{
 const response=await fetch('/api'+path,{...options,headers:{'Content-Type':'application/json','X-CSRF-Token':csrf,...options.headers}});
 if(response.status===401 && path!=='/session')window.dispatchEvent(new Event('signedout'));
 if(!response.ok){const error=await response.json().catch(()=>({detail:'Connection failed'}));throw new Error(typeof error.detail==='string'?error.detail:'Check the fields and try again.');}
 return response.json();
}
export const canLeave=()=>window.dispatchEvent(new Event('before-route-change',{cancelable:true}));
export const post=<T,>(path:string,body:unknown)=>api<T>(path,{method:'POST',body:JSON.stringify(body)});
// Retain intent IDs until a response is received, including across reloads.
export async function mutate<T>(path:string,payload:Record<string,unknown>):Promise<T>{
 const key='industrial:pending:'+path+':'+JSON.stringify(payload);
 const request_id=sessionStorage.getItem(key)||crypto.randomUUID();
 sessionStorage.setItem(key,request_id);
 const result=await post<T>(path,{...payload,request_id});
 sessionStorage.removeItem(key);
 return result;
}
export function uploadVideo(file:File, progress:(n:number)=>void):{promise:Promise<{upload_id:string;preparation_job_id:string}>,cancel:()=>void}{
 const xhr=new XMLHttpRequest();
 const promise=new Promise<{upload_id:string;preparation_job_id:string}>((resolve,reject)=>{
  xhr.open('POST','/api/uploads');xhr.setRequestHeader('X-CSRF-Token',csrf);xhr.setRequestHeader('X-Upload-Name',encodeURIComponent(file.name));xhr.setRequestHeader('Content-Type','application/octet-stream');
  xhr.upload.onprogress=e=>{if(e.lengthComputable)progress(e.loaded/e.total);};
  xhr.onload=()=>{let data;try{data=JSON.parse(xhr.responseText);}catch{reject(new Error('Upload response could not be read.'));return;}if(xhr.status>=200&&xhr.status<300)resolve(data);else reject(new Error(data.detail||'Upload failed.'));};
  xhr.onerror=()=>reject(new Error('Connection interrupted. Try the upload again.'));
  xhr.onabort=()=>reject(new Error('Upload cancelled.'));
  xhr.send(file);
 });
 return {promise,cancel:()=>xhr.abort()};
}
export function clock(t:number){t=Math.max(0,Number(t)||0);return Math.floor(t/60).toString().padStart(2,'0')+':'+Math.floor(t%60).toString().padStart(2,'0');}
export function interval(a:number,b:number){const precise=clock(a)===clock(b);const label=(t:number)=>clock(t)+(precise?'.'+Math.floor((t%1)*1000+1e-6).toString().padStart(3,'0'):'');return label(a)+'–'+label(b);}
export function date(t:string){return new Intl.DateTimeFormat(undefined,{day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit'}).format(new Date(t));}
export function bytes(n:number){return n>=1024**3?(n/1024**3).toFixed(1)+' GB':(n/1024**2).toFixed(1)+' MB';}
function mapTime(t:number,map:number[][],from:number,to:number){
 if(!map?.length)return 0;
 let lo=0,hi=map.length-1;
 while(lo<hi){const m=Math.ceil((lo+hi)/2);if(map[m][from]<=t)lo=m;else hi=m-1;}
 if(t<=map[0][from])return map[0][to];
 if(lo===map.length-1)return map[lo][to];
 const a=map[lo],b=map[lo+1];return a[to]+(t-a[from])/(b[from]-a[from])*(b[to]-a[to]);
}
export const toPreview=(t:number,map:number[][])=>mapTime(t,map,0,1);
export const toSource=(t:number,map:number[][])=>mapTime(t,map,1,0);
export function jobSummary(job:Job){
 if(job.status==='partial')return 'Partial analysis · inspect capability errors';
 if(job.status==='failed')return 'Analysis failed';
 if(job.status==='interrupted')return 'Interrupted · retry required';
 if(job.status==='cancelled')return 'Analysis cancelled';
 if(job.status==='completed'&&job.result.review_counts?.total)return `${job.result.review_counts.total} observations · ${job.result.review_counts.unreviewed} unreviewed`;
 if(job.status==='completed')return job.result.incident_count===0?'No candidates detected · review visibility':`${job.result.incident_count??0} candidates to review`;
 return job.stage;
}
