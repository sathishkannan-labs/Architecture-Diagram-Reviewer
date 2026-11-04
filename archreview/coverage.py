"""Diagram relationships establish visibility, never effective enforcement."""


def grounded(item):
    provenance = getattr(item, 'source', getattr(item, 'provenance', 'inferred'))
    return provenance != 'inferred' and bool(item.evidence) and (item.confidence is None or item.confidence >= .8)


def control_coverage(graph):
    apps = {'web_server', 'application_server'}
    policies = {
        'authentication': apps,
        'secrets_manager': apps | {'database'},
        'monitoring': apps | {'database'},
        'backup': {'database'},
    }
    rows = []
    for kind, service_types in policies.items():
        controls = [c for c in graph.components if c.type == kind and grounded(c)]
        for service in graph.components:
            if service.type not in service_types:
                continue
            linked = [c.id for c in controls if grounded(service) and any(
                {e.source, e.target} == {c.id, service.id} and grounded_edge(e)
                for e in graph.connections)]
            # A grounded authentication boundary explicitly covering a service
            # is also diagram evidence of a relationship, not enforcement.
            boundary_ids = [b.id for b in graph.boundaries if kind == 'authentication'
                and b.kind == 'authentication' and b.source != 'inferred' and b.evidence
                and service.id in b.component_ids and grounded(service)]
            rows.append({'component_id': service.id, 'control': kind,
                'status': 'relationship_shown' if linked or boundary_ids else 'unverified',
                'control_ids': linked, 'boundary_ids': boundary_ids,
                'explanation': 'A diagram relationship is shown; effectiveness is unverified.' if linked or boundary_ids
                    else 'No sufficiently grounded direct relationship or applicable boundary is shown. This does not prove the control is absent.'})
    return rows


def grounded_edge(edge):
    return edge.provenance != 'inferred' and bool(edge.evidence) and (edge.confidence is None or edge.confidence >= .8)
