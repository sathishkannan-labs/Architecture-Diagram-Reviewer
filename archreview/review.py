from .models import ArchitectureGraph, Decision, Finding, TargetArchitecture
from .coverage import control_coverage
from .scope import target_scope, open_questions


def review(graph: ArchitectureGraph) -> list[Finding]:
    findings = []
    components_by_id = {c.id: c for c in graph.components}
    def grounded(component):
        return component.source != 'inferred' and bool(component.evidence) and (component.confidence is None or component.confidence >= 0.8)
    def add(rule, title, severity, components, evidence, recommendation, confirmed=False):
        proven = confirmed and all(grounded(c) for c in components)
        findings.append(Finding(id=rule+":"+("+".join(c.id for c in components) or "missing-information"), rule_id=rule, title=title, severity=severity,
            component_ids=[c.id for c in components], evidence=evidence,
            recommendation=recommendation, confidence=0.95 if proven else 0.6,
            status='confirmed' if proven else 'unverified'))
    apps = [c for c in graph.components if c.type in ('web_server', 'application_server')]
    dbs = [c for c in graph.components if c.type == 'database']
    for app in apps:
        if app.instances is None or app.instances == 1 or not grounded(app):
            add('AR-001', 'Potential application single point of failure', 'high', [app],
                f'{app.label}: instance count is {app.instances or "unknown"}; redundancy must be confirmed. Diagram evidence: {app.evidence or "not available"}.',
                'Confirm redundancy; use at least two instances across availability zones.', app.instances == 1)
    for db in dbs:
        internet_edges = [e for e in graph.connections if e.target == db.id and
            components_by_id[e.source].type == 'internet']
        if db.exposure == 'public' or internet_edges:
            explicit = db.exposure == 'public' or any(e.provenance != 'inferred' and e.evidence and (e.confidence is None or e.confidence >= 0.8) and grounded(components_by_id[e.source]) for e in internet_edges)
            add('AR-003', 'Database may be directly exposed to the internet', 'critical', [db],
                'Public database placement or an Internet connection is represented. Diagram evidence: '+(db.evidence or 'not available')+'; connection evidence: '+('; '.join(e.evidence or 'not available' for e in internet_edges) or 'none')+'.',
                'Place the database in isolated private subnets; permit only application traffic.', explicit)
        elif db.exposure == 'unknown' or not grounded(db):
            add('AR-003', 'Database exposure is unknown', 'critical', [db],
                'Private database placement is not established by sufficiently grounded diagram evidence.', 'Confirm private placement and restricted access.')
    for db in dbs:
        if db.failover != 'present' or not grounded(db):
            add('AR-006', 'Database failover not established', 'high', [db],
                f'Database failover is reported as {db.failover}; provenance is {db.source}. Diagram evidence: {db.evidence or "not available"}.', 'Confirm recovery requirements; consider RDS Multi-AZ.', db.failover == 'absent')
    coverage = control_coverage(graph)
    for kind, rule, title, severity in [
        ('authentication','AR-004','Authentication coverage unverified','high'),
        ('secrets_manager','AR-005','Secrets management coverage unverified','high'),
        ('monitoring','AR-008','Monitoring coverage unverified','medium'),
        ('backup','AR-007','Backup and recovery coverage unverified','high')]:
        missing = [r['component_id'] for r in coverage if r['control'] == kind and r['status'] == 'unverified']
        if missing:
            add(rule, title, severity, [components_by_id[cid] for cid in missing],
                'No sufficiently grounded service relationship or applicable boundary establishes '+kind.replace('_',' ')+
                ' coverage for: '+', '.join(missing)+'. A standalone control box does not establish coverage; real-world absence is not proven.',
                'Confirm applicable service relationships, configuration and effectiveness with the owner. Record unknowns without inventing links.')
    for c in graph.components:
        if c.type == 'other' and 'queue' in c.label.lower():
            add('AR-009','Queue resilience unverified','medium',[c],
                'Queue failover annotation: '+c.failover+'. Delivery guarantees, retries and dead-letter handling are not established by this schema. Diagram evidence: '+(c.evidence or 'not available'),
                'Confirm redundancy, delivery semantics, retry policy and dead-letter handling. Do not assume they are absent.')
        if c.type == 'other' and 'object storage' in c.label.lower():
            add('AR-010','Object storage access policy unverified','high',[c],
                'Private placement alone does not establish an access policy. Diagram evidence: '+(c.evidence or 'not available'),
                'Confirm bucket policy, least-privilege access and encryption with the owner.')
    return findings


def propose_target(graph: ArchitectureGraph, findings: list[Finding]) -> TargetArchitecture:
    ids = [c.id for c in graph.components]
    def decision(id, description, rules, assumption):
        matches = [f for f in findings if f.rule_id in rules]
        return Decision(id=id, description=description,
            component_ids=sorted({cid for f in matches for cid in f.component_ids}) or ids,
            finding_ids=sorted({f.id for f in matches}), baseline_assumption=assumption)
    return TargetArchitecture(graph_revision=graph.revision(), scope=target_scope(graph),
      open_questions=open_questions(graph, findings), decisions=[
        decision('D-NET', 'Two-AZ VPC, public ALB subnets, private application subnets, isolated database subnets.',
                 ['AR-003'], 'Baseline: a new IPv4 VPC in the selected AWS region; no existing network is imported.'),
        decision('D-APP', 'Internet-facing HTTP ALB routes to at least two private ASG instances across two AZs.',
                 ['AR-001', 'AR-002'], 'Baseline: illustrative HTTP service; production TLS, application packaging, authentication, and monitoring require additional work.'),
        decision('D-DB', 'Private encrypted Multi-AZ RDS PostgreSQL with managed credentials and seven-day backups.',
                 ['AR-003', 'AR-005', 'AR-006', 'AR-007'], 'Baseline: application-to-database access is allowed on port 5432; application integration is not provisioned.'),
    ])


def ensure_target_matches(graph, target):
    expected = propose_target(graph, review(graph))
    if target.graph_revision != graph.revision() or target.decisions != expected.decisions or target.scope != expected.scope or target.open_questions != expected.open_questions:
        raise ValueError('Target decisions, scope or unresolved questions do not match this reviewed graph.')
