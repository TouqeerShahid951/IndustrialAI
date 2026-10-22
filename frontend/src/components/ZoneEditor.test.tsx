import React,{useState} from 'react';
import {render,fireEvent,cleanup} from '@testing-library/react';
import {it,expect,vi,afterEach} from 'vitest';
import {ZoneEditor} from './ZoneEditor';
afterEach(cleanup);
it('keeps keyboard selection valid after undo and at the point limit',()=>{
 vi.stubGlobal('ResizeObserver',class{observe(){}disconnect(){}});
 vi.spyOn(HTMLCanvasElement.prototype,'getContext').mockReturnValue(null);
 function Editor(){const [zone,setZone]=useState({name:'bay',points:[[.1,.1],[.2,.2]] as [number,number][]});return <><ZoneEditor editing zone={zone} onChange={setZone}/><button onClick={()=>setZone({...zone,points:zone.points.slice(0,-1)})}>Undo</button><output>{JSON.stringify(zone.points)}</output></>;}
 const view=render(<Editor/>),canvas=view.getByLabelText(/Restricted zone editor/);
 fireEvent.keyDown(canvas,{key:'Enter'});fireEvent.click(view.getByText('Undo'));fireEvent.keyDown(canvas,{key:'ArrowRight'});fireEvent.keyDown(canvas,{key:'Enter'});
 expect(JSON.parse(view.container.querySelector('output')!.textContent!)).toHaveLength(3);
 for(let i=0;i<35;i++)fireEvent.keyDown(canvas,{key:'Enter'});
 fireEvent.keyDown(canvas,{key:'ArrowRight'});
 expect(JSON.parse(view.container.querySelector('output')!.textContent!)).toHaveLength(32);
});
