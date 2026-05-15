# Interactivity Kit

Use this when the visual needs rich interaction beyond basic click-to-select. Copy the patterns you need into the `<script>` section of the generated HTML.

---

## 1. Zoom/Pan

### CSS

```css
.zoomable-container {
    overflow: hidden;
    cursor: grab;
    position: relative;
}
.zoomable-container.grabbing { cursor: grabbing; }
.zoomable-inner {
    transform-origin: 0 0;
    will-change: transform;
}
.zoom-controls {
    position: fixed;
    bottom: 1.5rem;
    right: 1.5rem;
    display: flex;
    gap: 0.5rem;
    align-items: center;
    z-index: 100;
}
.zoom-controls button {
    background: var(--bg-elevated);
    border: 1px solid var(--border-default);
    color: var(--text-body);
    border-radius: 6px;
    width: 2rem;
    height: 2rem;
    cursor: pointer;
    font-size: 1rem;
    display: flex;
    align-items: center;
    justify-content: center;
}
.zoom-controls button:hover { border-color: var(--border-active); }
.zoom-level {
    font-size: 0.75rem;
    color: var(--text-muted);
    min-width: 3rem;
    text-align: center;
}
```

### HTML

```html
<div class="zoomable-container" id="zoomContainer">
    <div class="zoomable-inner" id="zoomInner">
        <!-- diagram content here -->
    </div>
</div>
<div class="zoom-controls">
    <button id="zoomOut">−</button>
    <span class="zoom-level" id="zoomLevel">100%</span>
    <button id="zoomIn">+</button>
    <button id="zoomReset">⌂</button>
</div>
```

### JS

```javascript
function initZoomPan(containerId, innerId, opts = {}) {
    const container = document.getElementById(containerId);
    const inner = document.getElementById(innerId);
    const levelDisplay = document.getElementById('zoomLevel');
    const minScale = opts.min || 0.25;
    const maxScale = opts.max || 4;
    const onTransform = opts.onTransform || null;

    let scale = 1, panX = 0, panY = 0;
    let isDragging = false, startX, startY;

    function apply() {
        inner.style.transform = `translate(${panX}px, ${panY}px) scale(${scale})`;
        if (levelDisplay) levelDisplay.textContent = Math.round(scale * 100) + '%';
        if (onTransform) onTransform(scale, panX, panY);
    }

    container.addEventListener('wheel', (e) => {
        e.preventDefault();
        const delta = e.deltaY > 0 ? 0.9 : 1.1;
        const newScale = Math.min(maxScale, Math.max(minScale, scale * delta));
        const rect = container.getBoundingClientRect();
        const mx = e.clientX - rect.left;
        const my = e.clientY - rect.top;
        panX = mx - (mx - panX) * (newScale / scale);
        panY = my - (my - panY) * (newScale / scale);
        scale = newScale;
        apply();
    }, { passive: false });

    container.addEventListener('mousedown', (e) => {
        if (e.button !== 0) return;
        isDragging = true;
        startX = e.clientX - panX;
        startY = e.clientY - panY;
        container.classList.add('grabbing');
    });
    window.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        panX = e.clientX - startX;
        panY = e.clientY - startY;
        apply();
    });
    window.addEventListener('mouseup', () => {
        isDragging = false;
        container.classList.remove('grabbing');
    });

    let lastTouchDist = null;
    container.addEventListener('touchstart', (e) => {
        if (e.touches.length === 1) {
            isDragging = true;
            startX = e.touches[0].clientX - panX;
            startY = e.touches[0].clientY - panY;
        }
    });
    container.addEventListener('touchmove', (e) => {
        if (e.touches.length === 2) {
            e.preventDefault();
            const dist = Math.hypot(
                e.touches[0].clientX - e.touches[1].clientX,
                e.touches[0].clientY - e.touches[1].clientY
            );
            if (lastTouchDist) {
                const delta = dist / lastTouchDist;
                scale = Math.min(maxScale, Math.max(minScale, scale * delta));
                apply();
            }
            lastTouchDist = dist;
        } else if (isDragging && e.touches.length === 1) {
            panX = e.touches[0].clientX - startX;
            panY = e.touches[0].clientY - startY;
            apply();
        }
    }, { passive: false });
    container.addEventListener('touchend', () => {
        isDragging = false;
        lastTouchDist = null;
    });

    document.getElementById('zoomIn')?.addEventListener('click', () => {
        scale = Math.min(maxScale, scale * 1.2);
        apply();
    });
    document.getElementById('zoomOut')?.addEventListener('click', () => {
        scale = Math.max(minScale, scale * 0.8);
        apply();
    });
    document.getElementById('zoomReset')?.addEventListener('click', () => {
        scale = 1; panX = 0; panY = 0;
        apply();
    });

    apply();
    return { getScale: () => scale, reset: () => { scale = 1; panX = 0; panY = 0; apply(); } };
}
```

