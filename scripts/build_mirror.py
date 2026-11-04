"""Build-time-only installation of the pinned, verified Linux/amd64 provider.

The filesystem mirror is unpacked so Terraform can symlink its 674 MiB AWS
provider into each private workspace instead of filling the runtime tmpfs.
"""
import os
from pathlib import Path
import platform
import subprocess
import tempfile
import zipfile

VERSION='5.100.0'
PACKAGE='linux_amd64'

def unpack_mirror(mirror: Path):
    provider=mirror/'registry.terraform.io/hashicorp/aws'
    archive=provider/f'terraform-provider-aws_{VERSION}_{PACKAGE}.zip'
    destination=provider/VERSION/PACKAGE
    binary=f'terraform-provider-aws_v{VERSION}_x5'
    destination.mkdir(parents=True,exist_ok=True)
    # Terraform providers mirror already verified the downloaded provider.
    with zipfile.ZipFile(archive) as source:
        if set(source.namelist()) != {'LICENSE.txt',binary}:
            raise ValueError('Unexpected contents in the pinned AWS provider archive')
        for name in source.namelist():
            with source.open(name) as incoming, (destination/name).open('wb') as outgoing:
                import shutil
                shutil.copyfileobj(incoming,outgoing)
            (destination/name).chmod(0o755 if name==binary else 0o644)
    archive.unlink()
    # Filesystem mirrors discover unpacked directories; HTTP mirror indexes are unused.
    for path in provider.glob('*.json'):path.unlink()
    return destination/binary


def main():
    if platform.system()!='Linux' or platform.machine().lower() not in ('x86_64','amd64'):
        raise SystemExit('The v1 validator supports Linux/amd64 only. Use the supplied Docker image.')
    base=Path(os.getenv('TOOLCHAIN_ROOT','/opt')).expanduser().resolve()
    mirror=base/'terraform-mirror';locks=base/'terraform-lock'
    mirror.mkdir(parents=True,exist_ok=True);locks.mkdir(parents=True,exist_ok=True)
    binary=os.getenv('TERRAFORM_BIN','terraform')
    with tempfile.TemporaryDirectory() as directory:
        work=Path(directory)
        work.joinpath('versions.tf').write_text('''terraform {
 required_version = "= 1.9.8"
 required_providers {
  aws = {
   source = "hashicorp/aws"
   version = "= 5.100.0"
  }
 }
}
''')
        subprocess.run([binary,'init','-backend=false','-input=false'],cwd=work,check=True,timeout=1800)
        subprocess.run([binary,'providers','mirror',str(mirror)],cwd=work,check=True,timeout=1800)
        locks.joinpath('.terraform.lock.hcl').write_bytes(work.joinpath('.terraform.lock.hcl').read_bytes())
    unpack_mirror(mirror)
    for path in locks.iterdir():
        if path.is_file():path.chmod(0o644)

if __name__=='__main__':main()
