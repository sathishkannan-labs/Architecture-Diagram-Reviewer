import io
import json
import httpx
from PIL import Image
import pytest
from archreview.meta import MetaClient,ExtractionError,prepare_image,MAX_BYTES
from archreview.fixtures import load_fixture


def png(size=(80,80)):
    b=io.BytesIO();Image.new('RGB',size,'white').save(b,format='PNG');return b.getvalue()

def reply(content):return {'choices':[{'finish_reason':'stop','message':{'content':content}}]}

def test_real_request_shape_resizing_and_graph_validation():
    calls=[]
    def handler(request):
        assert str(request.url)=='https://api.meta.ai/v1/chat/completions'
        calls.append(json.loads(request.content))
        return httpx.Response(200,json=reply(load_fixture('single-server').model_dump_json()))
    c=MetaClient(key='test-only',transport=httpx.MockTransport(handler))
    assert c.extract(png((2000,1000))).revision()==load_fixture('single-server').revision()
    content=calls[0]['messages'][1]['content']
    assert content[1]['type']=='image_url'
    import base64
    image=Image.open(io.BytesIO(base64.b64decode(content[1]['image_url']['url'].split(',')[1])))
    assert image.size==(1600,800)
    c.close()

@pytest.mark.parametrize('body',['not-json','{"components":[]}',load_fixture('single-server').model_dump_json().replace('"observed"','"user_corrected"')])
def test_malformed_extraction(body):
    c=MetaClient(key='test-only',transport=httpx.MockTransport(lambda r:httpx.Response(200,json=reply(body))))
    with pytest.raises(ExtractionError):c.extract(png())
    c.close()

@pytest.mark.parametrize('status',[401,403,400,429,503])
def test_bounded_retries_and_safe_errors(status):
    calls=[]
    def handler(r):calls.append(r);return httpx.Response(status,json={'error':'do not expose this credential'})
    c=MetaClient(key='private-test-key',transport=httpx.MockTransport(handler),sleep=lambda _:None)
    with pytest.raises(ExtractionError) as exc:c.text_probe()
    assert len(calls)==(3 if status in (429,503) else 1)
    assert 'private-test-key' not in str(exc.value) and 'do not expose' not in str(exc.value)
    c.close()

def test_missing_credentials_prevents_network(monkeypatch):
    monkeypatch.delenv('MODEL_API_KEY',raising=False)
    c=MetaClient(transport=httpx.MockTransport(lambda _:pytest.fail('Network must not be called')))
    with pytest.raises(ExtractionError):c.text_probe()
    c.close()

@pytest.mark.parametrize('data',[b'bad',b'x'*(MAX_BYTES+1)])
def test_bad_upload(data):
    with pytest.raises(ExtractionError):prepare_image(data)

def test_decoded_size_limit():
    with pytest.raises(ExtractionError):prepare_image(png((5000,4100)))


@pytest.mark.parametrize('error',[httpx.RemoteProtocolError,httpx.ProxyError,httpx.DecodingError])
def test_other_transport_failures_are_sanitized(error):
    calls=[]
    def handler(request):
        calls.append(request)
        raise error('sensitive upstream details')
    c=MetaClient(key='private-test-key',transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(ExtractionError,match='Meta request failed') as exc:c.text_probe()
        assert len(calls)==1 and 'sensitive' not in str(exc.value)
    finally:c.close()


@pytest.mark.parametrize('choice',[None,'unexpected',42])
def test_invalid_choice_shape_is_sanitized(choice):
    c=MetaClient(key='test-only',transport=httpx.MockTransport(lambda r:httpx.Response(200,json={'choices':[choice]})))
    try:
        with pytest.raises(ExtractionError,match='unsupported response format'):c.text_probe()
    finally:c.close()


def test_unsupported_image_preserves_specific_error():
    b=io.BytesIO();Image.new('RGB',(10,10)).save(b,format='GIF')
    with pytest.raises(ExtractionError,match='Only PNG/JPEG'):prepare_image(b.getvalue())

@pytest.mark.parametrize('fence',['json','JSON',''])
def test_complete_fenced_graph_needs_one_call(fence):
    calls=[]
    body='\x60\x60\x60'+fence+'\n'+load_fixture('single-server').model_dump_json()+'\n\x60\x60\x60'
    def handler(request):
        calls.append(request)
        return httpx.Response(200,json=reply(body))
    c=MetaClient(key='test-only',transport=httpx.MockTransport(handler))
    try:
        assert c.extract(png()).revision()==load_fixture('single-server').revision()
        assert len(calls)==1
    finally:c.close()


def test_one_schema_retry_reuses_image_without_echoing_invalid_output():
    calls=[]
    def handler(request):
        calls.append(json.loads(request.content))
        return httpx.Response(200,json=reply('private-invalid-marker' if len(calls)==1 else load_fixture('single-server').model_dump_json()))
    c=MetaClient(key='test-only',transport=httpx.MockTransport(handler))
    try:
        assert c.extract(png()).revision()==load_fixture('single-server').revision()
        assert len(calls)==2
        assert calls[0]['messages'][1]==calls[1]['messages'][1]
        feedback=calls[1]['messages'][-1]['content']
        assert 'private-invalid-marker' not in feedback
        assert 'json_invalid' in feedback and 'never invent facts' in feedback
    finally:c.close()


@pytest.mark.parametrize('body',['not-json','{"components":[]}',load_fixture('single-server').model_dump_json().replace('"observed"','"user_corrected"'),'Explanation:\n'+load_fixture('single-server').model_dump_json()])
def test_failed_recovery_stops_after_exactly_two_calls(body):
    calls=[]
    def handler(request):
        calls.append(request)
        return httpx.Response(200,json=reply(body))
    c=MetaClient(key='test-only',transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(ExtractionError,match='after two attempts'):c.extract(png())
        assert len(calls)==2
    finally:c.close()


@pytest.mark.parametrize('reason',['length','content_filter'])
def test_refusal_or_incomplete_response_does_not_retry_schema(reason):
    calls=[]
    def handler(request):
        calls.append(request)
        return httpx.Response(200,json={'choices':[{'finish_reason':reason,'message':{'content':'{}'}}]})
    c=MetaClient(key='test-only',transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(ExtractionError,match='incomplete or refused'):c.extract(png())
        assert len(calls)==1
    finally:c.close()
