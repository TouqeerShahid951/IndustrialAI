import {useEffect,useRef,useState,type ReactNode} from 'react';
import {Play,Pause,CaretLeft,CaretRight,ArrowsOut,Eye} from '@phosphor-icons/react';
import {api,clock,labels,toPreview,toSource,type Upload,type Job,type Incident} from '../api';
type Observation={frame:number;time:number;model:string;boxes:{bbox:number[];canonical:string;class:string;track?:number}[]};
const preciseClock=(t:number)=>{const ms=Math.round(Math.max(0,t)*1000);return clock(ms/1000)+'.'+String(ms%1000).padStart(3,'0');};
const decisions={confirmed:'Confirmed',false_alarm:'False alarm',uncertain:'Uncertain'};
export function EvidencePlayer({upload,job,time,onTime,incidents=[],children}:{upload:Upload;job?:Job;time:number;onTime:(t:number)=>void;incidents?:Incident[];children?:ReactNode}){
 const video=useRef<HTMLVideoElement>(null),frame=useRef<HTMLDivElement>(null),container=useRef<HTMLDivElement>(null),reportedTime=useRef<number|null>(null);
 const [frames,setFrames]=useState(false),[playing,setPlaying]=useState(false),[mediaError,setMediaError]=useState(''),[observations,setObservations]=useState<Observation[]>([]),[overlays,setOverlays]=useState(true),[displayWidth,setDisplayWidth]=useState(640),[overlayError,setOverlayError]=useState(false);
 const map=upload.metadata.frame_map as number[][]||[],duration=Number(upload.metadata.duration||0),fps=Number(upload.metadata.fps||25);
 const width=Number(upload.metadata.width||640),height=Number(upload.metadata.height||360);
 const framePreviews=(upload.metadata.frames_preview||[]) as {source:number;artifact_id:string}[];
 const nearest=framePreviews.reduce((best,item)=>Math.abs(item.source-time)<Math.abs(best.source-time)?item:best,framePreviews[0]||{source:0,artifact_id:''});
 const displayTime=frames?nearest.source:time,position=duration?Math.min(100,Math.max(0,displayTime/duration*100)):0;
 // Normalize decoder floating-point noise at inclusive event boundaries.
 const publish=(t:number)=>{t=Math.round(t*1e6)/1e6;reportedTime.current=t;onTime(t);};
 const publishRef=useRef(publish);publishRef.current=publish;
 useEffect(()=>{
  if(video.current&&time!==reportedTime.current&&Math.abs(video.current.currentTime-toPreview(time,map))>.005){
   // Seek inside the frame: encoded preview PTS can round above its frame-map value.
   video.current.currentTime=toPreview(time,map)+Math.min(.001,.25/fps);
  }
 },[time,frames]);
 useEffect(()=>{
  const el=video.current;if(!el?.requestVideoFrameCallback)return;
  let handle:number;const update:VideoFrameRequestCallback=(_,metadata)=>{publishRef.current(toSource(metadata.mediaTime,map));handle=el.requestVideoFrameCallback(update);};
  handle=el.requestVideoFrameCallback(update);return()=>el.cancelVideoFrameCallback(handle);
 },[frames,upload.id]);
 useEffect(()=>{if(!frame.current||typeof ResizeObserver==='undefined')return;const observer=new ResizeObserver(([entry])=>setDisplayWidth(entry.contentRect.width||width));observer.observe(frame.current);return()=>observer.disconnect();},[width]);
 const chunk=Math.floor(displayTime/2)*2;
 useEffect(()=>{let active=true;setObservations([]);setOverlayError(false);if(job)api<Observation[]>(`/jobs/${job.id}/observations?start=${chunk}&end=${chunk+2}`).then(v=>{if(active)setObservations(v);}).catch(()=>{if(active)setOverlayError(true);});return()=>{active=false;};},[job?.id,chunk]);
 const byModel=new Map<string,Observation>();for(const row of observations){const old=byModel.get(row.model);if(!old||Math.abs(row.time-displayTime)<Math.abs(old.time-displayTime))byModel.set(row.model,row);}
 const boxes=[...byModel.values()].filter(row=>Math.abs(row.time-displayTime)<=.5/fps+.001).flatMap(row=>row.boxes);
 const unit=width/displayWidth;
 function seek(t:number){reportedTime.current=null;onTime(Math.min(Math.max(0,t),duration));}
 function step(direction:number){video.current?.pause();if(frames){const index=framePreviews.indexOf(nearest);seek(framePreviews[Math.max(0,Math.min(framePreviews.length-1,index+direction))]?.source||0);}else{let next:number|undefined;for(const p of map){if(direction>0&&p[0]>time+.001){next=p[0];break;}if(direction<0&&p[0]<time-.001)next=p[0];}seek(next??time);}}
 function toggle(){if(!video.current)return;if(playing)video.current.pause();else video.current.play().catch(()=>setMediaError('Playback unavailable. Use Frames to review still evidence.'));}
 const atPlayhead=(i:Incident)=>displayTime>=i.start-.000001&&displayTime<=i.end+.000001;
 const activeCount=incidents.filter(atPlayhead).length;
 return <div className="evidence-player" ref={container}>
  <div className="player-header"><span className="muted">{frames?'Source still · '+preciseClock(nearest.source):'Recorded video · '+clock(duration)}</span><div className="player-options">{job&&<button className="overlay-toggle" aria-pressed={overlays} onClick={()=>setOverlays(!overlays)}><Eye size={18}/>Overlays</button>}<div className="segments" aria-label="Evidence presentation"><button className={!frames?'selected':''} aria-pressed={!frames} onClick={()=>{seek(displayTime);setFrames(false);}}>Video</button><button className={frames?'selected':''} aria-pressed={frames} disabled={!framePreviews.length} onClick={()=>{video.current?.pause();setFrames(true);}}>Frames</button></div></div></div>
  <div className="evidence-frame" ref={frame} style={{aspectRatio:`${width}/${height}`}}>
   {frames?<img src={'/api/artifacts/'+nearest.artifact_id} alt={'Source frame at '+preciseClock(nearest.source)}/>:<video ref={video} src={'/api/artifacts/'+upload.metadata.preview_id} playsInline preload="metadata" onTimeUpdate={e=>{if(!e.currentTarget.requestVideoFrameCallback)publish(toSource(e.currentTarget.currentTime,map));}} onPlay={()=>setPlaying(true)} onPause={()=>setPlaying(false)} onEnded={()=>setPlaying(false)} onError={()=>setMediaError('Playback unavailable. Use Frames for source evidence.')} />}
   {overlays&&<svg viewBox={`0 0 ${width} ${height}`} className="evidence-overlay" role="img" aria-label="Model detection boxes and analysis zones">
    {(job?.config.zones||[]).filter(z=>z.points?.length).map((z,index)=><polygon key={index} points={z.points.map(p=>`${p[0]*width},${p[1]*height}`).join(' ')} fill="#A9C8B518" stroke="#fff" strokeWidth="2" strokeDasharray="6 4" vectorEffect="non-scaling-stroke"><title>{z.name} · analysis zone</title></polygon>)}
    {boxes.map((box,index)=>{const [x1,y1,x2,y2]=box.bbox;const candidate=['fire','smoke','no_helmet','cigarette'].includes(box.canonical);const color=candidate?'#67E8F9':'#fff';const label=box.class+(box.track!=null?' · Track '+box.track:' · model');const labelWidth=Math.min(width,(label.length*7.5+16)*unit),labelHeight=24*unit;const x=Math.max(0,Math.min(x1,width-labelWidth)),y=Math.max(0,Math.min(y1-labelHeight,height-labelHeight));return <g key={index}><title>{label}</title><rect x={x1} y={y1} width={x2-x1} height={y2-y1} fill="none" stroke="#101512" strokeWidth="5" vectorEffect="non-scaling-stroke"/><rect x={x1} y={y1} width={x2-x1} height={y2-y1} fill="none" stroke={color} strokeWidth="2" vectorEffect="non-scaling-stroke"/><rect x={x} y={y} width={labelWidth} height={labelHeight} rx={3*unit} fill="#101512"/><text x={x+8*unit} y={y+16*unit} fill={color} fontSize={13*unit} fontFamily="system-ui" fontWeight="600">{label}</text></g>;})}
   </svg>}{children}
  </div>
  {mediaError&&<p className="attention" role="status">{mediaError}</p>}
  <div className="transport">{!frames&&<button className="icon-button" aria-label={playing?'Pause':'Play'} onClick={toggle}>{playing?<Pause size={24}/>:<Play size={24} weight="fill"/>}</button>}<button className="icon-button" aria-label="Previous frame" onClick={()=>step(-1)}><CaretLeft size={22}/></button><span className="clock">{preciseClock(displayTime)} / {preciseClock(duration)}</span><button className="icon-button" aria-label="Next frame" onClick={()=>step(1)}><CaretRight size={22}/></button><button className="icon-button fullscreen" aria-label="Fullscreen evidence" onClick={()=>container.current?.requestFullscreen().catch(()=>setMediaError('Fullscreen unavailable in this browser.'))}><ArrowsOut size={24}/></button></div>
  <div className="source-timeline">
   <input aria-label="Seek source time" aria-valuetext={preciseClock(displayTime)+' original source time'} type="range" min="0" max={duration} step="any" value={displayTime} onChange={e=>seek(Number(e.target.value))} onKeyDown={e=>{if(e.key==='ArrowLeft'||e.key==='ArrowRight'){e.preventDefault();step(e.key==='ArrowLeft'?-1:1);}}}/>
   <div className="source-marks"><span>00:00</span><span>Original source time</span><span>{preciseClock(duration)}</span></div>
   {!!incidents.length&&<><div className="timeline-caption"><span>Event intervals · click to jump</span><span>{activeCount?`${activeCount} at playhead`:'No listed event at playhead'}</span></div><div className="incident-timeline" aria-label="Event intervals on original source time">{incidents.map(i=>{const active=atPlayhead(i);return <button key={i.id} className="event-row" aria-label={`Jump to ${labels[i.kind]} at ${preciseClock(i.start)}`} aria-current={active?'time':undefined} onClick={()=>{video.current?.pause();seek(i.start);}}><span className="event-description"><span><strong>{labels[i.kind]}</strong> <span className="clock">{preciseClock(i.start)}–{preciseClock(i.end)}</span></span><span>{i.origin==='manual'?'Manual':'Model'} · {i.decision?decisions[i.decision]:'Unreviewed'}</span></span><span className="event-track"><span className={'event-interval '+i.origin} style={{left:`${duration?i.start/duration*100:0}%`,width:`${duration?(i.end-i.start)/duration*100:0}%`}}/><span className="timeline-playhead" style={{left:`${position}%`}}/></span></button>;})}</div></>}
  </div>
  {(job||frames)&&<p className="overlay-note">{frames?'Sampled stills; use Video to inspect brief events. ':''}{job&&(overlayError?'Model boxes unavailable. Retry by seeking to another interval.':overlays?'Cyan: model candidates · white: other detections / zones. Boxes are model output; manual intervals have no boxes.':'Model overlays hidden.')}</p>}
 </div>;
}
