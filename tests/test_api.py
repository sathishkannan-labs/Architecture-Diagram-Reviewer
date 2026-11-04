import io
import zipfile
from fastapi.testclient import TestClient
from archreview.api import app

client=TestClient(app)

def test_local_adapter_workflow():
    session=client.post('/sessions/fixture',json={'fixture':'single-server'}).json()
    headers={'Authorization':'Bearer '+session['token']}
    assert client.post('/session/generate',headers=headers).status_code==409
    assert client.get('/session/download').status_code==401
    graph=session['graph'];graph['components'][1]['label']='Human edit'
    assert client.put('/session/graph',headers=headers,json=graph).status_code==200
    reviewed=client.post('/session/review',headers=headers)
    assert reviewed.status_code==200
    assert len(reviewed.json()['findings'])==6
    revision=__import__('archreview.models',fromlist=['TargetArchitecture']).TargetArchitecture.model_validate(reviewed.json()['target']).revision()
    assert client.post('/session/approve',headers=headers,json={'target_revision':revision}).status_code==409
    assert client.post('/session/approve',headers=headers,json={'target_revision':revision,'acknowledge_scope':True,'acknowledge_unknowns':True}).status_code==200
    assert client.post('/session/generate',headers=headers).json()['status'] in ('passed','not_run')
    request=client.get('/session/validation-request',headers=headers)
    assert request.status_code==200 and request.json()['approval']['target_revision']==revision
    download=client.get('/session/download',headers=headers)
    assert download.status_code==200
    with zipfile.ZipFile(io.BytesIO(download.content)) as z:assert 'traceability.json' in z.namelist()
    graph['components'][1]['label']='Second edit'
    client.put('/session/graph',headers=headers,json=graph)
    assert client.get('/session/download',headers=headers).status_code==409
    assert client.get('/session/validation-request',headers=headers).status_code==409

def test_bad_edits_rejected():
    session=client.post('/sessions/fixture',json={'fixture':'single-server'}).json()
    graph=session['graph'];graph['connections'][0]['target']='missing'
    assert client.put('/session/graph',headers={'Authorization':'Bearer '+session['token']},json=graph).status_code==422
