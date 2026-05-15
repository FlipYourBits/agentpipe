# Side-by-Side Comparison Type

Also read: nothing extra

Use for: 2-3 design options to choose from, approach comparisons, architecture trade-offs.

## HTML Structure

```html
<h1>Design Options</h1>
<p style="color: var(--text-muted); margin-bottom: 1.5rem; font-size: 0.9rem;">Click a card to select it. Use the checkmark to confirm your choice.</p>

<div class="comparison-grid">
    <div class="option-card card" data-option="A" tabindex="0">
        <div class="option-header">
            <div class="option-title">Option A</div>
            <span class="option-badge recommended">Recommended</span>
        </div>
        <p class="option-desc">Description of option A. What it is and why it exists.</p>

        <div class="attr-row">
            <span class="attr-label label">Complexity</span>
            <span class="attr-value">Low</span>
        </div>
        <div class="attr-row">
            <span class="attr-label label">Performance</span>
            <span class="attr-value">High</span>
        </div>
        <div class="attr-row">
            <span class="attr-label label">Maintainability</span>
            <span class="attr-value">High</span>
        </div>

        <div class="chips">
            <span class="chip pro">Simple API</span>
            <span class="chip pro">Testable</span>
            <span class="chip con">Less flexible</span>
        </div>
    </div>

    <div class="option-card card" data-option="B" tabindex="0">
        <div class="option-header">
            <div class="option-title">Option B</div>
        </div>
        <p class="option-desc">Description of option B. What it is and why it exists.</p>

        <div class="attr-row">
            <span class="attr-label label">Complexity</span>
            <span class="attr-value">Medium</span>
        </div>
        <div class="attr-row">
            <span class="attr-label label">Performance</span>
            <span class="attr-value">Medium</span>
        </div>
        <div class="attr-row">
            <span class="attr-label label">Maintainability</span>
            <span class="attr-value">Medium</span>
        </div>

        <div class="chips">
            <span class="chip pro">More flexible</span>
            <span class="chip con">More moving parts</span>
            <span class="chip con">Harder to test</span>
        </div>
    </div>

    <div class="option-card card" data-option="C" tabindex="0">
        <div class="option-header">
            <div class="option-title">Option C</div>
        </div>
        <p class="option-desc">Description of option C. What it is and why it exists.</p>

        <div class="attr-row">
            <span class="attr-label label">Complexity</span>
            <span class="attr-value">High</span>
        </div>
        <div class="attr-row">
            <span class="attr-label label">Performance</span>
            <span class="attr-value">Very High</span>
        </div>
        <div class="attr-row">
            <span class="attr-label label">Maintainability</span>
            <span class="attr-value">Low</span>
        </div>

        <div class="chips">
            <span class="chip pro">Maximum control</span>
            <span class="chip con">Hard to maintain</span>
            <span class="chip con">Over-engineered</span>
        </div>
    </div>
</div>

<div id="selectionNote" style="display:none; margin-top: 1.5rem; color: var(--text-secondary); font-size: 0.9rem;">
    Selected: <strong id="selectedLabel"></strong>
</div>
```

## CSS

```css
.comparison-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 1.25rem;
    align-items: start;
}

.option-card {
    cursor: pointer;
    position: relative;
    border-radius: 8px;
    padding: 1.25rem;
    outline: none;
    transition: border-color 0.2s ease, background 0.2s ease, transform 0.15s ease;
}

.option-card:hover {
    border-color: var(--border-active);
    background: var(--bg-elevated);
}

.option-card:focus {
    outline: 2px solid var(--border-active);
    outline-offset: 2px;
}

.option-card.selected {
    border-color: var(--color-success);
    background: var(--bg-elevated);
}

/* Checkmark badge on selected card */
.option-card.selected::after {
    content: '✓';
    position: absolute;
    top: 0.75rem;
    right: 0.75rem;
    width: 1.4rem;
    height: 1.4rem;
    background: var(--color-success);
    color: var(--bg-page);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    font-weight: 700;
    line-height: 1.4rem;
    text-align: center;
}

.option-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.75rem;
    flex-wrap: wrap;
}

.option-title {
    font-size: 1rem;
    font-weight: 700;
    color: var(--text-heading);
}

.option-badge {
    font-size: 0.68rem;
    font-weight: 600;
    padding: 0.15rem 0.5rem;
    border-radius: 9999px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

.option-badge.recommended {
    background: color-mix(in srgb, var(--color-success) 20%, transparent);
    color: var(--color-success);
    border: 1px solid color-mix(in srgb, var(--color-success) 40%, transparent);
}

.option-desc {
    font-size: 0.85rem;
    color: var(--text-secondary);
    margin-bottom: 1rem;
    line-height: 1.5;
}

.attr-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.35rem 0;
    border-bottom: 1px solid var(--border-default);
}

.attr-row:last-of-type {
    border-bottom: none;
    margin-bottom: 0.75rem;
}

.attr-label {
    font-size: 0.75rem;
}

.attr-value {
    font-size: 0.8rem;
    color: var(--text-secondary);
    font-weight: 500;
}

.chips {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin-top: 0.75rem;
}

.chip {
    font-size: 0.72rem;
    font-weight: 500;
    padding: 0.2rem 0.55rem;
    border-radius: 9999px;
}

.chip.pro {
    background: color-mix(in srgb, var(--color-success) 15%, transparent);
    color: var(--color-success);
    border: 1px solid color-mix(in srgb, var(--color-success) 30%, transparent);
}

.chip.con {
    background: color-mix(in srgb, var(--color-error) 15%, transparent);
    color: var(--color-error);
    border: 1px solid color-mix(in srgb, var(--color-error) 30%, transparent);
}
```

## JS

```javascript
document.addEventListener('DOMContentLoaded', () => {
    const cards = document.querySelectorAll('.option-card');
    const note = document.getElementById('selectionNote');
    const selectedLabel = document.getElementById('selectedLabel');

    function selectCard(card) {
        cards.forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
        const optionName = card.querySelector('.option-title')?.textContent || card.dataset.option;
        if (note) note.style.display = 'block';
        if (selectedLabel) selectedLabel.textContent = optionName;
    }

    cards.forEach(card => {
        card.addEventListener('click', () => selectCard(card));
        card.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                selectCard(card);
            }
        });
    });
});
```
