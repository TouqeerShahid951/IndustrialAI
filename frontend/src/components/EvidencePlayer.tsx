import {useEffect,useRef,useState,type ReactNode} from 'react';
import {Play,Pause,CaretLeft,CaretRight,ArrowsOut} from '@phosphor-icons/react';
import {api,clock,toPreview,toSource,type Upload,type Job,type Incident} from '../api';
type Observation={frame:number;time:number;model:string;boxes:{bbox:number[];canonical:string;class:string;track?:number}[]};
export function EvidencePlayer({upload,job,time,onTime,incidents=[],children}:{upload:Upload;job?:Job;time:number;onTime:(t:number)=>void;incidents?:Incident[];children?:ReactNode}){
 const video=useRef<HTMLVideoElement>(null),canvas=useRef<HTMLCanvasElement>(null),container=useRef<HTMLDivElement>(null);
 const [frames,setFrames]=useState(false),[playing,setPlaying]=useState(false),[mediaError,setMediaError]=useState(''),[observations,setObservations]=useState<Observation[]>([]);
 const map=upload.metadata.frame_map as number[][]||[],duration=Number(upload.metadata.duration||0),fps=Number(upload.metadata.fps||25);
 const width=Number(upload.metadata.width||640),height=Number(upload.metadata.height||360);
 const framePreviews=(upload.metadata.frames_preview||[]) as {source:number;artifact_id:string}[];
 const nearest=framePreviews.reduce((best,item)=>Math.abs(item.source-time)<Math.abs(best.source-time)?item:best,framePreviews[0]||{source:0,artifact_id:''});
 const displayTime=frames?nearest.source:time;
 useEffect(()=>{if(video.current && Math.abs(video.current.currentTime-toPreview(time,map))>.005)video.current.currentTime=toPreview(time,map);},[time,frames]);
 const chunk=Math.floor(displayTime/2)*2;
 useEffect(()=>{let active=true;if(job)api<Observation[]>(`/jobs/${job.id}/observations?start=${chunk}&end=${chunk+2}`).then(v=>{if(active)setObservations(v);}).catch(()=>{if(active)setObservations([]);});return()=>{active=false;};},[job?.id,chunk]);
 useEffect(()=>{const ctx=canvas.current?.getContext('2d');if(!ctx)return;ctx.clearRect(0,0,width,height);ctx.font=`${Math.max(12,width/75)}px system-ui`;ctx.lineWidth=Math.max(1,width/600);
  const byModel=new Map<string,Observation>();for(const row of observations){const old=byModel.get(row.model);if(!old||Math.abs(row.time-displayTime)<Math.abs(old.time-displayTime))byModel.set(row.model,row);}
  for(const row of byModel.values()){if(Math.abs(row.time-displayTime)>1/fps+.05)continue;for(const box of row.boxes){const candidate=['fire','smoke','no_helmet','cigarette'].includes(box.canonical);const color=candidate?'#FFB340':'#A9C8B5';const [x1,y1,x2,y2]=box.bbox;ctx.strokeStyle=color;ctx.strokeRect(x1,y1,x2-x1,y2-y1);const label=box.track?`Track ${box.track}`:box.class+' candidate';const textWidth=ctx.measureText(label).width;ctx.fillStyle='#17291E';ctx.fillRect(x1,Math.max(0,y1-22),textWidth+12,22);ctx.fillStyle=color;ctx.fillText(label,x1+6,Math.max(16,y1-6));}}
  for(const zone of job?.config.zones||[]){if(!zone.points?.length)continue;ctx.beginPath();zone.points.forEach((p:number[],i:number)=>i?ctx.lineTo(p[0]*width,p[1]*height):ctx.moveTo(p[0]*width,p[1]*height));ctx.closePath();ctx.fillStyle='rgba(169,200,181,.12)';ctx.fill();ctx.strokeStyle='#A9C8B5';ctx.stroke();}
 },[observations,displayTime,width,height,job?.id]);
 function seek(t:number){onTime(Math.min(Math.max(0,t),duration));}
 function step(direction:number){if(frames){const index=framePreviews.indexOf(nearest);seek(framePreviews[Math.max(0,Math.min(framePreviews.length-1,index+direction))]?.source||0);}else seek(time+direction/fps);}
 function toggle(){if(!video.current)return;if(playing)video.current.pause();else video.current.play().catch(()=>setMediaError('Playback unavailable. Use Frames to review still evidence.'));}
 return <div className="evidence-player" ref={container}>
  <div className="player-header"><span className="muted">{frames?'Source still · '+clock(nearest.source):'Recorded video · '+clock(duration)}</span><div className="segments" aria-label="Evidence presentation"><button className={!frames?'selected':''} aria-pressed={!frames} onClick={()=>setFrames(false)}>Video</button><button className={frames?'selected':''} aria-pressed={frames} onClick={()=>{video.current?.pause();setFrames(true);}}>Frames</button></div></div>
  <div className="evidence-frame" style={{aspectRatio:`${width}/${height}`}}>
   {frames?<img src={'/api/artifacts/'+nearest.artifact_id} alt={'Source frame at '+clock(nearest.source)}/>:<video ref={video} src={'/api/artifacts/'+upload.metadata.preview_id} playsInline preload="metadata" onTimeUpdate={e=>onTime(toSource(e.currentTarget.currentTime,map))} onPlay={()=>setPlaying(true)} onPause={()=>setPlaying(false)} onError={()=>setMediaError('Playback unavailable. Use Frames for source evidence.')} />}
   <canvas ref={canvas} width={width} height={height} className="evidence-overlay" aria-label="Detection and zone overlays"/>{children}
  </div>
  {mediaError&&<p className="attention" role="status">{mediaError}</p>}
  <div className="transport">{!frames&&<button className="icon-button" aria-label={playing?'Pause':'Play'} onClick={toggle}>{playing?<Pause size={24}/>:<Play size={24} weight="fill"/>}</button>}<button className="icon-button" aria-label="Previous frame" onClick={()=>step(-1)}><CaretLeft size={22}/></button><span className="clock">{clock(displayTime)} / {clock(duration)}</span><button className="icon-button" aria-label="Next frame" onClick={()=>step(1)}><CaretRight size={22}/></button><input aria-label="Seek source time" type="range" min="0" max={duration} step={frames?1:1/fps} value={time} onChange={e=>seek(Number(e.target.value))}/><button className="icon-button fullscreen" aria-label="Fullscreen evidence" onClick={()=>container.current?.requestFullscreen()}><ArrowsOut size={24}/></button></div>
  {!!incidents.length&&<div className="incident-timeline" aria-label="Candidate intervals">{incidents.map(i=><button key={i.id} style={{left:`${i.start/duration*100}%`,width:`${Math.max(1,(i.end-i.start)/duration*100)}%`}} title={`${i.kind} ${clock(i.start)}–${clock(i.end)}`} aria-label={'Seek '+i.kind+' at '+clock(i.start)} onClick={()=>seek(i.start)}/>)}</div>}
  <div className="source-marks"><span>00:00</span><span>Original source time</span><span>{clock(duration)}</span></div>
 </div>;
}
