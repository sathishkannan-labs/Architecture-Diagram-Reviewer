"""Explicit coverage of the fixed baseline; no automatic service consolidation."""
from .models import ScopeItem, OpenQuestion


def target_scope(graph, database_source_id=None):
    apps = [c for c in graph.components if c.type in ('web_server', 'application_server')]
    dbs = [c for c in graph.components if c.type == 'database']
    rows = []
    for c in graph.components:
        kind = c.type
        if kind == 'internet':
            status, ids, why = 'omitted', [], 'External clients are context; they are not provisioned.'
        elif kind == 'load_balancer':
            status, ids, why = 'included', ['D-APP'], 'The ALB role is included as a new HTTP ALB; existing listeners, TLS and routing are not imported.'
        elif kind == 'network':
            status, ids, why = 'replaced', ['D-NET'], 'A new two-AZ VPC baseline replaces this network role; no existing network is imported.'
        elif c in apps:
            status = 'replaced' if len(apps) == 1 else 'unsupported'
            ids = ['D-APP']
            why = ('One illustrative ASG replaces this application role; software, IAM and deployment are not configured.' if len(apps) == 1 else
                'Independent application/worker roles are not generated. The single illustrative ASG does not implement or consolidate these services.')
        elif kind == 'database':
            selected = c.id == database_source_id or (database_source_id is None and len(dbs) == 1)
            status = 'replaced' if selected else 'unsupported'
            ids = ['D-DB']
            why = ('One new Multi-AZ PostgreSQL baseline represents this selected database role; existing infrastructure and data are unchanged. Data migration is not implemented.' if selected else
                'Multiple database roles cannot be preserved by the single-RDS template. No source database or migration is selected automatically.')
        elif kind == 'backup':
            status, ids, why = 'replaced', ['D-DB'], 'Only seven-day backups on the new RDS are configured; the observed backup system, schedules and restore testing are not reproduced.'
        elif kind in ('authentication', 'secrets_manager', 'monitoring'):
            status, ids, why = 'omitted', [], 'Service-level '+kind.replace('_', ' ')+' integration and coverage are not generated. RDS-managed credentials do not implement application secrets access.'
        else:
            status, ids, why = 'unsupported', [], 'This component has no implementation in the fixed ALB/ASG/PostgreSQL template; it remains in the observed architecture only.'
        rows.append(ScopeItem(component_id=c.id, disposition=status, decision_ids=ids, explanation=why))
    return rows


def open_questions(graph, findings):
    rows = [OpenQuestion(id=f'Q-{i+1:03}', question=q, origin='graph') for i,q in enumerate(graph.unknowns)]
    rows.extend(OpenQuestion(id='Q-'+f.id, component_ids=f.component_ids,
        question=f.title+': '+f.evidence, origin='review') for f in findings if f.status == 'unverified')
    return rows


def require_acknowledgements(target, approval):
    if not approval.scope_acknowledged:
        raise ValueError('Explicit acknowledgment of the component scope and simplifications is required.')
    if target.open_questions and not approval.open_questions_acknowledged:
        raise ValueError('Acknowledge the unresolved questions before approval or generation.')
