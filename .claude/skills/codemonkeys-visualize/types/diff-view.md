# Diff View Type

Also read: nothing extra

Use for: before/after code changes, file diffs, patch previews. Unified and split view toggle. Line numbers, gutter markers, word-level highlights, collapsible unchanged regions.

## HTML Structure

```html
<h1>Diff: cli.py</h1>

<div class="diff-controls">
    <button class="diff-mode-btn active" id="btnUnified" onclick="showUnified()">Unified</button>
    <button class="diff-mode-btn" id="btnSplit" onclick="showSplit()">Split</button>
    <span class="diff-stats">
        <span class="added-stat">+12</span>
        <span class="removed-stat">−5</span>
    </span>
</div>

<!-- ═══ UNIFIED VIEW ═══ -->
<div class="diff-container" id="unifiedView">
    <!-- Collapsed unchanged block -->
    <div class="diff-collapsed" onclick="this.remove()">
        ↕ 18 unchanged lines — click to expand
    </div>

    <!-- Changed lines -->
    <div class="diff-line removed">
        <span class="diff-ln diff-ln-old">42</span>
        <span class="diff-ln diff-ln-new"> </span>
        <span class="diff-marker">−</span>
        <span class="diff-content">    result = subprocess.run(cmd, shell=True)</span>
    </div>
    <div class="diff-line added">
        <span class="diff-ln diff-ln-old"> </span>
        <span class="diff-ln diff-ln-new">42</span>
        <span class="diff-marker">+</span>
        <span class="diff-content">    result = subprocess.run(<span class="diff-word-add">shlex.split(cmd)</span>)</span>
    </div>

    <div class="diff-line context">
        <span class="diff-ln diff-ln-old">43</span>
        <span class="diff-ln diff-ln-new">43</span>
        <span class="diff-marker"> </span>
        <span class="diff-content">    return result.stdout</span>
    </div>
    <div class="diff-line context">
        <span class="diff-ln diff-ln-old">44</span>
        <span class="diff-ln diff-ln-new">44</span>
        <span class="diff-marker"> </span>
        <span class="diff-content">&#160;</span>
    </div>

    <div class="diff-line removed">
        <span class="diff-ln diff-ln-old">45</span>
        <span class="diff-ln diff-ln-new"> </span>
        <span class="diff-marker">−</span>
        <span class="diff-content">def run(files):</span>
    </div>
    <div class="diff-line added">
        <span class="diff-ln diff-ln-old"> </span>
        <span class="diff-ln diff-ln-new">45</span>
        <span class="diff-marker">+</span>
        <span class="diff-content">def run(<span class="diff-word-add">files: list[str]</span><span class="diff-word-del">files</span>):</span>
    </div>

    <!-- Another collapsed section -->
    <div class="diff-collapsed" onclick="this.remove()">
        ↕ 6 unchanged lines — click to expand
    </div>

    <div class="diff-line added">
        <span class="diff-ln diff-ln-old"> </span>
        <span class="diff-ln diff-ln-new">52</span>
        <span class="diff-marker">+</span>
        <span class="diff-content">    import shlex</span>
    </div>
</div>

<!-- ═══ SPLIT VIEW ═══ -->
<div class="diff-container diff-split" id="splitView" style="display:none">
    <div class="diff-pane diff-pane-old">
        <div class="diff-pane-header label">Before</div>
        <div class="diff-line removed">
            <span class="diff-ln">42</span>
            <span class="diff-content">    result = subprocess.run(cmd, shell=True)</span>
        </div>
        <div class="diff-line context">
            <span class="diff-ln">43</span>
            <span class="diff-content">    return result.stdout</span>
        </div>
        <div class="diff-line removed">
            <span class="diff-ln">45</span>
            <span class="diff-content">def run(files):</span>
        </div>
        <div class="diff-line context">
            <span class="diff-ln"> </span>
            <span class="diff-content">&#160;</span>
        </div>
    </div>
    <div class="diff-pane diff-pane-new">
        <div class="diff-pane-header label">After</div>
        <div class="diff-line added">
            <span class="diff-ln">42</span>
            <span class="diff-content">    result = subprocess.run(<span class="diff-word-add">shlex.split(cmd)</span>)</span>
        </div>
        <div class="diff-line context">
            <span class="diff-ln">43</span>
            <span class="diff-content">    return result.stdout</span>
        </div>
        <div class="diff-line added">
            <span class="diff-ln">45</span>
            <span class="diff-content">def run(<span class="diff-word-add">files: list[str]</span>):</span>
        </div>
        <div class="diff-line added">
            <span class="diff-ln">52</span>
            <span class="diff-content">    import shlex</span>
        </div>
    </div>
</div>
```

