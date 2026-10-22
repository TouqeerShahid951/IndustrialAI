"""One local process, guarded by an OS lock; no inference inside HTTP requests."""
import argparse
import fcntl
import os
import time
from pathlib import Path
from .media import Cancelled, prepare_preview
from .storage import Store


class Worker:
    def __init__(self, store):
        self.store=store
        self.lock=(store.root/'worker.lock').open('a+')
        try:
            fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            self.lock.close()
            raise RuntimeError('Another worker already owns this queue')
        store.recover()

    def close(self):
        (self.store.root/'worker.heartbeat').unlink(missing_ok=True)
        fcntl.flock(self.lock,fcntl.LOCK_UN)
        self.lock.close()

    def run_once(self):
        (self.store.root/'worker.heartbeat').write_text(str(time.time()))
        job=self.store.claim()
        if job is None:
            return False
        jid=job['id']
        def progress(stage, processed, expected):
            (self.store.root/'worker.heartbeat').write_text(str(time.time()))
            self.store.update_job(jid,stage=stage,processed=processed,expected=expected)
        def cancelled():
            return bool(self.store.job(jid)['cancel'])
        try:
            if cancelled():
                raise Cancelled()
            if job['kind']=='prepare_upload':
                result=prepare_preview(self.store,self.store.upload(job['upload_id']),progress,cancelled)
                status='completed'
            elif job['kind']=='analyze':
                from .pipeline import analyze
                status,result=analyze(self.store,job,progress,cancelled)
            elif job['kind']=='export':
                from .exports import export_job
                result=export_job(self.store,job,progress,cancelled)
                status='completed'
            else:
                raise ValueError('Unknown queue task')
            self.store.update_job(jid,status=status,result=result,stage=status.title())
        except Cancelled:
            self.store.update_job(jid,status='cancelled',stage='Cancelled')
            if job['kind']=='prepare_upload':
                self.store.update_upload(job['upload_id'],'cancelled')
        except Exception as exc:
            self.store.update_job(jid,status='failed',stage='Failed',error=str(exc)[:400])
            if job['kind']=='prepare_upload':
                self.store.update_upload(job['upload_id'],'failed')
        return True


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--data-dir',default=os.environ.get('MVP_DATA_DIR','var/mvp'))
    args=parser.parse_args()
    worker=Worker(Store(Path(args.data_dir)))
    try:
        while True:
            if not worker.run_once():
                time.sleep(.5)
    except KeyboardInterrupt:
        pass
    finally:
        worker.close()


if __name__=='__main__':
    main()
