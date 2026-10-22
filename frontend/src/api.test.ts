import {describe,it,expect} from 'vitest';
import {clock, toPreview, toSource, jobSummary} from './api';
describe('source-time and honest processing states',()=>{
 it('maps irregular source times without treating preview time as source',()=>{
  const map=[[0,0],[.04,.1],[.2,.2],[.25,.3]];
  expect(toPreview(.12,map)).toBeCloseTo(.15);
  expect(toSource(.15,map)).toBeCloseTo(.12);
 });
 it('distinguishes failure, partial and no candidates',()=>{
  expect(jobSummary({status:'failed',result:{incident_count:0}} as any)).not.toContain('No candidates');
  expect(jobSummary({status:'partial',result:{incident_count:0}} as any)).toContain('Partial');
  expect(jobSummary({status:'completed',result:{incident_count:0}} as any)).toContain('No candidates');
  expect(clock(65)).toBe('01:05');
 });
});
