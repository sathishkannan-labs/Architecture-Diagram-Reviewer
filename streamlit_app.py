import json
import os
from pathlib import Path
import pandas as pd
import streamlit as st
from archreview.meta import MetaClient, ExtractionError
from archreview.fixtures import NAMES, load_fixture
from archreview.models import ArchitectureGraph, ValidationReport
from archreview.service import Workflow
from archreview.editing import edited_graph
from archreview.config import load_local_env
from archreview.hosting import hosted, live_authorized
from archreview.visualization import graph_dot
from archreview.coverage import control_coverage

load_local_env(Path(__file__).with_name(".env"))

st.set_page_config(page_title='Architecture Diagram Reviewer',page_icon='🏗️',layout='wide')
st.title('Architecture Diagram Reviewer')
st.caption('Extract → correct → review → approve → generate → validate → download')
st.warning(ValidationReport().limitations)
st.sidebar.subheader('Demo status')
st.sidebar.write('Meta key: ' + ('configured (live access unverified)' if os.getenv('MODEL_API_KEY') else 'not configured'))
public_preview = hosted()
demo_code = ''
if public_preview:
    st.sidebar.caption('Public preview: Terraform execution is disabled; downloads report not_run.')
    demo_code = st.sidebar.text_input('Live demo code', type='password')
else:
    st.sidebar.caption('Docker provides the full restricted validator. Python-only mode supports editing and downloads.')
if st.sidebar.button('Start a new session'):
    st.session_state.pop('workflow',None)
    st.session_state.upload_revision=st.session_state.get('upload_revision',0)+1
    st.rerun()
st.info(('Public preview. Terraform validation is disabled. Sessions may reset when the free host sleeps. ' if public_preview else 'Local demonstration. ') + 'Live extraction sends the resized diagram to Meta. Fixture examples are synthetic and do not satisfy live acceptance.')
if 'upload_revision' not in st.session_state: st.session_state.upload_revision=0
mode=st.radio('Source',['Fixture example','Live Meta extraction'],horizontal=True)
if mode=='Fixture example':
    name=st.selectbox('Synthetic diagram',NAMES)
    st.image(str(Path(__file__).resolve().parent / 'examples' / (name+'.png')),width=650)
    if st.button('Load fixture (no AI call)'):
        st.session_state.workflow=Workflow(load_fixture(name),'fixture');st.rerun()
else:
    live_enabled = bool(os.getenv('MODEL_API_KEY')) and (not public_preview or live_authorized(demo_code))
    if public_preview and not live_enabled:
        st.info('Live mode needs an API key configured by the owner and the correct demo code. Fixture examples remain available.')
    if st.button('Test live text connection', disabled=not live_enabled):
        client=MetaClient(demo_code=demo_code)
        try:
            client.text_probe();st.success('Live text request succeeded. Image acceptance is still required.')
        except ExtractionError as exc:st.error(str(exc))
        finally:client.close()
    upload=st.file_uploader('PNG or JPEG, at most 5 MB / 20 megapixels',type=['png','jpg','jpeg'],key='image_'+str(st.session_state.upload_revision))
    if st.button('Extract with Meta',disabled=upload is None or not live_enabled):
        client=MetaClient(demo_code=demo_code)
        try:
            with st.spinner('Extracting architecture from the real image…'):
                graph=client.extract(upload.getvalue())
            st.session_state.workflow=Workflow(graph,'live_meta')
            st.session_state.upload_revision+=1
            st.rerun()
        except ExtractionError as exc:st.error(str(exc))
        finally:client.close()

w=st.session_state.get('workflow')
if not w:st.stop()
try:w.expire()
except ValueError as exc:
    st.session_state.pop('workflow',None);st.error(str(exc));st.stop()
st.subheader('1 · Correct the extracted observations')
st.caption('Active source: '+w.mode+' · graph revision '+w.graph.revision()[:16])
counts=st.columns(4)
for column,title,value in zip(counts,['Components','Connections','Boundaries','Unresolved observations'],
    [len(w.graph.components),len(w.graph.connections),len(w.graph.boundaries),len(w.graph.unknowns)]):
    column.metric(title,value)
with st.expander('Corrected graph preview', expanded=True):
    st.caption('Saved observations only. Public = red; private = green; unknown = gray. Dashed arrows are inferred. Control links show relationships, not effectiveness.')
    st.graphviz_chart(graph_dot(w.graph), use_container_width=True)
    if w.graph.boundaries:
        st.dataframe([{'Boundary':b.label,'Components':', '.join(b.component_ids),'Provenance':b.source} for b in w.graph.boundaries],hide_index=True)
