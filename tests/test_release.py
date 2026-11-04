import hashlib
import importlib.util
import json
from pathlib import Path
import zipfile
import pytest

spec=importlib.util.spec_from_file_location('release_verify',Path(__file__).resolve().parents[1]/'scripts/verify_release.py')
verifier=importlib.util.module_from_spec(spec);spec.loader.exec_module(verifier)

def release(tmp_path,mode='valid'):
    path=tmp_path/'release.zip';name=verifier.PREFIX+'README.md';content=b'test release\n'
    manifest={'git_commit':'test-commit','file_sha256':{name:hashlib.sha256(content).hexdigest()}}
    with zipfile.ZipFile(path,'w') as z:
        z.writestr(name,b'tampered' if mode=='tampered' else content)
        if mode=='extra':z.writestr(verifier.PREFIX+'unexpected.py','extra')
        z.writestr(verifier.MANIFEST,json.dumps(manifest))
    return path

def test_release_integrity(tmp_path):
    assert verifier.verify(release(tmp_path))['git_commit']=='test-commit'

@pytest.mark.parametrize('mode',['tampered','extra'])
def test_release_rejects_changed_or_added_files(tmp_path,mode):
    with pytest.raises(ValueError):verifier.verify(release(tmp_path,mode))
