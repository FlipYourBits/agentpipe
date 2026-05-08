import "clsx";
import { a4 as ssr_context, e as escape_html, a5 as store_get, a6 as unsubscribe_stores, a7 as ensure_array_like, a8 as attr_style, a9 as attr, a3 as derived$1, aa as stringify, ab as attr_class } from "../../chunks/renderer.js";
import { w as writable, d as derived } from "../../chunks/index.js";
function onDestroy(fn) {
  /** @type {SSRContext} */
  ssr_context.r.on_destroy(fn);
}
const lastEvent = writable(null);
let socket = null;
function disconnect() {
  socket?.close();
  socket = null;
}
const agents = writable([]);
const runs = writable(/* @__PURE__ */ new Map());
const selectedRunId = writable(null);
const selectedRun = derived(
  [runs, selectedRunId],
  ([$runs, $selectedRunId]) => $selectedRunId ? $runs.get($selectedRunId) ?? null : null
);
const sessionCost = derived(runs, ($runs) => {
  let total = 0;
  for (const run of $runs.values()) {
    total += run.cost_usd;
  }
  return total;
});
const runsByStatus = derived(runs, ($runs) => {
  const running = [];
  const queued = [];
  const completed = [];
  for (const run of $runs.values()) {
    if (run.status === "running") running.push(run);
    else if (run.status === "queued") queued.push(run);
    else completed.push(run);
  }
  return { running, queued, completed };
});
lastEvent.subscribe((event) => {
  if (!event) return;
  runs.update(($runs) => {
    const run = $runs.get(event.run_id);
    if (!run) return $runs;
    run.events.push(event);
    if (run.status === "queued") {
      run.status = "running";
      run.started_at = event.timestamp;
    }
    if (event.event_type === "TokenUpdate") {
      const data = event.data;
      const usage = data.usage;
      if (usage) {
        run.tokens = { input: usage.input_tokens ?? 0, output: usage.output_tokens ?? 0 };
      }
      run.cost_usd = data.cost_usd ?? run.cost_usd;
    } else if (event.event_type === "ToolCall") {
      const data = event.data;
      const toolName = data.tool_name;
      const toolInput = data.tool_input;
      let detail = toolName;
      if (["Read", "Edit", "Write"].includes(toolName)) {
        detail = `${toolName}(${toolInput?.file_path ?? "?"})`;
      } else if (toolName === "Grep") {
        detail = `Grep('${toolInput?.pattern ?? "?"}')`;
      } else if (toolName === "Bash") {
        const cmd = toolInput?.command ?? "";
        detail = `Bash($ ${cmd.slice(0, 60)})`;
      }
      run.current_tool = detail;
    } else if (event.event_type === "AgentCompleted") {
      run.status = "completed";
      run.current_tool = null;
      const data = event.data;
      const result = data.result;
      if (result) {
        run.cost_usd = result.cost_usd ?? run.cost_usd;
        run.result = result;
      }
    } else if (event.event_type === "AgentError") {
      run.status = "error";
      run.current_tool = null;
    }
    return new Map($runs);
  });
});
function TopBar($$renderer) {
  var $$store_subs;
  function formatCost(cost) {
    return `$${cost.toFixed(cost < 0.01 ? 4 : 2)}`;
  }
  $$renderer.push(`<header class="topbar svelte-yic9pk"><div class="brand svelte-yic9pk"><span class="logo svelte-yic9pk">🐒</span> <span class="title svelte-yic9pk">Codemonkeys</span></div> <div class="session-cost"><span class="label svelte-yic9pk">Session cost:</span> <span class="value svelte-yic9pk">${escape_html(formatCost(store_get($$store_subs ??= {}, "$sessionCost", sessionCost)))}</span></div></header>`);
  if ($$store_subs) unsubscribe_stores($$store_subs);
}
const fileTree = writable([]);
const searchQuery = writable("");
const selectedFiles = derived(fileTree, ($tree) => {
  const selected = [];
  function walk(nodes) {
    for (const node of nodes) {
      if (node.selected && !node.is_dir) {
        selected.push(node.path);
      }
      if (node.children) walk(node.children);
    }
  }
  walk($tree);
  return selected;
});
function FileTree($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let { nodes, depth = 0 } = $$props;
    function matchesSearch(node, query) {
      if (!query) return true;
      const q = query.toLowerCase();
      if (node.name.toLowerCase().includes(q)) return true;
      if (node.children) return node.children.some((c) => matchesSearch(c, q));
      return false;
    }
    const filteredNodes = derived$1(() => nodes.filter((n) => matchesSearch(n, store_get($$store_subs ??= {}, "$searchQuery", searchQuery))).sort((a, b) => {
      if (a.is_dir !== b.is_dir) return a.is_dir ? -1 : 1;
      return a.name.localeCompare(b.name);
    }));
    $$renderer2.push(`<!--[-->`);
    const each_array = ensure_array_like(filteredNodes());
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let node = each_array[$$index];
      $$renderer2.push(`<div class="tree-node svelte-124nk1e"${attr_style(`padding-left: ${stringify(depth * 16)}px`)}><span class="checkbox svelte-124nk1e" role="checkbox"${attr("aria-checked", node.selected)} tabindex="0">${escape_html(node.selected ? "☑" : "☐")}</span> `);
      if (node.is_dir) {
        $$renderer2.push("<!--[0-->");
        $$renderer2.push(`<span class="folder svelte-124nk1e" role="button" tabindex="0">${escape_html(node.expanded ? "📂" : "📁")} ${escape_html(node.name)}/</span>`);
      } else {
        $$renderer2.push("<!--[-1-->");
        $$renderer2.push(`<span class="file svelte-124nk1e">${escape_html(node.name)}</span>`);
      }
      $$renderer2.push(`<!--]--></div> `);
      if (node.is_dir && node.expanded && node.children) {
        $$renderer2.push("<!--[0-->");
        FileTree($$renderer2, { nodes: node.children, depth: depth + 1 });
        $$renderer2.push(`<!---->`);
      } else {
        $$renderer2.push("<!--[-1-->");
      }
      $$renderer2.push(`<!--]-->`);
    }
    $$renderer2.push(`<!--]-->`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
function GitButtons($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let activeMode = "";
    $$renderer2.push(`<div class="git-buttons svelte-qlrzk3"><button${attr_class("svelte-qlrzk3", void 0, { "active": activeMode === "changed" })}>Changed</button> <button${attr_class("svelte-qlrzk3", void 0, { "active": activeMode === "staged" })}>Staged</button> <button${attr_class("svelte-qlrzk3", void 0, { "active": activeMode === "all-py" })}>All .py</button></div>`);
  });
}
function DropZone($$renderer) {
  let dragover = false;
  $$renderer.push(`<div${attr_class("dropzone svelte-e3h709", void 0, { "dragover": dragover })} role="region" aria-label="Drop files here">Drop files here</div>`);
}
function FilePicker($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    $$renderer2.push(`<div class="picker svelte-1nm0yno"><div class="header svelte-1nm0yno"><div class="title-row svelte-1nm0yno"><div class="title svelte-1nm0yno">FILES</div> <div class="tree-controls svelte-1nm0yno"><button title="Expand all" class="svelte-1nm0yno">+</button> <button title="Collapse all" class="svelte-1nm0yno">−</button></div></div> `);
    GitButtons($$renderer2);
    $$renderer2.push(`<!----> <input class="search svelte-1nm0yno" type="text" placeholder="Search files..."${attr("value", store_get($$store_subs ??= {}, "$searchQuery", searchQuery))}/></div> <div class="tree svelte-1nm0yno">`);
    FileTree($$renderer2, {
      nodes: store_get($$store_subs ??= {}, "$fileTree", fileTree)
    });
    $$renderer2.push(`<!----></div> <div class="footer svelte-1nm0yno"><div class="count svelte-1nm0yno">${escape_html(store_get($$store_subs ??= {}, "$selectedFiles", selectedFiles).length)} files selected</div> `);
    DropZone($$renderer2);
    $$renderer2.push(`<!----></div></div>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
function AgentLauncher($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let selectedAgent = "";
    $$renderer2.push(`<div class="launcher svelte-1c246n9">`);
    $$renderer2.select(
      { value: selectedAgent, class: "" },
      ($$renderer3) => {
        $$renderer3.push(`<!--[-->`);
        const each_array = ensure_array_like(store_get($$store_subs ??= {}, "$agents", agents));
        for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
          let agent = each_array[$$index];
          $$renderer3.option({ value: agent.name }, ($$renderer4) => {
            $$renderer4.push(`${escape_html(agent.name)}`);
          });
        }
        $$renderer3.push(`<!--]-->`);
      },
      "svelte-1c246n9"
    );
    $$renderer2.push(` <button class="run-btn svelte-1c246n9"${attr("disabled", store_get($$store_subs ??= {}, "$selectedFiles", selectedFiles).length === 0, true)}>▶ Run</button> <div class="divider svelte-1c246n9"></div> <button class="kill-btn svelte-1c246n9">Kill All</button></div>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
function EventLog($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let { events, startedAt } = $$props;
    function formatTime(timestamp) {
      if (!startedAt) return "00:00.0";
      const elapsed = timestamp - startedAt;
      const mins = Math.floor(elapsed / 60);
      const secs = (elapsed % 60).toFixed(1);
      return mins > 0 ? `${mins}:${secs.padStart(4, "0")}` : secs.padStart(4, "0");
    }
    function eventColor(type) {
      if (type === "ToolCall" || type === "ToolResult") return "var(--yellow)";
      if (type === "ThinkingOutput") return "var(--purple)";
      if (type === "TextOutput") return "var(--green)";
      if (type === "AgentStarted") return "var(--accent)";
      if (type === "ToolDenied") return "var(--red)";
      if (type === "RateLimitHit") return "var(--red)";
      return "var(--text-dim)";
    }
    function eventLabel(type) {
      const labels = {
        AgentStarted: "START",
        ToolCall: "TOOL",
        ToolResult: "RESULT",
        ToolDenied: "DENIED",
        ThinkingOutput: "THINK",
        TextOutput: "TEXT",
        TokenUpdate: "TOKENS",
        RateLimitHit: "RATE"
      };
      return labels[type] ?? type;
    }
    function eventDetail(event) {
      const d = event.data;
      if (event.event_type === "AgentStarted") return `Agent started — model: ${d.model}`;
      if (event.event_type === "ToolCall") {
        const name = d.tool_name;
        const input = d.tool_input;
        if (["Read", "Edit", "Write"].includes(name)) return `${name}(${input?.file_path ?? "?"})`;
        if (name === "Grep") return `Grep('${input?.pattern ?? "?"}')`;
        if (name === "Bash") return `Bash($ ${input?.command ?? ""})`;
        return name;
      }
      if (event.event_type === "ToolResult") {
        const output = d.output ?? "";
        return `→ ${output}`;
      }
      if (event.event_type === "ThinkingOutput") return d.text ?? "";
      if (event.event_type === "TextOutput") return d.text ?? "";
      if (event.event_type === "ToolDenied") return `DENIED: ${d.tool_name}(${d.command})`;
      if (event.event_type === "RateLimitHit") return `Rate limited — waiting ${d.wait_seconds}s`;
      return "";
    }
    const displayEvents = derived$1(() => events.filter((e) => !["TokenUpdate", "RawMessage"].includes(e.event_type)));
    $$renderer2.push(`<div class="event-log svelte-wqyzhu"><!--[-->`);
    const each_array = ensure_array_like(displayEvents());
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let event = each_array[$$index];
      $$renderer2.push(`<div class="event-line svelte-wqyzhu"><span class="time svelte-wqyzhu">${escape_html(formatTime(event.timestamp))}</span> <span class="badge svelte-wqyzhu"${attr_style(`color: ${stringify(eventColor(event.event_type))}`)}>${escape_html(eventLabel(event.event_type))}</span> <span class="detail svelte-wqyzhu">${escape_html(eventDetail(event))}</span></div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
function AgentCard($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let { run } = $$props;
    let expanded = derived$1(() => store_get($$store_subs ??= {}, "$selectedRunId", selectedRunId) === run.run_id);
    function statusClass(status) {
      return `status-${status}`;
    }
    function formatTokens(n) {
      return n >= 1e3 ? `${(n / 1e3).toFixed(1)}k` : String(n);
    }
    function formatCost(cost) {
      return `$${cost.toFixed(cost < 0.01 ? 4 : 3)}`;
    }
    function formatDuration(run2) {
      if (!run2.started_at || !run2.completed_at) return "";
      const secs = run2.completed_at - run2.started_at;
      return secs >= 60 ? `${(secs / 60).toFixed(1)}m` : `${secs.toFixed(1)}s`;
    }
    function findingCount(run2) {
      if (run2.status !== "completed" || !run2.result) return null;
      const result = run2.result;
      const output = result.output;
      if (!output) return null;
      const results = output.results;
      return results?.length ?? null;
    }
    $$renderer2.push(`<div${attr_class(`card ${stringify(statusClass(run.status))}`, "svelte-lbl337", { "expanded": expanded() })} role="button" tabindex="0"><div class="card-header svelte-lbl337"><div class="left svelte-lbl337"><div class="status-dot svelte-lbl337"></div> <span class="agent-name svelte-lbl337">${escape_html(run.agent_name)}</span> <span class="model-badge svelte-lbl337">${escape_html(run.model)}</span> `);
    if (run.status === "queued") {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<span class="queue-label svelte-lbl337">queued</span>`);
    } else {
      $$renderer2.push("<!--[-1-->");
    }
    $$renderer2.push(`<!--]--> `);
    if (expanded()) {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<span class="expand-indicator svelte-lbl337">▾ expanded</span>`);
    } else {
      $$renderer2.push("<!--[-1-->");
    }
    $$renderer2.push(`<!--]--></div> <div class="right svelte-lbl337">`);
    if (run.status === "completed") {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<span class="duration svelte-lbl337">${escape_html(formatDuration(run))}</span>`);
    } else {
      $$renderer2.push("<!--[-1-->");
    }
    $$renderer2.push(`<!--]--> <span class="cost svelte-lbl337">${escape_html(formatCost(run.cost_usd))}</span></div></div> `);
    if (run.status === "running" || run.status === "completed") {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<div class="card-meta svelte-lbl337"><span class="tokens svelte-lbl337">⚡ ${escape_html(formatTokens(run.tokens.input))} in / ${escape_html(formatTokens(run.tokens.output))} out</span> `);
      if (run.status === "running" && run.current_tool) {
        $$renderer2.push("<!--[0-->");
        $$renderer2.push(`<span class="current-tool svelte-lbl337">${escape_html(run.current_tool)}</span>`);
      } else {
        $$renderer2.push("<!--[-1-->");
      }
      $$renderer2.push(`<!--]--> `);
      if (run.status === "completed") {
        $$renderer2.push("<!--[0-->");
        if (findingCount(run) !== null) {
          $$renderer2.push("<!--[0-->");
          $$renderer2.push(`<span class="findings svelte-lbl337">${escape_html(findingCount(run))} findings</span>`);
        } else {
          $$renderer2.push("<!--[-1-->");
        }
        $$renderer2.push(`<!--]-->`);
      } else {
        $$renderer2.push("<!--[-1-->");
      }
      $$renderer2.push(`<!--]--></div>`);
    } else {
      $$renderer2.push("<!--[-1-->");
    }
    $$renderer2.push(`<!--]--> `);
    if (run.status === "error") {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<div class="error-msg svelte-lbl337">${escape_html(run.result ?? "Unknown error")}</div>`);
    } else {
      $$renderer2.push("<!--[-1-->");
    }
    $$renderer2.push(`<!--]--> `);
    if (expanded()) {
      $$renderer2.push("<!--[0-->");
      EventLog($$renderer2, { events: run.events, startedAt: run.started_at });
    } else {
      $$renderer2.push("<!--[-1-->");
    }
    $$renderer2.push(`<!--]--></div>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
function AgentMonitor($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    $$renderer2.push(`<div class="monitor svelte-1pino47">`);
    AgentLauncher($$renderer2);
    $$renderer2.push(`<!----> <div class="cards svelte-1pino47">`);
    if (store_get($$store_subs ??= {}, "$runsByStatus", runsByStatus).running.length > 0) {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<div class="section-label svelte-1pino47">RUNNING</div> <!--[-->`);
      const each_array = ensure_array_like(store_get($$store_subs ??= {}, "$runsByStatus", runsByStatus).running);
      for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
        let run = each_array[$$index];
        AgentCard($$renderer2, { run });
      }
      $$renderer2.push(`<!--]-->`);
    } else {
      $$renderer2.push("<!--[-1-->");
    }
    $$renderer2.push(`<!--]--> `);
    if (store_get($$store_subs ??= {}, "$runsByStatus", runsByStatus).queued.length > 0) {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<div class="section-label svelte-1pino47">QUEUED</div> <!--[-->`);
      const each_array_1 = ensure_array_like(store_get($$store_subs ??= {}, "$runsByStatus", runsByStatus).queued);
      for (let $$index_1 = 0, $$length = each_array_1.length; $$index_1 < $$length; $$index_1++) {
        let run = each_array_1[$$index_1];
        AgentCard($$renderer2, { run });
      }
      $$renderer2.push(`<!--]-->`);
    } else {
      $$renderer2.push("<!--[-1-->");
    }
    $$renderer2.push(`<!--]--> `);
    if (store_get($$store_subs ??= {}, "$runsByStatus", runsByStatus).completed.length > 0) {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<div class="section-label svelte-1pino47">COMPLETED</div> <!--[-->`);
      const each_array_2 = ensure_array_like(store_get($$store_subs ??= {}, "$runsByStatus", runsByStatus).completed);
      for (let $$index_2 = 0, $$length = each_array_2.length; $$index_2 < $$length; $$index_2++) {
        let run = each_array_2[$$index_2];
        AgentCard($$renderer2, { run });
      }
      $$renderer2.push(`<!--]-->`);
    } else {
      $$renderer2.push("<!--[-1-->");
    }
    $$renderer2.push(`<!--]--> `);
    if (store_get($$store_subs ??= {}, "$runsByStatus", runsByStatus).running.length === 0 && store_get($$store_subs ??= {}, "$runsByStatus", runsByStatus).queued.length === 0 && store_get($$store_subs ??= {}, "$runsByStatus", runsByStatus).completed.length === 0) {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<div class="empty svelte-1pino47"><p>No agent runs yet.</p> <p class="hint svelte-1pino47">Select files on the left, pick an agent, and click Run.</p></div>`);
    } else {
      $$renderer2.push("<!--[-1-->");
    }
    $$renderer2.push(`<!--]--></div></div>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
