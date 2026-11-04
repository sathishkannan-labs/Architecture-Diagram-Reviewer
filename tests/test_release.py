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


def test_release_bundles_only_main_and_matches_published_revision(tmp_path,monkeypatch):
    import subprocess
    import shutil
    builder_spec=importlib.util.spec_from_file_location('release_builder',Path(__file__).resolve().parents[1]/'scripts/make_release.py')
    builder=importlib.util.module_from_spec(builder_spec);builder_spec.loader.exec_module(builder)
    source=tmp_path/'source';source.mkdir()
    def git(*args):return subprocess.check_output(['git',*args],cwd=source,text=True).strip()
    git('init','-b','main');git('config','user.name','Release Test');git('config','user.email','test@example.invalid')
    (source/'.gitignore').write_text('repository.bundle\nRELEASE_MANIFEST.json\n')
    (source/'pyproject.toml').write_text('[project]\nversion="test"\n')
    (source/'README.md').write_text('public main revision\n')
    git('add','.');git('commit','-m','public revision');main=git('rev-parse','HEAD')
    git('checkout','-b','private-draft')
    (source/'private-draft.txt').write_text('unpublished test-only content')
    git('add','.');git('commit','-m','unpublished draft');draft=git('rev-parse','HEAD')
    monkeypatch.setattr(builder,'ROOT',source)
    with pytest.raises(ValueError,match='HEAD must match main'):builder.build(tmp_path/'rejected.zip')
    git('checkout','main')
    output=tmp_path/'release.zip';builder.build(output)
    with zipfile.ZipFile(output) as z:
        manifest=json.loads(z.read(builder.PREFIX+'RELEASE_MANIFEST.json'))
        assert manifest['git_commit']==main
        assert z.read(builder.PREFIX+'README.md')==b'public main revision\n'
        assert builder.PREFIX+'private-draft.txt' not in z.namelist()
        bundle=tmp_path/'repository.bundle';bundle.write_bytes(z.read(builder.PREFIX+'repository.bundle'))
        assert git('bundle','list-heads',str(bundle))==main+' refs/heads/main'
        destination=tmp_path/'restored';z.extractall(destination)
    pub_spec=importlib.util.spec_from_file_location('release_publisher',Path(__file__).resolve().parents[1]/'scripts/publish.py')
    pub=importlib.util.module_from_spec(pub_spec);pub_spec.loader.exec_module(pub)
    root=destination/'architecture-diagram-reviewer';monkeypatch.setattr(pub,'ROOT',root)
    pub.publish('https://github.com/example/demo.git',False)
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()==main
    result=subprocess.run(['git','cat-file','-e',draft],cwd=root,capture_output=True)
    assert result.returncode!=0
