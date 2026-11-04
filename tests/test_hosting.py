import json
import httpx
import pytest
from archreview import hosting
from archreview.fixtures import load_fixture
from archreview.meta import MetaClient, ExtractionError
from archreview.validation import validate
from streamlit.testing.v1 import AppTest
from pathlib import Path


@pytest.fixture
def public(monkeypatch):
    monkeypatch.setenv('ARCHREVIEW_HOSTED', '1')
    monkeypatch.setenv('DEMO_CODE', 'private-test-demo-code')
    monkeypatch.setattr(hosting, 'LIVE_BUDGET', hosting.PreviewBudget())
    # Meta imports the singleton; replace that reference for isolated tests too.
    monkeypatch.setattr('archreview.meta.LIVE_BUDGET', hosting.LIVE_BUDGET)


def test_render_detection_cannot_be_disabled_by_false_flag(monkeypatch):
    monkeypatch.setenv('RENDER', 'true')
    monkeypatch.setenv('ARCHREVIEW_HOSTED', '0')
    assert hosting.hosted()


def test_validation_never_executes_in_public_preview(public, monkeypatch):
    monkeypatch.setattr('archreview.validation.shutil.which', lambda _: pytest.fail('No binary lookup allowed'))
    report, formatted = validate({'main.tf': 'invalid Terraform'})
    assert report.status == 'not_run' and report.stages[0].stage == 'hosting'
    assert formatted == {}


@pytest.mark.parametrize('code', ['', 'wrong'])
def test_live_requests_without_authorization_never_reach_network(public, code):
    client = MetaClient(key='test-key', demo_code=code,
        transport=httpx.MockTransport(lambda _: pytest.fail('Unauthorized network request')))
    try:
        with pytest.raises(ExtractionError, match='demo code'):
            client.text_probe()
    finally:
        client.close()


def test_missing_server_code_fails_closed(public, monkeypatch):
    monkeypatch.delenv('DEMO_CODE')
    assert not hosting.live_authorized('')
    with pytest.raises(hosting.PreviewLimit):
        with hosting.PreviewBudget().request(''):
            pytest.fail('Missing server code must block')


def test_shared_budget_concurrency_window_and_lifetime(public):
    now = [0]
    budget = hosting.PreviewBudget(clock=lambda: now[0])
    code = 'private-test-demo-code'
    with budget.request(code):
        with pytest.raises(hosting.PreviewLimit, match='already running'):
            with budget.request(code):
                pass
    for _ in range(19):
        with budget.request(code):
            pass
    with pytest.raises(hosting.PreviewLimit, match='budget'):
        with budget.request(code):
            pass
    now[0] = 3601
    with budget.request(code):
        pass
    budget.total = 100
    with pytest.raises(hosting.PreviewLimit, match='budget'):
        with budget.request(code):
            pass


def test_authorized_retry_is_one_operation_and_releases_slot(public):
    calls = []
    def handler(_):
        calls.append(1)
        return httpx.Response(503)
    client = MetaClient(key='test-key', demo_code='private-test-demo-code',
        transport=httpx.MockTransport(handler), sleep=lambda _: None)
    try:
        for _ in range(2):
            with pytest.raises(ExtractionError):
                client.text_probe()
        assert len(calls) == 6
        assert hosting.LIVE_BUDGET.total == 2
    finally:
        client.close()


def test_hosted_ui_fixture_to_download_and_live_gate(public, monkeypatch):
    monkeypatch.delenv('MODEL_API_KEY', raising=False)
    app = Path(__file__).resolve().parents[1] / 'streamlit_app.py'
    at = AppTest.from_file(str(app)).run()
    def click(label):
        next(b for b in at.button if b.label == label).click().run()
    click('Load fixture (no AI call)')
    click('Run architecture review')

    for checkbox in at.checkbox: checkbox.check().run()
    click('Record explicit approval')
    click('Generate trusted Terraform (validation disabled)')
    assert not at.exception
    workflow = at.session_state.workflow
    assert workflow.report.status == 'not_run'
    assert json.loads(workflow.files['validation-report.json'])['stages'][0]['stage'] == 'hosting'
    assert len(workflow.download()) > 0
    at.radio[0].set_value('Live Meta extraction').run()
    assert next(b for b in at.button if b.label == 'Test live text connection').disabled
    assert next(b for b in at.button if b.label == 'Extract with Meta').disabled
