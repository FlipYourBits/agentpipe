# Component Map Type

Also read: `svg-toolkit.md`

Use for: module/file dependency graphs, package relationships, import graphs. Nodes grouped in labeled clusters. Arrow style variants for coupling strength.

## HTML Structure

```html
<h1>Component Map</h1>
<div class="component-map diagram-container" id="compMap">
    <div class="cluster-grid">
        <div class="cluster" style="--cluster-color: var(--cat-blue)">
            <div class="cluster-title label">CLI Layer</div>
            <div class="cluster-nodes">
                <div class="comp-node node" id="mod-cli">cli.py</div>
            </div>
        </div>

        <div class="cluster" style="--cluster-color: var(--cat-green)">
            <div class="cluster-title label">Core</div>
            <div class="cluster-nodes">
                <div class="comp-node node" id="mod-runner">runner.py</div>
                <div class="comp-node node" id="mod-dispatch">dispatch.py</div>
                <div class="comp-node node" id="mod-config">config.py</div>
            </div>
        </div>

        <div class="cluster" style="--cluster-color: var(--cat-purple)">
            <div class="cluster-title label">Agents</div>
            <div class="cluster-nodes">
                <div class="comp-node node" id="mod-reviewer">code_reviewer.py</div>
                <div class="comp-node node" id="mod-editor">code_editor.py</div>
            </div>
        </div>

        <div class="cluster" style="--cluster-color: var(--cat-orange)">
            <div class="cluster-title label">Utils</div>
            <div class="cluster-nodes">
                <div class="comp-node node" id="mod-utils">utils.py</div>
                <div class="comp-node node" id="mod-models">models.py</div>
            </div>
        </div>
    </div>
</div>

<div class="map-legend">
    <div class="legend-row">
        <svg width="40" height="10" class="legend-svg"><line x1="0" y1="5" x2="40" y2="5" stroke="var(--cat-blue)" stroke-width="2" marker-end="url(#arr-legend)"/><defs><marker id="arr-legend" viewBox="0 0 10 7" refX="10" refY="3.5" markerWidth="6" markerHeight="5" orient="auto-start-reverse"><polygon points="0 0, 10 3.5, 0 7" fill="var(--cat-blue)"/></marker></defs></svg>
        <span class="label">Direct import (strong coupling)</span>
    </div>
    <div class="legend-row">
        <svg width="40" height="10" class="legend-svg"><line x1="0" y1="5" x2="40" y2="5" stroke="var(--cat-cyan)" stroke-width="2" stroke-dasharray="6 3"/></svg>
        <span class="label">Indirect / optional dependency</span>
    </div>
    <div class="legend-row">
        <svg width="40" height="10" class="legend-svg"><line x1="0" y1="5" x2="40" y2="5" stroke="var(--text-muted)" stroke-width="1" stroke-dasharray="3 3"/></svg>
        <span class="label">Loose coupling / interface only</span>
    </div>
</div>
```

## CSS

```css
.component-map {
    padding: 1.5rem;
    position: relative;
}

.cluster-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 1.5rem;
    align-items: flex-start;
}

.cluster {
    background: var(--bg-card);
    border: 1px solid var(--border-default);
    border-top: 3px solid var(--cluster-color, var(--cat-blue));
    border-radius: 8px;
    padding: 1rem;
    min-width: 160px;
}

.cluster-title {
    font-size: 0.72rem;
    color: var(--cluster-color, var(--cat-blue));
    margin-bottom: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

.cluster-nodes {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.comp-node {
    font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
    font-size: 0.78rem;
    cursor: default;
    display: block;
    transition: background 0.2s ease, border-color 0.2s ease;
    white-space: nowrap;
}

.comp-node:hover {
    background: var(--bg-elevated);
    border-color: var(--border-active);
}

.diagram-container {
    position: relative;
}
.diagram-container svg.connections {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    overflow: visible;
}

.map-legend {
    margin-top: 1.5rem;
    padding: 1rem;
    background: var(--bg-card);
    border: 1px solid var(--border-default);
    border-radius: 8px;
    display: inline-flex;
    flex-direction: column;
    gap: 0.6rem;
}

.legend-row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.legend-svg {
    flex-shrink: 0;
    overflow: visible;
}
```

## JS

Paste the full SVG toolkit block (createSVGOverlay, arrowMarker, connectElements, animateFlow, recalculate, highlightConnections, resetHighlight) then add:

```javascript
document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('compMap');
    const svg = createSVGOverlay(container);

    // Strong coupling — solid lines (direct imports)
    const strongDeps = [
        ['mod-cli',    'mod-runner',   'Direct import'],
        ['mod-runner', 'mod-dispatch', 'Direct import'],
        ['mod-runner', 'mod-config',   null],
    ];
    strongDeps.forEach(([fromId, toId, label]) => {
        const fromEl = document.getElementById(fromId);
        const toEl   = document.getElementById(toId);
        if (fromEl && toEl) {
            connectElements(svg, fromEl, toEl, {
                color: 'var(--cat-blue)',
                width: 2,
                arrow: 'end',
                label,
            });
        }
    });

    // Indirect dependency — dashed lines
    const looseDeps = [
        ['mod-dispatch', 'mod-reviewer', null],
        ['mod-dispatch', 'mod-editor',   null],
    ];
    looseDeps.forEach(([fromId, toId, label]) => {
        const fromEl = document.getElementById(fromId);
        const toEl   = document.getElementById(toId);
        if (fromEl && toEl) {
            const conn = connectElements(svg, fromEl, toEl, {
                color: 'var(--cat-cyan)',
                width: 2,
                arrow: 'end',
                label,
            });
            conn.path.setAttribute('stroke-dasharray', '6 3');
        }
    });

    // Loose coupling — dotted lines (interface/util)
    const interfaceDeps = [
        ['mod-reviewer', 'mod-utils',   null],
        ['mod-editor',   'mod-models',  null],
        ['mod-runner',   'mod-models',  null],
    ];
    interfaceDeps.forEach(([fromId, toId, label]) => {
        const fromEl = document.getElementById(fromId);
        const toEl   = document.getElementById(toId);
        if (fromEl && toEl) {
            const conn = connectElements(svg, fromEl, toEl, {
                color: 'var(--text-muted)',
                width: 1,
                arrow: 'end',
                label,
            });
            conn.path.setAttribute('stroke-dasharray', '3 3');
        }
    });

    // Hover-to-highlight
    document.querySelectorAll('.comp-node').forEach(node => {
        node.addEventListener('mouseenter', () => highlightConnections(node, svg));
        node.addEventListener('mouseleave', () => resetHighlight(svg));
    });
});
```
