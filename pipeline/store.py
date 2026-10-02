"""Local immutable store proving activation/rollback semantics.

Not the cloud deployer. Caller must supply a complete, trusted release validator.
"""
import hashlib
import json
import os
import re
import tempfile
from contextlib import contextmanager
from pathlib import Path

class ReleaseStore:
    def __init__(self,root):
        self.root=Path(root);self.objects=self.root/'objects';self.objects.mkdir(parents=True,exist_ok=True)
    @contextmanager
    def lock(self):
        path=self.root/'activation.lock'
        with path.open('x') as lock:lock.write(str(os.getpid()))
        try:yield
        finally:path.unlink(missing_ok=True)
    def _atomic(self,path,data):
        descriptor,name=tempfile.mkstemp(dir=path.parent,prefix='.pending-')
        try:
            with os.fdopen(descriptor,'wb') as out:out.write(data);out.flush();os.fsync(out.fileno())
            os.replace(name,path)
        finally:Path(name).unlink(missing_ok=True)
    def _read(self,identity):
        if not re.fullmatch('[a-f0-9]{64}',identity):raise ValueError('Invalid release identity')
        raw=(self.objects/f'{identity}.json').read_bytes()
        if hashlib.sha256(raw).hexdigest()!=identity:raise ValueError('Release checksum mismatch')
        return json.loads(raw)
    def publish(self,payload,validator):
        with self.lock():
            validator(payload)
            raw=json.dumps(payload,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
            identity=hashlib.sha256(raw).hexdigest();path=self.objects/f'{identity}.json'
            if not path.exists():self._atomic(path,raw)
            else:self._read(identity)
            self._atomic(self.root/'active.json',json.dumps({'id':identity}).encode())
            return identity
    def active(self):
        return self._read(json.loads((self.root/'active.json').read_text())['id'])
    def rollback(self,identity,validator):
        with self.lock():
            validator(self._read(identity))
            self._atomic(self.root/'active.json',json.dumps({'id':identity}).encode())
