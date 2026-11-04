"""Build a source-only release from committed Git files, including auditable history."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import tomllib
import zipfile

ROOT=Path(__file__).resolve().parents[1]
PREFIX='architecture-diagram-reviewer/'

def git(*args):
    return subprocess.run(['git',*args],cwd=ROOT,check=True,capture_output=True,text=True).stdout.strip()

def build(output):
    if git('status','--porcelain'):
        raise ValueError('Commit or remove working changes before building a release.')
    revision=git('rev-parse','HEAD')
    if revision != git('rev-parse','refs/heads/main'):
        raise ValueError('Release HEAD must match main so the archive and publisher use the same revision.')
    output=output.resolve();output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='archreview-release-') as directory:
        bundle=Path(directory)/'repository.bundle'
        git('bundle','create',str(bundle),'refs/heads/main')
        git('bundle','verify',str(bundle))
        if git('bundle','list-heads',str(bundle),'refs/heads/main').split()[0] != revision:
            raise ValueError('main changed during release preparation. Retry from a clean checkout.')
        git('archive','--format=zip','--prefix='+PREFIX,'--output='+str(output),revision)
        with zipfile.ZipFile(output,'a',zipfile.ZIP_DEFLATED) as archive:
            archive.write(bundle,PREFIX+'repository.bundle')
            hashes={name:hashlib.sha256(archive.read(name)).hexdigest() for name in archive.namelist() if not name.endswith('/')}
            manifest={'release_version':tomllib.loads((ROOT/'pyproject.toml').read_text())['project']['version'],'git_commit':revision,'file_sha256':hashes,
                'live_meta_acceptance':'not_verified','clean_docker_acceptance':'not_verified'}
            archive.writestr(PREFIX+'RELEASE_MANIFEST.json',json.dumps(manifest,indent=2))
    print(str(output))
    print('SHA256 '+hashlib.sha256(output.read_bytes()).hexdigest())

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT.parent/'architecture-diagram-reviewer-final.zip')
    args=parser.parse_args()
    try:build(args.output)
    except (ValueError,subprocess.CalledProcessError) as exc:
        parser.exit(1,'Release build failed: '+str(exc)+'\n')
