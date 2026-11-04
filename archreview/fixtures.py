from .models import ArchitectureGraph
from pathlib import Path

NAMES = ('single-server','public-database','redundant-private','complex-ccm')

def load_fixture(name):
    if name not in NAMES:
        raise ValueError('Unknown fixture')
    if name == 'complex-ccm':
        return ArchitectureGraph.model_validate_json((Path(__file__).parent/'data'/'complex-ccm.json').read_text())
    redundant = name == 'redundant-private'
    public = name == 'public-database'
    nodes = [dict(id='internet',type='internet',label='Internet',evidence='Internet label'),
        dict(id='app',type='application_server',label='Application',instances=2 if redundant else 1,
             exposure='private' if redundant else 'public', evidence='Application x2, private' if redundant else 'Application x1, public'),
        dict(id='db',type='database',label='PostgreSQL',exposure='public' if public else 'private',
             failover='present' if redundant else 'absent',evidence='PostgreSQL, '+('public' if public else 'private')+', failover '+('present' if redundant else 'absent'))]
    edges=[dict(source='app',target='db',evidence='Application arrow to PostgreSQL')]
    if redundant:
        nodes += [dict(id='alb',type='load_balancer',label='ALB',evidence='ALB label'),
            dict(id='auth',type='authentication',label='Authentication',evidence='Authentication label'),
            dict(id='secrets',type='secrets_manager',label='Secrets manager',evidence='Secrets manager label'),
            dict(id='monitoring',type='monitoring',label='Monitoring',evidence='Monitoring label')]
        edges += [dict(source='internet',target='alb',evidence='Internet arrow to ALB'),
                  dict(source='alb',target='app',evidence='ALB arrow to application')]
    else:
        edges += [dict(source='internet',target='app',evidence='Internet arrow to application')]
    if public:
        edges += [dict(source='internet',target='db',evidence='Direct Internet arrow to public PostgreSQL')]
    return ArchitectureGraph.model_validate(dict(components=nodes,connections=edges,
        unknowns=[] if redundant else ['Authentication, secrets management and monitoring are not shown.']))
