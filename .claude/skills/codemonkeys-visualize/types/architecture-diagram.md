# Architecture Diagram Type

Also read: `svg-toolkit.md`

Use for: components and their relationships, layered system architecture, module interaction diagrams.

## Graph Layout Strategy

**Do not use CSS flexbox/grid for node positioning.** Flexbox places nodes without considering edges, which causes overlapping arrows. Instead, use the computed layout approach below:

1. **Define nodes and edges as data** — JS arrays of `{ id, layer, ... }` and `{ from, to, label, color }`.
2. **Order nodes within each layer to minimize edge crossings.** Look at each node's connections to the layer below and place nodes so that downward edges flow left-to-right without crossing. A node that connects to left-side targets should be placed left; one that connects to right-side targets should be placed right.
3. **Position nodes with absolute positioning** — compute `x, y` per node, center each layer row within the total width. Use a fixed `NODE_W` and `NODE_PAD` for uniform spacing, and `LAYER_GAP` between layers.
4. **Use port-based edge routing** — instead of connecting from node center to node center, distribute connection points across the node's width:
   - Collect each node's outgoing edges (bottom ports) and incoming edges (top ports).
   - Sort ports by the x-center of the node at the other end.
   - Spread ports evenly across the node width with margin insets.
   - This fans edges out cleanly and prevents overlap at high-connectivity nodes.
5. **Route same-layer edges differently** — use side ports (left/right of node) with arched bezier curves above the row, not through the downward flow.
6. **Draw vertical bezier curves between layers** — control points should keep paths strictly downward: `C x1 y1+offset, x2 y2-offset, x2 y2`.

## HTML Structure

Nodes are rendered as absolutely-positioned `div` elements inside a relatively-positioned container. The container also holds an SVG overlay for edges.

```html
<h1>System Architecture</h1>
<div id="graph"></div>
```

## CSS

```css
#graph {
    position: relative;
    margin: 0 auto;
}

#graph svg {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    overflow: visible;
}

.layer-label {
    position: absolute;
    font-size: 0.7rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    writing-mode: vertical-lr;
    transform: rotate(180deg);
}

.node {
    position: absolute;
    background: var(--bg-card);
    border: 1px solid var(--border-default);
    border-radius: 8px;
    padding: 0.75rem 1rem;
    cursor: pointer;
    border-left: 3px solid var(--border-default);
    transition: background 0.2s ease, border-color 0.2s ease, opacity 0.2s ease, box-shadow 0.2s ease;
}
.node:hover {
    background: var(--bg-elevated);
    border-color: var(--border-active);
    box-shadow: 0 0 16px rgba(88, 166, 255, 0.12);
}
.node.dimmed { opacity: 0.12; }

.node-name {
    font-weight: 600;
    font-size: 0.85rem;
    color: var(--text-heading);
    font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
}
.node-role {
    font-size: 0.75rem;
    color: var(--text-secondary);
    margin-top: 0.1rem;
}
.node-desc {
    font-size: 0.7rem;
    color: var(--text-muted);
    line-height: 1.45;
    margin-top: 0.35rem;
}
```

## JS

Define all nodes and edges as data arrays, then compute layout and draw.

