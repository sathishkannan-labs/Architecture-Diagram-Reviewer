"""Finding-to-baseline explanation, never a claim of in-place remediation."""
def remediation_summary(graph, target, findings):
    scope = {s.component_id:s.disposition for s in target.scope}
    rows = []
    for f in findings:
        covered = bool(f.component_ids) and all(scope.get(cid) in ('included','replaced') for cid in f.component_ids)
        if f.status == 'confirmed' and covered and f.rule_id in ('AR-001','AR-003','AR-006'):
            status = 'Addressed in new baseline only'
            change = {'AR-001':'At least two ASG instances across two AZs.',
                'AR-003':'New private RDS; inbound PostgreSQL only from the application security group.',
                'AR-006':'Multi-AZ enabled on the new RDS.'}[f.rule_id]
            remaining = 'Existing infrastructure is unchanged. Migration, integration and operational testing are not implemented.'
        elif f.rule_id in ('AR-005','AR-007'):
            status = 'Partial baseline measure; unresolved'
            change = 'RDS-managed master credentials and seven-day RDS backups only.'
            remaining = 'Application secret retrieval, service coverage, recovery objectives and restore testing remain unverified.'
        else:
            status = 'Unresolved / outside generated scope'
            change = 'No implementation for these observed roles or controls.'
            remaining = 'Confirm with the owner; implement and test separately. The illustrative ASG does not consolidate independent services.'
        rows.append({'finding_id':f.id,'rule':f.rule_id,'severity':f.severity,'finding_status':f.status,
            'components':f.component_ids,'observed_problem':f.title,'evidence':f.evidence,
            'target_status':status,'proposed_change':change,'remaining_work':remaining})
    return rows
