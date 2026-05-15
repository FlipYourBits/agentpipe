---
name: codemonkeys-bugfix
description: Use when the user reports a bug, error, or failing test — traces root cause by reading stack traces and following call chains through code, writes a structured diagnosis to .codemonkeys/YYYYMMDD-HHMMSS_bug-diagnosis.md, then dispatches a sandboxed editor agent to apply the fix
---

You are investigating a bug. Trace the root cause methodically before proposing any fix.

**Phase markers:** Announce each phase to the user as you enter it: `[1/3] Investigation`, `[2/3] Diagnosis`, `[3/3] Fix`.

## Workflow

```dot
digraph bugfix {
  rankdir=TB; node [shape=box];
  start [label="Bug reported" shape=doublecircle];
  branch [label="Branch check" shape=diamond];
  create [label="Create fix/<slug>"];
  investigate [label="[1/3] Investigation\nParse → Read → Trace"];
  hypotheses [label="Form 2-3 hypotheses\nRank by likelihood"];
  evidence [label="Gather evidence for each"];
  diagnose [label="[2/3] Write diagnosis\n.codemonkeys/YYYYMMDD-HHMMSS_bug-diagnosis.md"];
  gate [label="User approves?" shape=diamond];
  fix [label="[3/3] Dispatch fix\ncodemonkeys edit --task-file"];
  verify [label="git diff + verify"];
  start -> branch;
  branch -> create [label="on main"];
  branch -> investigate [label="on fix/*"];
  create -> investigate;
  investigate -> hypotheses;
  hypotheses -> evidence;
  evidence -> diagnose;
  diagnose -> gate;
  gate -> fix [label="approved"];
  gate -> diagnose [label="revise"];
  fix -> verify;
}
```

## Red Flags — Stop and Follow the Process

| If you're thinking... | The reality is... |
|---|---|
| "I already know the fix" | Write the diagnosis anyway — your "obvious" fix misses the root cause 40% of the time. |
| "This is too simple for a full investigation" | Simple bugs have simple diagnoses. The process is fast when the bug is simple. |
| "Let me just try something quick" | Trial-and-error is not debugging. Trace the root cause first. |
| "The stack trace tells me everything" | Stack traces show where it failed, not why. Read the surrounding code. |
| "I'll write the diagnosis after I fix it" | The diagnosis gates the fix. No diagnosis, no dispatch. |

## Branch Setup

Before investigating, check the current branch with `git branch --show-current`.

- **On `main` or `master`:** Suggest creating a fix branch. Generate a name from the bug description: `fix/<short-slug>`. Ask: "You're on main. Want me to create `fix/<slug>` for this work?"
- **On matching prefix** (`fix/`, `bugfix/`, or `hotfix/`): Proceed silently.
- **On wrong prefix** (anything else): Warn the user: "You're on `<branch>` — that doesn't look like a fix branch. Want me to create `fix/<slug>` instead, or continue here?"

If creating a branch: `git checkout -b fix/<slug>`

## Investigation

1. **Parse the report.** If error output or a stack trace is provided, read the stack trace to identify the immediate failure point.

2. **Read failing tests.** If a failing test is mentioned, read it to understand expected vs. actual behavior.

3. **Trace the call chain.** Read the code at the failure point. Follow the call chain backwards to understand how the code reached this state.

4. **Form hypotheses.** Write 2-3 possible root causes, ranked by likelihood. For each:
   - What assumption would need to be violated for this to be the cause?
   - What evidence would confirm or rule it out?
   - Read the specific code paths that would prove or disprove it.
   
   If the description is vague or missing critical information, ask clarifying questions before investigating.

5. **Narrow to root cause.** Eliminate hypotheses that the evidence contradicts. If multiple remain, gather more evidence. Proceed only when you have one root cause with supporting evidence.

6. **Write the diagnosis.** Write findings to `.codemonkeys/YYYYMMDD-HHMMSS_bug-diagnosis.md`.

## Diagnosis Format

```markdown
# Bug Diagnosis

## Root Cause

<one-sentence description>

**Confidence:** high / medium / low

## Affected Files

- `<file_path>`
- `<file_path>`

## Explanation

<detailed explanation — how the code reaches the failure state, what assumption is violated>

## Proposed Fix

<what needs to change, not code — describe the approach>

## Related Tests

- `<test_file_path>` — <what it covers>

```

## Dispatching the fix

When the user approves the diagnosis and asks you to fix it, dispatch the fix through a codemonkeys agent:

```bash
codemonkeys edit <affected_file1> [affected_file2 ...] \
  --task-file .codemonkeys/<timestamp>_bug-diagnosis.md \
  --read-paths <related_test_file1>,<related_test_file2>
```

Use the actual timestamp from the file you wrote in step 6.

This runs a sandboxed `python_file_editor` agent with scoped Edit permissions on the affected files and Read-only access to related tests for context. One agent handles all affected files.

After the agent finishes, show `git diff` and offer to revert if needed.

When the user wants to commit the fix, invoke the `codemonkeys-smart-commit` skill. Do not use the built-in git commit workflow.

## Rules

- Do not modify any source files during investigation. Investigate only.
- Follow the evidence — read actual code, don't guess from file names.
- Report confidence honestly: "high" (clear root cause), "medium" (likely cause, need to verify), "low" (hypothesis, multiple possibilities).
- After writing the diagnosis, tell the user: "Diagnosis written to `.codemonkeys/YYYYMMDD-HHMMSS_bug-diagnosis.md` — review it and ask me to implement the fix when ready."
