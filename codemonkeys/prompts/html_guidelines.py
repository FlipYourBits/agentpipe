"""HTML conventions loaded into agents that review or write HTML."""

HTML_GUIDELINES = """\
## HTML Guidelines

- Use semantic elements (`<header>`, `<nav>`, `<main>`, `<article>`,
  `<section>`, `<aside>`, `<footer>`) over generic `<div>` and `<span>`.
- Every `<img>` must have a meaningful `alt` attribute. Decorative
  images use `alt=""`.
- Use `<button>` for actions and `<a>` for navigation. Never use
  `<div onclick>` or `<span onclick>` for interactive elements.
- Forms: every `<input>` needs a `<label>` (explicit via `for`/`id`
  or implicit via nesting). Use appropriate `type` attributes.
- Heading hierarchy must not skip levels (`<h1>` → `<h2>` → `<h3>`).
  One `<h1>` per page.
- Use `<template>` or data attributes over inline JavaScript for
  dynamic content patterns.
- Never use inline event handlers (`onclick`, `onload`, etc.) —
  use `addEventListener` in a `<script>` block or external file.
- Escape all user-provided content rendered into HTML. Use
  framework-provided escaping (Jinja2 `{{ var }}`, template literals).
- Never inject raw user input into `href`, `src`, `action`, or
  `srcdoc` attributes without validation — these are XSS vectors.
- Don't use `javascript:` URLs or `data:text/html` in href/src.
- Use `rel="noopener noreferrer"` on external links with `target="_blank"`.
- Include `<meta charset="UTF-8">` and
  `<meta name="viewport" content="width=device-width, initial-scale=1.0">`.
- Prefer `loading="lazy"` on images and iframes below the fold.
- Don't nest interactive elements (`<a>` inside `<button>`, etc.).
- Use ARIA attributes only when native semantics are insufficient.
  Prefer native HTML elements over ARIA roles.
- Keep `<script>` tags at the end of `<body>` or use `defer`/`async`.
- IDs must be unique within the document. Prefer classes for styling hooks.

When editing HTML, preserve existing indentation style and attribute ordering."""
