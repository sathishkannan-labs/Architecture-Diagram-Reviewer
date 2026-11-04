from pathlib import Path
import json
from streamlit.testing.v1 import AppTest

APP=Path(__file__).resolve().parents[1]/'streamlit_app.py'

def button(at,label):return next(b for b in at.button if b.label==label)

def fixture_ui():
    at=AppTest.from_file(str(APP)).run()
    button(at,'Load fixture (no AI call)').click().run()
    assert not at.exception
    return at

def test_unsaved_edits_block_review_and_generation():
    at=fixture_ui()
    details=json.loads(at.text_area[0].value)
    details['unknowns'].append('Human question awaiting save')
    at.text_area[0].set_value(json.dumps(details)).run()
    assert button(at,'Run architecture review').disabled
    button(at,'Save human corrections').click().run()
    assert not button(at,'Run architecture review').disabled
    assert len(at.session_state.workflow.corrections)==1
    button(at,'Run architecture review').click().run()

    for checkbox in at.checkbox: checkbox.check().run()
    button(at,'Record explicit approval').click().run()
    button(at,'Generate trusted Terraform and run actual validation').click().run()
    assert not at.exception
    assert at.session_state.workflow.report.status in ('passed','not_run')
    name=next(t for t in at.text_input if t.label=='Name')
    name.set_value('changed-target').run()
    assert button(at,'Generate trusted Terraform and run actual validation').disabled
    button(at,'Save target settings (invalidates approval)').click().run()
    assert at.session_state.workflow.approval is None
    assert at.session_state.workflow.files is None
    assert not at.exception


def test_live_status_updates_after_successful_calls_and_resets(monkeypatch):
    import io
    from archreview.fixtures import load_fixture
    monkeypatch.delenv('ARCHREVIEW_HOSTED',raising=False)
    monkeypatch.delenv('RENDER',raising=False)
    monkeypatch.setenv('MODEL_API_KEY','test-only-placeholder')
    class FakeClient:
        fail_text=False
        def __init__(self,**kwargs):pass
        def text_probe(self):
            from archreview.meta import ExtractionError
            if self.fail_text:raise ExtractionError('Mocked request failed')
            return 'Meta text connection ready'
        def extract(self,data):return load_fixture('single-server')
        def close(self):pass
    monkeypatch.setattr('archreview.meta.MetaClient',FakeClient)
    monkeypatch.setattr('streamlit.file_uploader',lambda *args,**kwargs:io.BytesIO(b'mocked-image'))
    at=AppTest.from_file(str(APP)).run()
    at.radio[0].set_value('Live Meta extraction').run()
    button(at,'Test live text connection').click().run()
    assert at.session_state.meta_text_status=='verified'
    assert any('Text API: verified in this session' in e.value for e in at.sidebar.caption)
    assert any('Image extraction: not tested in this session' in e.value for e in at.sidebar.caption)
    button(at,'Extract with Meta').click().run()
    assert at.session_state.meta_image_status=='verified'
    assert any('Image extraction: verified in this session' in e.value for e in at.sidebar.caption)
    assert not at.exception
    FakeClient.fail_text=True
    button(at,'Test live text connection').click().run()
    assert any('Text API: last request failed' in e.value for e in at.sidebar.caption)
    assert any('Image extraction: verified in this session' in e.value for e in at.sidebar.caption)
    button(at,'Start a new session').click().run()
    assert any('Text API: not tested in this session' in e.value for e in at.sidebar.caption)
    assert any('Image extraction: not tested in this session' in e.value for e in at.sidebar.caption)
