## CSS Guidelines

### Selectors & Specificity

- Keep specificity low. Prefer single class selectors over nested or compound selectors. Avoid `!important` except for utility overrides.
- Avoid deeply nested selectors (max 3 levels). Flat selectors are easier to override and maintain.
- Don't style by element type alone (`div`, `span`) — it's fragile and creates unintended side effects.
- Use attribute selectors for state variants where data attributes are more semantic than classes.

```css
/* Bad — high specificity, fragile */
#main-content .sidebar > div.widget ul li a.active {
  color: blue !important;
}

div {
  margin-bottom: 1rem;
}

.nav .nav-list .nav-item .nav-link {
  color: inherit;
}

/* Good — flat, low specificity */
.nav-link {
  color: inherit;
}

.nav-link[aria-current="page"] {
  color: var(--color-primary);
  font-weight: 600;
}

.widget-title {
  font-size: var(--text-lg);
}
```

### Custom Properties

- Use CSS custom properties (`--var-name`) for repeated values (colors, spacing, fonts). Define them on `:root` or component scope.
- Name custom properties by purpose, not value: `--color-primary` not `--blue-500`.
- Use component-scoped custom properties for local theme variations.
- Define a spacing scale and stick to it — don't introduce arbitrary values.

```css
/* Bad — magic numbers scattered everywhere */
.card {
  padding: 17px;
  margin-bottom: 23px;
  color: #3b82f6;
  font-size: 14.5px;
  border-radius: 6px;
}

.header {
  padding: 18px;
  color: #3b82f6;
}

/* Good — systematic design tokens */
:root {
  --color-primary: hsl(217 91% 60%);
  --color-text: hsl(220 15% 20%);
  --space-sm: 0.5rem;
  --space-md: 1rem;
  --space-lg: 1.5rem;
  --radius-md: 0.375rem;
  --text-sm: 0.875rem;
  --text-base: 1rem;
}

.card {
  padding: var(--space-lg);
  margin-bottom: var(--space-lg);
  color: var(--color-text);
  font-size: var(--text-sm);
  border-radius: var(--radius-md);
}

.card--featured {
  --card-accent: var(--color-primary);
  border-left: 3px solid var(--card-accent);
}
```

### Layout

- Use `flexbox` for one-dimensional layout, `grid` for two-dimensional. Avoid `float` for layout.
- Use `gap` with flexbox/grid instead of margin hacks for spacing between items.
- Don't set `height` on containers that hold dynamic content — use `min-height` or let content determine height.
- Use `auto-fit`/`auto-fill` with `minmax()` for responsive grids without media queries.

```css
/* Bad — float layout with margin hacks */
.container::after {
  content: "";
  display: table;
  clear: both;
}

.col {
  float: left;
  width: 33.333%;
  padding-left: 10px;
  padding-right: 10px;
}

.col:first-child {
  padding-left: 0;
}

/* Good — modern grid */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 20rem), 1fr));
  gap: var(--space-md);
}

/* Good — flexbox for single-axis alignment */
.toolbar {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.toolbar-spacer {
  margin-inline-start: auto;
}
```

### Units & Sizing

- Prefer `rem` for font sizes and spacing, `em` for component-relative sizing. Avoid `px` for text.
- Use logical properties (`margin-inline`, `padding-block`) over physical ones (`margin-left`, `padding-top`) for internationalization.
- Use viewport units (`dvh`, `svh`) cautiously — prefer `min-height: 100dvh` over `height: 100vh` for mobile.
- Use `clamp()` for fluid typography and spacing: `font-size: clamp(1rem, 0.5rem + 1.5vw, 1.5rem)`.

```css
/* Bad — fixed px, physical properties, broken on mobile */
.hero {
  height: 100vh;
  font-size: 48px;
  padding-left: 80px;
  padding-right: 80px;
}

/* Good — fluid, logical, responsive */
.hero {
  min-height: 100dvh;
  font-size: clamp(2rem, 1rem + 3vw, 3rem);
  padding-inline: clamp(1rem, 5vw, 5rem);
  padding-block: var(--space-lg);
}
```

