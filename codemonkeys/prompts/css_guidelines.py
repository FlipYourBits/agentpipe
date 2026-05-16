"""CSS conventions loaded into agents that review or write CSS."""

CSS_GUIDELINES = """\
## CSS Guidelines

- Keep specificity low. Prefer single class selectors over nested
  or compound selectors. Avoid `!important` except for utility overrides.
- Use CSS custom properties (`--var-name`) for repeated values
  (colors, spacing, fonts). Define them on `:root` or component scope.
- Use logical properties (`margin-inline`, `padding-block`) over
  physical ones (`margin-left`, `padding-top`) for internationalization.
- Prefer `rem` for font sizes and spacing, `em` for component-relative
  sizing. Avoid `px` for text.
- Use `flexbox` for one-dimensional layout, `grid` for two-dimensional.
  Avoid `float` for layout.
- Name classes by purpose, not appearance: `.card-header` not `.blue-bar`,
  `.visually-hidden` not `.display-none`.
- Group related properties: positioning, box model, typography,
  visual (color/background), then misc.
- Avoid deeply nested selectors (max 3 levels). Flat selectors are
  easier to override and maintain.
- Don't style by element type alone (`div`, `span`) — it's fragile
  and creates unintended side effects.
- Use `prefers-reduced-motion` media query when adding animations
  or transitions.
- Avoid `@import` in CSS files — it blocks parallel downloads.
  Use bundler imports or multiple `<link>` tags.
- Don't set `height` on containers that hold dynamic content —
  use `min-height` or let content determine height.
- Use `gap` with flexbox/grid instead of margin hacks for spacing
  between items.
- Consolidate duplicate property declarations. If the same rule
  appears in multiple selectors, extract a shared class.
- No commented-out rules, no dead selectors (selectors matching
  no elements in the current HTML).
- Match the surrounding codebase's naming convention (BEM, utility-first,
  module-scoped) over your own preferences.

When refactoring CSS, change behavior in the smallest diff that works.
Avoid reformatting unrelated rules in the same change."""
