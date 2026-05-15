# Table View Type

Also read: `interactivity.md`

Use for: structured data to explore — audit findings, file lists, metrics tables. Sortable columns, sticky header, expandable row details, badge-styled cells.

## HTML Structure

```html
<h1>Review Findings</h1>

<!-- Search bar (from interactivity kit) -->
<div class="search-bar">
    <input type="text" id="searchInput" placeholder="Filter findings...">
    <span class="count" id="searchCount"></span>
    <span class="hint">Press / to focus</span>
</div>

<div class="data-table-wrapper">
    <table class="data-table" id="findingsTable">
        <thead>
            <tr>
                <th data-sort="file">File <span class="sort-arrow">↕</span></th>
                <th data-sort="severity">Severity <span class="sort-arrow">↕</span></th>
                <th data-sort="category">Category <span class="sort-arrow">↕</span></th>
                <th data-sort="status">Status <span class="sort-arrow">↕</span></th>
                <th>Detail</th>
            </tr>
        </thead>
        <tbody>
            <tr class="data-row" data-searchable data-search="cli.py security high open">
                <td class="cell-code">cli.py</td>
                <td><span class="cell-badge high">High</span></td>
                <td>Security</td>
                <td><span class="cell-badge info">Open</span></td>
                <td>
                    <button class="expand-btn" aria-label="Show detail">▸</button>
                </td>
            </tr>
            <tr class="row-detail" id="detail-0">
                <td colspan="5" class="row-detail-content">
                    <strong>Finding:</strong> Shell injection risk in subprocess call on line 42.
                    Use <code>shlex.split()</code> or pass args as a list.
                </td>
            </tr>

            <tr class="data-row" data-searchable data-search="runner.py performance medium fixed">
                <td class="cell-code">runner.py</td>
                <td><span class="cell-badge medium">Medium</span></td>
                <td>Performance</td>
                <td><span class="cell-badge" style="background:color-mix(in srgb,var(--color-success) 15%,transparent);color:var(--color-success)">Fixed</span></td>
                <td>
                    <button class="expand-btn" aria-label="Show detail">▸</button>
                </td>
            </tr>
            <tr class="row-detail" id="detail-1">
                <td colspan="5" class="row-detail-content">
                    <strong>Finding:</strong> Sequential file reads in loop. Use <code>asyncio.gather()</code> to parallelize.
                </td>
            </tr>

            <tr class="data-row" data-searchable data-search="dispatch.py convention low open">
                <td class="cell-code">dispatch.py</td>
                <td><span class="cell-badge low">Low</span></td>
                <td>Convention</td>
                <td><span class="cell-badge info">Open</span></td>
                <td>
                    <button class="expand-btn" aria-label="Show detail">▸</button>
                </td>
            </tr>
            <tr class="row-detail" id="detail-2">
                <td colspan="5" class="row-detail-content">
                    <strong>Finding:</strong> Missing type annotations on <code>dispatch()</code> function signature.
                </td>
            </tr>
        </tbody>
    </table>
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
.search-bar .count { font-size: 0.75rem; color: var(--text-muted); white-space: nowrap; }
.search-bar .hint  { font-size: 0.7rem; color: var(--text-muted); opacity: 0.6; }
[data-searchable].search-hidden { display: none !important; }

/* Table wrapper */
.data-table-wrapper {
    overflow-x: auto;
    border: 1px solid var(--border-default);
    border-radius: 8px;
}

.data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
    background: var(--bg-card);
}

/* Sticky header */
.data-table thead {
    position: sticky;
    top: 0;
    z-index: 10;
    background: var(--bg-elevated);
}

.data-table th {
    padding: 0.65rem 0.9rem;
    text-align: left;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    border-bottom: 1px solid var(--border-default);
    white-space: nowrap;
}

.data-table th[data-sort] {
    cursor: pointer;
    user-select: none;
    transition: color 0.15s ease;
}

.data-table th[data-sort]:hover { color: var(--text-body); }

.data-table th.sorted-asc  .sort-arrow::after { content: '↑'; }
.data-table th.sorted-desc .sort-arrow::after { content: '↓'; }
.sort-arrow { color: var(--text-muted); font-size: 0.7rem; }
.data-table th.sorted-asc  .sort-arrow,
.data-table th.sorted-desc .sort-arrow { color: var(--border-active); }

/* Rows */
.data-table td {
    padding: 0.6rem 0.9rem;
    border-bottom: 1px solid var(--border-default);
    color: var(--text-secondary);
    vertical-align: middle;
}

.data-row:last-of-type td { border-bottom: none; }

/* Alternating row background */
.data-row:nth-child(4n+1) td { background: var(--bg-card); }
.data-row:nth-child(4n+3) td { background: color-mix(in srgb, var(--bg-elevated) 40%, var(--bg-card)); }

.data-row:hover td { background: var(--bg-elevated); }

/* Badges */
.cell-badge {
    display: inline-block;
    padding: 0.15rem 0.55rem;
    border-radius: 9999px;
    font-size: 0.7rem;
    font-weight: 600;
}

.cell-badge.high {
    background: color-mix(in srgb, var(--color-error) 15%, transparent);
    color: var(--color-error);
    border: 1px solid color-mix(in srgb, var(--color-error) 30%, transparent);
}

.cell-badge.medium {
    background: color-mix(in srgb, var(--color-warning) 15%, transparent);
    color: var(--color-warning);
    border: 1px solid color-mix(in srgb, var(--color-warning) 30%, transparent);
}

.cell-badge.low {
    background: color-mix(in srgb, var(--color-success) 15%, transparent);
    color: var(--color-success);
    border: 1px solid color-mix(in srgb, var(--color-success) 30%, transparent);
}

.cell-badge.info {
    background: color-mix(in srgb, var(--color-info) 15%, transparent);
    color: var(--color-info);
    border: 1px solid color-mix(in srgb, var(--color-info) 30%, transparent);
}

/* Code cell */
.cell-code {
    font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
    font-size: 0.8rem;
    color: var(--cat-cyan);
}

/* Expandable row detail */
.row-detail { display: none; }
.row-detail.open { display: table-row; }

.row-detail-content {
    padding: 0.75rem 1rem !important;
    background: var(--bg-elevated) !important;
    color: var(--text-secondary);
    font-size: 0.83rem;
    border-bottom: 1px solid var(--border-default);
}

.expand-btn {
    background: none;
    border: none;
    color: var(--text-muted);
    cursor: pointer;
    font-size: 0.75rem;
    padding: 0.25rem 0.4rem;
    border-radius: 4px;
    transition: background 0.15s ease, color 0.15s ease, transform 0.15s ease;
}

.expand-btn:hover { background: var(--bg-elevated); color: var(--text-body); }
.expand-btn.open { transform: rotate(90deg); color: var(--border-active); }
```

