import io
import json
import re
import time
import zipfile
import pytest
from pydantic import ValidationError
from archreview.fixtures import NAMES,load_fixture
from archreview.models import ArchitectureGraph,ValidationReport
from archreview.review import review
from archreview.service import Workflow

@pytest.mark.parametrize('name',NAMES)
def test_fixture_references(name):
    g=load_fixture(name);ids={c.id for c in g.components}
    assert all(set(f.component_ids)<=ids for f in review(g))

def test_six_mandatory_rules_and_explicit_evidence():
    findings=review(load_fixture('public-database'))
    assert {f.rule_id for f in findings}=={'AR-001','AR-003','AR-004','AR-005','AR-006','AR-008'}
    assert all(f.status=='confirmed' for f in findings if f.rule_id in ('AR-001','AR-003','AR-006'))
    assert all(f.status=='unverified' for f in findings if not f.component_ids)

def test_redundant_private_has_no_findings():
    assert review(load_fixture('redundant-private'))==[]

def test_uncertain_facts_are_not_confirmed():
    g=load_fixture('single-server')
    g.components[1].instances=None;g.components[2].exposure='unknown';g.components[2].failover='unknown'
    assert all(f.status=='unverified' for f in review(g))

def test_inferred_controls_do_not_suppress_visibility_questions():
    g=load_fixture('redundant-private')
    for c in g.components:c.source='inferred'
    assert {'AR-004','AR-005','AR-008'} <= {f.rule_id for f in review(g)}

@pytest.mark.parametrize('mutation',['duplicate','dangling','duplicate_edge','boundary','empty','unknown_field'])
def test_invalid_graph(mutation):
    d=load_fixture('single-server').model_dump()
    if mutation=='duplicate':d['components'].append(d['components'][0])
    if mutation=='dangling':d['connections'][0]['target']='missing'
    if mutation=='duplicate_edge':d['connections'].append(d['connections'][0])
    if mutation=='boundary':d['boundaries']=[dict(id='bad',kind='network',label='VPC',component_ids=['missing'])]
    if mutation=='empty':d['components']=[]
    if mutation=='unknown_field':d['execute']='evil'
    with pytest.raises(ValidationError):ArchitectureGraph.model_validate(d)

def fake_validator(files):return ValidationReport(status='not_run'),{}

def test_correction_invalidation_and_audit():
    w=Workflow(load_fixture('single-server'));original=w.original.model_dump()
    w.run_review();w.approve(w.target.revision());w.generate(fake_validator)
    changed=w.graph.model_copy(deep=True);changed.components[1].label='Human corrected application'
    changed.connections[0].evidence='Human confirmed arrow'
    w.correct(changed)
    assert w.graph.components[1].source=='user_corrected'
    assert w.graph.connections[0].provenance=='user_corrected'
    assert w.original.model_dump()==original
    assert len(w.corrections)==1
    assert w.findings is w.target is w.approval is w.files is w.report is None
    with pytest.raises(ValueError):w.generate(fake_validator)
    w.run_review();w.approve(w.target.revision());w.generate(fake_validator)
    assert json.loads(w.files['corrections.json'])[0]['after_revision']==w.graph.revision()

def test_target_revision_stale_approval():
    w=Workflow(load_fixture('single-server'));w.run_review();w.approve(w.target.revision())
    w.target.region='eu-west-1'
    with pytest.raises(ValueError):w.generate(fake_validator)

def test_target_configuration_invalidates_approval():
    w=Workflow(load_fixture('single-server'));w.run_review();w.approve(w.target.revision())
    w.configure_target(desired_capacity=3)
    assert w.approval is None
    with pytest.raises(ValueError):w.configure_target(name='" injection')
    with pytest.raises(ValueError):w.configure_target(decisions=[])

def test_every_resource_maps_to_approved_decision_and_zip_status():
    w=Workflow(load_fixture('single-server'));w.run_review();w.approve(w.target.revision());w.generate(fake_validator)
    m=json.loads(w.files['traceability.json'])
    addresses=set(re.findall(r'^resource "([^"]+)" "([^"]+)"',w.files['main.tf'],re.M))
    assert {'.'.join(a) for a in addresses}==set(m['resources'])
    assert len(addresses)>=25
    assert all(r['decision_id'] in m['decisions'] for r in m['resources'].values())
    assert m['target_revision']==w.approval.target_revision
    assert m['graph_revision']==w.graph.revision()
    with zipfile.ZipFile(io.BytesIO(w.download())) as z:
        assert json.loads(z.read('validation-report.json'))['status']=='not_run'
        assert 'ADR.md' in z.namelist()
    assert all(d.id in w.files['ADR.md'] for d in w.target.decisions)

def test_expiry_discards_artifacts_and_observations():
    w=Workflow(load_fixture('single-server'));w.run_review();w.approve(w.target.revision());w.generate(fake_validator)
    w.created-=3601
    with pytest.raises(ValueError):w.download()
    assert w.files is w.original is w.graph is None

def test_no_generation_without_approval():
    w=Workflow(load_fixture('single-server'));w.run_review()
    with pytest.raises(ValueError):w.generate(fake_validator)

def test_explicit_approval_rejects_wrong_revision():
    w=Workflow(load_fixture('single-server'));w.run_review()
    with pytest.raises(ValueError):w.approve('stale-target')
    assert w.approval is None

def test_low_confidence_is_unverified_and_findings_have_unique_ids():
    g=load_fixture('public-database')
    for c in g.components:c.confidence=.2
    findings=review(g)
    assert all(f.status=='unverified' for f in findings)
    assert len({f.id for f in findings})==len(findings)
    w=Workflow(g);w.run_review();w.approve(w.target.revision());w.generate(fake_validator)
    manifest=json.loads(w.files['traceability.json'])
    findings_by_id={f.id:f for f in findings}
    for d in manifest['decisions'].values():
        assert set(d['finding_ids'])<=set(findings_by_id)

def test_validator_exception_still_downloads_with_failure_status():
    w=Workflow(load_fixture('single-server'));w.run_review();w.approve(w.target.revision())
    w.generate(lambda f:(ValidationReport(status='passed'),{}))
    def broken(files):raise RuntimeError('private internal detail must not be exposed')
    report=w.generate(broken)
    assert report.status=='failed'
    assert 'private internal' not in report.model_dump_json()
    with zipfile.ZipFile(io.BytesIO(w.download())) as archive:
        assert json.loads(archive.read('validation-report.json'))['status']=='failed'
        assert '.terraform.lock.hcl' in archive.namelist()

def test_inferred_redundancy_private_network_and_failover_remain_questions():
    graph=load_fixture('redundant-private')
    for component in graph.components:component.source='inferred'
    findings=review(graph)
    assert {f.rule_id for f in findings}=={'AR-001','AR-003','AR-004','AR-005','AR-006','AR-008'}
    assert all(f.status=='unverified' for f in findings)

def test_uncertain_internet_edge_cannot_confirm_public_database():
    graph=load_fixture('public-database')
    graph.components[2].exposure='unknown'
    for edge in graph.connections:
        if edge.source=='internet' and edge.target=='db':edge.confidence=.2
    assert next(f for f in review(graph) if f.rule_id=='AR-003').status=='unverified'
