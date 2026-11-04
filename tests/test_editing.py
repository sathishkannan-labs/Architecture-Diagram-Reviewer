import json
import pytest
from archreview.editing import edited_graph
from archreview.fixtures import load_fixture

@pytest.mark.parametrize('details',['[]','{}','{"components":[]}','{"boundaries":[],"unknowns":[],"assumptions":[],"components":[]}'])
def test_details_cannot_replace_tables(details):
    graph=load_fixture('single-server')
    with pytest.raises(ValueError):edited_graph([c.model_dump() for c in graph.components],[],details)

def test_no_change_roundtrip_and_corrected_connection():
    graph=load_fixture('single-server');d=graph.model_dump()
    details=json.dumps({key:d[key] for key in ('boundaries','unknowns','assumptions')})
    assert edited_graph(d['components'],d['connections'],details).revision()==graph.revision()
    d['connections'][0]['target']='missing'
    with pytest.raises(ValueError):edited_graph(d['components'],d['connections'],details)
