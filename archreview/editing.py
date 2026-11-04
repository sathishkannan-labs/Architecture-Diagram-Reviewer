"""Shared edit validation; no Streamlit dependency."""
import json
from .models import ArchitectureGraph

DETAIL_KEYS = {'boundaries', 'unknowns', 'assumptions'}

def edited_graph(components: list[dict], connections: list[dict], details: str) -> ArchitectureGraph:
    extra = json.loads(details)
    if not isinstance(extra, dict) or set(extra) != DETAIL_KEYS:
        raise ValueError('Details must contain only boundaries, unknowns and assumptions.')
    return ArchitectureGraph.model_validate({'components': components, 'connections': connections, **extra})
