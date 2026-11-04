import json
import pytest
from archreview.fixtures import load_fixture
from archreview.service import Workflow
from archreview.remediation import remediation_summary
from archreview.models import ValidationReport


def workflow():
    w=Workflow(load_fixture('complex-ccm'));w.run_review();return w


def test_database_choice_changes_scope_and_revokes_approval():
    w=workflow();w.approve(w.target.revision(),acknowledge_scope=True,acknowledge_unknowns=True)
    old=w.target.revision()
    w.configure_target(database_source_id='legacy_postgresql')
    assert w.approval is None and w.target.revision()!=old
    scope={s.component_id:s.disposition for s in w.target.scope}
    assert scope['legacy_postgresql']=='replaced'
    assert scope['primary_postgresql']=='unsupported'
    rows=remediation_summary(w.graph,w.target,w.findings)
    assert next(r for r in rows if r['rule']=='AR-003')['target_status']=='Addressed in new baseline only'
    assert all(r['target_status']=='Unresolved / outside generated scope' for r in rows if r['rule']=='AR-001')
    with pytest.raises(ValueError):w.approve(old,acknowledge_scope=True,acknowledge_unknowns=True)
    w.approve(w.target.revision(),acknowledge_scope=True,acknowledge_unknowns=True)
    w.generate(lambda files:(ValidationReport(),{}))
    assert json.loads(w.files['approved-target.json'])['database_source_id']=='legacy_postgresql'
    assert len(json.loads(w.files['remediation-summary.json']))==len(w.findings)
    assert 'legacy_postgresql' in w.files['ADR.md']
    request=w.validation_request()
    from archreview.validation_request import load_request
    assert load_request(request.encode())[0].target.database_source_id=='legacy_postgresql'
    w.configure_target(database_source_id=None)
    assert w.approval is None
    assert all(s.disposition=='unsupported' for s in w.target.scope if s.component_id in ('legacy_postgresql','primary_postgresql'))


@pytest.mark.parametrize('source',['orders_service','missing_database'])
def test_invalid_database_choices_rejected(source):
    w=workflow();old=w.target.revision()
    with pytest.raises(ValueError):w.configure_target(database_source_id=source)
    assert w.target.revision()==old


def test_selection_tampering_rejected():
    w=workflow();w.target.database_source_id='legacy_postgresql'
    with pytest.raises(ValueError):w.approve(w.target.revision(),acknowledge_scope=True,acknowledge_unknowns=True)


def test_independent_baseline_does_not_claim_legacy_remediation():
    w=workflow();rows=remediation_summary(w.graph,w.target,w.findings)
    assert len(rows)==len(w.findings)
    assert next(r for r in rows if r['rule']=='AR-003')['target_status']=='Unresolved / outside generated scope'
    assert all(r['target_status']!='Addressed in new baseline only' for r in rows if r['finding_status']=='unverified')