---

## 2. Tooltips

### CSS

```css
.tooltip {
    position: fixed;
    background: var(--bg-elevated);
    border: 1px solid var(--border-default);
    border-radius: 6px;
    padding: 0.5rem 0.75rem;
    font-size: 0.8rem;
    color: var(--text-body);
    max-width: 300px;
    pointer-events: none;
    opacity: 0;
    z-index: 1000;
    box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    word-wrap: break-word;
}
.tooltip.visible { opacity: 1; }
```

### JS

```javascript
function initTooltips() {
    const tip = document.createElement('div');
    tip.className = 'tooltip';
    document.body.appendChild(tip);

    document.addEventListener('mouseover', (e) => {
        const target = e.target.closest('[data-tooltip]');
        if (!target) return;
        const isHtml = target.getAttribute('data-tooltip-html') === 'true';
        if (isHtml) tip.innerHTML = target.getAttribute('data-tooltip');
        else tip.textContent = target.getAttribute('data-tooltip');
        tip.classList.add('visible');
    });

    document.addEventListener('mousemove', (e) => {
        if (!tip.classList.contains('visible')) return;
        let x = e.clientX + 12;
        let y = e.clientY + 12;
        const rect = tip.getBoundingClientRect();
        if (x + rect.width > window.innerWidth) x = e.clientX - rect.width - 12;
        if (y + rect.height > window.innerHeight) y = e.clientY - rect.height - 12;
        tip.style.left = x + 'px';
        tip.style.top = y + 'px';
    });

    document.addEventListener('mouseout', (e) => {
        const target = e.target.closest('[data-tooltip]');
        if (!target) return;
        tip.classList.remove('visible');
    });
}
```

**Usage:** Add `data-tooltip="Hover text here"` on any element. For HTML content, also add `data-tooltip-html="true"`.

---

## 3. Expand/Collapse

### CSS

```css
.collapsible-header {
    cursor: pointer;
    user-select: none;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.collapsible-header::before {
    content: '▸';
    display: inline-block;
    transition: transform 0.2s ease;
    font-size: 0.75rem;
    color: var(--text-muted);
}
.collapsible-header.open::before { transform: rotate(90deg); }
.collapsible-body {
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.3s ease;
}
.collapsible-body.open { max-height: 2000px; }
```

### JS

```javascript
function initCollapsibles() {
    document.querySelectorAll('[data-collapsible]').forEach(header => {
        const body = header.nextElementSibling;
        if (!body) return;
        body.classList.add('collapsible-body');
        header.classList.add('collapsible-header');

        const group = header.getAttribute('data-collapse-group');
        const startOpen = header.hasAttribute('data-start-open');
        if (startOpen) {
            header.classList.add('open');
            body.classList.add('open');
        }

        header.addEventListener('click', () => {
            const opening = !header.classList.contains('open');

            if (group && opening) {
                document.querySelectorAll(`[data-collapse-group="${group}"]`).forEach(h => {
                    h.classList.remove('open');
                    h.nextElementSibling?.classList.remove('open');
                });
            }

            header.classList.toggle('open', opening);
            body.classList.toggle('open', opening);
        });
    });
}
```

