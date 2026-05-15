# Tree Hierarchy Type

Also read: `interactivity.md`

Use for: hierarchical structures — file trees, org charts, category hierarchies. Collapsible nodes with CSS connecting lines. Search auto-expands matched nodes.

## HTML Structure

```html
<h1>File Tree</h1>

<!-- Search bar (from interactivity kit) -->
<div class="search-bar">
    <input type="text" id="searchInput" placeholder="Filter files...">
    <span class="count" id="searchCount"></span>
    <span class="hint">Press / to focus</span>
</div>

<div class="tree">
    <!-- Root node -->
    <div class="tree-node">
        <div class="tree-item tree-toggle" data-tree-id="root">
            <span class="tree-icon">📁</span>
            <span class="tree-label">codemonkeys/</span>
            <span class="tree-meta label">12 files</span>
        </div>
        <div class="tree-children open" id="children-root">

            <div class="tree-node" data-searchable data-search="agents">
                <div class="tree-item tree-toggle" data-tree-id="agents">
                    <span class="tree-icon">📁</span>
                    <span class="tree-label">agents/</span>
                    <span class="tree-meta label">3 files</span>
                </div>
                <div class="tree-children open" id="children-agents">
                    <div class="tree-node" data-searchable data-search="code_reviewer.py">
                        <div class="tree-item">
                            <span class="tree-icon">🐍</span>
                            <span class="tree-label">code_reviewer.py</span>
                            <span class="tree-meta label">1.2 KB</span>
                        </div>
                    </div>
                    <div class="tree-node" data-searchable data-search="code_editor.py">
                        <div class="tree-item">
                            <span class="tree-icon">🐍</span>
                            <span class="tree-label">code_editor.py</span>
                            <span class="tree-meta label">0.9 KB</span>
                        </div>
                    </div>
                    <div class="tree-node" data-searchable data-search="__init__.py">
                        <div class="tree-item">
                            <span class="tree-icon">🐍</span>
                            <span class="tree-label">__init__.py</span>
                            <span class="tree-meta label">0.1 KB</span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="tree-node" data-searchable data-search="core">
                <div class="tree-item tree-toggle" data-tree-id="core">
                    <span class="tree-icon">📁</span>
                    <span class="tree-label">core/</span>
                    <span class="tree-meta label">4 files</span>
                </div>
                <div class="tree-children open" id="children-core">
                    <div class="tree-node" data-searchable data-search="runner.py">
                        <div class="tree-item">
                            <span class="tree-icon">🐍</span>
                            <span class="tree-label">runner.py</span>
                            <span class="tree-meta label">3.4 KB</span>
                        </div>
                    </div>
                    <div class="tree-node" data-searchable data-search="config.py">
                        <div class="tree-item">
                            <span class="tree-icon">🐍</span>
                            <span class="tree-label">config.py</span>
                            <span class="tree-meta label">1.1 KB</span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="tree-node" data-searchable data-search="cli.py">
                <div class="tree-item">
                    <span class="tree-icon">🐍</span>
                    <span class="tree-label">cli.py</span>
                    <span class="tree-meta label">2.8 KB</span>
                </div>
            </div>
        </div>
    </div>
</div>
```

## CSS

