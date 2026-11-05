import io
import json
from pathlib import Path
import zipfile
import pytest
from streamlit.testing.v1 import AppTest
from archreview.fixtures import load_fixture
from archreview.models import Connection, Boundary, ValidationReport
from archreview.review import review
from archreview.coverage import control_coverage
from archreview.service import Workflow
from archreview.visualization import graph_dot


def workflow():
    w = Workflow(load_fixture('complex-ccm'))
    w.run_review()
    return w


def approve(w):
    w.approve(w.target.revision(), acknowledge_scope=True, acknowledge_unknowns=True)


def test_live_complex_regression_preserves_topology_and_unknowns():
    g=load_fixture('complex-ccm')
    assert {c.id for c in g.components} == {'internet_clients','application_load_balancer','api_gateway_service',
        'legacy_postgresql','customer_portal','orders_service','document_worker','primary_postgresql',
        'message_queue','document_object_storage','identity_provider','secrets_manager','logs_metrics','db_backups'}
    assert {(e.source,e.target) for e in g.connections} == {
        ('internet_clients','application_load_balancer'),('application_load_balancer','api_gateway_service'),
        ('api_gateway_service','customer_portal'),('api_gateway_service','orders_service'),
        ('customer_portal','orders_service'),('customer_portal','primary_postgresql'),
        ('orders_service','primary_postgresql'),('orders_service','message_queue'),
        ('message_queue','document_worker'),('document_worker','document_object_storage'),
        ('document_worker','primary_postgresql'),('internet_clients','legacy_postgresql')}
    assert len(g.boundaries)==2 and len(g.unknowns)==5
    by_id={c.id:c for c in g.components}
    assert by_id['customer_portal'].instances==2
    assert by_id['primary_postgresql'].exposure=='private' and by_id['primary_postgresql'].failover=='present'
    assert by_id['legacy_postgresql'].exposure=='public' and by_id['legacy_postgresql'].failover=='absent'


def test_confirmed_complex_findings_and_open_coverage_are_separate():
    findings=review(load_fixture('complex-ccm'))
    assert {f.id for f in findings if f.status=='confirmed'} == {
        'AR-001:api_gateway_service','AR-001:orders_service','AR-001:document_worker',
        'AR-003:legacy_postgresql','AR-006:legacy_postgresql'}
    assert {f.rule_id for f in findings if f.status=='unverified'} == {'AR-004','AR-005','AR-007','AR-008','AR-009','AR-010'}


def test_standalone_control_boxes_do_not_establish_coverage():
    rows=control_coverage(load_fixture('complex-ccm'))
    assert len(rows)==18 and all(r['status']=='unverified' for r in rows)


def test_direct_control_links_apply_only_to_referenced_service():
    g=load_fixture('complex-ccm')
    g.connections.append(Connection(source='identity_provider',target='customer_portal',evidence='Explicit auth integration'))
    g.connections.append(Connection(source='orders_service',target='secrets_manager',evidence='Explicit secret retrieval'))
    rows=control_coverage(g)
    shown={(r['component_id'],r['control']) for r in rows if r['status']=='relationship_shown'}
    assert shown=={('customer_portal','authentication'),('orders_service','secrets_manager')}
    # portal -> orders must not spread authentication coverage transitively.
    assert ('orders_service','authentication') not in shown


@pytest.mark.parametrize('mutation',['inferred','low_confidence','no_evidence','inferred_control','uncertain_service'])
def test_uncertain_links_never_establish_coverage(mutation):
    g=load_fixture('complex-ccm')
    e=Connection(source='identity_provider',target='customer_portal',evidence='Explicit auth integration')
    if mutation=='inferred':e.provenance='inferred'
    if mutation=='low_confidence':e.confidence=.4
    if mutation=='no_evidence':e.evidence=None
    if mutation=='inferred_control':next(c for c in g.components if c.id=='identity_provider').source='inferred'
    if mutation=='uncertain_service':next(c for c in g.components if c.id=='customer_portal').confidence=.2
    g.connections.append(e)
    assert all(r['status']=='unverified' for r in control_coverage(g))


def test_auth_boundary_scope_is_limited_to_its_members():
    g=load_fixture('complex-ccm')
    g.boundaries.append(Boundary(id='auth_boundary',kind='authentication',label='Authenticated portal',
        component_ids=['customer_portal'],evidence='Explicit auth boundary'))
    shown=[r for r in control_coverage(g) if r['status']=='relationship_shown']
    assert len(shown)==1 and shown[0]['component_id']=='customer_portal'


def test_every_component_has_an_honest_scope_disposition():
    w=workflow();scope={s.component_id:s for s in w.target.scope}
    assert set(scope)=={c.id for c in w.graph.components}
    assert scope['application_load_balancer'].disposition=='included'
    assert scope['db_backups'].disposition=='replaced'
    assert scope['identity_provider'].disposition=='omitted'
    for cid in ['customer_portal','api_gateway_service','orders_service','document_worker',
                'primary_postgresql','legacy_postgresql','message_queue','document_object_storage']:
        assert scope[cid].disposition=='unsupported'


