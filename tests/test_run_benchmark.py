import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from scripts.benchmark_data import file_sha256
from scripts.run_benchmark import build_report, recording


class BenchmarkPipelineChecks(unittest.TestCase):
    def test_observations_provenance_coverage_and_incomplete_runs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            media = root/'clip.avi';media.write_bytes(b'fixture media')
            labels = root/'labels.json'
            labels.write_text(json.dumps({'review_status':'single_reviewer','events':[], 'reviewed_intervals':{'fire':[[0,2]],'smoke':[[0,2]]}}))
            manifest = root/'manifest.jsonl'
            clip = dict(clip_id='sample',local_path=str(media),annotation_path=str(labels),source_sha256=file_sha256(media),camera_id='cam',site_id='site',source_event_id='event',split='development',capture_origin='unverified_demo',permission_status='review_needed',duration_seconds=2,conditions=['orange_workwear'])
            manifest.write_text(json.dumps(clip)+'\n')
            run = root/'run';run.mkdir()
            weights = root/'weights.pt';weights.write_bytes(b'weights')
            summary = [dict(source=str(media),model='fire_smoke',frames=4,stride=1,source_fps=2)]
            (run/'summary.json').write_text(json.dumps(summary))
            with (run/'frames.csv').open('w',newline='') as f:
                writer=csv.writer(f);writer.writerow(['source','model','frame','source_seconds','predict_seconds','status','timestamp_basis'])
                for index in range(4):writer.writerow([str(media),'fire_smoke',index,index*.5,.01,'ok','container'])
            with (run/'detections.csv').open('w',newline='') as f:
                writer=csv.writer(f);writer.writerow(['source','model','frame','source_seconds','class','confidence','x1','y1','x2','y2'])
                for index in range(4):writer.writerow([str(media),'fire_smoke',index,index*.5,'fire',.9,0,0,10,10])
            metadata=dict(status='complete',source_hashes={str(media):file_sha256(media)},checkpoints={'fire_smoke':dict(path=str(weights),sha256=file_sha256(weights))},configuration={'timestamp_source':'container'},code_hashes={'evaluate.py':'a'*64})
            def save_metadata():
                metadata['artifacts']={name:file_sha256(run/name) for name in ('summary.json','frames.csv','detections.csv')}
                (run/'metadata.json').write_text(json.dumps(metadata))
            save_metadata()
            report=build_report(manifest,[run])
            fire=report['per_capability']['fire']
            self.assertEqual(fire['policies']['timed']['FP'],1)
            self.assertAlmostEqual(fire['coverage_seconds'],2)
            self.assertFalse(report['gate_passed'])
            self.assertEqual(report['per_capability']['smoking']['status'],'not_annotated')
            annotation_hash = report['scoring_provenance']['annotation_sha256']['sample']
            self.assertIn('temporal.py', report['scoring_provenance']['code_hashes'])
            self.assertEqual(report['scoring_provenance']['parameters']['timed']['min_span_seconds'], 1.0)
            annotation = json.loads(labels.read_text())
            annotation['excluded_intervals'] = [dict(kind='smoke',start_seconds=0,end_seconds=2,reason='ambiguous')]
            labels.write_text(json.dumps(annotation))
            changed = build_report(manifest,[run])
            self.assertEqual(changed['per_capability']['fire']['policies']['timed']['FP'],1)
            self.assertEqual(changed['per_capability']['fire']['coverage_seconds'],2)
            self.assertEqual(changed['per_capability']['smoke']['coverage_seconds'],0)
            self.assertNotEqual(changed['scoring_provenance']['annotation_sha256']['sample'],annotation_hash)
            annotation['frames'] = [dict(time_seconds=0,review_status='reviewed',image_width=20,image_height=20,
                                          objects=[dict(**{'class':'helmet'},bbox_xyxy=[0,0,10,10])])]
            labels.write_text(json.dumps(annotation))
            helmet_run = root/'helmet-run';shutil.copytree(run,helmet_run)
            for name in ('frames.csv','detections.csv','summary.json'):
                path = helmet_run/name
                path.write_text(path.read_text().replace('fire_smoke','helmet').replace(',fire,',',Hardhat,').replace(',0,0,10,10',',4,0,14,10'))
            helmet_metadata = dict(metadata,checkpoints={'helmet':metadata['checkpoints']['fire_smoke']},
                                   artifacts={name:file_sha256(helmet_run/name) for name in ('frames.csv','detections.csv','summary.json')})
            (helmet_run/'metadata.json').write_text(json.dumps(helmet_metadata))
            heads = build_report(manifest,[run,helmet_run])['head_objects']
            self.assertEqual(next(h['TP'] for h in heads if h['category']=='helmet' and h['iou_threshold']==.3),1)
            self.assertEqual(next(h['FN'] for h in heads if h['category']=='helmet' and h['iou_threshold']==.5),1)
            with (run/'frames.csv').open('a') as f:f.write('changed\n')
            with self.assertRaisesRegex(ValueError,'hash'):
                build_report(manifest,[run])
            metadata['status']='running';save_metadata()
            with self.assertRaisesRegex(ValueError,'complete'):
                build_report(manifest,[run])

    def test_truncated_recording_has_only_one_sample_of_coverage(self):
        clip = dict(local_path='/tmp/clip.avi',duration_seconds=1,clip_id='clip')
        summary = dict(model='fire_smoke',frames=1,stride=1,source_fps=30)
        observations = [dict(source='/tmp/clip.avi',model='fire_smoke',frame='0',source_seconds='0',predict_seconds='.01',status='ok',timestamp_basis='container')]
        rec = recording(clip,summary,[],observations)
        self.assertEqual(rec['coverage'],[[0,1/30]])
