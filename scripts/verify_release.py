"""Verify release file membership and byte integrity without extracting or executing it."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

PREFIX='architecture-diagram-reviewer/'
MANIFEST=PREFIX+'RELEASE_MANIFEST.json'

def verify(path):
    with zipfile.ZipFile(path) as archive:
        if len(archive.namelist())!=len(set(archive.namelist())):raise ValueError('Duplicate ZIP members')
        if archive.testzip() is not None:raise ValueError('Corrupt ZIP member')
        manifest=json.loads(archive.read(MANIFEST))
        names={name for name in archive.namelist() if not name.endswith('/') and name!=MANIFEST}
        if names!=set(manifest['file_sha256']):raise ValueError('Archive membership differs from manifest')
        for name in names:
            relative=Path(name)
            if not name.startswith(PREFIX) or relative.is_absolute() or '..' in relative.parts:
                raise ValueError('Unsafe archive member path')
            if hashlib.sha256(archive.read(name)).hexdigest()!=manifest['file_sha256'][name]:
                raise ValueError('Hash mismatch: '+name)
        print(f'Integrity verified: {len(names)} files, commit {manifest["git_commit"]}')
        print('Integrity is not evidence of live Meta or Docker acceptance.')
        return manifest

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive',type=Path)
    args=parser.parse_args()
    try:verify(args.archive)
    except (ValueError,KeyError,OSError,zipfile.BadZipFile) as exc:parser.exit(1,'Release verification failed: '+str(exc)+'\n')
