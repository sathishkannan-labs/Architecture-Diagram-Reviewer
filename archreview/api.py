"""Optional local adapter. Opaque bearer sessions, no persistent accounts."""
import secrets
import threading
import time
from fastapi import FastAPI, File, UploadFile, Header, HTTPException
from pydantic import BaseModel
from .models import ArchitectureGraph
from .service import Workflow
from .meta import MetaClient, ExtractionError, MAX_BYTES
from .fixtures import load_fixture

app=FastAPI(title='Architecture Reviewer — local adapter')
_sessions={}
_guard=threading.Lock()

class Start(BaseModel):
    fixture: str

class ApprovalRequest(BaseModel):
    target_revision: str
    acknowledge_scope: bool = False
    acknowledge_unknowns: bool = False

class Settings(BaseModel):
    region: str
    name: str
    desired_capacity: int

def _store(workflow):
    with _guard:
        for token in list(_sessions):
            if time.monotonic()-_sessions[token].created>=3600:del _sessions[token]
        if len(_sessions)>=50:raise HTTPException(429,'Local session capacity reached')
        token=secrets.token_urlsafe(32);_sessions[token]=workflow
    return {'token':token,'mode':workflow.mode,'graph':workflow.graph.model_dump()}

def _get(authorization):
    if not authorization or not authorization.startswith('Bearer '):raise HTTPException(401,'Session token required')
    with _guard:w=_sessions.get(authorization[7:])
    if w is None:raise HTTPException(404,'Unknown session')
    try:w.expire()
    except ValueError:raise HTTPException(410,'Session expired') from None
    return w

@app.get('/health')
def health():return {'status':'ok','hosting':'local only'}

@app.post('/sessions/fixture')
def fixture(body:Start):
    try:return _store(Workflow(load_fixture(body.fixture)))
    except ValueError:raise HTTPException(422,'Unknown fixture') from None

@app.post('/sessions/extract')
def extract(image:UploadFile=File(...)):
    data=image.file.read(MAX_BYTES+1)
    client=MetaClient()
    try:return _store(Workflow(client.extract(data),'live_meta'))
    except ExtractionError as exc:raise HTTPException(422,str(exc)) from None
    finally:image.file.close();client.close()

@app.put('/session/graph')
def correct(graph:ArchitectureGraph,authorization:str|None=Header(default=None)):
    w=_get(authorization);w.correct(graph);return {'revision':w.graph.revision()}

@app.post('/session/review')
def review(authorization:str|None=Header(default=None)):
    w=_get(authorization);w.run_review();return {'findings':[f.model_dump() for f in w.findings],'target':w.target.model_dump()}

@app.put('/session/target')
def configure(body:Settings,authorization:str|None=Header(default=None)):
    w=_get(authorization)
    try:w.configure_target(**body.model_dump());return w.target.model_dump()
    except ValueError:raise HTTPException(422,'Invalid or unavailable target') from None

@app.post('/session/approve')
def approve(body:ApprovalRequest,authorization:str|None=Header(default=None)):
    w=_get(authorization)
    try:
        w.approve(body.target_revision, acknowledge_scope=body.acknowledge_scope, acknowledge_unknowns=body.acknowledge_unknowns)
        return w.approval.model_dump()
    except ValueError as exc:raise HTTPException(409,str(exc)) from None

@app.post('/session/generate')
def generate(authorization:str|None=Header(default=None)):
    w=_get(authorization)
    try:return w.generate().model_dump()
    except ValueError:raise HTTPException(409,'Approval required') from None

@app.get('/session/download')
def download(authorization:str|None=Header(default=None)):
    from fastapi.responses import Response
    w=_get(authorization)
    try:return Response(w.download(),media_type='application/zip',headers={'Content-Disposition':'attachment; filename="architecture.zip"'})
    except ValueError:raise HTTPException(409,'Generate approved target first') from None

@app.get('/session/validation-request')
def validation_request(authorization:str|None=Header(default=None)):
    from fastapi.responses import Response
    w=_get(authorization)
    try:return Response(w.validation_request(),media_type='application/json',headers={'Content-Disposition':'attachment; filename="validation-request.json"'})
    except ValueError as exc:raise HTTPException(409,str(exc)) from None
