# Timeline Type

Also read: `svg-toolkit.md` only if milestones have dependency arrows between them

Use for: phases, milestones, schedules, roadmaps. Vertical track with phases as colored bars and milestone diamonds. "Today" marker as a dashed horizontal line.

## HTML Structure

```html
<h1>Project Timeline</h1>

<div class="timeline">
    <div class="timeline-track">
        <!-- Today marker — set top% to match current progress through timeline -->
        <div class="tl-now" style="top: 40%">
            <span class="tl-now-label label">Today</span>
        </div>

        <!-- Phase: dates are informational labels -->
        <div class="tl-phase" style="--phase-color: var(--cat-blue)"
             data-tooltip="Jan–Feb 2026: Initial design and agent scaffolding">
            <div class="tl-phase-bar"></div>
            <div class="tl-phase-content">
                <div class="tl-phase-name">Phase 1: Design</div>
                <div class="tl-phase-dates label">Jan – Feb 2026</div>
                <ul class="tl-phase-items">
                    <li>Define agent protocol</li>
                    <li>Scaffold CLI commands</li>
                </ul>
            </div>
        </div>

        <!-- Milestone -->
        <div class="tl-milestone" style="--milestone-color: var(--cat-green)"
             data-tooltip="v0.1 alpha shipped Mar 1">
            <div class="tl-milestone-diamond"></div>
            <div class="tl-milestone-label">v0.1 Alpha — Mar 1</div>
        </div>

        <div class="tl-phase" style="--phase-color: var(--cat-green)"
             data-tooltip="Mar–Apr 2026: Implementation sprint">
            <div class="tl-phase-bar"></div>
            <div class="tl-phase-content">
                <div class="tl-phase-name">Phase 2: Implementation</div>
                <div class="tl-phase-dates label">Mar – Apr 2026</div>
                <ul class="tl-phase-items">
                    <li>Core agent logic</li>
                    <li>Editor integration</li>
                    <li>Test coverage</li>
                </ul>
            </div>
        </div>

        <!-- Milestone -->
        <div class="tl-milestone" style="--milestone-color: var(--cat-yellow)"
             data-tooltip="v0.5 beta — May 1">
            <div class="tl-milestone-diamond"></div>
            <div class="tl-milestone-label">v0.5 Beta — May 1</div>
        </div>

        <div class="tl-phase" style="--phase-color: var(--cat-purple)"
             data-tooltip="May–Jun 2026: Hardening and release prep">
            <div class="tl-phase-bar"></div>
            <div class="tl-phase-content">
                <div class="tl-phase-name">Phase 3: Hardening</div>
                <div class="tl-phase-dates label">May – Jun 2026</div>
                <ul class="tl-phase-items">
                    <li>Performance benchmarks</li>
                    <li>Documentation</li>
                </ul>
            </div>
        </div>

        <!-- Milestone -->
        <div class="tl-milestone" style="--milestone-color: var(--cat-cyan)"
             data-tooltip="v1.0 GA — Jul 1">
            <div class="tl-milestone-diamond"></div>
            <div class="tl-milestone-label">v1.0 GA — Jul 1</div>
        </div>
    </div>
</div>
```

## CSS

