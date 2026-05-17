## HTML Guidelines

### Semantic Structure

- Use semantic elements (`<header>`, `<nav>`, `<main>`, `<article>`, `<section>`, `<aside>`, `<footer>`) over generic `<div>` and `<span>`.
- Heading hierarchy must not skip levels (`<h1>` -> `<h2>` -> `<h3>`). One `<h1>` per page.
- Use `<template>` or data attributes over inline JavaScript for dynamic content patterns.
- Use landmark roles implicitly via semantic elements — don't add redundant `role="navigation"` to `<nav>`.

```html
<!-- Bad -->
<div class="header">
  <div class="nav">
    <div class="nav-item"><a href="/">Home</a></div>
  </div>
</div>
<div class="content">
  <div class="title">Page Title</div>
  <div class="text">Some content here.</div>
</div>

<!-- Good -->
<header>
  <nav aria-label="Main">
    <ul>
      <li><a href="/">Home</a></li>
    </ul>
  </nav>
</header>
<main>
  <h1>Page Title</h1>
  <p>Some content here.</p>
</main>
```

### Interactive Elements

- Use `<button>` for actions and `<a>` for navigation. Never use `<div onclick>` or `<span onclick>` for interactive elements.
- Never use inline event handlers (`onclick`, `onload`, etc.) — use `addEventListener` in a `<script>` block or external file.
- Don't nest interactive elements (`<a>` inside `<button>`, etc.).
- Buttons that don't submit a form must have `type="button"` to prevent accidental form submission.

```html
<!-- Bad -->
<div class="btn" onclick="doThing()">Click me</div>
<a href="#" onclick="submitForm(); return false;">Submit</a>
<button>
  <a href="/somewhere">Navigate</a>
</button>

<!-- Good -->
<button type="button" class="btn" id="action-trigger">Click me</button>
<a href="/results">View Results</a>
<form>
  <button type="submit">Submit</button>
</form>

<script>
  document.getElementById("action-trigger").addEventListener("click", doThing);
</script>
```

### Forms & Inputs

- Every `<input>` needs a `<label>` (explicit via `for`/`id` or implicit via nesting). Use appropriate `type` attributes.
- Use `<fieldset>` and `<legend>` to group related controls.
- Always include `name` attributes on form controls — controls without `name` don't submit.
- Use `autocomplete` attributes for common fields (name, email, address, etc.) to improve UX and password manager support.
- Provide visible error messages associated with inputs via `aria-describedby`.

```html
<!-- Bad -->
<input type="text" placeholder="Email">
<input type="text" placeholder="Password">
<div class="error">Invalid email</div>

<!-- Good -->
<form>
  <fieldset>
    <legend>Login</legend>

    <label for="email">Email</label>
    <input
      type="email"
      id="email"
      name="email"
      autocomplete="email"
      required
      aria-describedby="email-error"
    >
    <span id="email-error" class="error" role="alert">Invalid email address</span>

    <label for="password">Password</label>
    <input
      type="password"
      id="password"
      name="password"
      autocomplete="current-password"
      required
    >

    <button type="submit">Log in</button>
  </fieldset>
</form>
```

### Images & Media

- Every `<img>` must have a meaningful `alt` attribute. Decorative images use `alt=""`.
- Use `<picture>` with `<source>` for responsive images or format alternatives.
- Prefer `loading="lazy"` on images and iframes below the fold.
- Always include `width` and `height` attributes on `<img>` to prevent layout shift (CLS).

```html
<!-- Bad -->
<img src="hero.png">
<img src="decorative-swirl.svg">
<img src="product.jpg" alt="image">

<!-- Good -->
<img src="hero.png" alt="Team collaborating around a whiteboard" width="1200" height="600">
<img src="decorative-swirl.svg" alt="" role="presentation">
<picture>
  <source srcset="product.avif" type="image/avif">
  <source srcset="product.webp" type="image/webp">
  <img src="product.jpg" alt="Blue running shoes, side view" width="400" height="300" loading="lazy">
</picture>
```

### Security

