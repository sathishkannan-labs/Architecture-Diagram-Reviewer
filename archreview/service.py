"""Session-owned workflow; Streamlit and FastAPI use this service directly."""
from __future__ import annotations
from datetime import datetime, timezone
import io
import json
import time
import zipfile
import threading
import weakref
from functools import wraps

def serialized(method):
    @wraps(method)
    def call(self, *args, **kwargs):
        with self._lock:
            return method(self, *args, **kwargs)
    return call

def _expire_reference(reference):
    workflow = reference()
    if workflow is not None:
        try: workflow.expire()
        except ValueError: pass

from .models import ArchitectureGraph, Approval, TargetArchitecture, ValidationReport, StageResult
from .review import review, propose_target, ensure_target_matches
from .scope import require_acknowledgements

class Workflow:
    def __init__(self, graph: ArchitectureGraph, mode='fixture'):
        self._lock = threading.RLock()
        self.original = graph.model_copy(deep=True)
        self.graph = graph.model_copy(deep=True)
        self.mode = mode
        self.created = time.monotonic()
        self.corrections = []
        self.findings = None
        self.target = None
        self.approval = None
        self.files = None
        self.report = None
        self.generated_at = None
        timer = threading.Timer(3600.1, _expire_reference, args=[weakref.ref(self)])
        timer.daemon = True
        timer.start()

    @serialized
    def expire(self):
        if time.monotonic() - self.created >= 3600:
            self.files = self.report = self.approval = self.target = self.findings = None
            self.corrections = []
            self.original = self.graph = None
            raise ValueError('Session expired after one hour. Start a new extraction.')
        if self.generated_at and time.monotonic() - self.generated_at >= 3600:
            self.files = self.report = None

    @serialized
    def correct(self, candidate: ArchitectureGraph):
        self.expire()
        candidate = candidate.model_copy(deep=True)
        old = {c.id:c for c in self.graph.components}
        for c in candidate.components:
            if c.id not in old or c.model_dump() != old[c.id].model_dump():
                c.source = 'user_corrected'
        edges = {(e.source,e.target):e for e in self.graph.connections}
        for e in candidate.connections:
            if (e.source,e.target) not in edges or e.model_dump() != edges[e.source,e.target].model_dump():
                e.provenance = 'user_corrected'
        boundaries = {b.id:b for b in self.graph.boundaries}
        for b in candidate.boundaries:
            if b.id not in boundaries or b.model_dump() != boundaries[b.id].model_dump():
                b.source = 'user_corrected'
        candidate = ArchitectureGraph.model_validate(candidate.model_dump())
        if candidate.revision() == self.graph.revision():
            return
        self.corrections.append({'before_revision':self.graph.revision(), 'after_revision':candidate.revision(),
            'at':datetime.now(timezone.utc).isoformat(), 'graph':candidate.model_dump()})
        self.graph = candidate
        self.findings = self.target = self.approval = self.files = self.report = None

    @serialized
    def run_review(self):
        self.expire()
        self.findings = review(self.graph)
        self.target = propose_target(self.graph, self.findings)
        self.approval = self.files = self.report = None
        return self.findings

    @serialized
    def configure_target(self, **changes):
        self.expire()
        if self.target is None:
            raise ValueError('Review the graph first.')
        allowed = {'region','name','desired_capacity','instance_type','db_instance_class'}
        if set(changes) - allowed:
            raise ValueError('Only supported target settings can be changed.')
        target = TargetArchitecture.model_validate({**self.target.model_dump(), **changes})
        if target.revision() != self.target.revision():
            self.target = target
            self.approval = self.files = self.report = None

    @serialized
    def approve(self, target_revision: str, *, acknowledge_scope=False, acknowledge_unknowns=False):
        self.expire()
        if self.target is None or self.target.graph_revision != self.graph.revision():
            raise ValueError('Review the current graph before approval.')
        if target_revision != self.target.revision():
            raise ValueError('The target changed since it was displayed. Review and approve the new revision.')
        ensure_target_matches(self.graph, self.target)
        approval = Approval(target_revision=self.target.revision(), approved_at=datetime.now(timezone.utc).isoformat(),
            scope_acknowledged=acknowledge_scope, open_questions_acknowledged=acknowledge_unknowns)
        require_acknowledgements(self.target, approval)
        self.approval = approval
        self.files = self.report = None

    @serialized
    def assert_approved(self):
        self.expire()
        if not self.target or not self.approval or self.target.graph_revision != self.graph.revision() or self.approval.target_revision != self.target.revision():
            raise ValueError('Explicit approval of this target revision is required.')
        # Rebuild the approved decision set so accidental in-place tampering cannot introduce arbitrary decisions.
        ensure_target_matches(self.graph, self.target)
        require_acknowledgements(self.target, self.approval)

    @serialized
    def generate(self, validator=None):
        from .generation import render
        from .validation import validate
        self.assert_approved()
        self.files = self.report = None
        files = render(self.target, self.approval, self.graph, self.original,
                       self.corrections, self.mode)
        try:
            report, formatted = (validator or validate)(files)
        except Exception:
            report = ValidationReport(status='failed', stages=[StageResult(
                stage='runtime', status='failed',
                output='Validation could not complete. Check the toolchain configuration; no success is claimed.')])
            formatted = {}
        self.assert_approved()
        files.update(formatted)
        files['validation-report.json'] = report.model_dump_json(indent=2)
        self.files, self.report = files, report
        self.generated_at = time.monotonic()
        try:
            self.files['validation-request.json']=self.validation_request()
        except ValueError:
            self.files['validation-request-unavailable.txt']='Request exceeds the GitHub demo limit. Use the local Docker workflow.'
        return self.report

    @serialized
    def validation_request(self):
        from .validation_request import build_request
        self.assert_approved()
        return build_request(self.graph,self.original,self.corrections,self.target,self.approval,self.mode)

    @serialized
    def download(self):
        self.assert_approved()
        if self.files is None:
            raise ValueError('Generate artifacts first.')
        result = io.BytesIO()
        with zipfile.ZipFile(result, 'w', zipfile.ZIP_DEFLATED) as archive:
            for name, content in self.files.items():
                archive.writestr(name, content)
        return result.getvalue()