```css
.timeline {
    max-width: 700px;
    padding: 1rem 0;
}

.timeline-track {
    position: relative;
    padding-left: 3rem;
}

/* Vertical center line */
.timeline-track::before {
    content: '';
    position: absolute;
    left: 1.25rem;
    top: 0;
    bottom: 0;
    width: 2px;
    background: var(--border-default);
    border-radius: 1px;
}

/* Phase row */
.tl-phase {
    position: relative;
    margin-bottom: 1rem;
    display: flex;
    gap: 1rem;
    align-items: flex-start;
}

/* Phase dot on the track line */
.tl-phase::before {
    content: '';
    position: absolute;
    left: -1.75rem;
    top: 0.55rem;
    width: 0.75rem;
    height: 0.75rem;
    border-radius: 50%;
    background: var(--phase-color, var(--cat-blue));
    border: 2px solid var(--bg-page);
    z-index: 1;
}

/* Colored left bar */
.tl-phase-bar {
    width: 3px;
    min-height: 100%;
    background: var(--phase-color, var(--cat-blue));
    border-radius: 2px;
    flex-shrink: 0;
    align-self: stretch;
}

.tl-phase-content {
    background: var(--bg-card);
    border: 1px solid var(--border-default);
    border-radius: 8px;
    padding: 0.85rem 1rem;
    flex: 1;
    transition: border-color 0.2s ease, background 0.2s ease;
}

.tl-phase-content:hover {
    border-color: var(--border-active);
    background: var(--bg-elevated);
}

.tl-phase-name {
    font-weight: 600;
    font-size: 0.9rem;
    color: var(--text-heading);
    margin-bottom: 0.2rem;
}

.tl-phase-dates {
    font-size: 0.72rem;
    margin-bottom: 0.5rem;
}

.tl-phase-items {
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
    padding: 0;
}

.tl-phase-items li {
    font-size: 0.82rem;
    color: var(--text-secondary);
    padding-left: 0.75rem;
    position: relative;
}

.tl-phase-items li::before {
    content: '·';
    position: absolute;
    left: 0;
    color: var(--text-muted);
}

/* Milestone row */
.tl-milestone {
    position: relative;
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1rem;
    cursor: default;
}

.tl-milestone-diamond {
    width: 0.75rem;
    height: 0.75rem;
    background: var(--milestone-color, var(--cat-yellow));
    transform: rotate(45deg);
    flex-shrink: 0;
    position: absolute;
    left: -1.75rem;
    z-index: 1;
    border: 2px solid var(--bg-page);
}

.tl-milestone-label {
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--milestone-color, var(--cat-yellow));
    padding: 0.25rem 0.6rem;
    border-radius: 9999px;
    background: color-mix(in srgb, var(--milestone-color, var(--cat-yellow)) 12%, transparent);
    border: 1px solid color-mix(in srgb, var(--milestone-color, var(--cat-yellow)) 30%, transparent);
}

/* Today marker */
.tl-now {
    position: absolute;
    left: -0.5rem;
    right: 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    z-index: 2;
    pointer-events: none;
}

.tl-now::before {
    content: '';
    display: block;
    width: 100%;
    height: 0;
    border-top: 2px dashed var(--color-warning);
    position: absolute;
    left: 0;
}

.tl-now-label {
    position: relative;
    background: var(--bg-page);
    padding: 0.1rem 0.4rem;
    border-radius: 4px;
    font-size: 0.7rem;
    color: var(--color-warning);
    white-space: nowrap;
    left: -2.5rem;
    border: 1px solid var(--color-warning);
}
```

## JS

```javascript
document.addEventListener('DOMContentLoaded', () => {
    // Simple tooltip support via data-tooltip attributes
    const tip = document.createElement('div');
    tip.style.cssText = [
        'position:fixed',
        'background:var(--bg-elevated)',
        'border:1px solid var(--border-default)',
        'border-radius:6px',
        'padding:0.5rem 0.75rem',
        'font-size:0.8rem',
        'color:var(--text-body)',
        'max-width:260px',
        'pointer-events:none',
        'opacity:0',
        'z-index:1000',
        'box-shadow:0 4px 12px rgba(0,0,0,0.4)',
        'transition:opacity 0.15s ease',
    ].join(';');
    document.body.appendChild(tip);

    document.addEventListener('mouseover', (e) => {
        const target = e.target.closest('[data-tooltip]');
        if (!target) return;
        tip.textContent = target.getAttribute('data-tooltip');
        tip.style.opacity = '1';
    });
    document.addEventListener('mousemove', (e) => {
        if (tip.style.opacity === '0') return;
        let x = e.clientX + 12;
        let y = e.clientY + 12;
        const rect = tip.getBoundingClientRect();
        if (x + rect.width  > window.innerWidth)  x = e.clientX - rect.width  - 12;
        if (y + rect.height > window.innerHeight) y = e.clientY - rect.height - 12;
        tip.style.left = x + 'px';
        tip.style.top  = y + 'px';
    });
    document.addEventListener('mouseout', (e) => {
        if (!e.target.closest('[data-tooltip]')) return;
        tip.style.opacity = '0';
    });

    // If milestone dependency arrows are needed, paste the SVG toolkit block here
    // and use connectElements() to draw arrows between .tl-milestone elements.
    // Wrap the .timeline in a .diagram-container and call createSVGOverlay().
});
```
