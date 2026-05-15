# Metrics Dashboard Type

Also read: nothing extra (inline SVG, not connection toolkit)

Use for: KPI cards with trends, sparklines, bar charts, donut charts. All charts are inline SVG — no external libraries.

## HTML Structure

```html
<h1>Review Metrics</h1>

<!-- KPI cards -->
<div class="dashboard-grid" id="kpiGrid">
    <div class="kpi-card card">
        <div class="kpi-label label">Files Reviewed</div>
        <div class="kpi-value">124</div>
        <div class="kpi-trend up">↑ 18% vs last week</div>
        <div class="kpi-sparkline" id="spark-files"></div>
    </div>
    <div class="kpi-card card">
        <div class="kpi-label label">Findings</div>
        <div class="kpi-value">47</div>
        <div class="kpi-trend down">↓ 12% vs last week</div>
        <div class="kpi-sparkline" id="spark-findings"></div>
    </div>
    <div class="kpi-card card">
        <div class="kpi-label label">Fix Rate</div>
        <div class="kpi-value">83%</div>
        <div class="kpi-trend up">↑ 5pts vs last week</div>
        <div class="kpi-sparkline" id="spark-fixrate"></div>
    </div>
    <div class="kpi-card card">
        <div class="kpi-label label">Avg Findings/File</div>
        <div class="kpi-value">0.38</div>
        <div class="kpi-trend flat">→ Stable</div>
        <div class="kpi-sparkline" id="spark-avg"></div>
    </div>
</div>

<div class="charts-row">
    <!-- Bar chart -->
    <div class="chart-card card">
        <div class="chart-title">Findings by Category</div>
        <div class="bar-chart">
            <div class="bar-row">
                <span class="bar-label">Security</span>
                <div class="bar-track">
                    <div class="bar-fill" style="width:72%; --bar-color: var(--color-error)"></div>
                </div>
                <span class="bar-val">18</span>
            </div>
            <div class="bar-row">
                <span class="bar-label">Performance</span>
                <div class="bar-track">
                    <div class="bar-fill" style="width:56%; --bar-color: var(--color-warning)"></div>
                </div>
                <span class="bar-val">14</span>
            </div>
            <div class="bar-row">
                <span class="bar-label">Convention</span>
                <div class="bar-track">
                    <div class="bar-fill" style="width:40%; --bar-color: var(--cat-blue)"></div>
                </div>
                <span class="bar-val">10</span>
            </div>
            <div class="bar-row">
                <span class="bar-label">Quality</span>
                <div class="bar-track">
                    <div class="bar-fill" style="width:20%; --bar-color: var(--cat-purple)"></div>
                </div>
                <span class="bar-val">5</span>
            </div>
        </div>
    </div>

    <!-- Donut chart -->
    <div class="chart-card card">
        <div class="chart-title">Status Breakdown</div>
        <div class="donut-container">
            <svg class="donut" viewBox="0 0 120 120" width="140" height="140">
                <!-- Segments drawn as stroke-dasharray on a circle
                     circumference = 2πr = 2π×44 ≈ 276.46
                     Each segment: dasharray="portion gap" offset from previous -->
                <circle cx="60" cy="60" r="44" fill="none"
                    stroke="var(--color-success)" stroke-width="18"
                    stroke-dasharray="199 77"
                    stroke-dashoffset="69"
                    transform="rotate(-90 60 60)"/>
                <circle cx="60" cy="60" r="44" fill="none"
                    stroke="var(--color-info)" stroke-width="18"
                    stroke-dasharray="55 221"
                    stroke-dashoffset="-130"
                    transform="rotate(-90 60 60)"/>
                <circle cx="60" cy="60" r="44" fill="none"
                    stroke="var(--color-error)" stroke-width="18"
                    stroke-dasharray="22 254"
                    stroke-dashoffset="-185"
                    transform="rotate(-90 60 60)"/>
                <text x="60" y="56" text-anchor="middle" fill="var(--text-heading)"
                      font-size="16" font-weight="700" font-family="system-ui,sans-serif">47</text>
                <text x="60" y="70" text-anchor="middle" fill="var(--text-muted)"
                      font-size="8" font-family="system-ui,sans-serif">findings</text>
            </svg>
            <div class="donut-legend">
                <div class="donut-legend-item">
                    <span class="donut-dot" style="background:var(--color-success)"></span>
                    Fixed (72%)
                </div>
                <div class="donut-legend-item">
                    <span class="donut-dot" style="background:var(--color-info)"></span>
                    In Review (20%)
                </div>
                <div class="donut-legend-item">
                    <span class="donut-dot" style="background:var(--color-error)"></span>
                    Open (8%)
                </div>
            </div>
        </div>
    </div>
</div>
```

