"""Only escaped labels and fixed DOT attributes; never execute diagram text."""


def graph_dot(graph):
    def quote(value):
        text = str(value).replace('\\', '\\\\').replace('"', '\\"')
        text = text.replace('\r\n', '\\n').replace('\n', '\\n').replace('\r', '\\n')
        return '"' + text + '"'
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

def graph_svg(graph):
    """Render an escaped, dependency-free overview; tables retain full evidence."""
    from collections import defaultdict, deque
    from html import escape
    from textwrap import wrap

    ids = [c.id for c in graph.components]
    incoming = {cid: 0 for cid in ids}
    outgoing = defaultdict(list)
    for edge in graph.connections:
        outgoing[edge.source].append(edge.target)
        incoming[edge.target] += 1
    roots = [c.id for c in graph.components if c.type == 'internet']
    roots += [cid for cid in ids if not incoming[cid] and cid not in roots]
    # Shortest visible path provides a stable layout even when the graph cycles.
    ranks = {cid: 0 for cid in roots}
    queue = deque(roots)
    while queue:
        source = queue.popleft()
        for target in outgoing[source]:
            if target not in ranks:
                ranks[target] = ranks[source] + 1
                queue.append(target)
    disconnected_rank = max(ranks.values(), default=-1) + 1
    for cid in ids:
        ranks.setdefault(cid, disconnected_rank)
    levels = defaultdict(list)
    for cid in ids:
        levels[ranks[cid]].append(cid)
    positions = {}
    row = 0
    for rank in sorted(levels):
        group = levels[rank]
        for offset in range(0, len(group), 3):
            chunk = group[offset:offset + 3]
            start = (980 - (len(chunk) * 280 + (len(chunk) - 1) * 40)) / 2
            for index, cid in enumerate(chunk):
                positions[cid] = (start + index * 320, 30 + row * 190)
            row += 1
    height = max(210, row * 190 + 30)
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="980" height="{height}" viewBox="0 0 980 {height}" role="img" aria-label="Saved architecture observations">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b"/></marker></defs>']
    for edge in graph.connections:
        sx, sy = positions[edge.source]
        tx, ty = positions[edge.target]
        if ty > sy:
            sx += 140; sy += 140; tx += 140
            mid = (sy + ty) / 2
            path = f'M {sx} {sy} C {sx} {mid}, {tx} {mid}, {tx} {ty}'
        else:
            sx += 280; sy += 70; ty += 70
            bend = max(sx, tx + 280) + 25
            path = f'M {sx} {sy} C {bend} {sy - 100}, {bend} {ty - 100}, {tx + 280} {ty}'
        dash = ' stroke-dasharray="7 5"' if edge.provenance == 'inferred' else ''
        label = escape(edge.source + ' → ' + edge.target + ' | ' + edge.provenance)
        lines.append(f'<path data-connection="true" d="{path}" fill="none" stroke="#64748b" stroke-width="2" marker-end="url(#arrow)"{dash}><title>{label}</title></path>')
    for component in graph.components:
        x, y = positions[component.id]
        fill = {'public': '#fee2e2', 'private': '#dcfce7', 'unknown': '#f1f5f9'}[component.exposure]
        label_lines = wrap(component.label, 34)[:3] or ['']
        detail = component.type + ' | ' + component.exposure
        lines.append(f'<g data-component="{escape(component.id)}"><title>{escape(component.label)}</title><rect x="{x}" y="{y}" width="280" height="140" rx="10" fill="{fill}" stroke="#475569"/>')
        text_lines = [component.id, *label_lines, detail, component.source]
        for index, text in enumerate(text_lines):
            weight = 'bold' if index == 0 else 'normal'
            lines.append(f'<text x="{x + 12}" y="{y + 20 + index * 20}" font-family="sans-serif" font-size="12" font-weight="{weight}" fill="#0f172a">{escape(text)}</text>')
        lines.append('</g>')
    lines.append('</svg>')
    return '\n'.join(lines)
