import hashlib
import json
import pytest
from archreview.fixtures import load_fixture
from archreview.models import OpenQuestion, ValidationReport, StageResult
from archreview.presentation import group_questions
from archreview.service import Workflow
from archreview.validation_request import build_request,load_request,validate_request,MAX_REQUEST_BYTES


def workflow():
    w=Workflow(load_fixture('complex-ccm'))
    changed=w.graph.model_copy(deep=True)
    changed.components[4].label='Customer self-service portal x2'
    w.correct(changed);w.run_review()
    w.approve(w.target.revision(),acknowledge_scope=True,acknowledge_unknowns=True)
    return w


def test_question_groups_reduce_display_without_dropping_evidence():
    w=workflow();groups=group_questions(w.target.open_questions)
    assert {g['topic'] for g in groups}=={'controls','recovery','queue','storage'}
    assert len(groups)==4 and len(w.target.open_questions)==11
    flattened=[q for g in groups for q in g['entries']]
    assert sorted(q['id'] for q in flattened)==sorted(q.id for q in w.target.open_questions)
    assert sorted(q['question'] for q in flattened)==sorted(q.question for q in w.target.open_questions)
    assert sum(len(g['question_ids']) for g in groups)==11


def test_unknown_question_topics_remain_visible():
    q=OpenQuestion(id='custom',question='Confirm the business owner',origin='graph')
    groups=group_questions([q])
    assert groups[0]['topic']=='other' and groups[0]['entries']==[q.model_dump()]


def test_split_backup_questions_from_new_live_run_stay_in_one_topic():
    w=workflow()
    original=w.target.open_questions
    replacement=[q for q in original if 'DB backups schedule and restore tests' not in q.question]
    replacement.extend([OpenQuestion(id='split-schedule',question='Schedule for DB backups is not shown',origin='graph'),
        OpenQuestion(id='split-restore',question='Restore tests for DB backups are not shown',origin='graph')])
    groups=group_questions(replacement)
    assert len(replacement)==12 and len(groups)==4
    recovery=next(g for g in groups if g['topic']=='recovery')
    assert {'split-schedule','split-restore'}<=set(recovery['question_ids'])


def test_request_carries_exact_approval_audit_and_template_hashes_without_env_secrets(monkeypatch):
    monkeypatch.setenv('MODEL_API_KEY','private-meta-test-value')
    monkeypatch.setenv('DEMO_CODE','private-demo-test-value')
    w=workflow();data=w.validation_request().encode();request,files=load_request(data)
    assert b'private-meta-test-value' not in data and b'private-demo-test-value' not in data
    assert request.target.revision()==w.approval.target_revision
    assert request.graph.revision()==w.graph.revision()
    assert request.original.revision()==w.original.revision()
    assert len(request.corrections)==1
    assert set(request.expected_files)=={'main.tf','outputs.tf','variables.tf','versions.tf','.terraform.lock.hcl'}
    assert all(request.expected_files[k]==hashlib.sha256(files[k].encode()).hexdigest() for k in request.expected_files)


@pytest.mark.parametrize('mutation',['hash','scope','approval','graph','audit','terraform','version','mode'])
def test_invalid_or_stale_requests_never_reach_validator(mutation):
    w=workflow();payload=json.loads(w.validation_request())
    if mutation=='hash':payload['expected_files']['main.tf']='0'*64
    if mutation=='scope':payload['target']['scope'].clear()
    if mutation=='approval':payload['approval']['scope_acknowledged']=False
    if mutation=='graph':payload['graph']['components'][0]['label']='Changed graph'
    if mutation=='audit':payload['corrections'].clear()
    if mutation=='terraform':payload['main.tf']='resource "evil" "payload" {}'
    if mutation=='version':payload['schema_version']=99
    if mutation=='mode':payload['mode']='unknown-source'
    with pytest.raises(ValueError):
        validate_request(json.dumps(payload).encode(),lambda _:pytest.fail('Untrusted request reached validator'))


def test_oversized_request_rejected_before_json_parse():
    with pytest.raises(ValueError,match='too large'):load_request(b'x'*(MAX_REQUEST_BYTES+1))


def test_template_mismatch_rejected_when_template_changes(monkeypatch):
    w=workflow();data=w.validation_request().encode()
    import archreview.validation_request as module
    render=module.render
    def changed(*args):
        files=render(*args);files['main.tf']+='\n# updated trusted template\n';return files
    monkeypatch.setattr(module,'render',changed)
    with pytest.raises(ValueError,match='hashes changed'):load_request(data)


@pytest.mark.parametrize('status',['passed','failed','timed_out','not_run'])
def test_validation_bundle_matches_request_and_preserves_actual_status(status):
    w=workflow();data=w.validation_request().encode()
    report,files=validate_request(data,lambda files:(ValidationReport(status=status,stages=[StageResult(stage='test-only',status=status)]),{}))
    assert report.status==status
    assert json.loads(files['validation-report.json'])['status']==status
    context=json.loads(files['validation-context.json'])
    assert context['request_sha256']==hashlib.sha256(data).hexdigest()
    assert context['target_revision']==w.approval.target_revision
    assert context['graph_revision']==w.graph.revision()
    assert json.loads(files['original-extraction.json'])==w.original.model_dump()
    assert len(json.loads(files['corrections.json']))==1


def test_generated_zip_contains_request_and_question_groups():
    w=workflow();w.generate(lambda _:(ValidationReport(status='not_run'),{}))
    request,files=load_request(w.files['validation-request.json'].encode())
    assert request.target.revision()==w.target.revision()
    assert len(json.loads(w.files['question-groups.json']))==4


def test_request_requires_current_approval():
    w=workflow();g=w.graph.model_copy(deep=True);g.unknowns.append('New question')
    w.correct(g)
    with pytest.raises(ValueError):w.validation_request()
