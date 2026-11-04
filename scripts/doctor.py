"""Offline readiness inventory. Never prints secrets and never calls Meta."""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def inspect():
    dependencies = {}
    for name in ('pydantic','streamlit','httpx','jinja2','Pillow','fastapi'):
        try: dependencies[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError: dependencies[name] = None
    docker = shutil.which('docker')
    docker_ready = False
    if docker:
        try:
            docker_ready = subprocess.run([docker,'info','--format','{{.ServerVersion}}'],
                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=10).returncode == 0
        except (OSError,subprocess.SubprocessError): pass
    uid = getattr(os,'getuid',lambda:None)()
    return {
        'python':platform.python_version(), 'platform':platform.system(),
        'python_dependencies':dependencies,
        'python_ui_dependencies_present':all(dependencies.values()),
        'docker_installed':bool(docker), 'docker_daemon_ready':docker_ready,
        'meta_key_in_terminal_environment':bool(os.getenv('MODEL_API_KEY')),
        'compose_env_file_present':(ROOT/'.env').is_file(),
        'live_meta_acceptance':'not_verified',
        'restricted_validator_requires':'Linux, non-root execution, libseccomp, Terraform 1.9.8 and AWS 5.100.0 mirror',
        'current_uid':uid,
        'note':'This inventory does not run extraction or Terraform validation. The UI and live acceptance script read the project .env; existing nonempty terminal variables take precedence.',
    }

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json',action='store_true')
    args=parser.parse_args()
    result=inspect()
    if args.json:print(json.dumps(result,indent=2))
    else:
        print('Architecture Diagram Reviewer — local readiness')
        print('Python UI dependencies:', 'present' if result['python_ui_dependencies_present'] else 'install .[test] in a venv')
        print('Docker:', 'ready' if result['docker_daemon_ready'] else 'not available; start/install Docker Desktop for full validation')
        print('Meta key in this terminal:', 'configured; access unverified' if result['meta_key_in_terminal_environment'] else 'not set')
        print(result['note'])