**Usage (basic):** Add `data-collapsible` to the header element; the next sibling becomes the collapsible body. Add `data-start-open` to expand by default.

**Usage (accordion):** Add `data-collapse-group="name"` to multiple headers sharing the same group name — opening one closes the others.

---

## 4. Search/Filter

### CSS

```css
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
```

### HTML

```html
<div class="search-bar">
    <input type="text" id="searchInput" placeholder="Filter...">
    <span class="count" id="searchCount"></span>
    <span class="hint">Press / to focus</span>
</div>
```

### JS

```javascript
function initSearch() {
    const input = document.getElementById('searchInput');
    const countEl = document.getElementById('searchCount');
    if (!input) return;
    const items = document.querySelectorAll('[data-searchable]');

    let debounceTimer;
    function filter() {
        const q = input.value.toLowerCase().trim();
        let visible = 0;
        items.forEach(item => {
            const text = (item.getAttribute('data-search') || item.textContent).toLowerCase();
            const match = !q || text.includes(q);
            item.classList.toggle('search-hidden', !match);
            if (match) visible++;
        });
        if (countEl) countEl.textContent = q ? `${visible} of ${items.length}` : '';
    }

    input.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(filter, 150);
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === '/' && document.activeElement !== input) {
            e.preventDefault();
            input.focus();
        }
        if (e.key === 'Escape' && document.activeElement === input) {
            input.value = '';
            filter();
            input.blur();
        }
    });
}
```

---

## 5. Keyboard Navigation

### CSS

```css
[data-nav]:focus {
    outline: 2px solid var(--border-active);
    outline-offset: 2px;
}
.shortcuts-overlay {
    position: fixed;
    bottom: 1.5rem;
    right: 1.5rem;
    background: var(--bg-elevated);
    border: 1px solid var(--border-default);
    border-radius: 8px;
    padding: 1rem;
    font-size: 0.75rem;
    color: var(--text-muted);
    z-index: 200;
    display: none;
}
.shortcuts-overlay.visible { display: block; }
.shortcuts-overlay kbd {
    background: var(--bg-card);
    border: 1px solid var(--border-default);
    border-radius: 3px;
    padding: 0.1rem 0.35rem;
    font-family: inherit;
    font-size: 0.7rem;
}
```

### JS

```javascript
function initKeyboardNav() {
    const items = Array.from(document.querySelectorAll('[data-nav]'))
        .sort((a, b) => Number(a.dataset.nav) - Number(b.dataset.nav));
    if (!items.length) return;
    items.forEach(item => item.setAttribute('tabindex', '0'));

    let currentIdx = -1;

    document.addEventListener('keydown', (e) => {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

        if (e.key === '?') {
            const overlay = document.querySelector('.shortcuts-overlay');
            if (overlay) overlay.classList.toggle('visible');
            return;
        }
        if (e.key === 'Escape') {
            items.forEach(i => i.blur());
            currentIdx = -1;
            const overlay = document.querySelector('.shortcuts-overlay');
            if (overlay) overlay.classList.remove('visible');
            return;
        }
        if (e.key === 'ArrowDown' || e.key === 'ArrowRight') {
            e.preventDefault();
            currentIdx = Math.min(currentIdx + 1, items.length - 1);
            items[currentIdx].focus();
        }
        if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
            e.preventDefault();
            currentIdx = Math.max(currentIdx - 1, 0);
            items[currentIdx].focus();
        }
        if (e.key === 'Enter' && currentIdx >= 0) {
            items[currentIdx].click();
        }
    });
}
```

---

## 6. Initialization

```javascript
document.addEventListener('DOMContentLoaded', () => {
    initTooltips();
    initCollapsibles();
    initSearch();
    initKeyboardNav();
    // If using zoom/pan with SVG connections:
    // initZoomPan('zoomContainer', 'zoomInner', {
    //     onTransform: () => recalculate(svg)
    // });
});
```
