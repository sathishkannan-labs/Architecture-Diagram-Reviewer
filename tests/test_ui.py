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
    assert button(at,'Run the six-rule review').disabled
    button(at,'Save human corrections').click().run()
    assert not button(at,'Run the six-rule review').disabled
    assert len(at.session_state.workflow.corrections)==1
    button(at,'Run the six-rule review').click().run()
    at.checkbox[0].check().run()
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
