"""Regenerate only approved trusted templates; never accept submitted Terraform."""
import hashlib
import json
from pydantic import Field
from .models import StrictModel, ArchitectureGraph, TargetArchitecture, Approval
from .generation import render, TEMPLATES

MAX_REQUEST_BYTES = 50_000
WORKFLOW_URL = 'https://github.com/sathishkannan-labs/Architecture-Diagram-Reviewer/actions/workflows/validate-target.yml'


class ValidationRequest(StrictModel):
    schema_version: int = 1
    graph: ArchitectureGraph
    original: ArchitectureGraph
    corrections: list[dict] = Field(default_factory=list, max_length=100)
    target: TargetArchitecture
    approval: Approval
    mode: str
    expected_files: dict[str,str]


def hashes(files):
    return {name:hashlib.sha256(files[name].encode()).hexdigest()
        for name in (*TEMPLATES,'.terraform.lock.hcl') if name in files}


def build_request(graph, original, corrections, target, approval, mode):
    files=render(target,approval,graph,original,corrections,mode)
    request=ValidationRequest(graph=graph,original=original,corrections=corrections,
        target=target,approval=approval,mode=mode,expected_files=hashes(files))
    data=request.model_dump_json()
    if len(data.encode())>MAX_REQUEST_BYTES:
        raise ValueError('This request exceeds the GitHub demo limit. Use the local Docker workflow for this architecture.')
    return data


def load_request(data):
    if len(data)>MAX_REQUEST_BYTES:raise ValueError('Validation request is too large.')
    request=ValidationRequest.model_validate_json(data)
    if request.schema_version!=1 or request.mode not in ('fixture','live_meta'):
        raise ValueError('Unsupported validation request.')
    revision=request.original.revision()
    for correction in request.corrections:
        graph=ArchitectureGraph.model_validate(correction.get('graph'))
        if correction.get('before_revision')!=revision or correction.get('after_revision')!=graph.revision():
            raise ValueError('Correction audit revisions do not match.')
        revision=graph.revision()
    if revision!=request.graph.revision():raise ValueError('Correction audit does not reach the current graph.')
    files=render(request.target,request.approval,request.graph,request.original,request.corrections,request.mode)
    if request.expected_files!=hashes(files):
        raise ValueError('Template/lock hashes changed. Regenerate the request from the current application before validating.')
    return request,files


def validate_request(data, validator=None):
    from .validation import validate
    request,files=load_request(data)
    report,formatted=(validator or validate)(files)
    files.update(formatted)
    files['validation-report.json']=report.model_dump_json(indent=2)
    files['validation-request.json']=data.decode()
    context={'request_sha256':hashlib.sha256(data).hexdigest(),
        'graph_revision':request.graph.revision(),'target_revision':request.target.revision(),
        'mode':request.mode,'expected_template_files':request.expected_files,
        'validated_output_files':hashes(files),'status':report.status,
        'note':'Regenerated from the approved graph using trusted templates; no plan or apply ran.'}
    files['validation-context.json']=json.dumps(context,indent=2)
    return report,files
