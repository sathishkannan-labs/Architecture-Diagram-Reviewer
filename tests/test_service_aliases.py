import pytest
from archreview.fixtures import load_fixture
from archreview.review import review
from archreview.scope import target_scope


@pytest.mark.parametrize('label,rule',[
    ('Queue','AR-009'),('Amazon SQS','AR-009'),('Kafka events','AR-009'),('RabbitMQ','AR-009'),
    ('Object storage','AR-010'),('Object-storage','AR-010'),('S3 bucket','AR-010'),('Archive bucket','AR-010')])
def test_aliases_raise_questions_without_claiming_controls_are_absent(label,rule):
    graph=load_fixture('single-server')
    item=graph.components[-1]
    item.type='other';item.label=label
    findings=[f for f in review(graph) if f.rule_id==rule]
    assert len(findings)==1 and findings[0].status=='unverified'
    assert next(s for s in target_scope(graph,None) if s.component_id==item.id).disposition=='unsupported'


@pytest.mark.parametrize('label',['enqueue handler','bucketeer','s3proxy','Kafkaesque processor'])
def test_aliases_respect_word_boundaries(label):
    graph=load_fixture('single-server')
    graph.components[-1].type='other';graph.components[-1].label=label
    assert not any(f.rule_id in ('AR-009','AR-010') for f in review(graph))
