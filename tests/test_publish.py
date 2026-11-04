import importlib.util
from pathlib import Path
import shutil
import subprocess
import pytest

spec=importlib.util.spec_from_file_location('release_publish',Path(__file__).resolve().parents[1]/'scripts/publish.py')
publisher=importlib.util.module_from_spec(spec);spec.loader.exec_module(publisher)

def git(root,*args):
    return subprocess.run(['git',*args],cwd=root,check=True,capture_output=True,text=True).stdout.strip()

@pytest.mark.parametrize('url',['https://user:secret@github.com/owner/repo','https://elsewhere.test/owner/repo','https://github.com/owner/repo?token=secret','-option'])
def test_publish_rejects_unsafe_destinations(url,monkeypatch):
    monkeypatch.setattr(publisher,'git',lambda *a,**k:pytest.fail('Git must not run'))
    with pytest.raises(ValueError):publisher.publish(url)

def test_packaged_bundle_can_be_restored_without_network_or_push(tmp_path,monkeypatch,capsys):
    source=tmp_path/'source';source.mkdir()
    git(source,'init','-b','main');git(source,'config','user.name','Release Test');git(source,'config','user.email','test@example.invalid')
    (source/'.gitignore').write_text('repository.bundle\n')
    (source/'README.md').write_text('test project\n')
    (source/'start-demo.sh').write_text('#!/bin/sh\necho demo\n')
    (source/'start-demo.sh').chmod(0o755)
    git(source,'add','.');git(source,'update-index','--chmod=+x','start-demo.sh');git(source,'commit','-m','test source')
    destination=tmp_path/'delivery';destination.mkdir()
    for name in ('.gitignore','README.md','start-demo.sh'):shutil.copyfile(source/name,destination/name)
    git(source,'bundle','create',str(destination/'repository.bundle'),'--all')
    monkeypatch.setattr(publisher,'ROOT',destination)
    publisher.publish('https://github.com/example/architecture-demo.git',False)
    assert git(destination,'branch','--show-current')=='main'
    assert git(destination,'status','--porcelain')==''
    assert git(destination,'rev-parse','HEAD')==git(source,'rev-parse','HEAD')
    assert git(destination,'remote','get-url','publish')=='https://github.com/example/architecture-demo.git'
    assert 'No push performed' in capsys.readouterr().out
    with pytest.raises(ValueError):publisher.publish('https://github.com/example/different.git')
