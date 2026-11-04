"""Publish the packaged history to a user-specified empty GitHub repository.
Requires the user's normal Git credentials. Does not create repositories, overwrite
remotes, force-push, rewrite history or commit unreviewed working files.
"""
import argparse
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]

def git(*args, capture=False):
    result=subprocess.run(['git',*args],cwd=ROOT,check=True,text=True,
                          stdout=subprocess.PIPE if capture else None)
    return result.stdout.strip() if capture else None

def publish(repository, push=False):
    if not re.fullmatch(r'https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?',repository):
        raise ValueError('Use an HTTPS GitHub repository URL without credentials or query parameters.')
    if not (ROOT/'.git').exists():
        bundle=ROOT/'repository.bundle'
        if not bundle.is_file():raise ValueError('No Git history or repository.bundle found.')
        git('init','-b','import-history')
        # ZIP extraction may discard executable bits; retain the bundle's index modes.
        git('config','core.filemode','false')
        git('fetch',str(bundle),'refs/heads/main:refs/heads/main')
        git('symbolic-ref','HEAD','refs/heads/main')
        git('reset','--mixed','HEAD')
    if git('status','--porcelain',capture=True):
        raise ValueError('Working files changed. Review and commit them before publishing.')
    remotes=git('remote',capture=True).splitlines()
    if 'publish' in remotes:
        if git('remote','get-url','publish',capture=True)!=repository:
            raise ValueError('The publish remote already points elsewhere. Update it explicitly using Git.')
    else:git('remote','add','publish',repository)
    if push:
        git('push','--set-upstream','publish','main')
    else:
        print('Remote prepared. No push performed. Re-run with --push to publish main.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',required=True)
    parser.add_argument('--push',action='store_true')
    args=parser.parse_args()
    try:publish(args.repo,args.push)
    except (ValueError,subprocess.CalledProcessError) as exc:
        parser.exit(1,'Publish did not complete: '+(str(exc) if isinstance(exc,ValueError) else 'Git command failed; inspect the Git output above.')+'\n')