- Escape all user-provided content rendered into HTML. Use framework-provided escaping.
- Never inject raw user input into `href`, `src`, `action`, or `srcdoc` attributes without validation — these are XSS vectors.
- Don't use `javascript:` URLs or `data:text/html` in href/src.
- Use `rel="noopener noreferrer"` on external links with `target="_blank"`.
- Set Content Security Policy headers — don't rely on HTML-level sanitization alone.

```html
<!-- Bad — XSS vectors -->
<a href="{{user_input}}">Link</a>
<div>Welcome, {{raw_username}}</div>
<iframe srcdoc="{{user_html}}"></iframe>

<!-- Good — escaped and validated -->
<a href="/profile/{{url_encoded_id}}">Profile</a>
<div>Welcome, <span class="username">{{escaped_username}}</span></div>
<a href="https://external.com" target="_blank" rel="noopener noreferrer">External Link</a>
```

### Accessibility

- Use ARIA attributes only when native semantics are insufficient. Prefer native HTML elements over ARIA roles.
- Provide `aria-label` or `aria-labelledby` for interactive elements without visible text.
- Use `aria-live` regions for dynamic content that updates without a page reload.
- Ensure all functionality is keyboard-accessible. Test with Tab, Enter, Escape, and arrow keys.
- Use `role="alert"` for error messages that need immediate attention, `role="status"` for non-urgent updates.

```html
<!-- Bad — ARIA overriding native semantics -->
<div role="button" tabindex="0" aria-label="Submit form">Submit</div>
<div role="navigation">
  <div role="list">
    <div role="listitem"><a href="/">Home</a></div>
  </div>
</div>

<!-- Good — native semantics, ARIA only where needed -->
<button type="submit">Submit</button>
<nav aria-label="Main">
  <ul>
    <li><a href="/">Home</a></li>
  </ul>
</nav>

<!-- Good — ARIA for custom widget -->
<div role="tablist" aria-label="Settings sections">
  <button role="tab" aria-selected="true" aria-controls="panel-general" id="tab-general">General</button>
  <button role="tab" aria-selected="false" aria-controls="panel-privacy" id="tab-privacy">Privacy</button>
</div>
<div role="tabpanel" id="panel-general" aria-labelledby="tab-general">
  <!-- panel content -->
</div>
```

### Document Meta

- Include `<meta charset="UTF-8">` and `<meta name="viewport" content="width=device-width, initial-scale=1.0">`.
- Keep `<script>` tags at the end of `<body>` or use `defer`/`async`.
- Use `defer` for scripts that depend on the DOM; `async` for analytics and third-party scripts that don't.
- IDs must be unique within the document. Prefer classes for styling hooks.
- Use the `<link rel="preload">` hint for critical resources (fonts, above-fold images).

```html
<!-- Bad -->
<html>
<head>
  <script src="app.js"></script>
</head>
<body>
  <div id="content" id="main">...</div>
</body>

<!-- Good -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Page Title</title>
  <link rel="preload" href="/fonts/inter.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="/styles/main.css">
</head>
<body>
  <main id="content">...</main>
  <script src="/js/app.js" defer></script>
</body>
</html>
```

### Tables

- Use `<table>` only for tabular data, never for layout.
- Include `<thead>`, `<tbody>`, and optionally `<tfoot>` for structure.
- Use `<th scope="col">` for column headers and `<th scope="row">` for row headers.
- Add `<caption>` to describe the table's purpose for screen readers.

```html
<!-- Bad -->
<table>
  <tr><td><b>Name</b></td><td><b>Role</b></td></tr>
  <tr><td>Alice</td><td>Engineer</td></tr>
</table>

<!-- Good -->
<table>
  <caption>Team members and their roles</caption>
  <thead>
    <tr>
      <th scope="col">Name</th>
      <th scope="col">Role</th>
      <th scope="col">Start Date</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Alice</td>
      <td>Engineer</td>
      <td><time datetime="2025-03-15">Mar 15, 2025</time></td>
    </tr>
  </tbody>
</table>
```

When editing HTML, preserve existing indentation style and attribute ordering.
