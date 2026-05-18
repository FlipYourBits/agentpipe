## JavaScript/TypeScript Guidelines

### Modules & Imports

- Use TypeScript strict mode when available. Prefer `.ts`/`.tsx` over `.js`/`.jsx` for new files.
- Prefer named exports over default exports. Named exports are refactor-friendly and produce better editor autocomplete.
- Don't mix `require()` and `import` in the same file. Prefer ESM `import`/`export` for new code.
- Group imports: external packages, then internal modules — separated by a blank line.
- Use barrel exports (`index.ts`) sparingly — they break tree-shaking and cause circular imports.

```typescript
// Bad
import utils from "../utils";
const { readFile } = require("fs");
import { thing } from "../../deeply/nested/internal/module";

// Good
import { readFile } from "node:fs/promises";
import { z } from "zod";

import { processItem } from "../processing";
import type { Config } from "../types";
```

### Type Safety

- Type-hint function parameters and return values. Avoid `any` — use `unknown` when the type is genuinely not known, then narrow.
- Don't use `@ts-ignore` or `@ts-expect-error` without a comment explaining why the type system is wrong.
- Use `readonly` for object properties and array parameters that should not be mutated.
- Use discriminated unions over type assertions for narrowing.
- Use `satisfies` to validate a value matches a type without widening.
- Prefer `interface` for objects that will be extended; `type` for unions, intersections, and computed types.

```typescript
// Bad — loses type safety
function handle(event: any) {
  return event.data.value;
}

const config = {
  port: 3000,
  host: "localhost",
} as Config;

// Good — narrowed and type-safe
function handle(event: unknown): string {
  if (!isMessageEvent(event)) {
    throw new InvalidEventError(event);
  }
  return event.data.value;
}

const config = {
  port: 3000,
  host: "localhost",
} satisfies Config;
```

### Variables & Declarations

- Prefer `const` over `let`; never use `var`.
- Use template literals over string concatenation.
- Use optional chaining (`?.`) and nullish coalescing (`??`) instead of manual null checks or `||` for defaults.
- Prefer `===` and `!==` over `==` and `!=`.
- Destructure objects and arrays when accessing multiple properties.

```typescript
// Bad
var name = user.profile ? user.profile.name : "Anonymous";
let greeting = "Hello, " + name + "!";
if (value == null) { /* ... */ }

// Good
const name = user.profile?.name ?? "Anonymous";
const greeting = `Hello, ${name}!`;
if (value === null || value === undefined) { /* ... */ }
```

### Functions

- Keep functions short and single-purpose. If a function exceeds ~40 lines or three nesting levels, extract a helper.
- Name things for what they mean, not what they are. Boolean variables start with `is`, `has`, `should`, `can`.
- Use object parameters for functions with more than 2 arguments.
- Prefer arrow functions for callbacks and inline functions; named `function` declarations for top-level.
- Use early returns to reduce nesting.

```typescript
// Bad
function processOrder(id, userId, items, discount, shipping, priority) {
  if (items.length > 0) {
    if (userId) {
      const total = items.reduce((sum, item) => {
        if (item.available) {
          return sum + item.price;
        } else {
          return sum;
        }
      }, 0);
      // ... more nesting
    }
  }
}

// Good
interface ProcessOrderArgs {
  orderId: string;
  userId: string;
  items: readonly OrderItem[];
  discount?: number;
  shipping: ShippingMethod;
  isPriority?: boolean;
}

function processOrder({ orderId, userId, items, discount = 0, shipping, isPriority = false }: ProcessOrderArgs): OrderResult {
  if (items.length === 0) {
    return OrderResult.empty(orderId);
  }

  const availableItems = items.filter((item) => item.isAvailable);
  const subtotal = computeSubtotal(availableItems);
  const total = applyDiscount(subtotal, discount);

  return OrderResult.create({ orderId, userId, total, shipping, isPriority });
}
```

### Async & Promises

- Use `async`/`await` over raw Promise chains. Always handle rejections — unhandled promise rejections crash Node and silently fail in browsers.
- Never use `async` on a function that doesn't `await` anything — it wraps the return in an unnecessary Promise.
- Use `Promise.allSettled` when tasks are independent and you need all results. Use `Promise.all` only when one failure should abort everything.
- Avoid mixing callbacks and promises. Wrap callback APIs with `util.promisify` or manual Promise constructors.
- Never `await` inside a loop when iterations are independent — use `Promise.all` or batching.

```typescript
// Bad — sequential when it could be parallel
async function loadUserData(ids: string[]) {
  const results = [];
  for (const id of ids) {
    const user = await fetchUser(id);
    results.push(user);
  }
  return results;
}

// Bad — swallows the rejection reason
async function getData() {
  try {
    return await fetch(url);
  } catch {
    return null;
  }
}

// Good — parallel, preserves errors
async function loadUserData(ids: string[]): Promise<User[]> {
  const results = await Promise.all(ids.map((id) => fetchUser(id)));
  return results;
}

// Good — error has context
async function getData(): Promise<Response> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new FetchError(`GET ${url} failed: ${response.status}`);
  }
  return response;
}
```