def test_both_acknowledgments_are_required_by_service():
    w=workflow()
    for kwargs in [{},{'acknowledge_scope':True},{'acknowledge_unknowns':True}]:
        with pytest.raises(ValueError):w.approve(w.target.revision(),**kwargs)
        assert w.approval is None
    approve(w)
    assert w.approval.scope_acknowledged and w.approval.open_questions_acknowledged


@pytest.mark.parametrize('field',['scope','open_questions','acknowledgment'])
def test_tampering_cannot_bypass_generation(field):
    w=workflow();approve(w)
    if field=='scope':w.target.scope[0].disposition='included'
    if field=='open_questions':w.target.open_questions.clear()
    if field=='acknowledgment':w.approval.scope_acknowledged=False
    with pytest.raises(ValueError):w.generate(lambda _:pytest.fail('Validation must not run'))


def test_all_unknowns_scope_and_coverage_survive_download():
    w=workflow();approve(w)
    w.generate(lambda _:(ValidationReport(status='not_run'),{}))
    with zipfile.ZipFile(io.BytesIO(w.download())) as z:
        questions=json.loads(z.read('open-questions.json'))
        assert [q['question'] for q in questions if q['origin']=='graph']==w.graph.unknowns
        assert len(questions)==11
        assert len(json.loads(z.read('component-scope.json')))==14
        assert len(json.loads(z.read('control-coverage.json')))==18
        manifest=json.loads(z.read('traceability.json'))
        assert manifest['component_scope']==json.loads(z.read('component-scope.json'))
        assert manifest['open_questions']==questions
        assert manifest['approval']['scope_acknowledged']
        assert len(manifest['resources'])==26
        assert b'unsupported' in z.read('ADR.md')
        for unknown in w.graph.unknowns:assert unknown in z.read('ADR.md').decode()
        assert z.read('corrected-graph.dot').decode()==graph_dot(w.graph)


def test_graph_unknown_edit_revokes_approval_and_download():
    w=workflow();approve(w);old_revision=w.target.revision()
    changed=w.graph.model_copy(deep=True);changed.unknowns.append('New owner clarification required')
    w.correct(changed)
    assert w.target is w.approval is w.files is None
    w.run_review()
    assert w.target.revision()!=old_revision
    with pytest.raises(ValueError):w.download()


def test_preview_escapes_untrusted_labels_and_preserves_all_arrows():
    g=load_fixture('complex-ccm')
    g.components[0].label='Malicious "]; evil [URL="https://bad.test" ]\nnext'
    dot=graph_dot(g)
    assert dot.count(' -> ')==12
    assert '"label="' not in dot
    assert '\\"' in dot and '\\nnext' in dot
    assert len(dot.splitlines())==30


def test_complex_ui_requires_scope_and_unknown_acknowledgments(monkeypatch):
    monkeypatch.setenv('ARCHREVIEW_HOSTED','1')
    app=Path(__file__).resolve().parents[1]/'streamlit_app.py'
    at=AppTest.from_file(str(app)).run()
    at.selectbox[0].select('complex-ccm').run()
    def button(label):return next(b for b in at.button if b.label==label)
    button('Load fixture (no AI call)').click().run()
    assert not at.exception
    button('Run architecture review').click().run()
    at.checkbox[0].check().run()
    assert button('Record explicit approval').disabled
    at.checkbox[1].check().run()
    assert button('Record explicit approval').disabled
    at.checkbox[2].check().run()
    assert not button('Record explicit approval').disabled
    button('Record explicit approval').click().run()
    button('Generate approved Terraform').click().run()
    assert not at.exception
    assert len(json.loads(at.session_state.workflow.files['component-scope.json']))==14


def test_graph_preview_preserves_unicode_without_dot_unicode_escapes():
    from archreview.visualization import graph_dot
    g=load_fixture('single-server')
    g.components[0].label='தமிழ் Données 数据 🏗️ "quoted" \\ path\r\nnext'
    dot=graph_dot(g)
    assert 'தமிழ் Données 数据 🏗️' in dot
    assert '\\u' not in dot
    assert '\\"quoted\\"' in dot and '\\\\ path\\nnext' in dot

def test_svg_preview_preserves_nodes_edges_and_escapes_labels():
    import xml.etree.ElementTree as ET
    from archreview.visualization import graph_svg
    g=load_fixture('complex-ccm')
    g.components[0].label='<script>alert("no")</script> தமிழ்'
    g.connections[0].provenance='inferred'
    svg=graph_svg(g)
    root=ET.fromstring(svg)
    assert len([e for e in root.iter() if e.attrib.get('data-component')])==14
    edges=[e for e in root.iter() if e.attrib.get('data-connection')]
    assert len(edges)==12 and edges[0].attrib['stroke-dasharray']=='7 5'
    assert not any(e.tag.endswith('script') for e in root.iter())
    assert 'தமிழ்' in svg and '&lt;script&gt;' in svg
    assert svg==graph_svg(g)


def test_svg_handles_cycles_without_inventing_nodes():
    import xml.etree.ElementTree as ET
    from archreview.visualization import graph_svg
    g=load_fixture('single-server')
    g.connections.append(g.connections[0].model_copy(update={'source':g.components[-1].id,'target':g.components[0].id}))
    root=ET.fromstring(graph_svg(g))
    assert len([e for e in root.iter() if e.attrib.get('data-component')])==3
    assert len([e for e in root.iter() if e.attrib.get('data-connection')])==3
