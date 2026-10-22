import {it,expect,vi,afterEach} from 'vitest';
import {mutate} from './api';
afterEach(()=>{vi.unstubAllGlobals();sessionStorage.clear();});
it('retries a committed mutation with the same ID and payload after response loss',async()=>{
 const bodies:any[]=[];let lost=true;
 vi.stubGlobal('fetch',vi.fn(async(_path,options)=>{bodies.push(JSON.parse(options.body));if(lost){lost=false;throw new Error('Response lost');}return {ok:true,json:async()=>({id:'saved'})};}));
 await expect(mutate('/jobs/j/incidents',{note:'Observed',start:1})).rejects.toThrow('Response lost');
 await mutate('/jobs/j/incidents',{note:'Observed',start:1});
 expect(bodies[1]).toEqual(bodies[0]);
 await mutate('/jobs/j/incidents',{note:'Observed',start:1});
 expect(bodies[2].request_id).not.toEqual(bodies[1].request_id);
});
