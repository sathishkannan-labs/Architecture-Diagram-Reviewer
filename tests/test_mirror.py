import importlib.util
from pathlib import Path
import zipfile
import pytest
import sys

pytestmark=pytest.mark.skipif(sys.platform != "linux",reason="Provider mirror targets Linux/amd64")

spec=importlib.util.spec_from_file_location('mirror_builder',Path(__file__).resolve().parents[1]/'scripts/build_mirror.py')
mirror=importlib.util.module_from_spec(spec);spec.loader.exec_module(mirror)

def package(root,extra=None):
    directory=root/'registry.terraform.io/hashicorp/aws';directory.mkdir(parents=True)
    p=directory/'terraform-provider-aws_5.100.0_linux_amd64.zip'
    with zipfile.ZipFile(p,'w') as z:
        z.writestr('LICENSE.txt','test-only license')
        z.writestr('terraform-provider-aws_v5.100.0_x5','test-only binary')
        if extra:z.writestr(extra,'unexpected content')
    (directory/'index.json').write_text('{}')
    return p

def test_unpacked_mirror_removes_runtime_extraction_requirement(tmp_path):
    archive=package(tmp_path)
    binary=mirror.unpack_mirror(tmp_path)
    assert binary.read_text()=='test-only binary'
    assert binary.stat().st_mode & 0o111
    assert not archive.exists()
    assert not list(archive.parent.glob('*.json'))
    assert binary.parent==archive.parent/'5.100.0/linux_amd64'

def test_unexpected_archive_paths_are_rejected(tmp_path):
    package(tmp_path,'../../escape')
    with pytest.raises(ValueError):mirror.unpack_mirror(tmp_path)
    assert not (tmp_path/'registry.terraform.io/hashicorp/aws/escape').exists()