## JS

Paste initSearch() from interactivity.md, then add:

```javascript
function initSortableTable(tableId) {
    const table = document.getElementById(tableId);
    if (!table) return;

    table.querySelectorAll('th[data-sort]').forEach(th => {
        th.addEventListener('click', () => {
            const key = th.getAttribute('data-sort');
            const tbody = table.querySelector('tbody');
            const allRows = Array.from(tbody.querySelectorAll('tr'));

            // Separate data rows from detail rows
            const dataRows = allRows.filter(r => r.classList.contains('data-row'));
            const detailRows = allRows.filter(r => r.classList.contains('row-detail'));

            const currentDir = th.classList.contains('sorted-asc') ? 'desc' : 'asc';
            table.querySelectorAll('th').forEach(h => h.classList.remove('sorted-asc', 'sorted-desc'));
            th.classList.add(currentDir === 'asc' ? 'sorted-asc' : 'sorted-desc');

            const colIndex = Array.from(th.parentElement.children).indexOf(th);
            dataRows.sort((a, b) => {
                const aText = a.cells[colIndex]?.textContent.trim().toLowerCase() || '';
                const bText = b.cells[colIndex]?.textContent.trim().toLowerCase() || '';
                return currentDir === 'asc'
                    ? aText.localeCompare(bText)
                    : bText.localeCompare(aText);
            });

            // Re-insert sorted data rows with their detail rows immediately after
            dataRows.forEach(row => {
                tbody.appendChild(row);
                const detailId = row.nextElementSibling?.classList.contains('row-detail')
                    ? row.nextElementSibling
                    : detailRows.find(d => d.id === `detail-${dataRows.indexOf(row)}`);
                if (detailId) tbody.appendChild(detailId);
            });
        });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    initSearch();
    initSortableTable('findingsTable');

    // Expandable rows
    document.querySelectorAll('.expand-btn').forEach((btn, i) => {
        btn.addEventListener('click', () => {
            const detail = document.getElementById(`detail-${i}`);
            if (!detail) return;
            const isOpen = detail.classList.contains('open');
            detail.classList.toggle('open', !isOpen);
            btn.classList.toggle('open', !isOpen);
        });
    });
});
```
