"""Compact topic groups; original questions and approval data remain intact."""

TOPICS = {
    'controls': ('Service control coverage', 'Confirm authentication, secrets and monitoring relationships for each service.'),
    'recovery': ('Backups and recovery', 'Confirm backup coverage, schedules and restore testing.'),
    'queue': ('Queue resilience', 'Confirm redundancy, delivery guarantees, retries and dead-letter handling.'),
    'storage': ('Storage access policy', 'Confirm document-storage policy, encryption and least-privilege access.'),
    'other': ('Other open questions', 'Clarify the remaining diagram information with the architecture owner.'),
}


def group_questions(questions):
    groups = {}
    for q in questions:
        text = q.question.lower()
        if any(s in text for s in ('backup','restore','recovery')): key='recovery'
        elif any(s in text for s in ('queue','dead-letter','delivery guarantee')): key='queue'
        elif any(s in text for s in ('object storage','storage access','storage policy')): key='storage'
        elif any(s in text for s in ('authentication','identity','secret','monitoring','logs / metrics','shared control','consumer links')): key='controls'
        else: key='other'
        if key not in groups:
            title, summary = TOPICS[key]
            groups[key] = {'topic':key,'title':title,'summary':summary,'question_ids':[], 'component_ids':[], 'entries':[]}
        group=groups[key]
        group['question_ids'].append(q.id)
        group['component_ids']=sorted(set(group['component_ids'])|set(q.component_ids))
        group['entries'].append(q.model_dump())
    return [groups[key] for key in TOPICS if key in groups]
