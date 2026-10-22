"""Local setup, never reachable through the web API."""
import argparse
import getpass
import hashlib
import json
import os
from pathlib import Path
from .auth import configure
from .pipeline import REGISTRY,checkpoint


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['models','password','check'])
    parser.add_argument('--data-dir',default=os.environ.get('MVP_DATA_DIR','var/mvp'))
    args=parser.parse_args();root=Path(args.data_dir).resolve();root.mkdir(parents=True,exist_ok=True)
    if args.action=='password':
        password=getpass.getpass('New operator password (at least 12 characters): ')
        if len(password)<12 or password!=getpass.getpass('Confirm password: '):
            raise SystemExit('Passwords do not match or are shorter than 12 characters.')
        configure(root,password)
        (root/'operator-password.txt').unlink(missing_ok=True)
        print('Password updated. Restart the API to apply it and end old sessions.')
        return
    for alias,entry in REGISTRY.items():
        path=checkpoint(alias,root)
        if args.action=='models' and not path.is_file():
            if alias=='pose':
                from ultralytics import YOLO
                path.parent.mkdir(parents=True,exist_ok=True)
                YOLO(str(path))
            else:
                from huggingface_hub import hf_hub_download
                hf_hub_download(entry['repository'],'best.pt',revision=entry['revision'])
        if not path.is_file():
            raise SystemExit(f'Missing {alias}. Run python -m backend.manage models.')
        with path.open('rb') as handle:
            actual=hashlib.file_digest(handle,'sha256').hexdigest()
        if actual!=entry['sha256']:
            raise SystemExit(f'{alias} SHA256 mismatch. No substitute model will be used.')
        print(f'{alias}: verified')
    if not Path('/usr/bin/avconvert').exists():
        raise SystemExit('Native avconvert is required on this Mac.')
    print('Local model and codec preflight passed.')


if __name__=='__main__':
    main()
