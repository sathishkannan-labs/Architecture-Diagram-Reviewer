from __future__ import annotations
import json
import os
from pathlib import Path
import re
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from .models import ValidationReport

TEMPLATES = ('versions.tf', 'variables.tf', 'main.tf', 'outputs.tf')
LOCK_PATH = Path(os.getenv('TERRAFORM_LOCK_FILE', str(Path(__file__).with_name('provider.lock.hcl'))))
DISCLAIMER = ValidationReport().limitations

def render(target, approval, graph, original, corrections, mode):
    if approval.target_revision != target.revision() or target.graph_revision != graph.revision():
        raise ValueError('Approval or graph revision is stale.')
    env = Environment(loader=FileSystemLoader(Path(__file__).parent / 'templates'),
                      undefined=StrictUndefined, autoescape=False, keep_trailing_newline=True)
    files = {name:env.get_template(name+'.j2').render(target=target, revision=target.revision()) for name in TEMPLATES}
    decisions = {d.id:d.model_dump() for d in target.decisions}
    resources = {}
    for filename, content in files.items():
        declarations = re.findall(r'^resource "([^"]+)" "([^"]+)"', content, re.M)
        annotated = re.findall(r'# Decision: ([A-Z-]+)\s+resource "([^"]+)" "([^"]+)"', content)
        if len(declarations) != len(annotated):
            raise ValueError('Unmapped Terraform resource in trusted template.')
        for decision, kind, name in annotated:
            if decision not in decisions:
                raise ValueError('Template refers to an unapproved decision.')
            resources[f'{kind}.{name}'] = {'decision_id':decision, 'file':filename}
    manifest = {'schema_version':1, 'mode':mode, 'graph_revision':graph.revision(),
        'target_revision':target.revision(), 'approval':approval.model_dump(),
        'decisions':decisions, 'resources':resources}
    files['traceability.json'] = json.dumps(manifest, indent=2)
    files['original-extraction.json'] = original.model_dump_json(indent=2)
    files['corrected-graph.json'] = graph.model_dump_json(indent=2)
    files['corrections.json'] = json.dumps(corrections, indent=2)
    files['approved-target.json'] = target.model_dump_json(indent=2)
    from .review import review
    files['findings.json'] = json.dumps([f.model_dump() for f in review(graph)], indent=2)
    files['ADR.md'] = '# ADR: Approved two-AZ AWS baseline\n\n' + DISCLAIMER + '\n\n' + (
        f'Extraction mode: **{mode}**\n\nObserved revision: `{graph.revision()}`\n\n'
        f'Approved target: `{target.revision()}` at {approval.approved_at}\n\n')
    for d in target.decisions:
        files['ADR.md'] += (f'## {d.id}\n\n{d.description}\n\nObservations: {", ".join(d.component_ids)}. '
            f'Findings: {", ".join(d.finding_ids) or "none"}.\n\n{d.baseline_assumption or ""}\n\n')
    files['ADR.md'] += ('## Unresolved controls and consequences\n\n'
        'This target does not automatically resolve every finding. Authentication, authorization, TLS, '
        'application delivery, monitoring and alerting remain unresolved. HTTP port 80 is illustrative. '
        'No NAT, VPC endpoints, instance role or application bootstrap is configured. '
        'Private instances cannot download packages or retrieve managed DB credentials without additional '
        'networking and least-privilege IAM. Supply a tested regional AMI with a service on port 8080 '
        'and `/health`. Region AZ names are a/b; account-specific availability has not been checked. '
        'No provisioning was attempted.\n')
    files['README.md'] = ('# Generated infrastructure — review required\n\n' + DISCLAIMER + '\n\n'
        'See ADR.md for decisions and unresolved controls; traceability.json maps all resources. '
        'Read validation-report.json before using any files. No plan or apply has been run. '
        'A missing lock file means the toolchain build is unavailable; run the supplied Docker build '
        'to create a genuine provider lock file. A fabricated lock file is never substituted.\n')
    if LOCK_PATH.is_file():
        files['.terraform.lock.hcl'] = LOCK_PATH.read_text()
    return files