## CSS

```css
.dashboard-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 1rem;
    margin-bottom: 1.5rem;
}

.kpi-card {
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
}

.kpi-label {
    font-size: 0.72rem;
    margin-bottom: 0.1rem;
}

.kpi-value {
    font-size: 2rem;
    font-weight: 700;
    color: var(--text-heading);
    line-height: 1.1;
}

.kpi-trend {
    font-size: 0.75rem;
    font-weight: 500;
}

.kpi-trend.up   { color: var(--color-success); }
.kpi-trend.down { color: var(--color-error); }
.kpi-trend.flat { color: var(--text-muted); }

.kpi-sparkline {
    margin-top: 0.5rem;
    height: 32px;
}

.kpi-sparkline svg {
    width: 100%;
    height: 32px;
    overflow: visible;
}

/* Charts row */
.charts-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1rem;
}

.chart-card {
    padding: 1.25rem;
}

.chart-title {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text-secondary);
    margin-bottom: 1rem;
}

/* Bar chart */
.bar-chart {
    display: flex;
    flex-direction: column;
    gap: 0.65rem;
}

.bar-row {
    display: flex;
    align-items: center;
    gap: 0.6rem;
}

.bar-label {
    font-size: 0.78rem;
    color: var(--text-muted);
    min-width: 80px;
    white-space: nowrap;
}

.bar-track {
    flex: 1;
    height: 8px;
    background: var(--bg-elevated);
    border-radius: 4px;
    overflow: hidden;
}

.bar-fill {
    height: 100%;
    background: var(--bar-color, var(--cat-blue));
    border-radius: 4px;
    transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.bar-val {
    font-size: 0.75rem;
    color: var(--text-muted);
    min-width: 1.5rem;
    text-align: right;
    font-variant-numeric: tabular-nums;
}

/* Donut chart */
.donut-container {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    flex-wrap: wrap;
}

.donut {
    flex-shrink: 0;
    filter: drop-shadow(0 2px 8px rgba(0,0,0,0.3));
}

.donut-legend {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.donut-legend-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.8rem;
    color: var(--text-secondary);
}

.donut-dot {
    width: 0.6rem;
    height: 0.6rem;
    border-radius: 50%;
    flex-shrink: 0;
}
```

## JS

```javascript
// sparkline(containerEl, data, color)
// data: array of numbers. Draws a polyline scaled to the container height.
function sparkline(containerEl, data, color) {
    if (!data || !data.length) return;
    const w = containerEl.offsetWidth || 160;
    const h = 32;
    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;

    const points = data.map((v, i) => {
        const x = (i / (data.length - 1)) * w;
        const y = h - ((v - min) / range) * (h - 4) - 2;
        return `${x},${y}`;
    }).join(' ');

    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', `0 0 ${w} ${h}`);
    svg.setAttribute('width', w);
    svg.setAttribute('height', h);

    // Area fill under the line
    const areaPoints = `0,${h} ` + points + ` ${w},${h}`;
    const area = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
    area.setAttribute('points', areaPoints);
    area.setAttribute('fill', color);
    area.setAttribute('opacity', '0.12');
    svg.appendChild(area);

    // Line
    const line = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
    line.setAttribute('points', points);
    line.setAttribute('fill', 'none');
    line.setAttribute('stroke', color);
    line.setAttribute('stroke-width', '1.5');
    line.setAttribute('stroke-linejoin', 'round');
    line.setAttribute('stroke-linecap', 'round');
    svg.appendChild(line);

    containerEl.appendChild(svg);
}

document.addEventListener('DOMContentLoaded', () => {
    // Replace with real data arrays
    sparkline(document.getElementById('spark-files'),    [40, 55, 72, 60, 80, 95, 124], 'var(--cat-blue)');
    sparkline(document.getElementById('spark-findings'), [80, 70, 60, 65, 55, 50, 47],  'var(--color-error)');
    sparkline(document.getElementById('spark-fixrate'),  [60, 65, 70, 72, 78, 80, 83],  'var(--color-success)');
    sparkline(document.getElementById('spark-avg'),      [0.4, 0.38, 0.42, 0.39, 0.37, 0.38, 0.38], 'var(--cat-cyan)');
});
```

## Donut Segment Math

For a circle with r=44 (circumference ≈ 276.46):

- Segment length = percentage × 276.46
- Gap = 276.46 − segment length
- stroke-dashoffset for nth segment = −(sum of all previous segment lengths + gaps)
- `transform="rotate(-90 cx cy)"` starts the first segment at the top (12 o'clock)
