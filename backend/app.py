import hmac
import os
import time
from collections import defaultdict
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
from .auth import configure, issue, password_matches, verify
from .schemas import Login
from .storage import Store


def create_app(data_dir=None):
    root = Path(data_dir or os.environ.get('MVP_DATA_DIR', 'var/mvp')).resolve()
    store = Store(root)
    settings = configure(root)
    app = FastAPI(title='Industrial AI', version='0.1.0', docs_url=None, redoc_url=None)
    app.state.store = store
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
        response = JSONResponse({'status': 'signed_out'})
        response.delete_cookie('industrial_session')
        return response

    @app.get('/api/uploads')
    def uploads():
        return []

    @app.get('/api/jobs/{jid}')
    def job(jid: str):
        result = store.job(jid)
        if not result:
            raise HTTPException(404, 'Job not found')
        return result

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

    return app