### Naming & Organization

- Name classes by purpose, not appearance: `.card-header` not `.blue-bar`, `.visually-hidden` not `.display-none`.
- Group related properties: positioning, box model, typography, visual (color/background), then misc.
- Match the surrounding codebase's naming convention (BEM, utility-first, module-scoped) over your own preferences.
- Consolidate duplicate property declarations. If the same rule appears in multiple selectors, extract a shared class.

```css
/* Bad — named by appearance, unordered properties */
.blue-box {
  color: white;
  float: left;
  background: blue;
  width: 200px;
  font-size: 14px;
  position: absolute;
  padding: 10px;
  top: 0;
}

/* Good — named by purpose, logically ordered */
.notification-badge {
  /* positioning */
  position: absolute;
  inset-block-start: 0;
  inset-inline-end: 0;

  /* box model */
  padding: var(--space-sm);
  min-inline-size: 1.5rem;

  /* typography */
  font-size: var(--text-sm);
  text-align: center;

  /* visual */
  color: var(--color-on-primary);
  background-color: var(--color-primary);
  border-radius: var(--radius-full);
}
```

### Responsive Design

- Use `min-width` media queries (mobile-first) over `max-width` (desktop-first).
- Prefer intrinsic sizing (`auto-fit`, `clamp`, `min()`, `max()`) over breakpoint-driven layout shifts.
- Use container queries (`@container`) for component-level responsiveness when supported.
- Don't hide content at breakpoints — reorganize or reflow. Hidden content is still downloaded.

```css
/* Bad — desktop-first, brittle breakpoints */
.sidebar {
  width: 300px;
  float: left;
}

@media (max-width: 768px) {
  .sidebar {
    float: none;
    width: 100%;
  }
}

/* Good — mobile-first, intrinsic */
.layout {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-md);
}

@media (min-width: 48rem) {
  .layout {
    grid-template-columns: 20rem 1fr;
  }
}

/* Good — container query for component reflow */
.card-container {
  container-type: inline-size;
}

@container (min-width: 30rem) {
  .card {
    grid-template-columns: auto 1fr;
  }
}
```

### Motion & Accessibility

- Use `prefers-reduced-motion` media query when adding animations or transitions.
- Keep animations short (150-300ms) and purposeful — they communicate state changes, not decoration.
- Use `transform` and `opacity` for animations — they don't trigger layout recalculation.
- Never animate `width`, `height`, `top`, `left` — they cause layout thrashing.

```css
/* Bad — animates layout properties, ignores motion preferences */
.dropdown {
  height: 0;
  overflow: hidden;
  transition: height 0.5s ease;
}

.dropdown.open {
  height: 300px;
}

/* Good — transform-based, respects preferences */
.dropdown {
  transform: scaleY(0);
  transform-origin: top;
  opacity: 0;
  transition: transform 200ms ease, opacity 200ms ease;
}

.dropdown.open {
  transform: scaleY(1);
  opacity: 1;
}

@media (prefers-reduced-motion: reduce) {
  .dropdown {
    transition: none;
  }
}
```

### Anti-Patterns

- Avoid `@import` in CSS files — it blocks parallel downloads. Use bundler imports or multiple `<link>` tags.
- No commented-out rules, no dead selectors (selectors matching no elements in the current HTML).
- Don't use `*` universal selector for styles other than box-sizing resets.
- Avoid `z-index` wars — define a z-index scale with custom properties and stick to it.

```css
/* Bad — z-index chaos */
.modal {
  z-index: 99999;
}

.tooltip {
  z-index: 999999;
}

.dropdown {
  z-index: 9999;
}

/* Good — defined scale */
:root {
  --z-dropdown: 100;
  --z-sticky: 200;
  --z-modal-backdrop: 300;
  --z-modal: 400;
  --z-tooltip: 500;
}

.modal {
  z-index: var(--z-modal);
}

.tooltip {
  z-index: var(--z-tooltip);
}
```

When refactoring CSS, change behavior in the smallest diff that works. Avoid reformatting unrelated rules in the same change.
