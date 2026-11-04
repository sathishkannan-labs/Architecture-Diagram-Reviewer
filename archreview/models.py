from __future__ import annotations

import hashlib
import json
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

Provenance = Literal['observed', 'inferred', 'user_corrected']

class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', validate_assignment=True)

class Component(StrictModel):
    id: str = Field(pattern=r'^[a-z][a-z0-9_]{0,63}$')
    type: Literal['internet', 'web_server', 'application_server', 'load_balancer',
                  'database', 'authentication', 'secrets_manager', 'monitoring', 'backup',
                  'network', 'other']
    label: str = Field(min_length=1, max_length=200)
    evidence: str | None = Field(default=None, max_length=2000)
    confidence: float | None = Field(default=None, ge=0, le=1)
    source: Provenance = 'observed'
    exposure: Literal['public', 'private', 'unknown'] = 'unknown'
    instances: int | None = Field(default=None, ge=1, le=10000)
    failover: Literal['present', 'absent', 'unknown'] = 'unknown'

class Connection(StrictModel):
    source: str
    target: str
    evidence: str | None = Field(default=None, max_length=2000)
    confidence: float | None = Field(default=None, ge=0, le=1)
    provenance: Provenance = 'observed'

class Boundary(StrictModel):
    id: str
    kind: Literal['network', 'authentication']
    label: str
    component_ids: list[str]
    evidence: str | None = None
    source: Provenance = 'observed'

class ArchitectureGraph(StrictModel):
    components: list[Component] = Field(min_length=1, max_length=100)
    connections: list[Connection] = Field(default_factory=list, max_length=300)
    boundaries: list[Boundary] = Field(default_factory=list, max_length=50)
    unknowns: list[str] = Field(default_factory=list, max_length=100)
    assumptions: list[str] = Field(default_factory=list, max_length=100)

    @model_validator(mode='after')
    def references(self):
        ids = [c.id for c in self.components]
        if len(ids) != len(set(ids)):
            raise ValueError('Component IDs must be unique')
        if len({b.id for b in self.boundaries}) != len(self.boundaries):
            raise ValueError('Boundary IDs must be unique')
        edges = [(c.source, c.target) for c in self.connections]
        if len(edges) != len(set(edges)):
            raise ValueError('Duplicate connections are not allowed')
        for a, b in edges:
            if a not in ids or b not in ids:
                raise ValueError('Connections must reference existing components')
        if any(cid not in ids for b in self.boundaries for cid in b.component_ids):
            raise ValueError('Boundaries must reference existing components')
        return self

    def revision(self) -> str:
        return digest(self.model_dump())

class Finding(StrictModel):
    id: str
    rule_id: str
    title: str
    severity: Literal['critical', 'high', 'medium', 'low']
    component_ids: list[str]
    evidence: str
    recommendation: str
    confidence: float = Field(ge=0, le=1)
    status: Literal['confirmed', 'unverified']

class ContextSuggestion(StrictModel):
    component_ids: list[str]
    suggestion: str = Field(max_length=3000)

class ContextReview(StrictModel):
    suggestions: list[ContextSuggestion] = Field(max_length=10)

class Decision(StrictModel):
    id: str
    description: str
    component_ids: list[str]
    finding_ids: list[str]
    baseline_assumption: str | None = None

class ScopeItem(StrictModel):
    component_id: str
    disposition: Literal['included', 'replaced', 'omitted', 'unsupported']
    decision_ids: list[str] = Field(default_factory=list)
    explanation: str

class OpenQuestion(StrictModel):
    id: str
    component_ids: list[str] = Field(default_factory=list)
    question: str
    origin: Literal['graph', 'review']

class TargetArchitecture(StrictModel):
    graph_revision: str
    database_source_id: str | None = Field(default=None, pattern=r'^[a-z][a-z0-9_]{0,63}$')
    region: Literal['us-east-1', 'us-west-2', 'eu-west-1'] = 'us-east-1'
    name: str = Field(default='archreview-demo', min_length=3, max_length=20,
                      pattern=r'^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$')
    desired_capacity: int = Field(default=2, ge=2, le=4)
    availability_zones: Literal[2] = 2
    instance_type: Literal['t3.micro', 't3.small'] = 't3.micro'
    db_instance_class: Literal['db.t3.micro', 'db.t3.small'] = 'db.t3.micro'
    decisions: list[Decision]
    scope: list[ScopeItem] = Field(default_factory=list)
    open_questions: list[OpenQuestion] = Field(default_factory=list)

    def revision(self) -> str:
        return digest(self.model_dump())

class Approval(StrictModel):
    target_revision: str
    approved_at: str
    scope_acknowledged: bool = False
    open_questions_acknowledged: bool = False

class StageResult(StrictModel):
    stage: str
    status: Literal['passed', 'failed', 'timed_out', 'not_run']
    output: str = ''
    exit_code: int | None = None

class ValidationReport(StrictModel):
    status: Literal['passed', 'failed', 'timed_out', 'not_run'] = 'not_run'
    stages: list[StageResult] = Field(default_factory=list)
    limitations: str = ('Terraform validation checks configuration validity only. It does not prove '
                         'security, successful AWS provisioning, application functionality, or production readiness.')

def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
