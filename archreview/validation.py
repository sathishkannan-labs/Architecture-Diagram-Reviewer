from __future__ import annotations
try:
    import fcntl
except ImportError:  # Windows still supports the UI and status-bearing downloads.
    fcntl = None
import json
import os
from pathlib import Path
import selectors
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from .models import StageResult, ValidationReport
from .hosting import hosted

TIMEOUT = 180
MAX_OUTPUT = 64 * 1024
LAUNCHER = Path(__file__).with_name('validator_exec.py').resolve()


def _run(arguments, cwd, environment, deadline, limit=MAX_OUTPUT):
    """Fixed callers only. No shell, no caller-supplied environment or code."""
    identity = {'user':65534, 'group':65534, 'extra_groups':[]} if getattr(os, 'getuid', lambda: -1)() == 0 else {}
    process = subprocess.Popen([sys.executable,'-I',str(LAUNCHER),*arguments], cwd=cwd,
        env=environment, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, start_new_session=True, close_fds=True, **identity)
    output = bytearray()
    status = None
    selector = selectors.DefaultSelector()
    selector.register(process.stdout,selectors.EVENT_READ)
    try:
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                status = 'timed_out'
                break
            for key, _ in selector.select(min(0.1,remaining)):
                chunk = os.read(key.fileobj.fileno(),8192)
                if not chunk:
                    selector.unregister(key.fileobj)
                elif len(output)+len(chunk) > limit:
                    output.extend(chunk[:max(0,limit-len(output))])
                    status = 'failed'
                    break
                else:
                    output.extend(chunk)
            if status:
                break
        if status:
            os.killpg(process.pid,signal.SIGKILL)
        process.wait(timeout=max(0.01,deadline-time.monotonic()) if not status else 5)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid,signal.SIGKILL)
        process.wait()
        status = 'timed_out'
    finally:
        selector.close()
        process.stdout.close()
    result = output.decode('utf-8',errors='replace')
    if status == 'failed':
        result += '\n[Output limit exceeded; process group terminated.]'
    if process.returncode == 78:
        status = 'not_run'
    return StageResult(stage='',status=status or ('passed' if process.returncode == 0 else 'failed'),
                       output=result,exit_code=process.returncode)


def validate(files):
    report = ValidationReport()
    formatted = {}
    if hosted():
        report.stages.append(StageResult(stage='hosting', status='not_run',
            output='Terraform execution is disabled in the public preview. Download the artifacts and use the local Docker workflow for actual validation.'))
        return report, formatted
    if not sys.platform.startswith('linux') or fcntl is None:
        report.stages.append(StageResult(stage='platform', status='not_run',
            output='Restricted validation requires Linux. Use Docker Desktop with Linux containers. UI and downloads remain available.'))
        return report, formatted
    binary = shutil.which(os.getenv('TERRAFORM_BIN','terraform'))
    mirror = Path(os.getenv('TERRAFORM_MIRROR','/opt/terraform-mirror')).resolve()
    provider_dir = mirror / 'registry.terraform.io/hashicorp/aws'
    if not binary or not provider_dir.is_dir() or '.terraform.lock.hcl' not in files:
        report.stages.append(StageResult(stage='dependencies',status='not_run',
            output='Terraform binary, bundled provider mirror, or genuine provider lock file unavailable. Build the Docker image.'))
        return report, formatted
    try:
        with open(Path(tempfile.gettempdir()) / 'archreview-validator.lock','a') as lock:
            try:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:
                report.stages.append(StageResult(stage='concurrency',status='not_run',output='One validation is already running. Retry later.'))
                return report, formatted
            with tempfile.TemporaryDirectory(prefix='archreview-') as directory:
                work = Path(directory)
                # Root is only an optional local orchestrator. All executed validation runs as nobody.
                uid = 65534 if os.getuid() == 0 else os.getuid()
                gid = 65534 if os.getuid() == 0 else os.getgid()
                os.chown(work,uid,gid)
                allowed = {'main.tf','versions.tf','variables.tf','outputs.tf','.terraform.lock.hcl'}
                for name in allowed:
                    if name in files:
                        path = work / name
                        path.write_text(files[name]); path.chmod(0o600); os.chown(path,uid,gid)
                config = work / 'terraform.rc'
                # JSON string literal is valid HCL string escaping for the trusted filesystem path.
                config.write_text('provider_installation {\n filesystem_mirror {\n path = '+json.dumps(str(mirror))+'\n include = ["registry.terraform.io/hashicorp/aws"]\n }\n}\n')
                config.chmod(0o600);os.chown(config,uid,gid)
                env = {'PATH':'/usr/local/bin:/usr/bin:/bin','HOME':directory,'TMPDIR':directory,
                    'TF_CLI_CONFIG_FILE':str(config),'TF_IN_AUTOMATION':'1','CHECKPOINT_DISABLE':'1',
                    'AWS_EC2_METADATA_DISABLED':'true','LANG':'C.UTF-8','GOMAXPROCS':'2'}
                deadline = time.monotonic()+TIMEOUT
                commands = [('version',['version','-json']),('fmt',['fmt','-no-color']),
                    ('fmt-check',['fmt','-check','-no-color']),
                    ('init',['init','-backend=false','-input=false','-lockfile=readonly','-no-color']),
                    ('validate',['validate','-json'])]
                budget = MAX_OUTPUT
                for stage, args in commands:
                    item = _run([str(Path(binary).resolve()),*args],work,env,deadline,budget)
                    item.stage = stage
                    budget -= len(item.output.encode())
                    if stage == 'version' and item.status == 'passed':
                        try:
                            if json.loads(item.output)['terraform_version'] != '1.9.8':
                                item.status='failed';item.output='Pinned Terraform 1.9.8 is required.'
                        except (ValueError,KeyError):
                            item.status='failed';item.output='Unable to verify Terraform version.'
                    if stage == 'validate' and item.status == 'passed':
                        try:
                            validation = json.loads(item.output)
                            if validation.get('valid') is not True or validation.get('error_count', 0) != 0:
                                item.status = 'failed'
                        except (ValueError, TypeError, AttributeError):
                            item.status = 'failed'
                            item.output = 'Terraform returned an invalid structured validation report.'
                    report.stages.append(item)
                    if item.status != 'passed':
                        report.status = item.status
                        break
                else:
                    report.status='passed'
                for name in allowed - {'.terraform.lock.hcl'}:
                    if (work/name).is_file():
                        formatted[name]=(work/name).read_text()
    except (OSError, subprocess.SubprocessError):
        report.status='not_run'
        report.stages.append(StageResult(stage='runtime',status='not_run',output='Non-root execution or validation runtime dependencies unavailable. No success is claimed.'))
    return report,formatted
