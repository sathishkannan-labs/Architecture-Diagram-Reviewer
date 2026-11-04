from archreview.fixtures import load_fixture
from archreview.service import Workflow
w=Workflow(load_fixture('single-server'))
w.run_review();w.approve(w.target.revision());report=w.generate()
print(report.model_dump_json(indent=2))
if report.status != 'passed':
    raise SystemExit('Offline initialization/validation gate failed')
