import hmac
import os
import time
import asyncio
from collections import defaultdict
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
from .auth import configure, issue, password_matches, verify, revoke_sessions
from .schemas import Login, Analysis, UploadRecord, JobRecord, IncidentRecord, Review, ManualIncident, Export
from .storage import Store, TERMINAL


def create_app(data_dir=None):
    root = Path(data_dir or os.environ.get('MVP_DATA_DIR', 'var/mvp')).resolve()
    store = Store(root)
    settings = configure(root)
    app = FastAPI(title='Industrial AI', version='0.1.0', docs_url=None, redoc_url=None)
    app.state.store = store
    admission_lock = asyncio.Lock()
    attempts = defaultdict(list)

    @app.middleware('http')
    async def access(request: Request, call_next):
        path = request.url.path
        public = path == '/api/health' or (path == '/api/session' and request.method == 'POST')
        if request.method not in ('GET', 'HEAD'):
            origin = request.headers.get('origin')
            if origin and origin != str(request.base_url).rstrip('/'):
                return JSONResponse({'detail': 'Cross-origin writes are not allowed'}, 403)
        if path.startswith('/api/') and not public:
            session = verify(request.cookies.get('industrial_session', ''), settings)
            if not session:
                return JSONResponse({'detail': 'Sign in to continue'}, 401)
            if request.method not in ('GET', 'HEAD') and not hmac.compare_digest(request.headers.get('x-csrf-token', ''), session['csrf']):
                return JSONResponse({'detail': 'Invalid session token. Reload and sign in.'}, 403)
            request.state.session = session
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'same-origin'
        response.headers['Content-Security-Policy'] = "default-src 'self'; img-src 'self' blob: data:; media-src 'self' blob:; style-src 'self' 'unsafe-inline'; script-src 'self'; frame-ancestors 'none'"
        if path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-store'
        return response

    @app.get('/api/health')
    def health():
        return {'status': 'ok', 'version': '0.1.0'}

    @app.post('/api/session')
    def login(body: Login, request: Request):
        address = request.client.host
        recent = [t for t in attempts[address] if t > time.monotonic()-300]
        attempts[address] = recent
        if len(recent) >= 10:
            raise HTTPException(429, 'Too many attempts. Try again in five minutes.')
        if not password_matches(body.password, settings):
            recent.append(time.monotonic())
            raise HTTPException(401, 'Incorrect operator password')
        attempts.pop(address, None)
        cookie, csrf = issue(settings)
        response = JSONResponse({'csrf': csrf})
        response.set_cookie('industrial_session', cookie, httponly=True, samesite='strict', secure=request.url.scheme == 'https', max_age=43200)
        return response

    @app.get('/api/session')
    def session(request: Request):
        return {'csrf': request.state.session['csrf']}

    @app.delete('/api/session')
    def logout():
        revoke_sessions(root,settings)
        response = JSONResponse({'status': 'signed_out'})
        response.delete_cookie('industrial_session')
        return response

    @app.get('/api/uploads', response_model=list[UploadRecord])
    def uploads():
        return [public_upload(u) for u in store.query('SELECT * FROM uploads ORDER BY created DESC')]

    def public_upload(upload, detail=False):
        result={k:v for k,v in upload.items() if k != 'path'}
        if not detail:
            result['metadata']={k:v for k,v in upload['metadata'].items() if k not in ('frame_map','frames_preview')}
        return result | {'jobs':store.query('SELECT * FROM jobs WHERE upload_id=? ORDER BY created DESC',(upload['id'],))}

    @app.post('/api/uploads', status_code=202)
    async def upload(request: Request):
        from .media import admit_upload
        async with admission_lock:
            return await admit_upload(store,request.stream(),request.headers.get('x-upload-name',''))

    @app.get('/api/uploads/{uid}', response_model=UploadRecord)
    def upload_detail(uid: str):
        result=store.upload(uid)
        if not result:
            raise HTTPException(404,'Upload not found')
        return public_upload(result,True)

    @app.get('/api/capabilities')
    def capabilities():
        from .pipeline import REGISTRY,checkpoint
        heartbeat=root/'worker.heartbeat'
        return {'capabilities':['fire','smoke','smoking','no_helmet','intrusion'],
                'models':{key:{'available':checkpoint(key,root).is_file(),'sha256':entry['sha256']} for key,entry in REGISTRY.items()},
                'worker_available':heartbeat.exists() and time.time()-heartbeat.stat().st_mtime<120,
                'limits':{'max_bytes':250*1024**2,'max_seconds':300,'max_width':1920,'max_height':1080,'max_fps':60}}

    @app.post('/api/uploads/{uid}/jobs', response_model=JobRecord, status_code=202)
    def start_analysis(uid: str, body: Analysis):
        upload=store.upload(uid)
        if not upload:
            raise HTTPException(404,'Upload not found')
        if upload['status']!='ready':
            raise HTTPException(409,'Wait for a ready preview before starting analysis.')
        from .rules import validate_zone
        try:
            for zone in body.zones:
                validate_zone(zone.points)
            if 'intrusion' in body.capabilities and not body.zones:
                raise ValueError('Draw and finish a restricted zone before starting analysis.')
            if len(set(body.capabilities))!=len(body.capabilities):
                raise ValueError('Choose each detection only once.')
            if body.device=='mps':
                import torch
                if not torch.backends.mps.is_available():
                    raise ValueError('MPS is unavailable. Explicitly select CPU to analyze on this computer.')
            config=body.model_dump(mode='json',exclude={'request_id'})
            from .pipeline import PROFILE,REGISTRY
            config['profile']=PROFILE
            config['models']={k:v['sha256'] for k,v in REGISTRY.items()}
            return store.create_job(uid,'analyze',config,str(body.request_id))
        except ValueError as exc:
            raise HTTPException(422,str(exc)) from exc

    @app.get('/api/jobs/{jid}', response_model=JobRecord)
    def job(jid: str):
        result = store.job(jid)
        if not result:
            raise HTTPException(404, 'Job not found')
        return result

    @app.post('/api/jobs/{jid}/cancel', response_model=JobRecord)
    def cancel(jid: str):
        with store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            result=db.execute('SELECT * FROM jobs WHERE id=?',(jid,)).fetchone()
            if not result:
                raise HTTPException(404,'Job not found')
            if result['status']=='queued':
                db.execute("UPDATE jobs SET cancel=1,status='cancelled',stage='Cancelled' WHERE id=?",(jid,))
                if result['kind']=='prepare_upload':
                    db.execute("UPDATE uploads SET status='cancelled' WHERE id=?",(result['upload_id'],))
            elif result['status']=='running':
                db.execute('UPDATE jobs SET cancel=1 WHERE id=?',(jid,))
        return store.job(jid)

    @app.get('/api/jobs/{jid}/incidents', response_model=list[IncidentRecord])
    def incidents(jid: str):
        if not store.job(jid):
            raise HTTPException(404,'Job not found')
        return store.incidents(jid)

    @app.get('/api/incidents', response_model=list[IncidentRecord])
    def history():
        return store.incidents()

    @app.post('/api/jobs/{jid}/incidents', response_model=IncidentRecord, status_code=201)
    def missed(jid: str, body: ManualIncident):
        job=store.job(jid)
        if not job:
            raise HTTPException(404,'Job not found')
        if job['kind']!='analyze' or job['status'] not in TERMINAL:
            raise HTTPException(409,'Wait until analysis stops before adding an observation.')
        duration=store.upload(job['upload_id'])['metadata']['duration']
        if not 0<=body.start<body.end<=duration:
            raise HTTPException(422,'Choose an interval within the original source duration.')
        evidence={'label':'manually observed '+body.kind.value,'level':'human observation','initial_review':body.initial_review.model_dump()}
        try:
            iid=store.add_incident(jid,body.kind.value,body.start,body.end,evidence,'manual',str(body.request_id),body.initial_review.model_dump())
        except ValueError as exc:
            raise HTTPException(409,str(exc)) from exc
        return next(i for i in store.incidents(jid) if i['id']==iid)

    @app.post('/api/incidents/{iid}/reviews')
    def review(iid: str, body: Review):
        if not store.one('SELECT id FROM incidents WHERE id=?',(iid,)):
            raise HTTPException(404,'Incident not found')
        try:
            return store.review(iid,body.decision,body.note,body.expected_version,str(body.request_id))
        except ValueError as exc:
            raise HTTPException(409,str(exc)) from exc

    @app.get('/api/incidents/{iid}/reviews')
    def review_history(iid: str):
        return store.query('SELECT * FROM reviews WHERE incident_id=? ORDER BY version DESC',(iid,))

    @app.post('/api/jobs/{jid}/exports', response_model=JobRecord, status_code=202)
    def export(jid: str, body: Export):
        job=store.job(jid)
        if not job:
            raise HTTPException(404,'Job not found')
        if job['kind']!='analyze' or job['status'] not in TERMINAL:
            raise HTTPException(409,'Finish or cancel analysis before exporting.')
        if body.format=='mp4' and body.incident_id is None:
            raise HTTPException(422,'Select one incident for an evidence clip.')
        if body.incident_id and not store.one('SELECT id FROM incidents WHERE id=? AND job_id=?',(str(body.incident_id),jid)):
            raise HTTPException(422,'Incident does not belong to this analysis.')
        config={'format':body.format,'incident_id':str(body.incident_id) if body.incident_id else None,'source_job':jid}
        try:
            return store.create_job(job['upload_id'],'export',config,str(body.request_id))
        except ValueError as exc:
            raise HTTPException(409,str(exc)) from exc

    @app.post('/api/jobs/{jid}/retry', response_model=JobRecord, status_code=202)
    def retry(jid: str, body: dict):
        from uuid import UUID
        job=store.job(jid)
        if not job:
            raise HTTPException(404,'Job not found')
        if job['status'] not in ('failed','cancelled','interrupted','partial'):
            raise HTTPException(409,'Only stopped or partial jobs can be retried.')
        try:
            request_id=str(UUID(body.get('request_id','')))
            new=store.create_job(job['upload_id'],job['kind'],job['config'],request_id)
        except (ValueError,TypeError,AttributeError) as exc:
            raise HTTPException(422,'A new valid request ID is required.') from exc
        if job['kind']=='prepare_upload':
            store.update_upload(job['upload_id'],'preparing')
        return new

    @app.get('/api/storage')
    def storage_status():
        from .media import capacity,QUOTA,MIN_FREE
        import shutil
        used=sum(p.stat().st_size for p in root.rglob('*') if p.is_file())
        return {'used':used,'quota':QUOTA,'free':shutil.disk_usage(root).free,'minimum_free':MIN_FREE}

    @app.delete('/api/uploads/{uid}')
    def delete_upload(uid: str):
        upload=store.upload(uid)
        if not upload:
            raise HTTPException(404,'Upload not found')
        with store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute("SELECT id FROM jobs WHERE upload_id=? AND status IN ('queued','running')",(uid,)).fetchone():
                raise HTTPException(409,'Cancel active jobs before deleting this upload.')
            db.execute("UPDATE uploads SET status='deleting' WHERE id=?",(uid,))
        paths=[upload['path']]+[a['path'] for a in store.query('SELECT path FROM artifacts WHERE upload_id=?',(uid,))]
        # Failed/interrupted passes can have unregistered partial files; each job owns its directory.
        for job in store.query('SELECT id FROM jobs WHERE upload_id=?',(uid,)):
            for folder in ('analysis','exports'):
                directory=root/folder/job['id']
                if directory.exists():
                    paths.extend(str(p.relative_to(root)) for p in directory.rglob('*') if p.is_file())
        try:
            for relative in paths:
                path=(root/relative).resolve()
                if not path.is_relative_to(root) or path==root:
                    raise OSError('Invalid artifact binding')
                path.unlink(missing_ok=True)
        except OSError as exc:
            raise HTTPException(507,'Cleanup could not finish. Retry Delete after freeing space or checking file access.') from exc
        with store.connect() as db:
            db.execute('DELETE FROM uploads WHERE id=?',(uid,))
        return {'status':'deleted'}

    @app.get('/api/jobs/{jid}/observations')
    def observations(jid: str, start: float=0, end: float=2):
        import json,math
        result=store.job(jid)
        if not result:
            raise HTTPException(404,'Job not found')
        if not all(math.isfinite(t) for t in (start,end)) or not 0<=start<end or end-start>2.01:
            raise HTTPException(422,'Request a source interval of at most two seconds.')
        rows=[]
        for aid in result['result'].get('raw_artifacts',{}).values():
            artifact=store.one('SELECT * FROM artifacts WHERE id=?',(aid,))
            if artifact:
                with (root/artifact['path']).open() as handle:
                    for line in handle:
                        row=json.loads(line)
                        if row['time']>end:
                            break
                        if row['time']>=start:
                            rows.append(row)
        return rows

    @app.get('/api/artifacts/{aid}')
    def artifact(aid: str, request: Request):
        result = store.one('SELECT * FROM artifacts WHERE id=?', (aid,))
        if not result:
            raise HTTPException(404, 'Artifact not found')
        path = (root/result['path']).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise HTTPException(404, 'Artifact unavailable')
        # One range is enough for browser seeking and bounds multi-range parsing.
        if ',' in request.headers.get('range', ''):
            raise HTTPException(416, 'Request one byte range at a time')
        return FileResponse(path, media_type=result['mime'], filename=result['name'], content_disposition_type='inline' if result['kind'] in ('preview', 'thumbnail', 'frame') else 'attachment')

    frontend=Path(__file__).resolve().parents[1]/'frontend/dist/client'
    @app.get('/{path:path}', include_in_schema=False)
    def static(path: str):
        if path.startswith('api/'):
            raise HTTPException(404,'API endpoint not found')
        target=(frontend/path).resolve()
        if target.is_relative_to(frontend) and target.is_file():
            return FileResponse(target)
        if (frontend/'index.html').is_file():
            return FileResponse(frontend/'index.html')
        raise HTTPException(503,'Frontend has not been built. Run npm --prefix frontend run build.')

    return app
