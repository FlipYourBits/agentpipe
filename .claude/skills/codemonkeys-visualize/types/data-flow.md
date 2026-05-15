# Data Flow Type

Also read: `svg-toolkit.md`

Use for: data moving through a pipeline, request/response flows, ETL steps, processing stages with branching paths.

## HTML Structure

```html
<h1>Data Flow: Review Pipeline</h1>
<div class="flow-diagram diagram-container" id="flowDiagram">
    <div class="flow-track">
        <div class="flow-step card" id="step-input">
            <span class="step-num">1</span>
            <div class="step-name">Input</div>
            <div class="step-desc label">File paths from CLI</div>
        </div>
        <div class="flow-step card" id="step-dispatch">
            <span class="step-num">2</span>
            <div class="step-name">Dispatch</div>
            <div class="step-desc label">AgentRunner.run()</div>
        </div>
        <div class="flow-step card" id="step-review">
            <span class="step-num">3</span>
            <div class="step-name">Review</div>
            <div class="step-desc label">Parallel agent calls</div>
        </div>
        <div class="flow-step card" id="step-merge">
            <span class="step-num">4</span>
            <div class="step-name">Merge</div>
            <div class="step-desc label">Aggregate findings</div>
        </div>
        <div class="flow-step card" id="step-output">
            <span class="step-num">5</span>
            <div class="step-name">Output</div>
            <div class="step-desc label">HTML report</div>
        </div>
    </div>

    <!-- Error branch nodes — positioned via CSS or inline style -->
    <div class="flow-step error-branch card" id="step-error" style="margin-top:2rem; margin-left: 3rem;">
        <span class="step-num error">!</span>
        <div class="step-name">Error Handler</div>
        <div class="step-desc label">Log + continue</div>
    </div>
</div>

<div class="flow-legend">
    <span class="legend-item happy">Happy path</span>
    <span class="legend-item error">Error branch</span>
</div>
```

## CSS

```css
.flow-diagram {
    padding: 1.5rem;
    position: relative;
}

.flow-track {
    display: flex;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
}

.flow-step {
    position: relative;
    min-width: 130px;
    padding: 1rem;
    cursor: default;
    transition: background 0.2s ease, border-color 0.2s ease;
}

.flow-step:hover {
    background: var(--bg-elevated);
    border-color: var(--border-active);
}

.error-branch {
    border-left: 3px solid var(--color-error);
}

.step-num {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.5rem;
    height: 1.5rem;
    border-radius: 50%;
    background: var(--color-info);
    color: var(--bg-page);
    font-size: 0.7rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
}

.step-num.error {
    background: var(--color-error);
}

.step-name {
    font-weight: 600;
    font-size: 0.9rem;
    color: var(--text-heading);
}

.step-desc {
    margin-top: 0.25rem;
    font-size: 0.72rem;
}

.flow-legend {
    display: flex;
    gap: 1.5rem;
    margin-top: 1.5rem;
    padding-left: 1.5rem;
}

.legend-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.8rem;
    color: var(--text-muted);
}

.legend-item::before {
    content: '';
    display: inline-block;
    width: 2rem;
    height: 2px;
    border-radius: 1px;
}

.legend-item.happy::before {
    background: var(--color-info);
}

.legend-item.error::before {
    background: var(--color-error);
    border-top: 2px dashed var(--color-error);
    background: transparent;
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

@keyframes flowDash {
    to { stroke-dashoffset: -12; }
}
```

## JS

Paste the full SVG toolkit block (createSVGOverlay, arrowMarker, connectElements, animateFlow, recalculate, highlightConnections, resetHighlight) then add:

```javascript
document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('flowDiagram');
    const svg = createSVGOverlay(container);

    // Happy path — animated dashes in info color
    const happyPath = [
        ['step-input',    'step-dispatch'],
        ['step-dispatch', 'step-review'],
        ['step-review',   'step-merge'],
        ['step-merge',    'step-output'],
    ];
    happyPath.forEach(([fromId, toId]) => {
        const fromEl = document.getElementById(fromId);
        const toEl   = document.getElementById(toId);
        if (fromEl && toEl) {
            connectElements(svg, fromEl, toEl, {
                color: 'var(--color-info)',
                width: 2,
                animate: true,
                arrow: 'end',
            });
        }
    });

    // Error branch — dashed in error color
    const errorEl = document.getElementById('step-error');
    const dispatchEl = document.getElementById('step-dispatch');
    if (dispatchEl && errorEl) {
        const conn = connectElements(svg, dispatchEl, errorEl, {
            color: 'var(--color-error)',
            width: 2,
            arrow: 'end',
            curvature: 0.3,
        });
        conn.path.setAttribute('stroke-dasharray', '6 3');
    }

    // Hover-to-highlight
    document.querySelectorAll('.flow-step').forEach(node => {
        node.addEventListener('mouseenter', () => highlightConnections(node, svg));
        node.addEventListener('mouseleave', () => resetHighlight(svg));
    });
});
```
