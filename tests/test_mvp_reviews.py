from uuid import uuid4
from tests.test_mvp_api import APITests


class ReviewTests(APITests):
    def setUp(self):
        super().setUp()
        self.headers=self.login()
        store=self.client.app.state.store
        upload=store.add_upload('clip.mp4','none.mp4','hash',1,{'duration':20})
        self.job=store.create_job(upload['id'],'analyze',{'capabilities':['smoke']},str(uuid4()))
        store.update_job(self.job['id'],status='completed')

    def manual(self, **extra):
        body={'request_id':str(uuid4()),'kind':'smoke','start':3,'end':8,'initial_review':{'decision':'uncertain','note':'plume unclear'}} | extra
        return body,self.client.post('/api/jobs/'+self.job['id']+'/incidents',json=body,headers=self.headers)

    def test_manual_review_idempotency_and_audit(self):
        body,response=self.manual()
        self.assertEqual(response.status_code,201,response.text)
        incident=response.json()
        self.assertEqual(incident['origin'],'manual')
        duplicate=self.client.post('/api/jobs/'+self.job['id']+'/incidents',json=body,headers=self.headers)
        self.assertEqual(duplicate.json()['id'],incident['id'])
        review={'request_id':str(uuid4()),'decision':'false_alarm','note':'review corrected','expected_version':1}
        url='/api/incidents/'+incident['id']+'/reviews'
        self.assertEqual(self.client.post(url,json=review,headers=self.headers).status_code,200)
        self.assertEqual(self.client.post(url,json=review,headers=self.headers).json()['version'],2)
        stale=dict(review,request_id=str(uuid4()))
        self.assertEqual(self.client.post(url,json=stale,headers=self.headers).status_code,409)
        store=self.client.app.state.store
        self.assertEqual(len(store.query('SELECT * FROM reviews WHERE incident_id=?',(incident['id'],))),2)
        from backend.storage import Store
        self.assertEqual(Store(self.root).incidents()[0]['decision'],'false_alarm')

    def test_invalid_intervals_and_notes_rollback(self):
        for extra in [{'end':2},{'end':25},{'start':-1},{'initial_review':{'decision':'uncertain','note':'x'*1001}}]:
            _,response=self.manual(**extra)
            self.assertEqual(response.status_code,422,response.text)
        self.assertEqual(self.client.app.state.store.incidents(),[])
