"""Single-operator password and signed, expiring session cookies using stdlib."""
import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from pathlib import Path


def configure(root, password=None):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    path = root/'settings.json'
    if path.exists() and password is None:
        return json.loads(path.read_text())
    salt = secrets.token_hex(16)
    if password is None:
        password = secrets.token_urlsafe(18)
        credentials = root/'operator-password.txt'
        credentials.write_text(password+'\n')
        credentials.chmod(0o600)
    result = {'salt': salt, 'password_hash': hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1).hex(),
              'secret': secrets.token_hex(32)}
    path.write_text(json.dumps(result))
    path.chmod(0o600)
    return result


def password_matches(password, settings):
    computed = hashlib.scrypt(password.encode(), salt=settings['salt'].encode(), n=16384, r=8, p=1).hex()
    return hmac.compare_digest(computed, settings['password_hash'])


def revoke_sessions(root, settings):
    settings['secret']=secrets.token_hex(32)
    path=Path(root)/'settings.json'
    temporary=path.with_suffix('.'+secrets.token_hex(6)+'.tmp')
    descriptor=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    try:
        with os.fdopen(descriptor,'w') as handle:
            json.dump(settings,handle)
        os.replace(temporary,path)
    finally:
        temporary.unlink(missing_ok=True)


def sign(value, secret):
    return hmac.new(secret.encode(), value.encode(), hashlib.sha256).hexdigest()


def issue(settings):
    csrf = secrets.token_urlsafe(24)
    value = base64.urlsafe_b64encode(json.dumps({'exp': time.time()+43200, 'csrf': csrf}).encode()).decode()
    return value+'.'+sign(value, settings['secret']), csrf


def verify(cookie, settings):
    try:
        value, signature = cookie.split('.')
        if not hmac.compare_digest(sign(value, settings['secret']), signature):
            return None
        session = json.loads(base64.urlsafe_b64decode(value))
        return session if session['exp'] > time.time() else None
    except (ValueError, KeyError, TypeError):
        return None