const queue = writable([]);
derived(
  queue,
  ($queue) => $queue.filter((item) => item.selected).length
);
derived(queue, ($queue) => ({
  high: $queue.filter((i) => i.severity === "high").length,
  medium: $queue.filter((i) => i.severity === "medium").length,
  low: $queue.filter((i) => i.severity === "low").length,
  info: $queue.filter((i) => i.severity === "info").length
}));
function FindingsList($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let { findings, checkedIndices } = $$props;
    function severityColor(severity) {
      const colors = {
        high: "var(--red)",
        medium: "var(--yellow)",
        low: "var(--blue)",
        info: "var(--text-dim)"
      };
      return colors[severity] ?? "var(--text-dim)";
    }
    $$renderer2.push(`<!--[-->`);
    const each_array = ensure_array_like(findings);
    for (let i = 0, $$length = each_array.length; i < $$length; i++) {
      let finding = each_array[i];
      $$renderer2.push(`<div class="finding svelte-1cw3cwe"><div class="finding-header svelte-1cw3cwe"><div class="left svelte-1cw3cwe"><span class="checkbox svelte-1cw3cwe" role="checkbox"${attr("aria-checked", checkedIndices.has(i))} tabindex="0">${escape_html(checkedIndices.has(i) ? "☑" : "☐")}</span> <div><div class="title svelte-1cw3cwe">${escape_html(finding.title)}</div> <div class="location svelte-1cw3cwe">${escape_html(finding.file)}${escape_html(finding.line ? `:${finding.line}` : "")}</div></div></div> <span class="severity svelte-1cw3cwe"${attr_style(`color: ${stringify(severityColor(finding.severity))}; border-color: ${stringify(severityColor(finding.severity))}`)}>${escape_html(finding.severity)}</span></div> `);
      if (finding.description) {
        $$renderer2.push("<!--[0-->");
        $$renderer2.push(`<div class="description svelte-1cw3cwe">${escape_html(finding.description)}</div>`);
      } else {
        $$renderer2.push("<!--[-1-->");
      }
      $$renderer2.push(`<!--]--></div>`);
    }
    $$renderer2.push(`<!--]-->`);
  });
}
function ResultsPanel($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let activeTab = "results";
    let checkedIndices = /* @__PURE__ */ new Set();
    function getFindings() {
      if (!store_get($$store_subs ??= {}, "$selectedRun", selectedRun)?.result) return [];
      const result = store_get($$store_subs ??= {}, "$selectedRun", selectedRun).result;
      const output = result.output;
      if (!output?.results) return [];
      return output.results;
    }
    const findings = derived$1(getFindings);
    $$renderer2.push(`<div class="results-panel svelte-w4gtgs"><div class="tabs svelte-w4gtgs"><button${attr_class("tab svelte-w4gtgs", void 0, { "active": activeTab === "results" })}>Results</button> <button${attr_class("tab svelte-w4gtgs", void 0, { "active": activeTab === "queue" })}>Fixer Queue `);
    if (store_get($$store_subs ??= {}, "$queue", queue).length > 0) {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<span class="queue-badge svelte-w4gtgs">${escape_html(store_get($$store_subs ??= {}, "$queue", queue).length)}</span>`);
    } else {
      $$renderer2.push("<!--[-1-->");
    }
    $$renderer2.push(`<!--]--></button></div> `);
    {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<div class="results-content svelte-w4gtgs">`);
      if (store_get($$store_subs ??= {}, "$selectedRun", selectedRun)) {
        $$renderer2.push("<!--[0-->");
        $$renderer2.push(`<div class="results-header svelte-w4gtgs"><span class="agent-label svelte-w4gtgs">${escape_html(store_get($$store_subs ??= {}, "$selectedRun", selectedRun).agent_name)}</span> `);
        if (store_get($$store_subs ??= {}, "$selectedRun", selectedRun).status === "running") {
          $$renderer2.push("<!--[0-->");
          $$renderer2.push(`<span class="streaming svelte-w4gtgs">streaming...</span>`);
        } else {
          $$renderer2.push("<!--[-1-->");
        }
        $$renderer2.push(`<!--]--></div> `);
        if (findings().length > 0) {
          $$renderer2.push("<!--[0-->");
          $$renderer2.push(`<div class="findings-list svelte-w4gtgs">`);
          FindingsList($$renderer2, {
            findings: findings(),
            checkedIndices
          });
          $$renderer2.push(`<!----></div> <div class="results-actions svelte-w4gtgs"><button class="add-btn svelte-w4gtgs"${attr("disabled", checkedIndices.size === 0, true)}>Add to Queue (${escape_html(checkedIndices.size)})</button> <button class="export-btn svelte-w4gtgs">Export</button></div>`);
        } else if (store_get($$store_subs ??= {}, "$selectedRun", selectedRun).status === "completed") {
          $$renderer2.push("<!--[1-->");
          $$renderer2.push(`<div class="empty svelte-w4gtgs">No findings.</div>`);
        } else {
          $$renderer2.push("<!--[-1-->");
          $$renderer2.push(`<div class="empty svelte-w4gtgs">Results will appear as the agent completes analysis...</div>`);
        }
        $$renderer2.push(`<!--]-->`);
      } else {
        $$renderer2.push("<!--[-1-->");
        $$renderer2.push(`<div class="empty svelte-w4gtgs">Click an agent card to view its results.</div>`);
      }
      $$renderer2.push(`<!--]--></div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    onDestroy(() => {
      disconnect();
    });
    $$renderer2.push(`<div class="dashboard svelte-1uha8ag">`);
    TopBar($$renderer2);
    $$renderer2.push(`<!----> <main class="panels svelte-1uha8ag"><aside class="file-picker svelte-1uha8ag">`);
    FilePicker($$renderer2);
    $$renderer2.push(`<!----></aside> <section class="agent-monitor svelte-1uha8ag">`);
    AgentMonitor($$renderer2);
    $$renderer2.push(`<!----></section> <aside class="results-panel svelte-1uha8ag">`);
    ResultsPanel($$renderer2);
    $$renderer2.push(`<!----></aside></main></div>`);
  });
}
export {
  _page as default
};
