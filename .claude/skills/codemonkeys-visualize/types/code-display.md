# Code Display Type

Also read: nothing extra

Use for: syntax-highlighted code with line numbers, annotations, and line highlights. Gutter dots expand to inline notes on click.

## HTML Structure

```html
<h1>Code Display: cli.py</h1>

<div class="code-block">
    <!-- Header bar -->
    <div class="code-header">
        <span class="code-filename">codemonkeys/cli.py</span>
        <span class="code-lang label">Python</span>
    </div>

    <!-- Code body -->
    <div class="code-body">

        <!-- Normal line -->
        <div class="code-line" data-line="1">
            <span class="code-gutter">1</span>
            <span class="code-content"><span class="syn-keyword">import</span> <span class="syn-builtin">subprocess</span></span>
        </div>

        <!-- Line with annotation -->
        <div class="code-line highlighted" data-line="42">
            <span class="code-gutter has-anno">
                42
                <span class="anno-dot" onclick="toggleAnno('anno-42')" title="View annotation">●</span>
            </span>
            <span class="code-content">    result = <span class="syn-builtin">subprocess</span>.<span class="syn-function">run</span>(cmd, <span class="syn-keyword">shell</span>=<span class="syn-keyword">True</span>)</span>
        </div>
        <div class="anno-popup" id="anno-42">
            <span class="anno-icon">⚠</span>
            <div class="anno-text">
                <strong>Security:</strong> Shell injection risk. The <code>shell=True</code> flag allows
                arbitrary command execution if <code>cmd</code> contains user input.
                Use <code>shlex.split(cmd)</code> and pass args as a list instead.
            </div>
        </div>

        <!-- Normal lines -->
        <div class="code-line" data-line="43">
            <span class="code-gutter">43</span>
            <span class="code-content">    <span class="syn-keyword">return</span> result.stdout</span>
        </div>
        <div class="code-line" data-line="44">
            <span class="code-gutter">44</span>
            <span class="code-content">&#160;</span>
        </div>

        <!-- Another annotated line -->
        <div class="code-line highlighted" data-line="45">
            <span class="code-gutter has-anno">
                45
                <span class="anno-dot" onclick="toggleAnno('anno-45')" title="View annotation">●</span>
            </span>
            <span class="code-content"><span class="syn-keyword">def</span> <span class="syn-function">run</span>(files):</span>
        </div>
        <div class="anno-popup" id="anno-45">
            <span class="anno-icon">ℹ</span>
            <div class="anno-text">
                <strong>Convention:</strong> Missing type annotation. Add <code>files: list[str]</code>
                to improve IDE support and static analysis coverage.
            </div>
        </div>

        <div class="code-line" data-line="46">
            <span class="code-gutter">46</span>
            <span class="code-content">    <span class="syn-comment"># dispatch to agent runner</span></span>
        </div>
        <div class="code-line" data-line="47">
            <span class="code-gutter">47</span>
            <span class="code-content">    <span class="syn-keyword">for</span> f <span class="syn-keyword">in</span> files:</span>
        </div>
        <div class="code-line" data-line="48">
            <span class="code-gutter">48</span>
            <span class="code-content">        runner.<span class="syn-function">run</span>(f)</span>
        </div>
    </div>
</div>
```

## CSS

```css
.code-block {
    border: 1px solid var(--border-default);
    border-radius: 8px;
    overflow: hidden;
    font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
    font-size: 0.82rem;
    line-height: 1.6;
    background: var(--bg-card);
    max-width: 900px;
}

/* Header */
.code-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.55rem 1rem;
    background: var(--bg-elevated);
    border-bottom: 1px solid var(--border-default);
}

.code-filename {
    font-size: 0.8rem;
    color: var(--text-secondary);
}

.code-lang {
    font-size: 0.7rem;
    font-family: system-ui, sans-serif;
}

/* Body */
.code-body {
    overflow-x: auto;
}

/* Individual lines */
.code-line {
    display: flex;
    align-items: stretch;
    min-height: 1.6em;
}

.code-line:hover {
    background: color-mix(in srgb, var(--bg-elevated) 50%, transparent);
}

.code-line.highlighted {
    background: color-mix(in srgb, var(--color-warning) 8%, transparent);
    border-left: 2px solid var(--color-warning);
}

/* Gutter with line number */
.code-gutter {
    min-width: 3.5rem;
    padding: 0 0.75rem 0 0.5rem;
    text-align: right;
    color: var(--text-muted);
    font-size: 0.75rem;
    border-right: 1px solid var(--border-default);
    user-select: none;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 0.4rem;
    flex-shrink: 0;
    position: relative;
}

.code-gutter.has-anno {
    color: var(--color-warning);
}

/* Annotation dot */
.anno-dot {
    font-size: 0.6rem;
    color: var(--color-warning);
    cursor: pointer;
    flex-shrink: 0;
    line-height: 1;
    transition: transform 0.15s ease, color 0.15s ease;
}

.anno-dot:hover {
    transform: scale(1.4);
    color: var(--cat-orange);
}

/* Code content */
.code-content {
    padding: 0 1rem;
    white-space: pre;
    display: flex;
    align-items: center;
    min-width: 0;
    color: var(--text-body);
}

/* Annotation popup (inline, below the line) */
.anno-popup {
    display: none;
    gap: 0.6rem;
    padding: 0.65rem 1rem 0.65rem 4rem;
    background: color-mix(in srgb, var(--color-warning) 8%, var(--bg-elevated));
    border-top: 1px solid color-mix(in srgb, var(--color-warning) 20%, var(--border-default));
    border-bottom: 1px solid color-mix(in srgb, var(--color-warning) 20%, var(--border-default));
    font-family: system-ui, sans-serif;
    font-size: 0.82rem;
    color: var(--text-secondary);
    line-height: 1.5;
    align-items: flex-start;
}

.anno-popup.open {
    display: flex;
}

.anno-icon {
    font-size: 0.9rem;
    flex-shrink: 0;
    margin-top: 0.1rem;
}

.anno-text {
    flex: 1;
}

/* Syntax highlight tokens */
.syn-keyword  { color: var(--cat-pink);   font-weight: 600; }
.syn-string   { color: var(--cat-green); }
.syn-comment  { color: var(--text-muted); font-style: italic; }
.syn-number   { color: var(--cat-orange); }
.syn-type     { color: var(--cat-cyan); }
.syn-function { color: var(--cat-blue); }
.syn-operator { color: var(--text-secondary); }
.syn-builtin  { color: var(--cat-purple); }
```

