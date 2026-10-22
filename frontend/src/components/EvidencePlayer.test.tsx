import React from 'react';
import {render,cleanup} from '@testing-library/react';
import {afterEach,it,expect,vi} from 'vitest';
import {EvidencePlayer} from './EvidencePlayer';
afterEach(()=>{cleanup();vi.restoreAllMocks();});
it('seeks a single frame rather than ignoring sub-200ms changes',()=>{
 vi.spyOn(HTMLCanvasElement.prototype,'getContext').mockReturnValue(null);
 const upload={metadata:{fps:25,width:640,height:360,duration:3,preview_id:'p',frame_map:[[0,0],[.04,.04],[.08,.08]],frames_preview:[]}} as any;
 const {container,rerender}=render(<EvidencePlayer upload={upload} time={0} onTime={()=>{}}/>);
 rerender(<EvidencePlayer upload={upload} time={.04} onTime={()=>{}}/>);
 expect(container.querySelector('video')!.currentTime).toBeCloseTo(.04);
});