## CSS

```css
/* Controls */
.diff-controls {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 1rem;
    flex-wrap: wrap;
}

.diff-mode-btn {
    background: var(--bg-card);
    border: 1px solid var(--border-default);
    color: var(--text-muted);
    border-radius: 6px;
    padding: 0.35rem 0.8rem;
    font-size: 0.8rem;
    cursor: pointer;
    transition: background 0.15s, border-color 0.15s, color 0.15s;
}

.diff-mode-btn:hover { border-color: var(--border-active); color: var(--text-body); }
.diff-mode-btn.active {
    background: var(--bg-elevated);
    border-color: var(--border-active);
    color: var(--text-heading);
}

.diff-stats {
    margin-left: auto;
    font-size: 0.82rem;
    font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
}

.added-stat   { color: var(--color-success); }
.removed-stat { color: var(--color-error); margin-left: 0.5rem; }

/* Unified container */
.diff-container {
    border: 1px solid var(--border-default);
    border-radius: 8px;
    overflow: hidden;
    font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
    font-size: 0.82rem;
    line-height: 1.55;
    background: var(--bg-card);
}

/* Individual lines */
.diff-line {
    display: flex;
    align-items: stretch;
    min-height: 1.55em;
}

.diff-line.added   { background: color-mix(in srgb, var(--color-success) 10%, transparent); }
.diff-line.removed { background: color-mix(in srgb, var(--color-error)   10%, transparent); }
.diff-line.context { background: transparent; }

/* Line numbers */
.diff-ln {
    min-width: 2.5rem;
    padding: 0 0.5rem;
    text-align: right;
    color: var(--text-muted);
    font-size: 0.75rem;
    border-right: 1px solid var(--border-default);
    user-select: none;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: flex-end;
}

.diff-ln-old { background: color-mix(in srgb, var(--bg-page) 30%, transparent); }
.diff-ln-new { background: color-mix(in srgb, var(--bg-elevated) 30%, transparent); }

/* Gutter marker (+/-/ ) */
.diff-marker {
    width: 1.5rem;
    text-align: center;
    flex-shrink: 0;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
}

.diff-line.added   .diff-marker { color: var(--color-success); }
.diff-line.removed .diff-marker { color: var(--color-error); }
.diff-line.context .diff-marker { color: var(--text-muted); }

/* Content */
.diff-content {
    padding: 0 0.75rem;
    white-space: pre;
    overflow-x: auto;
    flex: 1;
    display: flex;
    align-items: center;
}

/* Word-level highlights */
.diff-word-add {
    background: color-mix(in srgb, var(--color-success) 30%, transparent);
    border-radius: 2px;
    padding: 0 0.1rem;
}

.diff-word-del {
    background: color-mix(in srgb, var(--color-error) 30%, transparent);
    border-radius: 2px;
    padding: 0 0.1rem;
    text-decoration: line-through;
    opacity: 0.7;
}

/* Collapsed unchanged region */
.diff-collapsed {
    padding: 0.4rem 1rem;
    font-size: 0.78rem;
    color: var(--text-muted);
    background: var(--bg-elevated);
    border-top: 1px solid var(--border-default);
    border-bottom: 1px solid var(--border-default);
    cursor: pointer;
    text-align: center;
    transition: background 0.15s ease, color 0.15s ease;
}

.diff-collapsed:hover {
    background: var(--bg-card);
    color: var(--text-body);
}

/* Split view */
.diff-split {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0;
}

.diff-pane {
    overflow-x: auto;
}

.diff-pane-old {
    border-right: 1px solid var(--border-default);
}

.diff-pane-header {
    padding: 0.4rem 0.75rem;
    font-size: 0.72rem;
    background: var(--bg-elevated);
    border-bottom: 1px solid var(--border-default);
}

/* Single line number column in split panes */
.diff-split .diff-ln {
    min-width: 2rem;
}
```

## JS

```javascript
function showUnified() {
    document.getElementById('unifiedView').style.display = 'block';
    document.getElementById('splitView').style.display = 'none';
    document.getElementById('btnUnified').classList.add('active');
    document.getElementById('btnSplit').classList.remove('active');
}

function showSplit() {
    document.getElementById('unifiedView').style.display = 'none';
    document.getElementById('splitView').style.display = 'grid';
    document.getElementById('btnUnified').classList.remove('active');
    document.getElementById('btnSplit').classList.add('active');
}

document.addEventListener('DOMContentLoaded', () => {
    showUnified(); // Default to unified view
});
```
