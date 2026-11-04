"""Only escaped labels and fixed DOT attributes; never execute diagram text."""
import json


def graph_dot(graph):
    quote = lambda s: json.dumps(str(s), ensure_ascii=True)
    lines = ['digraph architecture {', 'rankdir=TB;',
        'node [shape=box, style="rounded,filled", fontname="sans-serif"];']
    for c in graph.components:
        fill = {'public':'#fee2e2', 'private':'#dcfce7', 'unknown':'#f1f5f9'}[c.exposure]
        label = c.id+'\n'+c.label+'\n'+c.type+' | '+c.exposure
        if c.instances is not None: label += ' | instances='+str(c.instances)
        if c.type == 'database': label += '\nfailover='+c.failover
        label += '\n'+c.source
        lines.append(quote(c.id)+' [label='+quote(label)+', fillcolor='+quote(fill)+'];')
    for e in graph.connections:
        style = 'dashed' if e.provenance == 'inferred' else 'solid'
        lines.append(quote(e.source)+' -> '+quote(e.target)+' [style='+quote(style)+'];')
    lines.append('}')
    return '\n'.join(lines)
