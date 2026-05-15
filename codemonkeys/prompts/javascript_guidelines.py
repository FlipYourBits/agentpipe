"""JavaScript/TypeScript code conventions loaded into agents that review or write JS/TS."""

JAVASCRIPT_GUIDELINES = """\
## Code Guidelines

- Use TypeScript strict mode when available. Prefer `.ts`/`.tsx` over
  `.js`/`.jsx` for new files.
- Prefer `const` over `let`; never use `var`.
- Type-hint function parameters and return values. Avoid `any` —
  use `unknown` when the type is genuinely not known, then narrow.
- Use `async`/`await` over raw Promise chains. Always handle
  rejections — unhandled promise rejections crash Node and silently
  fail in browsers.
- Prefer named exports over default exports. Named exports are
  refactor-friendly and produce better editor autocomplete.
- Use template literals over string concatenation.
- Use optional chaining (`?.`) and nullish coalescing (`??`)
  instead of manual null checks or `||` for defaults.
- Prefer `===` and `!==` over `==` and `!=`.
- Keep functions short and single-purpose. If a function
  exceeds ~40 lines or three nesting levels, extract a helper.
- Name things for what they mean, not what they are.
  Boolean variables start with `is`, `has`, `should`, `can`.
- Handle errors explicitly. Don't catch and swallow — either
  recover meaningfully or let the error propagate with context.
- Don't use `@ts-ignore` or `@ts-expect-error` without a comment
  explaining why the type system is wrong.
- Use `readonly` for object properties and array parameters
  that should not be mutated.
- Prefer `Array.from()`, spread, `map`, `filter`, `reduce`
  over imperative loops when the intent is clearer.
- Don't mix `require()` and `import` in the same file. Prefer
  ESM `import`/`export` for new code.
- No dead code, no commented-out blocks, no `// TODO` without
  a concrete plan attached.
- Match the surrounding codebase's style (formatter, import order,
  naming) over your own preferences.

When refactoring, change behavior in the smallest diff that works.
Avoid drive-by reformatting in the same change as a logic edit."""
