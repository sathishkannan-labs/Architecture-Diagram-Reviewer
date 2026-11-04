"""Validate a bounded graph/approval request in the existing isolated Docker image."""
import argparse
from pathlib import Path
import zipfile
from archreview.validation_request import validate_request, MAX_REQUEST_BYTES


def execute(request_path, output_path):
    with request_path.open('rb') as f:data=f.read(MAX_REQUEST_BYTES+1)
    if not data.strip():
        from archreview.fixtures import load_fixture
        from archreview.service import Workflow
        workflow=Workflow(load_fixture('complex-ccm'))
        workflow.run_review()
        workflow.approve(workflow.target.revision(),acknowledge_scope=True,acknowledge_unknowns=True)
        data=workflow.validation_request().encode()
    if len(data)>MAX_REQUEST_BYTES:raise ValueError('Request exceeds the allowed size.')
    report,files=validate_request(data)
    with zipfile.ZipFile(output_path,'w',zipfile.ZIP_DEFLATED) as z:
        for name,content in files.items():z.writestr(name,content)
    print('Terraform validation: '+report.status+'. Download the report ZIP and inspect validation-context.json for the matching revisions.')
    return 0 if report.status=='passed' else 1


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--request',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    try:raise SystemExit(execute(args.request,args.output))
    except (ValueError,OSError):
        p.exit(2,'Validation request rejected or runtime dependency unavailable. No validation pass is claimed.\n')