with st.expander('Original extraction (retained for audit)'):
    st.json(w.original.model_dump())
key=w.graph.revision()
components=st.data_editor(pd.DataFrame([c.model_dump() for c in w.graph.components]),
    num_rows='dynamic',disabled=['source'],key='nodes_'+key,use_container_width=True)
cols=['source','target','evidence','confidence','provenance']
connections=st.data_editor(pd.DataFrame([e.model_dump() for e in w.graph.connections],columns=cols),
    num_rows='dynamic',disabled=['provenance'],key='edges_'+key,use_container_width=True)
with st.expander('Boundaries, unresolved information and assumptions'):
    details=st.text_area('JSON for boundaries / unknowns / assumptions',json.dumps({k:w.graph.model_dump()[k] for k in ['boundaries','unknowns','assumptions']},indent=2),height=220,key='details_'+key)
clean=lambda frame:json.loads(frame.to_json(orient='records'))
try:
    candidate=edited_graph(clean(components),clean(connections),details)
    pending_edits=candidate.revision()!=w.graph.revision()
    invalid_edits=False
except (ValueError,TypeError):
    candidate=None;pending_edits=True;invalid_edits=True
if pending_edits:
    st.warning('Unsaved graph edits. Save valid corrections before review, approval, generation or download.')
if st.button('Save human corrections'):
    if invalid_edits:
        st.error('Invalid edit. Check unique IDs, connection references, field values and details JSON. No correction was saved.')
    else:
        w.correct(candidate);st.rerun()
with st.expander('Quick label correction'):
    selected=st.selectbox('Component to correct',[c.id for c in w.graph.components],key='quick_component_'+key)
    current=next(c for c in w.graph.components if c.id==selected)
    with st.form('quick_label_'+key+'_'+selected):
        label=st.text_input('Corrected component label',current.label)
        evidence=st.text_input('Correction evidence',current.evidence or '')
        if st.form_submit_button('Record label correction',disabled=pending_edits):
            try:
                candidate=w.graph.model_copy(deep=True)
                edited=next(c for c in candidate.components if c.id==selected)
                edited.label=label;edited.evidence=evidence
                w.correct(candidate);st.rerun()
            except ValueError:st.error('A component label must contain 1–200 characters.')
if w.corrections:st.caption(f'{len(w.corrections)} human correction revision(s) recorded.')
st.subheader('2 · Review risk evidence')
if st.button('Run architecture review',disabled=pending_edits):
    w.run_review();st.rerun()
if w.findings is None:st.stop()
if not w.findings:st.success('No findings from the implemented diagram checks. This is not a security assessment.')
else:
    left,right=st.columns(2)
    left.metric('Confirmed weaknesses',sum(f.status=='confirmed' for f in w.findings))
    right.metric('Unverified controls or facts',sum(f.status=='unverified' for f in w.findings))
    st.dataframe([{'Finding':f.id,'Severity':f.severity,'Status':f.status,'Title':f.title,'Components':', '.join(f.component_ids) or 'Missing diagram information'} for f in w.findings],use_container_width=True,hide_index=True)
    for finding in w.findings:
        with st.expander(finding.id+' · '+finding.title):
            st.write('Evidence: '+finding.evidence)
            st.write('Recommendation: '+finding.recommendation)
st.subheader('Unresolved questions carried into approval')
st.caption('Diagram unknowns and unverified review findings remain open. Acknowledgment does not resolve them.')
if w.target.open_questions:
    st.dataframe([{'ID':q.id,'Origin':q.origin,'Components':', '.join(q.component_ids) or 'Diagram information',
        'Question':q.question} for q in w.target.open_questions], hide_index=True, use_container_width=True)
else:st.info('No unresolved questions were recorded. This does not establish production readiness.')
with st.expander('Service-level control coverage',expanded=True):
    st.caption('Only sufficiently grounded direct connections or applicable authentication boundaries count as shown relationships. Transitive links and standalone control boxes do not prove service coverage.')
    st.dataframe(control_coverage(w.graph),hide_index=True,use_container_width=True)
