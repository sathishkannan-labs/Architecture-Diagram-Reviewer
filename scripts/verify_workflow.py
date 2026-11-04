"""Deterministic fixture integration check; never claims live Meta acceptance."""
import argparse
import io
import json
from pathlib import Path
import sys
import zipfile
from archreview.fixtures import NAMES,load_fixture
from archreview.service import Workflow


def verify(require_validation=False,output=None):
    summary={'mode':'fixture','live_meta_acceptance':'not_run','diagrams':[]}
    if output:output.mkdir(parents=True,exist_ok=True)
    for name in NAMES:
        workflow=Workflow(load_fixture(name),'fixture')
        corrected=workflow.graph.model_copy(deep=True)
        corrected.components[0].label+=' (human review simulation)'
        workflow.correct(corrected)
        workflow.run_review();workflow.approve(workflow.target.revision())
        report=workflow.generate()
        archive=workflow.download()
        with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
            manifest=json.loads(bundle.read('traceability.json'))
            assert manifest['approval']['target_revision']==manifest['target_revision']
            assert len(manifest['resources'])==26
            assert len(json.loads(bundle.read('corrections.json')))==1
            assert '.terraform.lock.hcl' in bundle.namelist()
            assert json.loads(bundle.read('validation-report.json'))['status']==report.status
        # Prove correction revokes both approval and downloadable artifacts.
        changed=workflow.graph.model_copy(deep=True);changed.components[0].label+=' changed'
        workflow.correct(changed)
        try:workflow.download()
        except ValueError:pass
        else:raise AssertionError('Stale approval allowed a download')
        summary['diagrams'].append({'name':name,'workflow_checks':'passed','validation':report.status,'traced_resources':26})
        if output:(output/(name+'.zip')).write_bytes(archive)
    passed=all(item['validation']=='passed' for item in summary['diagrams'])
    summary['full_live_acceptance']='not_run'
    summary['restricted_validation']='passed' if passed else 'incomplete'
    if output:(output/'fixture-summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))
    if any(item['validation'] in ('failed','timed_out') for item in summary['diagrams']):return 1
    if require_validation and not passed:return 2
    return 0

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--require-validation',action='store_true')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    raise SystemExit(verify(args.require_validation,args.output))
