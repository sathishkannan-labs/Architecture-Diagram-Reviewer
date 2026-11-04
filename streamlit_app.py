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

load_local_env(Path(__file__).with_name(".env"))

st.set_page_config(page_title='Architecture Diagram Reviewer',page_icon='🏗️',layout='wide')
st.title('Architecture Diagram Reviewer')
st.caption('Extract → correct → review → approve → generate → validate → download')
st.warning(ValidationReport().limitations)
st.sidebar.subheader('Demo status')
st.sidebar.write('Meta key: ' + ('configured (live access unverified)' if os.getenv('MODEL_API_KEY') else 'not configured'))
st.sidebar.caption('Docker provides the full restricted validator. Python-only mode supports editing and downloads.')
if st.sidebar.button('Start a new session'):
    st.session_state.pop('workflow',None)
    st.session_state.upload_revision=st.session_state.get('upload_revision',0)+1
    st.rerun()
st.info('Local demonstration. Live extraction sends the resized diagram to Meta. Fixture examples are synthetic and do not satisfy live acceptance.')
if 'upload_revision' not in st.session_state: st.session_state.upload_revision=0
mode=st.radio('Source',['Fixture example','Live Meta extraction'],horizontal=True)
if mode=='Fixture example':
    name=st.selectbox('Synthetic diagram',NAMES)
    st.image(str(Path(__file__).resolve().parent / 'examples' / (name+'.png')),width=650)
    if st.button('Load fixture (no AI call)'):
        st.session_state.workflow=Workflow(load_fixture(name),'fixture');st.rerun()
else:
    if st.button('Test live text connection'):
        client=MetaClient()
        try:
            client.text_probe();st.success('Live text request succeeded. Image acceptance is still required.')
        except ExtractionError as exc:st.error(str(exc))
        finally:client.close()
    upload=st.file_uploader('PNG or JPEG, at most 5 MB / 20 megapixels',type=['png','jpg','jpeg'],key='image_'+str(st.session_state.upload_revision))
    if st.button('Extract with Meta',disabled=upload is None):
        client=MetaClient()
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
if st.button('Run the six-rule review',disabled=pending_edits):
    w.run_review();st.rerun()
if w.findings is None:st.stop()
if not w.findings:st.success('No findings from these six diagram checks. This is not a security assessment.')
else:
    left,right=st.columns(2)
    left.metric('Confirmed weaknesses',sum(f.status=='confirmed' for f in w.findings))
    right.metric('Unverified controls or facts',sum(f.status=='unverified' for f in w.findings))
    st.dataframe([{'Finding':f.id,'Severity':f.severity,'Status':f.status,'Title':f.title,'Components':', '.join(f.component_ids) or 'Missing diagram information'} for f in w.findings],use_container_width=True,hide_index=True)
    for finding in w.findings:
        with st.expander(finding.id+' · '+finding.title):
            st.write('Evidence: '+finding.evidence)
            st.write('Recommendation: '+finding.recommendation)
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
with st.expander('Full proposed target and baseline assumptions'):st.json(w.target.model_dump())
st.warning('Unresolved in target: TLS, authentication, monitoring, application packaging, credential access and deployment readiness. HTTP is illustrative; private instances have no internet egress. Read the generated ADR.')
consent=st.checkbox('I approve this target revision and its explicit baseline assumptions.',key='consent_'+w.target.revision())
if st.button('Record explicit approval',disabled=not consent or pending_edits or pending_target):w.approve(w.target.revision());st.rerun()
if not w.approval:st.stop()
st.success('Approved revision '+w.approval.target_revision[:16])
st.subheader('4 · Generate and validate')
if st.button('Generate trusted Terraform and run actual validation',disabled=pending_edits or pending_target):
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
    st.download_button('Download artifacts · '+w.report.status,w.download(),file_name='architecture-'+w.report.status+'.zip',mime='application/zip',disabled=pending_edits or pending_target)
