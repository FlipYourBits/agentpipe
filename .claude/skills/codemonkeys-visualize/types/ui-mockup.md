# UI Mockup Type

Also read: nothing extra

Use for: interface layouts, wireframes, component libraries, screen designs. Muted palette to convey "this is a mockup, not final UI."

## HTML Structure

```html
<h1>UI Mockup: Dashboard</h1>
<p style="color: var(--text-muted); margin-bottom: 1.5rem; font-size: 0.85rem;">Wireframe — not final design. Annotations numbered below.</p>

<div class="mockup-frame">
    <!-- Title bar with window dots -->
    <div class="mockup-titlebar">
        <div class="titlebar-dots">
            <span class="dot dot-red"></span>
            <span class="dot dot-yellow"></span>
            <span class="dot dot-green"></span>
        </div>
        <div class="titlebar-url label">localhost:3000/dashboard</div>
    </div>

    <!-- Navigation bar -->
    <nav class="mock-navbar">
        <div class="mock-logo">Codemonkeys</div>
        <div class="mock-nav-links">
            <a class="mock-nav-link active" href="#">Reviews</a>
            <a class="mock-nav-link" href="#">History</a>
            <a class="mock-nav-link" href="#">Settings</a>
        </div>
        <div class="mock-nav-actions">
            <button class="mock-btn secondary">Sign in</button>
        </div>
    </nav>

    <!-- Page content -->
    <div class="mock-content">
        <!-- Section 1: hero / toolbar -->
        <div class="mock-section">
            <div class="mock-toolbar">
                <input class="mock-input" type="text" placeholder="Search files..." readonly>
                <button class="mock-btn primary">
                    <span class="mock-pin" data-annotation="1">1</span>
                    Run Review
                </button>
            </div>
        </div>

        <!-- Section 2: cards row -->
        <div class="mock-section">
            <div class="mock-cards-row">
                <div class="mock-card">
                    <div class="mock-card-label label">Files reviewed</div>
                    <div class="mock-card-value">24</div>
                </div>
                <div class="mock-card">
                    <div class="mock-card-label label">Findings</div>
                    <div class="mock-card-value">
                        7
                        <span class="mock-pin" data-annotation="2">2</span>
                    </div>
                </div>
                <div class="mock-card">
                    <div class="mock-card-label label">Fixed</div>
                    <div class="mock-card-value">3</div>
                </div>
            </div>
        </div>

        <!-- Section 3: data table -->
        <div class="mock-section">
            <div class="mock-section-title label">Recent Reviews</div>
            <table class="mock-table">
                <thead>
                    <tr>
                        <th>File</th>
                        <th>Severity</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><code>cli.py</code></td>
                        <td>Medium</td>
                        <td>Fixed</td>
                    </tr>
                    <tr>
                        <td><code>runner.py</code></td>
                        <td>High</td>
                        <td>Pending</td>
                    </tr>
                    <tr>
                        <td><code>dispatch.py</code></td>
                        <td>Low</td>
                        <td>Fixed</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</div>

<!-- Annotation list -->
<div class="annotation-list">
    <h2>Annotations</h2>
    <div class="annotation-item">
        <span class="mock-pin">1</span>
        <span>Primary CTA — triggers agent pipeline. Should confirm if >50 files selected.</span>
    </div>
    <div class="annotation-item">
        <span class="mock-pin">2</span>
        <span>Finding count links to filtered table view showing only flagged files.</span>
    </div>
</div>
```

## CSS

