import json
import os
from pathlib import Path
import sys
import tempfile
import time
import pytest
from archreview.validation import _run,validate

pytestmark=pytest.mark.skipif(sys.platform != "linux",reason="Restricted validator tests require Linux")

@pytest.fixture
def work():
    with tempfile.TemporaryDirectory(prefix='validator-test-') as directory:
        path=Path(directory)
        if os.getuid()==0:
            try: os.chown(path,65534,65534)
            except OSError: pytest.skip('Host maps only UID 0; non-root execution requires the Docker image')
        yield path

@pytest.fixture
def env(work):return {'PATH':'/usr/bin:/bin','HOME':str(work),'TMPDIR':str(work)}

def run(work,env,code,seconds=5,limit=65536):
    return _run([sys.executable,'-I','-c',code],work,env,time.monotonic()+seconds,limit)

def test_nonroot_and_no_credentials_or_ip_egress(work,env,monkeypatch):
    monkeypatch.setenv('AWS_SECRET_ACCESS_KEY','must-not-be-inherited')
    code='''import os,socket,errno
assert os.getuid()!=0
assert 'AWS_SECRET_ACCESS_KEY' not in os.environ
for family in (socket.AF_INET,socket.AF_INET6):
 try: socket.socket(family,socket.SOCK_STREAM)
 except OSError as e: assert e.errno==errno.EPERM
 else: raise AssertionError('Network egress permitted')
s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);s.close()
print('non-root; no cloud credentials; IPv4/IPv6 blocked; local RPC permitted')
'''
    result=run(work,env,code)
    assert result.status=='passed',result.output

def test_exit_failure(work,env):
    result=run(work,env,'import sys;print("invalid configuration");sys.exit(1)')
    assert result.status=='failed' and result.exit_code==1

def test_timeout(work,env):
    result=run(work,env,'import time;time.sleep(10)',seconds=.2)
    assert result.status=='timed_out'

def test_bounded_output(work,env):
    result=run(work,env,'import os;\nwhile True: os.write(1,b"x"*8192)',limit=1000)
    assert result.status=='failed' and len(result.output)<1100
    assert 'Output limit' in result.output

def test_unavailable_binary(monkeypatch):
    monkeypatch.setenv('TERRAFORM_BIN','/definitely/missing/terraform')
    report,_=validate({})
    assert report.status=='not_run' and report.stages[0].stage=='dependencies'


@pytest.fixture
def supervisor_only(monkeypatch,tmp_path):
    """Exercise process supervision using a real child, independently of security preflight.
    This test-only Popen adapter is never used by the application.
    """
    import subprocess
    original=subprocess.Popen
    def spawn(args,**kwargs):
        for name in ('user','group','extra_groups'):kwargs.pop(name,None)
        return original(args[3:],**kwargs)
    monkeypatch.setattr('archreview.validation.subprocess.Popen',spawn)
    return tmp_path,{'PATH':'/usr/bin:/bin','HOME':str(tmp_path),'TMPDIR':str(tmp_path)}

def test_supervisor_timeout(supervisor_only):
    path,environment=supervisor_only
    assert run(path,environment,'import time;time.sleep(10)',seconds=.2).status=='timed_out'

def test_supervisor_output_limit(supervisor_only):
    path,environment=supervisor_only
    result=run(path,environment,'import os;\nwhile True: os.write(1,b"x"*8192)',limit=1000)
    assert result.status=='failed' and len(result.output)<1100

def test_supervisor_exit_failure(supervisor_only):
    path,environment=supervisor_only
    assert run(path,environment,'import sys;sys.exit(1)').status=='failed'

def test_security_launcher_refuses_root():
    if os.getuid()!=0:pytest.skip('Root-specific preflight check')
    import subprocess
    from archreview.validation import LAUNCHER
    result=subprocess.run([sys.executable,'-I',str(LAUNCHER),'/usr/bin/true'],capture_output=True,text=True,env={'PATH':'/usr/bin:/bin'})
    assert result.returncode==78 and 'preflight unavailable' in result.stderr

def test_fixed_arguments_minimal_env_and_init_failure(monkeypatch,tmp_path):
    from archreview.models import StageResult
    import archreview.validation as validator
    (tmp_path/'registry.terraform.io/hashicorp/aws').mkdir(parents=True)
    monkeypatch.setenv('TERRAFORM_MIRROR',str(tmp_path))
    monkeypatch.setattr(validator.shutil,'which',lambda _:'/usr/bin/terraform')
    monkeypatch.setattr(validator.os,'chown',lambda *args:None)
    calls=[]
    def command(args,cwd,environment,deadline,limit):
        calls.append(args)
        assert not any(k.startswith('AWS_') and k!='AWS_EC2_METADATA_DISABLED' for k in environment)
        assert 'MODEL_API_KEY' not in environment and 'HTTP_PROXY' not in environment
        assert 'direct' not in (Path(cwd)/'terraform.rc').read_text()
        if args[1]=='version':return StageResult(stage='',status='passed',output='{"terraform_version":"1.9.8"}')
        return StageResult(stage='',status='failed' if args[1]=='init' else 'passed',output='Provider binary unavailable' if args[1]=='init' else '')
    monkeypatch.setattr(validator,'_run',command)
    report,_=validate({'.terraform.lock.hcl':'genuine lock placeholder for orchestration-only test'})
    assert report.status=='failed'
    assert calls[-1][1:]==['init','-backend=false','-input=false','-lockfile=readonly','-no-color']
    assert all('plan' not in args and 'apply' not in args for args in calls)

def test_windows_fallback_preserves_artifact_workflow(monkeypatch):
    import archreview.validation as validator
    monkeypatch.setattr(validator.sys,'platform','win32')
    report,formatted=validator.validate({})
    assert report.status=='not_run' and report.stages[0].stage=='platform'
    assert formatted=={}

def test_zero_exit_cannot_override_invalid_validate_json(monkeypatch,tmp_path):
    from archreview.models import StageResult
    import archreview.validation as validator
    (tmp_path/'registry.terraform.io/hashicorp/aws').mkdir(parents=True)
    monkeypatch.setenv('TERRAFORM_MIRROR',str(tmp_path))
    monkeypatch.setattr(validator.shutil,'which',lambda _:'/usr/bin/terraform')
    monkeypatch.setattr(validator.os,'chown',lambda *args:None)
    def command(args,*unused):
        output='{"terraform_version":"1.9.8"}' if args[1]=='version' else '{"valid": false,"error_count": 1}' if args[1]=='validate' else ''
        return StageResult(stage='',status='passed',output=output)
    monkeypatch.setattr(validator,'_run',command)
    report,_=validate({'.terraform.lock.hcl':'orchestration-only fixture'})
    assert report.status=='failed' and report.stages[-1].stage=='validate'
