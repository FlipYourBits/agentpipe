# SVG Connection Toolkit

Use this when the visual needs lines/arrows between elements (architecture diagrams, data flows, component maps). Copy the functions you need into the `<script>` section of the generated HTML.

## Architecture

HTML nodes are laid out with CSS (grid, flexbox, absolute positioning). An SVG overlay sits on top of the container and draws paths between the nodes. The SVG has `pointer-events: none` so clicks pass through to the HTML beneath.

## Setup

Add this CSS to the container that holds the diagram:

```css
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
```

## Core Functions

Paste this entire block into `<script>`. All functions are self-contained.

```javascript
function createSVGOverlay(container) {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.classList.add('connections');
    svg.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
    container.style.position = 'relative';
    container.appendChild(svg);

    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    svg.appendChild(defs);

    svg._connections = [];
    svg._defs = defs;

    function resize() {
        svg.setAttribute('width', container.scrollWidth);
        svg.setAttribute('height', container.scrollHeight);
    }
    resize();
    new ResizeObserver(resize).observe(container);

    return svg;
}

function arrowMarker(svg, id, color) {
    const marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
    marker.setAttribute('id', id);
    marker.setAttribute('viewBox', '0 0 10 7');
    marker.setAttribute('refX', '10');
    marker.setAttribute('refY', '3.5');
    marker.setAttribute('markerWidth', '8');
    marker.setAttribute('markerHeight', '6');
    marker.setAttribute('orient', 'auto-start-reverse');
    const poly = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
    poly.setAttribute('points', '0 0, 10 3.5, 0 7');
    poly.setAttribute('fill', color);
    marker.appendChild(poly);
    svg._defs.appendChild(marker);
    return id;
}

function connectElements(svg, fromEl, toEl, options = {}) {
    const {
        color = '#58a6ff',
        width = 2,
        animate = false,
        label = null,
        arrow = 'end',
        curvature = 0.5,
    } = options;

    const containerRect = svg.parentElement.getBoundingClientRect();

    function elCenter(el) {
        const r = el.getBoundingClientRect();
        return {
            x: r.left + r.width / 2 - containerRect.left,
            y: r.top + r.height / 2 - containerRect.top,
            w: r.width, h: r.height,
            top: r.top - containerRect.top,
            bottom: r.bottom - containerRect.top,
            left: r.left - containerRect.left,
            right: r.right - containerRect.left,
        };
    }

    function bestSides(a, b) {
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        let fromSide, toSide;
        if (Math.abs(dx) > Math.abs(dy)) {
            fromSide = dx > 0
                ? { x: a.right, y: a.y }
                : { x: a.left, y: a.y };
            toSide = dx > 0
                ? { x: b.left, y: b.y }
                : { x: b.right, y: b.y };
        } else {
            fromSide = dy > 0
                ? { x: a.x, y: a.bottom }
                : { x: a.x, y: a.top };
            toSide = dy > 0
                ? { x: b.x, y: b.top }
                : { x: b.x, y: b.bottom };
        }
        return { from: fromSide, to: toSide };
    }

    const a = elCenter(fromEl);
    const b = elCenter(toEl);
    const sides = bestSides(a, b);

    const dx = sides.to.x - sides.from.x;
    const dy = sides.to.y - sides.from.y;
    const dist = Math.sqrt(dx * dx + dy * dy);
    const offset = dist * curvature * 0.5;

    let cp1, cp2;
    if (Math.abs(dx) > Math.abs(dy)) {
        cp1 = { x: sides.from.x + offset, y: sides.from.y };
        cp2 = { x: sides.to.x - offset, y: sides.to.y };
    } else {
        cp1 = { x: sides.from.x, y: sides.from.y + offset };
        cp2 = { x: sides.to.x, y: sides.to.y - offset };
    }

    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    const d = `M ${sides.from.x} ${sides.from.y} C ${cp1.x} ${cp1.y}, ${cp2.x} ${cp2.y}, ${sides.to.x} ${sides.to.y}`;
    path.setAttribute('d', d);
    path.setAttribute('stroke', color);
    path.setAttribute('stroke-width', width);
    path.setAttribute('fill', 'none');

    const markerId = `arrow-${color.replace('#', '')}`;
    if (!svg.querySelector(`#${markerId}`)) {
        arrowMarker(svg, markerId, color);
    }
    if (arrow === 'end' || arrow === 'both') {
        path.setAttribute('marker-end', `url(#${markerId})`);
    }
    if (arrow === 'start' || arrow === 'both') {
        path.setAttribute('marker-start', `url(#${markerId})`);
    }

    if (animate) {
        path.setAttribute('stroke-dasharray', '8 4');
        path.style.animation = 'flowDash 1s linear infinite';
    }

    svg.appendChild(path);

    const conn = { path, fromEl, toEl, options };
    svg._connections.push(conn);

    if (label) {
        const midX = (sides.from.x + sides.to.x) / 2;
        const midY = (sides.from.y + sides.to.y) / 2;
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', midX);
        text.setAttribute('y', midY - 8);
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('fill', 'var(--text-muted)');
        text.setAttribute('font-size', '0.7rem');
        text.setAttribute('font-family', 'system-ui, sans-serif');
        text.textContent = label;
        svg.appendChild(text);
        conn.labelEl = text;
    }

    return conn;
}