```css
.mockup-frame {
    border: 1px solid var(--border-default);
    border-radius: 10px;
    overflow: hidden;
    background: var(--bg-card);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    max-width: 900px;
}

/* Title bar */
.mockup-titlebar {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.6rem 1rem;
    background: var(--bg-elevated);
    border-bottom: 1px solid var(--border-default);
}

.titlebar-dots {
    display: flex;
    gap: 0.4rem;
}

.dot {
    width: 0.65rem;
    height: 0.65rem;
    border-radius: 50%;
    opacity: 0.7;
}

.dot-red    { background: var(--color-error); }
.dot-yellow { background: var(--color-warning); }
.dot-green  { background: var(--color-success); }

.titlebar-url {
    font-size: 0.75rem;
    color: var(--text-muted);
}

/* Navbar */
.mock-navbar {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    padding: 0.75rem 1.25rem;
    background: var(--bg-elevated);
    border-bottom: 1px solid var(--border-default);
    flex-wrap: wrap;
}

.mock-logo {
    font-weight: 700;
    font-size: 0.95rem;
    color: var(--text-heading);
    margin-right: auto;
}

.mock-nav-links {
    display: flex;
    gap: 1.25rem;
}

.mock-nav-link {
    font-size: 0.85rem;
    color: var(--text-muted);
    text-decoration: none;
    padding-bottom: 0.15rem;
}

.mock-nav-link.active {
    color: var(--text-body);
    border-bottom: 2px solid var(--color-info);
}

.mock-nav-actions {
    display: flex;
    gap: 0.5rem;
}

/* Content area */
.mock-content {
    padding: 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
}

.mock-section {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.mock-section-title {
    font-size: 0.75rem;
    margin-bottom: 0.25rem;
}

.mock-toolbar {
    display: flex;
    gap: 0.75rem;
    align-items: center;
}

/* Shared button styles */
.mock-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.45rem 1rem;
    border-radius: 6px;
    font-size: 0.82rem;
    font-weight: 500;
    cursor: default;
    border: 1px solid transparent;
    white-space: nowrap;
}

.mock-btn.primary {
    background: color-mix(in srgb, var(--color-info) 20%, var(--bg-elevated));
    border-color: var(--color-info);
    color: var(--color-info);
}

.mock-btn.secondary {
    background: var(--bg-card);
    border-color: var(--border-default);
    color: var(--text-secondary);
}

/* Input */
.mock-input {
    background: var(--bg-page);
    border: 1px solid var(--border-default);
    border-radius: 6px;
    padding: 0.45rem 0.75rem;
    color: var(--text-muted);
    font-size: 0.82rem;
    flex: 1;
    min-width: 0;
    cursor: default;
}

/* KPI cards row */
.mock-cards-row {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
}

.mock-card {
    flex: 1;
    min-width: 100px;
    background: var(--bg-page);
    border: 1px solid var(--border-default);
    border-radius: 8px;
    padding: 1rem;
}

.mock-card-label {
    font-size: 0.72rem;
    margin-bottom: 0.3rem;
}

.mock-card-value {
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--text-heading);
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* Table */
.mock-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.83rem;
}

.mock-table th {
    text-align: left;
    padding: 0.5rem 0.75rem;
    font-size: 0.72rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    border-bottom: 1px solid var(--border-default);
}

.mock-table td {
    padding: 0.55rem 0.75rem;
    border-bottom: 1px solid var(--border-default);
    color: var(--text-secondary);
}

.mock-table tr:last-child td {
    border-bottom: none;
}

/* Annotation pins */
.mock-pin {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.2rem;
    height: 1.2rem;
    min-width: 1.2rem;
    border-radius: 50%;
    background: var(--cat-orange);
    color: var(--bg-page);
    font-size: 0.65rem;
    font-weight: 700;
    line-height: 1;
    cursor: default;
}

/* Annotation list */
.annotation-list {
    margin-top: 1.5rem;
    max-width: 900px;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.annotation-item {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    font-size: 0.85rem;
    color: var(--text-secondary);
    padding: 0.5rem 0;
    border-bottom: 1px solid var(--border-default);
}

.annotation-item:last-child {
    border-bottom: none;
}
```

## JS

```javascript
// Minimal: no complex interaction needed for basic wireframes.
// Add annotation toggles if interactive annotations are needed.
document.addEventListener('DOMContentLoaded', () => {
    // Clicking a pin in the mockup scrolls to its annotation
    document.querySelectorAll('.mock-pin[data-annotation]').forEach(pin => {
        pin.style.cursor = 'pointer';
        pin.addEventListener('click', (e) => {
            e.stopPropagation();
            const num = pin.getAttribute('data-annotation');
            const annos = document.querySelectorAll('.annotation-item');
            annos.forEach((anno, i) => {
                if (String(i + 1) === num) {
                    anno.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    anno.style.outline = '2px solid var(--border-active)';
                    setTimeout(() => anno.style.outline = '', 1500);
                }
            });
        });
    });
});
```
