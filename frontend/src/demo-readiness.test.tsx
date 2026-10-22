import React from 'react';
import {render,screen,fireEvent,waitFor,cleanup,act,within} from '@testing-library/react';
import {it,expect,vi,beforeEach,afterEach} from 'vitest';
import {App} from './App';
import {Uploads,Progress} from './pages/Uploads';
import {ManualDialog} from './pages/Review';
import {Incidents} from './pages/Incidents';
vi.mock('./components/EvidencePlayer',()=>({EvidencePlayer:()=> <div>Source evidence</div>}));
const job={id:'j',upload_id:'u',kind:'analyze',status:'completed',stage:'Completed',processed:20,expected:20,created:'2026-10-22T07:00:00Z',config:{camera:'Factory demo'},result:{incident_count:1},error:null};
const upload={id:'u',name:'factory.mp4',status:'ready',created:job.created,metadata:{duration:3},jobs:[job,{...job,id:'old'}]};
const incident={id:'i',job_id:'j',kind:'smoke',origin:'model',start:0,end:1,evidence:{level:'raw'},created:job.created,version:0,decision:null,note:null};
function mockAPI(extra:(path:string,options?:any)=>any=()=>undefined){vi.stubGlobal('fetch',vi.fn(async(path:string,options:any)=>({ok:true,status:200,json:async()=>await (extra(path,options)??({'/api/session':{csrf:'token'},'/api/uploads':[upload],'/api/uploads/u':upload,'/api/jobs/j':job,'/api/jobs/j/incidents':[incident],'/api/incidents':[incident],'/api/incidents/i/reviews':[], '/api/storage':{used:1,quota:100},'/api/capabilities':{worker_available:true}} as any)[path])})));}
beforeEach(()=>{history.replaceState(null,'','#/uploads');sessionStorage.clear();vi.stubGlobal('scrollTo',()=>{});HTMLDialogElement.prototype.showModal=function(){this.setAttribute('open','');};HTMLDialogElement.prototype.close=function(){this.removeAttribute('open');};});
afterEach(()=>{cleanup();vi.useRealTimers();vi.restoreAllMocks();vi.unstubAllGlobals();});
it('offers another analysis and access to earlier runs without uploading again',async()=>{
 mockAPI();render(<Uploads/>);
 expect(await screen.findByRole('link',{name:'New analysis'})).toHaveAttribute('href','#/setup/u');
 fireEvent.click(screen.getByText('Activity (2)'));
 expect(screen.getByRole('link',{name:/Analysis.*old/})).toHaveAttribute('href','#/review/old');
});
it('preserves a review draft when browser navigation is declined',async()=>{
 history.replaceState(null,'','#/review/j');mockAPI();vi.spyOn(window,'confirm').mockReturnValue(false);render(<App/>);
 fireEvent.click(await screen.findByRole('button',{name:/Smoke.*Raw flag/}));
 fireEvent.change(screen.getByRole('textbox',{name:'Review notes'}),{target:{value:'Do not lose this draft'}});
 await act(async()=>{history.replaceState(null,'','#/history');window.dispatchEvent(new HashChangeEvent('hashchange'));});
 expect(screen.getByRole('textbox',{name:'Review notes'})).toHaveValue('Do not lose this draft');
 expect(location.hash).toBe('#/review/j');
});
it('does not export a previous incident source while new details are loading',async()=>{
 let resolveSlow:(value:any)=>void=()=>{};const slow=new Promise(r=>resolveSlow=r);
 const second={...incident,id:'second',job_id:'other',kind:'fire'};
 mockAPI(path=>path==='/api/incidents'?[incident,second]:path==='/api/jobs/other'?slow:path==='/api/incidents/second/reviews'?[]:undefined);
 render(<Incidents/>);const views=await screen.findAllByRole('button',{name:'View'});fireEvent.click(views[0]);
 await waitFor(()=>expect(screen.getByRole('button',{name:'Export evidence'})).toBeEnabled());
 fireEvent.click(screen.getByRole('button',{name:/Close incident details/i}));fireEvent.click(views[1]);
 expect(screen.getByRole('button',{name:'Export evidence'})).toBeDisabled();
 await act(async()=>resolveSlow({...job,id:'other'}));
 await waitFor(()=>expect(screen.getByRole('button',{name:'Export evidence'})).toBeEnabled());
 expect(screen.getByRole('dialog',{name:'Incident details'})).toBeVisible();
});
it('retries progress polling after a temporary connection failure',async()=>{
 vi.useFakeTimers();let calls=0;vi.stubGlobal('fetch',vi.fn(async(path:string)=>{if(path==='/api/jobs/j'&&++calls===1)throw new Error('Offline');return {ok:true,json:async()=>path==='/api/jobs/j'?job:path==='/api/capabilities'?{worker_available:true}:upload};}));
 render(<Progress id="j"/>);await act(async()=>{});await act(async()=>{await vi.advanceTimersByTimeAsync(2100);});
 expect(screen.getByRole('heading',{name:'Completed'})).toBeVisible();expect(screen.queryByRole('alert')).not.toBeInTheDocument();
});
it('remembers the last review destination after visiting history',async()=>{
 history.replaceState(null,'','#/review/j');mockAPI();render(<App/>);await screen.findByText('Source evidence');
 await act(async()=>{history.replaceState(null,'','#/history');window.dispatchEvent(new HashChangeEvent('hashchange'));});
 expect(within(screen.getByRole('navigation')).getByRole('link',{name:'Review'})).toHaveAttribute('href','#/review/j');
});

it('keeps a manual observation until explicit in-app discard',()=>{
 const close=vi.fn();vi.spyOn(window,'confirm').mockReturnValue(false);
 render(<ManualDialog job={job as any} upload={upload as any} sourceTime={0} onClose={close} onSaved={()=>{}}/>);
 fireEvent.click(screen.getByRole('radio',{name:'Uncertain'}));fireEvent.click(screen.getByRole('button',{name:'Cancel'}));
 expect(close).not.toHaveBeenCalled();fireEvent.click(screen.getByRole('button',{name:'Keep editing'}));
 expect(screen.getByRole('radio',{name:'Uncertain'})).toBeChecked();
 fireEvent.click(screen.getByRole('button',{name:'Close Add missed incident'}));fireEvent.click(screen.getByRole('button',{name:'Discard observation'}));
 expect(close).toHaveBeenCalledTimes(1);expect(window.confirm).not.toHaveBeenCalled();
});