```css
/* Search bar (from interactivity kit) */
.search-bar {
    position: sticky;
    top: 0;
    z-index: 50;
    padding: 0.75rem 0;
    background: var(--bg-page);
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}
.search-bar input {
    flex: 1;
    background: var(--bg-card);
    border: 1px solid var(--border-default);
    border-radius: 6px;
    padding: 0.5rem 0.75rem;
    color: var(--text-body);
    font-size: 0.85rem;
    outline: none;
}
.search-bar input:focus { border-color: var(--border-active); }
.search-bar .count {
    font-size: 0.75rem;
    color: var(--text-muted);
    white-space: nowrap;
}
.search-bar .hint {
    font-size: 0.7rem;
    color: var(--text-muted);
    opacity: 0.6;
}
[data-searchable].search-hidden { opacity: 0.12; }

/* Tree */
.tree {
    font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
    font-size: 0.85rem;
}

.tree-node {
    position: relative;
}

/* Vertical connecting line for children */
.tree-children {
    padding-left: 1.4rem;
    position: relative;
    overflow: hidden;
    max-height: 5000px;
    transition: max-height 0.3s ease, opacity 0.2s ease;
    opacity: 1;
}

.tree-children.collapsed {
    max-height: 0;
    opacity: 0;
}

/* Left border line */
.tree-children::before {
    content: '';
    position: absolute;
    left: 0.6rem;
    top: 0;
    bottom: 0;
    width: 1px;
    background: var(--border-default);
}

.tree-item {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    cursor: default;
    color: var(--text-secondary);
    line-height: 1.4;
    transition: background 0.15s ease, color 0.15s ease;
}

.tree-item:hover {
    background: var(--bg-elevated);
    color: var(--text-body);
}

.tree-toggle {
    cursor: pointer;
}

/* Chevron before toggleable items */
.tree-toggle::before {
    content: '▸';
    font-size: 0.65rem;
    color: var(--text-muted);
    display: inline-block;
    transition: transform 0.2s ease;
    margin-right: 0.1rem;
    flex-shrink: 0;
}

.tree-toggle.open::before {
    transform: rotate(90deg);
}

.tree-icon {
    font-size: 0.85rem;
    flex-shrink: 0;
    line-height: 1;
}

.tree-label {
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.tree-meta {
    font-size: 0.7rem;
    margin-left: auto;
    white-space: nowrap;
    flex-shrink: 0;
    color: var(--text-muted);
    font-family: system-ui, sans-serif;
}
```

## JS

Paste the initSearch() function from interactivity.md, then add:

```javascript
function toggleTree(id) {
    const toggle = document.querySelector(`[data-tree-id="${id}"]`);
    const children = document.getElementById(`children-${id}`);
    if (!toggle || !children) return;
    const isOpen = toggle.classList.contains('open');
    toggle.classList.toggle('open', !isOpen);
    children.classList.toggle('collapsed', isOpen);
}

// Auto-expand ancestors of search matches
function expandToMatch(query) {
    if (!query) return;
    document.querySelectorAll('[data-searchable]').forEach(node => {
        const text = (node.getAttribute('data-search') || node.textContent).toLowerCase();
        if (!text.includes(query)) return;
        // Walk up and open parent tree-children
        let el = node.parentElement;
        while (el) {
            if (el.classList.contains('tree-children') && el.classList.contains('collapsed')) {
                el.classList.remove('collapsed');
                el.style.opacity = '1';
                el.style.maxHeight = '5000px';
                // Also open the toggle above
                const treeId = el.id.replace('children-', '');
                const toggle = document.querySelector(`[data-tree-id="${treeId}"]`);
                if (toggle) toggle.classList.add('open');
            }
            el = el.parentElement;
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    // Wire up toggle clicks
    document.querySelectorAll('.tree-toggle').forEach(toggle => {
        toggle.addEventListener('click', () => {
            const id = toggle.getAttribute('data-tree-id');
            if (id) toggleTree(id);
        });
    });

    // Init search with auto-expand
    const input = document.getElementById('searchInput');
    const countEl = document.getElementById('searchCount');
    if (input) {
        const items = document.querySelectorAll('[data-searchable]');
        let debounceTimer;
        input.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                const q = input.value.toLowerCase().trim();
                let visible = 0;
                items.forEach(item => {
                    const text = (item.getAttribute('data-search') || item.textContent).toLowerCase();
                    const match = !q || text.includes(q);
                    item.classList.toggle('search-hidden', !match);
                    if (match) visible++;
                });
                if (countEl) countEl.textContent = q ? `${visible} of ${items.length}` : '';
                if (q) expandToMatch(q);
            }, 150);
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === '/' && document.activeElement !== input) {
                e.preventDefault();
                input.focus();
            }
            if (e.key === 'Escape' && document.activeElement === input) {
                input.value = '';
                input.dispatchEvent(new Event('input'));
                input.blur();
            }
        });
    }
});
```