```javascript
// --- Data ---
const NODES = [
    // Order within each layer matters — sort to minimize crossings (see strategy above)
    { id: 'node-cli',      layer: 0, name: 'CLI',        role: 'codemonkeys/cli.py', desc: '...' },
    { id: 'node-api',      layer: 0, name: 'REST API',   role: 'api/server.py',      desc: '...' },
    { id: 'node-runner',   layer: 1, name: 'AgentRunner', role: 'core/runner.py',     desc: '...' },
    { id: 'node-dispatch', layer: 1, name: 'Dispatcher',  role: 'core/dispatch.py',   desc: '...' },
    { id: 'node-reviewer', layer: 2, name: 'Reviewer',    role: 'agents/reviewer.py', desc: '...' },
    { id: 'node-editor',   layer: 2, name: 'Editor',      role: 'agents/editor.py',   desc: '...' },
];

const EDGES = [
    { from: 'node-cli',      to: 'node-runner',   label: 'invokes',    color: '#58a6ff' },
    { from: 'node-api',      to: 'node-runner',   label: 'invokes',    color: '#58a6ff' },
    { from: 'node-runner',   to: 'node-dispatch', label: 'dispatches', color: '#3fb950' },
    { from: 'node-dispatch', to: 'node-reviewer', label: 'spawns',     color: '#bc8cff' },
    { from: 'node-dispatch', to: 'node-editor',   label: 'spawns',     color: '#bc8cff' },
];

// --- Layout ---
const NODE_W = 220, NODE_PAD = 28, LAYER_GAP = 120, LEFT_MARGIN = 40;
const graph = document.getElementById('graph');
const nodeEls = {}, nodeData = {};

// Render nodes invisibly to measure heights
NODES.forEach(n => {
    const el = document.createElement('div');
    el.className = 'node';
    el.id = n.id;
    el.innerHTML = `<div class="node-name">${n.name}</div>` +
                   `<div class="node-role">${n.role}</div>` +
                   `<div class="node-desc">${n.desc}</div>`;
    el.style.width = NODE_W + 'px';
    el.style.visibility = 'hidden';
    graph.appendChild(el);
    nodeEls[n.id] = el;
    nodeData[n.id] = n;
});

// Measure, compute positions, then show
const nodeHeights = {};
NODES.forEach(n => { nodeHeights[n.id] = nodeEls[n.id].offsetHeight; });

const layers = {};
NODES.forEach(n => { (layers[n.layer] ??= []).push(n.id); });
const layerKeys = Object.keys(layers).map(Number).sort((a, b) => a - b);

const layerMaxH = layerKeys.map(k => Math.max(...layers[k].map(id => nodeHeights[id])));
const layerY = [];
let curY = 0;
layerKeys.forEach((k, i) => { layerY[k] = curY; curY += layerMaxH[i] + LAYER_GAP; });

const totalWidth = Math.max(...layerKeys.map(k => {
    const ids = layers[k];
    return ids.length * NODE_W + (ids.length - 1) * NODE_PAD;
}));

const nodePos = {};
layerKeys.forEach(k => {
    const ids = layers[k];
    const rowW = ids.length * NODE_W + (ids.length - 1) * NODE_PAD;
    const offX = LEFT_MARGIN + (totalWidth - rowW) / 2;
    ids.forEach((id, i) => {
        nodePos[id] = {
            x: offX + i * (NODE_W + NODE_PAD),
            y: layerY[k] + (layerMaxH[k] - nodeHeights[id]) / 2,
            w: NODE_W, h: nodeHeights[id],
        };
    });
});

Object.entries(nodePos).forEach(([id, p]) => {
    const el = nodeEls[id];
    el.style.left = p.x + 'px';
    el.style.top = p.y + 'px';
    el.style.visibility = 'visible';
});

const maxX = Math.max(...Object.values(nodePos).map(p => p.x + p.w));
const maxY = Math.max(...Object.values(nodePos).map(p => p.y + p.h));
graph.style.width = (maxX + LEFT_MARGIN) + 'px';
graph.style.height = (maxY + 20) + 'px';

// --- Port-based edge routing ---
const svgNS = 'http://www.w3.org/2000/svg';
const svg = document.createElementNS(svgNS, 'svg');
svg.setAttribute('width', graph.style.width);
svg.setAttribute('height', graph.style.height);
graph.appendChild(svg);

const defs = document.createElementNS(svgNS, 'defs');
svg.appendChild(defs);

function getMarker(color) {
    const safeId = 'arr-' + color.replace(/[^a-zA-Z0-9]/g, '');
    if (document.getElementById(safeId)) return safeId;
    const marker = document.createElementNS(svgNS, 'marker');
    marker.setAttribute('id', safeId);
    marker.setAttribute('viewBox', '0 0 10 7');
    marker.setAttribute('refX', '9');
    marker.setAttribute('refY', '3.5');
    marker.setAttribute('markerWidth', '7');
    marker.setAttribute('markerHeight', '5');
    marker.setAttribute('orient', 'auto');
    const poly = document.createElementNS(svgNS, 'polygon');
    poly.setAttribute('points', '0 0, 10 3.5, 0 7');
    poly.setAttribute('fill', color);
    marker.appendChild(poly);
    defs.appendChild(marker);
    return safeId;
}

// Collect outgoing (bottom) and incoming (top) edges per node
const outgoing = {}, incoming = {};
EDGES.forEach((e, i) => {
    (outgoing[e.from] ??= []).push({ idx: i, other: e.to });
    (incoming[e.to] ??= []).push({ idx: i, other: e.from });
});

function centerX(id) { return nodePos[id].x + nodePos[id].w / 2; }

// Spread ports across node width, sorted by the x-center of the far end
function spreadPorts(nodeId, portList, side) {
    const pos = nodePos[nodeId];
    const sorted = portList.slice().sort((a, b) => centerX(a.other) - centerX(b.other));
    const margin = 24;
    const usable = pos.w - 2 * margin;
    const result = {};
    sorted.forEach((p, i) => {
        const frac = sorted.length === 1 ? 0.5 : i / (sorted.length - 1);
        result[p.idx] = {
            x: pos.x + margin + frac * usable,
            y: side === 'bottom' ? pos.y + pos.h : pos.y,
        };
    });
    return result;
}

// Side ports for same-layer edges
function sidePort(nodeId, side) {
    const p = nodePos[nodeId];
    return side === 'right'
        ? { x: p.x + p.w, y: p.y + p.h / 2 }
        : { x: p.x, y: p.y + p.h / 2 };
}

// Compute ports for all cross-layer edges
const bottomPorts = {}, topPorts = {};
Object.keys(outgoing).forEach(id => {
    const down = outgoing[id].filter(p => nodeData[p.other].layer > nodeData[id].layer);
    Object.assign(bottomPorts, spreadPorts(id, down, 'bottom'));
});
Object.keys(incoming).forEach(id => {
    const up = incoming[id].filter(p => nodeData[p.other].layer < nodeData[id].layer);
    Object.assign(topPorts, spreadPorts(id, up, 'top'));
});

// Draw edges
const edgeEls = [];
EDGES.forEach((e, i) => {
    const sameLayer = nodeData[e.from].layer === nodeData[e.to].layer;
    let x1, y1, x2, y2, d;

    if (sameLayer) {
        const fromRight = centerX(e.from) < centerX(e.to);
        const fp = sidePort(e.from, fromRight ? 'right' : 'left');
        const tp = sidePort(e.to, fromRight ? 'left' : 'right');
        x1 = fp.x; y1 = fp.y; x2 = tp.x; y2 = tp.y;
        const bulge = 40;
        const dx = x2 - x1;
        d = `M ${x1} ${y1} C ${x1 + dx * 0.3} ${y1 - bulge}, ${x2 - dx * 0.3} ${y2 - bulge}, ${x2} ${y2}`;
    } else {
        if (!bottomPorts[i] || !topPorts[i]) return;
        x1 = bottomPorts[i].x; y1 = bottomPorts[i].y;
        x2 = topPorts[i].x;    y2 = topPorts[i].y;
        const cpOff = Math.abs(y2 - y1) * 0.4;
        d = `M ${x1} ${y1} C ${x1} ${y1 + cpOff}, ${x2} ${y2 - cpOff}, ${x2} ${y2}`;
    }

    const path = document.createElementNS(svgNS, 'path');
    path.setAttribute('d', d);
    path.setAttribute('stroke', e.color);
    path.setAttribute('stroke-width', '1.8');
    path.setAttribute('fill', 'none');
    path.setAttribute('marker-end', `url(#${getMarker(e.color)})`);
    if (e.dashed) path.setAttribute('stroke-dasharray', '6 4');
    svg.appendChild(path);

    const mx = (x1 + x2) / 2, my = (y1 + y2) / 2 + (sameLayer ? -28 : 0);
    const text = document.createElementNS(svgNS, 'text');
    text.setAttribute('x', mx);
    text.setAttribute('y', my - 6);
    text.setAttribute('text-anchor', 'middle');
    text.setAttribute('fill', '#8b949e');
    text.setAttribute('font-size', '0.65rem');
    text.setAttribute('font-family', 'system-ui, sans-serif');
    text.textContent = e.label;
    svg.appendChild(text);

    edgeEls.push({ path, text, from: e.from, to: e.to });
});