### Error Handling

- Handle errors explicitly. Don't catch and swallow — either recover meaningfully or let the error propagate with context.
- Use custom Error classes for domain errors. Always include a descriptive `message`.
- Narrow catch blocks — check `instanceof` before accessing error-specific properties.
- In TypeScript, caught errors are `unknown` — narrow before using.

```typescript
// Bad
try {
  await saveData(payload);
} catch (e) {
  console.log("error");
}

// Bad — assumes error shape
try {
  await saveData(payload);
} catch (e: any) {
  return { error: e.message };
}

// Good
try {
  await saveData(payload);
} catch (error) {
  if (error instanceof ValidationError) {
    throw new UserFacingError(`Invalid data: ${error.field}`, { cause: error });
  }
  if (error instanceof NetworkError) {
    logger.warn("Save failed, will retry", { error });
    return enqueueRetry(payload);
  }
  throw error;
}
```

### Data Modeling

- Use Zod or similar for runtime validation at system boundaries (API inputs, env vars, config files).
- Use TypeScript interfaces/types for internal data structures — no runtime overhead.
- Never pass untyped objects between functions. Define interfaces at module boundaries.
- Use `as const` for literal tuples and string unions derived from arrays.

```typescript
// Bad
function createUser(data: object) {
  const name = (data as any).name;
  // ...
}

// Good
const CreateUserSchema = z.object({
  name: z.string().min(1),
  email: z.string().email(),
  role: z.enum(["admin", "user"]),
});

type CreateUserInput = z.infer<typeof CreateUserSchema>;

function createUser(input: CreateUserInput): User {
  return { id: generateId(), ...input, createdAt: new Date() };
}

// At the boundary
const parsed = CreateUserSchema.parse(req.body);
const user = createUser(parsed);
```

### React Patterns (when applicable)

- Prefer function components with hooks over class components.
- Keep components small — if a component exceeds ~100 lines, extract sub-components.
- Colocate state with where it's used. Lift state only when siblings need it.
- Use `useMemo`/`useCallback` only for expensive computations or stable references passed to memoized children — not by default.
- Never mutate state directly. Use immutable updates or `immer`.
- Name event handlers with `handle` prefix: `handleClick`, `handleSubmit`.

```tsx
// Bad — prop drilling, oversized component, premature memo
const App = React.memo(({ data, onUpdate, onDelete, onRefresh, theme, locale }) => {
  const processed = useMemo(() => data.map((d) => d.name), [data]);
  // ... 200 lines of JSX
});

// Good — focused, clear responsibility
function UserCard({ user, onRemove }: UserCardProps) {
  const handleRemove = () => {
    if (confirm(`Remove ${user.name}?`)) {
      onRemove(user.id);
    }
  };

  return (
    <article className="user-card">
      <h3>{user.name}</h3>
      <p>{user.email}</p>
      <button onClick={handleRemove} type="button">Remove</button>
    </article>
  );
}
```

### Iteration & Data Transforms

- Prefer `Array.from()`, spread, `map`, `filter`, `reduce` over imperative loops when the intent is clearer.
- Use `for...of` when you need early exit (`break`/`return`) or side effects per iteration.
- Never mutate the array you're iterating over.
- Prefer `Map` and `Set` over plain objects when keys are dynamic or you need guaranteed insertion order.

```typescript
// Bad
const results = [];
for (let i = 0; i < items.length; i++) {
  if (items[i].active) {
    results.push(items[i].name.toUpperCase());
  }
}

// Good
const results = items
  .filter((item) => item.active)
  .map((item) => item.name.toUpperCase());

// Good — early exit needed
function findFirst(items: Item[], predicate: (item: Item) => boolean): Item | undefined {
  for (const item of items) {
    if (predicate(item)) return item;
  }
  return undefined;
}
```

### Testing

- Test behavior, not implementation details. Tests should survive refactors.
- Use descriptive test names that read as sentences: `it("returns empty array when no items match")`.
- Prefer `toEqual` for deep comparisons, `toBe` for primitives and references.
- Mock at the boundary (HTTP, filesystem, clock) — not internal functions.
- Use `beforeEach` for shared setup only when every test in the block needs it.

```typescript
// Bad — tests implementation
describe("UserService", () => {
  it("calls the database", async () => {
    const spy = jest.spyOn(db, "query");
    await getUser("123");
    expect(spy).toHaveBeenCalledWith("SELECT * FROM users WHERE id = ?", ["123"]);
  });
});

// Good — tests behavior
describe("getUser", () => {
  it("returns the user when found", async () => {
    const user = await getUser("123");
    expect(user).toEqual({ id: "123", name: "Alice", email: "alice@test.com" });
  });

  it("throws NotFoundError when user does not exist", async () => {
    await expect(getUser("nonexistent")).rejects.toThrow(NotFoundError);
  });
});
```

