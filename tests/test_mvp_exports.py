import json
from uuid import uuid4
from tests.test_mvp_reviews import ReviewTests
from backend.exports import export_job


class ExportTests(ReviewTests):
    def test_json_csv_and_private_download(self):
        _,response=self.manual(initial_review={'decision':'uncertain','note':'=1+1'})
        self.assertEqual(response.status_code,201,response.text)
        store=self.client.app.state.store
        for format in ('csv','json'):
            job=store.create_job(self.job['upload_id'],'export',{'format':format,'source_job':self.job['id'],'incident_id':None},str(uuid4()))
            result=export_job(store,job,lambda *a:None,lambda:False)
            url='/api/artifacts/'+result['artifact_id']
            exported=self.client.get(url)
            self.assertEqual(exported.status_code,200)
            if format=='csv':
                self.assertIn("'=1+1",exported.text)
            else:
                self.assertEqual(exported.json()['incidents'][0]['decision'],'uncertain')
            self.client.cookies.clear()
            self.assertEqual(self.client.get(url).status_code,401)
            self.headers=self.login()

    def test_export_progress_finishes_at_the_exact_output_count(self):
        from tests.test_mvp_media import video
        from backend.media import probe
        store=self.client.app.state.store
        video(self.root/'none.mp4',51,10)
        store.update_upload(self.job['upload_id'],'ready',probe(self.root/'none.mp4'))
        _,response=self.manual(start=1,end=2)
        for format in ('json','csv','mp4'):
            job=store.create_job(self.job['upload_id'],'export',{'format':format,'source_job':self.job['id'],'incident_id':response.json()['id']},str(uuid4()))
            progress=[]
            result=export_job(store,job,lambda *values:progress.append(values),lambda:False)
            self.assertTrue(progress,format)
            self.assertEqual(progress[-1][1],progress[-1][2],format)
            if format=='mp4':
                artifact=store.one('SELECT path FROM artifacts WHERE id=?',(result['manifest_id'],))
                count=len(json.loads((self.root/artifact['path']).read_text())['clip']['frame_map'])
                self.assertEqual(progress[-1][1],count)