// Hover interaction
Object.entries(nodeEls).forEach(([id, el]) => {
    el.addEventListener('mouseenter', () => {
        const connected = new Set([id]);
        edgeEls.forEach(ee => {
            const hit = ee.from === id || ee.to === id;
            ee.path.style.opacity = hit ? '1' : '0.1';
            ee.path.style.strokeWidth = hit ? '2.8px' : '1.8px';
            ee.text.style.opacity = hit ? '1' : '0.1';
            if (hit) { connected.add(ee.from); connected.add(ee.to); }
        });
        Object.entries(nodeEls).forEach(([nid, nel]) => {
            nel.classList.toggle('dimmed', !connected.has(nid));
        });
    });
    el.addEventListener('mouseleave', () => {
        edgeEls.forEach(ee => {
            ee.path.style.opacity = '1';
            ee.path.style.strokeWidth = '1.8px';
            ee.text.style.opacity = '1';
        });
        Object.values(nodeEls).forEach(nel => nel.classList.remove('dimmed'));
    });
});
```

## Layer Color Convention

Apply layer-specific `border-left-color` via CSS classes (e.g. `.layer-skill`, `.layer-cli`, `.layer-agent`) or `data-layer` attributes:

| data-layer | Color variable | Suggested use |
|---|---|---|
| 0 | --cat-blue | Presentation / entry points |
| 1 | --cat-green | Core / orchestration |
| 2 | --cat-purple | Agents / workers |
| 3 | --cat-orange | Storage / persistence |
| 4 | --cat-cyan | External / integrations |
