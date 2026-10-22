import React from 'react';
import {render,screen,fireEvent,waitFor,cleanup} from '@testing-library/react';
import {afterEach,it,expect,vi} from 'vitest';
import {Progress} from './Uploads';
afterEach(()=>{cleanup();vi.restoreAllMocks();});
it('shows a failed job without claiming a negative result and exposes retry',async()=>{
 vi.stubGlobal('fetch',vi.fn(async(url:string)=>({ok:true,json:async()=>url.includes('/jobs/')?{id:'j',upload_id:'u',kind:'analyze',status:'failed',stage:'Failed',processed:3,expected:10,error:'Detector unavailable',result:{},config:{}}:{id:'u',name:'clip.mp4',metadata:{duration:2}}})));
 render(<Progress id="j"/>);
 expect(await screen.findByRole('heading',{name:'Failed'})).toBeVisible();
 expect(screen.getByRole('alert')).toHaveTextContent('Detector unavailable');
 expect(screen.queryByText(/No candidates detected/)).not.toBeInTheDocument();
 expect(screen.getByRole('button',{name:'Retry as new job'})).toBeEnabled();
});
it('sends a real cancellation request and preserves the resulting status',async()=>{
 const fetcher=vi.fn(async(url:string,options:any)=>({ok:true,json:async()=>url.endsWith('/cancel')?{id:'j',upload_id:'u',kind:'analyze',status:'cancelled',stage:'Cancelled',processed:3,expected:10,result:{},config:{}}:url.includes('/jobs/')?{id:'j',upload_id:'u',kind:'analyze',status:'running',stage:'Checking frames',processed:3,expected:10,result:{},config:{}}:{id:'u',name:'clip.mp4',metadata:{duration:2}}}));
 vi.stubGlobal('fetch',fetcher);render(<Progress id="j"/>);
 fireEvent.click(await screen.findByRole('button',{name:'Cancel analysis'}));
 await waitFor(()=>expect(fetcher.mock.calls.some(([url,options])=>url==='/api/jobs/j/cancel'&&options.method==='POST')).toBe(true));
 expect(await screen.findByRole('heading',{name:'Cancelled'})).toBeVisible();
});