function animateFlow(pathEl, speed = 1) {
    pathEl.setAttribute('stroke-dasharray', '8 4');
    pathEl.style.animation = `flowDash ${1 / speed}s linear infinite`;
}

function recalculate(svg) {
    svg._connections.forEach(conn => {
        svg.removeChild(conn.path);
        if (conn.labelEl) svg.removeChild(conn.labelEl);
    });
    const oldConns = [...svg._connections];
    svg._connections = [];
    oldConns.forEach(({ fromEl, toEl, options }) => {
        connectElements(svg, fromEl, toEl, options);
    });
}

function highlightConnections(nodeEl, svg) {
    svg._connections.forEach(conn => {
        const involved = conn.fromEl === nodeEl || conn.toEl === nodeEl;
        conn.path.style.opacity = involved ? '1' : '0.15';
        conn.path.style.strokeWidth = involved
            ? (conn.options.width || 2) + 1 + 'px'
            : conn.options.width || 2 + 'px';
        if (conn.labelEl) conn.labelEl.style.opacity = involved ? '1' : '0.15';
    });
}

function resetHighlight(svg) {
    svg._connections.forEach(conn => {
        conn.path.style.opacity = '1';
        conn.path.style.strokeWidth = (conn.options.width || 2) + 'px';
        if (conn.labelEl) conn.labelEl.style.opacity = '1';
    });
}
```

## Required CSS Animation

Add this to the `<style>` block when using animated connections:

```css
@keyframes flowDash {
    to { stroke-dashoffset: -12; }
}
```

## Usage Pattern

```javascript
// After DOM is ready
const container = document.querySelector('.diagram-container');
const svg = createSVGOverlay(container);

// Connect nodes by their DOM elements
const nodeA = document.getElementById('node-cli');
const nodeB = document.getElementById('node-core');
connectElements(svg, nodeA, nodeB, {
    color: 'var(--cat-blue)',
    animate: true,
    label: 'dispatches',
    arrow: 'end',
});

// Hover-to-highlight on nodes
document.querySelectorAll('.node').forEach(node => {
    node.addEventListener('mouseenter', () => highlightConnections(node, svg));
    node.addEventListener('mouseleave', () => resetHighlight(svg));
});

// Recalculate on window resize (already handled by ResizeObserver,
// but call manually after zoom/pan transforms or expand/collapse)
```

## Context

This is the SVG toolkit for the codemonkeys-visualize skill. It will be read by the agent when building architecture diagrams, data flows, and component maps. The functions need to be copy-paste ready — agents drop them directly into `<script>` blocks.