### Style & Conventions

- No dead code, no commented-out blocks, no `// TODO` without a concrete plan attached.
- Match the surrounding codebase's style (formatter, import order, naming) over your own preferences.
- Use early returns to reduce nesting. Flat is better than nested.
- Prefer explicit `undefined` over implicit. Don't rely on JavaScript's implicit returns or coercion.
- Use `const enum` for compile-time constants in TypeScript (when not using `isolatedModules`).

When refactoring, change behavior in the smallest diff that works. Avoid drive-by reformatting in the same change as a logic edit.

---

## JS/TS Security Checklist

### injection

- XSS via `innerHTML`, `dangerouslySetInnerHTML`, `document.write()`, or unescaped template literals in DOM
- SQL injection in raw queries or string-concatenated ORM calls
- Command injection via `child_process.exec()` with user input (use `execFile` or `spawn` with array args)
- Path traversal — user-controlled paths passed to `fs` without confining to a base directory
- SSRF — outbound fetch/axios URLs built from user input without host allowlist
- Template injection — user input interpolated into server-side templates
- Log injection — user strings logged without newline sanitization
- Open redirect — user-controlled URLs passed to `res.redirect()` or `window.location`

### prototype_pollution

- `Object.assign()` or spread from user-controlled input without sanitization
- Recursive merge functions that don't guard `__proto__`, `constructor`, `prototype` keys
- User input used as dynamic property keys without validation

### auth

- Auth bypass paths (missing middleware, conditional skips)
- Authorization checks at the wrong layer (client-only, missing on API)
- IDOR — operations that trust a client-supplied resource ID without ownership check
- JWT: `alg=none` bypass, missing expiry validation, weak signing keys
- CSRF — state-changing endpoints without anti-CSRF tokens

### secrets

- Hardcoded API keys, tokens, passwords, connection strings
- Secrets in client-side bundles (anything in `src/` or browser code)
- Weak cryptographic operations (use `crypto` module, not custom implementations)
- TLS verification disabled

### eval_and_dynamic

- `eval()`, `Function()`, `setTimeout(string)`, `setInterval(string)` with user-controlled input
- Dynamic `import()` with user-controlled module paths
- `new RegExp()` with unsanitized user input (regex DoS / catastrophic backtracking)

### output_security

- Missing Content-Security-Policy headers
- Auth cookies without `httpOnly`, `secure`, `sameSite`
- PII/credentials in logs, error responses, or client-side state

### Exclusions — DO NOT REPORT (JS/TS Security)

- Code quality issues (code quality checklist owns these)
- Dependency vulnerabilities (npm audit owns these)
- Denial of service beyond regex DoS (out of scope)

## JS/TS Resilience Checklist

### async_handling

- Unhandled Promise rejections — missing `.catch()` or try/catch around `await`
- Fire-and-forget async calls that should be awaited
- Race conditions from shared mutable state across async operations
- Missing `AbortController` for cancellable fetch/network requests
- Missing error boundaries in React component trees

### resource_management

- Event listeners added without corresponding cleanup (`removeEventListener`, `unsubscribe`)
- Timers (`setInterval`, `setTimeout`) not cleared on component unmount or scope exit
- WebSocket/SSE connections not closed on cleanup
- Closures capturing references that prevent garbage collection

### error_recovery

- I/O operations (fetch, DB, file) without timeout configuration
- Missing retry logic on transient failures (network calls, rate-limited APIs)
- Error paths that don't log — silent `catch {}` blocks
- Missing fallback UI for failed data fetches

### Exclusions — DO NOT REPORT (JS/TS Resilience)

- Broad error catching (code quality checklist owns this)
- General try/catch patterns (code quality checklist owns this)

## JS/TS Performance Checklist

### rendering

- Unnecessary React re-renders — missing `memo`, `useMemo`, `useCallback` where measurably impactful
- Component key prop issues — missing keys in lists, or using array index as key when items reorder
- Large component trees re-rendering due to state lifted too high

### bundle_and_loading

- Importing entire libraries when only a submodule is needed (`import _ from 'lodash'` vs `import get from 'lodash/get'`)
- Missing code splitting / lazy loading for routes or heavy components
- Large static data structures inlined in JS bundles

### computation

- Redundant work inside a loop — invariant computation that should be hoisted out
- N+1 API calls — loading related data one item at a time inside a loop
- Sequential `await` calls that could be `Promise.all()`
- Missing debounce/throttle on frequent event handlers (scroll, resize, input)

### dom_and_memory

- DOM manipulation inside tight loops without batching
- Event listeners on window/document without cleanup
- Growing arrays/maps that are never pruned (memory leak pattern)

### Exclusions — DO NOT REPORT (JS/TS Performance)

- Missing error handling (resilience checklist owns this)
- Micro-optimizations with no measurable impact