st.subheader('3 · Approve the proposed AWS target')
st.caption('The corrected observations stay separate. The target adds a two-AZ ALB, private ASG instances, and private Multi-AZ PostgreSQL.')
region=st.selectbox('Region',['us-east-1','us-west-2','eu-west-1'],index=['us-east-1','us-west-2','eu-west-1'].index(w.target.region),key='region_'+w.target.revision())
target_name=st.text_input('Name',w.target.name,key='name_'+w.target.revision())
capacity=st.number_input('Desired application instances',2,4,w.target.desired_capacity,key='capacity_'+w.target.revision())
pending_target=(region!=w.target.region or target_name!=w.target.name or capacity!=w.target.desired_capacity)
if pending_target:st.info('Save target settings before approving or generating this target.')
if st.button('Save target settings (invalidates approval)',disabled=pending_edits):
    try:w.configure_target(region=region,name=target_name,desired_capacity=capacity);st.rerun()
    except ValueError:st.error('Use a 3–20 character lowercase target name, beginning with a letter.')
st.table([{'ID':d.id,'Proposed change':d.description,'Observed components':', '.join(d.component_ids),'Finding references':', '.join(d.finding_ids) or 'Baseline assumption'} for d in w.target.decisions])
st.subheader('Component scope and simplifications')
st.warning('This fixed target is a new illustrative baseline. It does not reproduce the entire uploaded architecture or migrate existing services/data. Unsupported roles are not automatically merged into the ASG or RDS.')
labels={c.id:c.label for c in w.graph.components}
st.dataframe([{'Component':s.component_id,'Label':labels[s.component_id],'Disposition':s.disposition,
    'Decision references':', '.join(s.decision_ids) or 'No generated implementation','Explanation':s.explanation} for s in w.target.scope],hide_index=True,use_container_width=True)
unsupported=sum(s.disposition=='unsupported' for s in w.target.scope)
if unsupported:st.error(f'{unsupported} component role(s) are unsupported by this template. They remain in the observed graph and will not be implemented by the generated Terraform.')
with st.expander('Full proposed target and baseline assumptions'):st.json(w.target.model_dump())
st.warning('Unresolved in target: TLS, authentication, monitoring, application packaging, credential access and deployment readiness. HTTP is illustrative; private instances have no internet egress. Read the generated ADR.')
consent=st.checkbox('I approve this target revision and its explicit baseline assumptions.',key='consent_'+w.target.revision())
scope_consent=st.checkbox('I acknowledge the component scope, omissions, unsupported roles and accepted simplifications.',key='scope_consent_'+w.target.revision())
unknown_consent=st.checkbox('I acknowledge that the listed questions remain unresolved.',key='unknown_consent_'+w.target.revision()) if w.target.open_questions else True
if st.button('Record explicit approval',disabled=not (consent and scope_consent and unknown_consent) or pending_edits or pending_target):
    w.approve(w.target.revision(),acknowledge_scope=scope_consent,acknowledge_unknowns=unknown_consent);st.rerun()
if not w.approval:st.stop()
st.success('Approved revision '+w.approval.target_revision[:16])
st.subheader('4 · Generate and download' if public_preview else '4 · Generate and validate')
if st.button('Generate trusted Terraform (validation disabled)' if public_preview else 'Generate trusted Terraform and run actual validation',disabled=pending_edits or pending_target):
    try:
        with st.spinner('Validating offline, up to 180 seconds…'):w.generate()
        st.rerun()
    except ValueError as exc:st.error(str(exc))
if w.report:
    st.write('Validation status: **'+w.report.status+'**')
    if w.report.status=='not_run':st.info('Actual Terraform validation is unavailable in this runtime. The download includes the reason and all generated artifacts.')
    elif w.report.status=='passed':st.success('Terraform initialization and validation passed. This does not establish security or application readiness.')
    elif w.report.status=='timed_out':st.warning('Validation exceeded the time limit. No successful validation is claimed.')
    else:st.error('Validation failed. Inspect the stage output and download the report for diagnosis.')
    for stage in w.report.stages:
        with st.expander(stage.stage+' · '+stage.status,expanded=stage.status!='passed'):st.code(stage.output,language='text')
    manifest=json.loads(w.files['traceability.json'])
    st.caption('Resource traceability · approved target '+manifest['target_revision'][:16])
    st.dataframe([{'Resource':address,'Decision':item['decision_id'],'Template output':item['file']} for address,item in manifest['resources'].items()],hide_index=True,use_container_width=True)
    with st.expander('Full traceability manifest'):st.json(manifest)
    with st.expander('Architecture decision record'):st.code(w.files['ADR.md'],language='markdown')
    st.caption(f'Download includes component-scope.json, open-questions.json and control-coverage.json; {len(w.target.open_questions)} question(s) remain unresolved.')
    st.download_button('Download artifacts · '+w.report.status,w.download(),file_name='architecture-'+w.report.status+'.zip',mime='application/zip',disabled=pending_edits or pending_target)