## JS

```javascript
function toggleAnno(id) {
    const popup = document.getElementById(id);
    if (!popup) return;
    const isOpen = popup.classList.contains('open');
    // Close all open popups first (one at a time)
    document.querySelectorAll('.anno-popup.open').forEach(p => p.classList.remove('open'));
    if (!isOpen) popup.classList.add('open');
}

// Basic Python syntax highlighter using regex.
// Escape the code string first, then apply token replacements in order.
// Returns HTML string — set innerHTML of a .code-content span.
function highlightPython(code) {
    // Escape HTML first
    let s = code
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

    // Order matters: comments and strings first to avoid re-processing their contents.
    // Multi-line strings are not handled; single-file inline usage only.
    const rules = [
        // Comments
        [/(#[^\n]*)/g,
            '<span class="syn-comment">$1</span>'],
        // Triple-quoted strings (simplified, single line)
        [/(""".*?"""|'''.*?''')/g,
            '<span class="syn-string">$1</span>'],
        // Single/double quoted strings
        [/("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')/g,
            '<span class="syn-string">$1</span>'],
        // Keywords
        [/\b(False|None|True|and|as|assert|async|await|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield)\b/g,
            '<span class="syn-keyword">$1</span>'],
        // Built-in types and functions
        [/\b(int|str|float|bool|list|dict|tuple|set|type|object|print|len|range|enumerate|zip|map|filter|super|property|staticmethod|classmethod|isinstance|issubclass|hasattr|getattr|setattr|open|Exception|ValueError|TypeError|KeyError|IndexError|subprocess|sys|os|re|json)\b/g,
            '<span class="syn-builtin">$1</span>'],
        // Function definitions
        [/\bdef\s+([a-zA-Z_]\w*)/g,
            'def <span class="syn-function">$1</span>'],
        // Function calls (heuristic: word followed by open paren not after 'def')
        [/(?<!def\s)\b([a-zA-Z_]\w*)\s*(?=\()/g,
            '<span class="syn-function">$1</span>'],
        // Numbers
        [/\b(\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\b/g,
            '<span class="syn-number">$1</span>'],
        // Decorators
        [/(@[a-zA-Z_][\w.]*)/g,
            '<span class="syn-type">$1</span>'],
        // Type annotations (simplified: word after : or -> not inside string)
        [/:\s*([A-Z][a-zA-Z_][\w\[\], |]*)/g,
            ': <span class="syn-type">$1</span>'],
    ];

    rules.forEach(([pattern, replacement]) => {
        s = s.replace(pattern, replacement);
    });

    return s;
}

document.addEventListener('DOMContentLoaded', () => {
    // If you want to auto-highlight .code-content spans containing raw code,
    // uncomment and adapt:
    // document.querySelectorAll('.code-content[data-raw]').forEach(el => {
    //     el.innerHTML = highlightPython(el.getAttribute('data-raw'));
    // });
});
```

## Annotation Workflow

1. Add `class="highlighted"` to any `.code-line` that has a finding.
2. Add `class="has-anno"` to its `.code-gutter` and an `.anno-dot` span with `onclick="toggleAnno('anno-N')"`.
3. Insert an `.anno-popup` div with `id="anno-N"` immediately after the `.code-line`.
4. The popup shows inline below the flagged line when clicked; clicking again or clicking another anno closes it.
