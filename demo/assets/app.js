"use strict";

const sections = [
  ["overview", "总览", "Overview", "研究范围包含 7 个 cohort。解释复跑和 Banking 重复任务，再进入 Slack 07。"],
  ["exposure", "暴露、采纳与执行", "Exposure, Adoption & Execution", "先读 74 个确认暴露与 6 个 UNKNOWN。解释采纳需要语义标注，再对照两名 Worker 的工具调用。"],
  ["provenance", "通信图与信息流", "Communication Graph vs Information Flow", "点开 m_1 和 m_2，再点网页虚线。比较同一个 Worker 的两条可观察来源。"],
  ["topology", "自适应拓扑", "Adaptive Topology", "打开一例发生变化的执行，切换 Turn 0 和 Turn 1。比较完整配置的效用、token 与延迟。"],
  ["workers", "多智能体协作效率", "Collaboration Efficiency", "切换 suite 和条件，读 paired outcomes。说明固定调度同时引入任务分配与汇报协议。"],
  ["audit", "风险识别与行动预防", "Audit vs Execution", "从首次目标调用播到 Audit。对照 Clean 的目标调用、归档 risk_score 和实际 mutation。"],
  ["method", "方法与复现", "Methodology & Reproducibility", "用数据清单定位源表与 SHA-256。汇报结论时保留单种子、direct attack 和部分溯源的范围。"],
];

const datasets = ["summary", "episodes", "topology", "worker_comparison", "case_slack_07", "audit_timeline", "data_manifest"];
const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const page = $("#page");
const dialog = $("#replay-dialog");
const present = $("#present");
const footer = $("#page-footer");
const state = {
  route: "overview", presenting: false, cohort: null, overviewSuite: "all", overviewCondition: "all", overviewScene: "all",
  stage: "exposure", graphEdge: "m_1", topoSuite: "all", topoScene: "travel_15", topoCondition: "clean",
  topoTurn: 0, topoCompare: false, topoNode: null, workerSuite: "all", workerCondition: "attack",
  replayCondition: "attack", replayIndex: 0, replayTimer: null,
};
let data;

const esc = (value) => String(value ?? "UNKNOWN").replace(/[&<>"']/g, (char) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
const n = (value) => value == null ? "UNKNOWN" : new Intl.NumberFormat("en-US").format(value);
const pct = (count, total) => total ? `${(100 * count / total).toFixed(2)}%` : "—";
const sec = (value) => value == null ? "UNKNOWN" : `${value.toFixed(2)} s`;
const millions = (value) => value == null ? "UNKNOWN" : `${(value / 1e6).toFixed(2)}M`;
const ratio = (count, total) => total ? `${n(count)}/${n(total)}` : "—";
const yes = (value) => value == null ? "UNKNOWN" : value ? "是" : "否";
const suiteName = (name) => ({ all: "全部 suites", banking: "Banking", slack: "Slack", travel: "Travel", workspace: "Workspace" })[name] || name;
const conditionName = (name) => ({ all: "全部条件", clean: "Clean", attack: "Attack" })[name] || name;
const cohortLabel = (cohort) => cohort.id === "gpt4o_star" ? "GPT-6 Luna · 星形协作 · 4K" : cohort.label;
const actorName = (id) => ({
  agent_0: "Coordinator", agent_1: "Worker 1", agent_2: "Worker 2",
  final_synthesizer: "Final Synthesizer", constraint_reconciler: "Constraint Reconciler",
  external: "外部网页", target: "评分目标",
})[id] || id;
const icon = (id) => `<svg class="icon" aria-hidden="true"><use href="assets/icons.svg#${id}"/></svg>`;
const button = (label, attributes = "", primary = false) =>
  `<button type="button" class="button${primary ? " primary" : ""}" ${attributes}>${label}</button>`;
const select = (id, label, values, selected, format = (x) => x) =>
  `<label for="${id}">${label}<select id="${id}">${values.map((v) =>
    `<option value="${esc(v)}"${String(v) === String(selected) ? " selected" : ""}>${esc(format(v))}</option>`).join("")}</select></label>`;
const tag = (label, cls = "") => `<span class="tag ${cls}">${esc(label)}</span>`;
const note = (content, cls = "") => `<p class="note ${cls}">${content}</p>`;
const panel = (heading, body, subtitle = "", extra = "") =>
  `<section class="panel ${extra}"><div class="panel-head"><div><h2>${heading}</h2>${subtitle ? `<p class="micro">${subtitle}</p>` : ""}</div></div>${body}</section>`;
const metrics = (items) => `<div class="metrics">${items.map(([value, label, detail]) =>
  `<div class="metric"><strong>${value}</strong><span>${label}</span>${detail ? `<small>${detail}</small>` : ""}</div>`).join("")}</div>`;
const values = (items) => `<dl class="value-list">${items.map(([name, value]) => `<div><dt>${name}</dt><dd>${value}</dd></div>`).join("")}</dl>`;
const table = (headers, rows) => `<div class="table-scroll"><table><thead><tr>${headers.map((header, i) =>
  `<th scope="col"${i ? ' class="num"' : ""}>${esc(header)}</th>`).join("")}</tr></thead><tbody>${rows.map(([label, ...cells]) =>
  `<tr><th scope="row">${esc(label)}</th>${cells.map((cell) => `<td class="num">${esc(cell)}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
const dataLinks = (...names) => `<div class="source-links"><span>本地数据</span>${names.map((name) =>
  `<a href="data/${name}.json">${name}.json</a>`).join("")}<a href="#method">来源与校验</a></div>`;

function sourceLink(path, label = path) {
  const base = data.data_manifest.source_url;
  return `<a href="${esc(base + path.split("/").map(encodeURIComponent).join("/"))}" target="_blank" rel="noopener noreferrer">${esc(label)} ${icon("link")}</a>`;
}

function heading(title, intro, badge = "", tone = "") {
  const [, , english] = sections.find(([id]) => id === state.route);
  const number = sections.findIndex(([id]) => id === state.route);
  return `<header class="page-head"><p class="eyebrow">${number < 6 ? `Insight ${String(number).padStart(2, "0")} · ` : ""}${english}</p>
    <h1>${title}</h1><p>${intro}</p>${badge ? `<div>${tag(badge, tone)}</div>` : ""}</header>`;
}

function navigation() {
  const current = sections.findIndex(([id]) => id === state.route);
  $("#navigation").innerHTML = `<p class="nav-label">研究章节</p>${sections.map(([id, title, english], i) =>
    `<a class="nav-item" href="#${id}"${id === state.route ? ' aria-current="page"' : ""}><span class="nav-index">${i === 0 ? "◎" : i === 6 ? "↳" : `0${i}`}</span><span><b>${title}</b><small>${english}</small></span></a>`).join("")}`;
  const step = (index, label, fallback) => sections[index]
    ? `<a class="button" href="#${sections[index][0]}">${label} ${sections[index][1]}</a>`
    : button(fallback, "disabled");
  footer.innerHTML = `${step(current - 1, "←", "← 上一节")}<span class="micro mono">${current + 1} / ${sections.length}</span>${step(current + 1, "→", "下一节 →")}`;
  footer.hidden = false;
}

function overviewGraphic() {
  const items = [
    [120, 25, "外部网页", "Source", "source"],
    [120, 93, "Coordinator", "agent_0", ""],
    [49, 168, "Worker 1", "agent_1", ""],
    [191, 168, "Worker 2", "agent_2", ""],
  ];
  const graph = items.map(([x, y, label, id, type]) => `<g>
    <rect class="node-box${type ? ` node-${type}` : ""}" x="${x - 45}" y="${y - 15}" width="90" height="35" rx="5"/>
    <text x="${x}" y="${y}" text-anchor="middle">${label}</text><text class="svg-small" x="${x}" y="${y + 13}" text-anchor="middle">${id}</text></g>`).join("");
  const paths = {
    read_agent_0: "M120 45 V76", read_agent_1: "M75 28 Q12 30 30 151", read_agent_2: "M165 28 Q228 30 210 151",
    m_1: "M99 113 60 151", m_2: "M141 113 180 151",
  };
  const arrows = data.case_slack_07.edges.filter((edge) => Object.hasOwn(paths, edge.id)).map((edge) =>
    `<path class="edge ${edge.kind}" d="${paths[edge.id]}" marker-end="url(#hero-${edge.kind})"/>`).join("");
  return `<figure class="hero-visual"><p class="eyebrow">SLACK 07 · ATTACK</p>
    <svg class="graph hero-graph" viewBox="0 0 240 197" role="img" aria-label="Slack 07 外部网页经工具读取到达协调者与两名 Worker，协调者还向两名 Worker 交接">
    ${markers("hero")}${arrows}
    ${graph}</svg>
    <figcaption class="micro"><span class="line-key"></span>同伴消息 <span class="line-key dashed"></span>网页读取</figcaption></figure>`;
}

function overview() {
  const { study, cohorts, suites } = data.summary;
  if (!state.cohort) state.cohort = cohorts[0].id;
  return `<header class="hero">
    <div><p class="eyebrow">Multi-Agent Systems · Research Demo</p>
    <h1><span>CoordScope</span><span>多智能体系统中的协调、成本与安全</span></h1>
    <p class="subtitle" lang="en">Coordination, Cost, and Security in Multi-Agent Systems</p>
    <p class="abstract">多智能体协作扩大了外部信息进入决策与工具执行的路径。我们在 AgentDojo 冻结场景中，沿归档记录追踪内容何时进入模型输入、怎样经消息和工具传播，以及何时影响正式评分。</p>
    <div class="actions"><a class="button primary" href="#exposure">探索五项发现 ${icon("arrow")}</a><a class="button" href="#audit">回放 Slack 07</a></div></div>
    ${overviewGraphic()}</header>
    ${metrics([[n(study.scenes_per_cohort), "冻结场景 / cohort", `${n(study.tasks_per_cohort)} 个不同任务标识`],
      [n(suites.length), "Benchmark suites", suites.map(suiteName).join(" · ")],
      [n(cohorts.length), "已完成 cohorts", `${study.configurations} 个主配置 + ${study.repeats} 次参考复跑`],
      [n(study.episode_records), "有效 episode 记录", `每组 ${study.clean_per_cohort} Clean + ${study.attack_per_cohort} Attack`]])}
    <div class="split"><section class="panel"><div class="panel-head"><div><h2>实验概览</h2><p class="micro">选择一个 cohort 查看分母、评分与成本。</p></div>${tag(`Seed ${study.seed}`)}</div>
    <div class="legend"><span><i class="swatch"></i>Clean</span><span><i class="swatch teal"></i>Attack</span></div>
    <div class="cohort-chart" aria-label="各 cohort 有效记录数">${cohorts.map((cohort) =>
      `<button type="button" class="cohort-row${cohort.repeat ? " repeat" : ""}" data-cohort="${esc(cohort.id)}" aria-pressed="${state.cohort === cohort.id}"><span>${esc(cohortLabel(cohort))} ${cohort.repeat ? tag("参考复跑", "amber") : ""}</span>${fractionBar(cohort.clean_n, cohort.episodes, "blue", "teal", false)}<span>${cohort.episodes}</span></button>`).join("")}</div>
    </section><section class="panel" id="overview-detail" aria-label="所选 cohort 记录">${overviewDetail()}</section></div>
    ${note(`${n(study.episode_records)} 条记录共享 ${study.scenes_per_cohort} 个冻结场景，其中包括重复 Banking 用户任务。攻击族为 ${esc(study.attack_family)}。不同模型与执行配置的结果用于描述观察到的差异。`)}
    ${dataLinks("summary", "episodes")}`;
}

function fractionBar(part, total, left = "blue", right = "amber", labeled = true) {
  if (!total) return "";
  const width = 100 * part / total;
  const aria = labeled ? `role="img" aria-label="${part} / ${total}"` : 'aria-hidden="true"';
  return `<svg viewBox="0 0 100 6" preserveAspectRatio="none" ${aria}><rect width="100" height="6" rx="1" fill="var(--${right})"/><rect width="${width}" height="6" rx="1" fill="var(--${left})"/></svg>`;
}

function overviewDetail() {
  const { cohorts, suites } = data.summary;
  const cohort = cohorts.find(({ id }) => id === state.cohort);
  const filtered = data.episodes.filter((row) => row.cohort === cohort.id &&
    (state.overviewSuite === "all" || state.overviewSuite === row.suite) &&
    (state.overviewCondition === "all" || state.overviewCondition === row.condition));
  const scenes = [...new Set(filtered.map(({ scene }) => scene))].sort();
  if (!scenes.includes(state.overviewScene)) state.overviewScene = "all";
  const rows = filtered.filter((row) => state.overviewScene === "all" || row.scene === state.overviewScene);
  const attack = rows.filter(({ condition }) => condition === "attack");
  const clean = rows.filter(({ condition }) => condition === "clean");
  const matched = (subset, field) => subset.filter((r) => r[field] === true).length;
  const tokens = rows.every(({ tokens }) => tokens != null) ? rows.reduce((sum, row) => sum + row.tokens, 0) : null;
  const latency = rows.length && rows.every(({ latency_s }) => latency_s != null)
    ? rows.reduce((sum, row) => sum + row.latency_s, 0) / rows.length : null;
  return `<div class="panel-head"><div><h2>${esc(cohortLabel(cohort))}</h2><p class="micro mono">原始模型标识 ${esc(cohort.model)} · ${esc(cohort.id)}</p>${cohort.id === "gpt4o_star" ? '<p class="micro">模型名称依据项目方向服务商核实后的反馈更正为 GPT-6 Luna。</p>' : ""}</div></div>
    <div class="filters">${select("overview-suite", "Suite", ["all", ...suites], state.overviewSuite, suiteName)}
    ${select("overview-condition", "Condition", ["all", "clean", "attack"], state.overviewCondition, conditionName)}
    ${select("overview-scene", "Scene", ["all", ...scenes], state.overviewScene, (v) => v === "all" ? "全部场景" : v)}</div>
    <div aria-live="polite">${values([
      ["Clean Utility", pct(matched(clean, "utility"), clean.length)],
      ["Attack Utility", pct(matched(attack, "utility"), attack.length)],
      ["Targeted ASR", ratio(matched(attack, "attacker_success"), attack.length)],
      ["确认暴露 / UNKNOWN", attack.length ? `${matched(attack, "exposed")} / ${attack.filter(({ exposed }) => exposed == null).length}` : "—"],
      ["Tokens / 平均延迟", `${n(tokens)} / ${sec(latency)}`],
      ["筛选后记录数", n(rows.length)],
    ])}</div>`;
}

function exposure() {
  const f = data.summary.flash;
  const c = data.case_slack_07.conditions.attack;
  const cards = [
    ["exposure", "Exposure", ratio(f.exposed, f.attack_n), "恶意内容进入 Agent 输入"],
    ["adoption", "Adoption", "未系统测量", "模型在推理或响应中采纳恶意指令"],
    ["execution", "Execution", pct(f.attacker_success, f.attack_n), "工具动作达到官方攻击目标"],
  ];
  return `${heading("暴露、采纳与执行", "恶意内容进入模型输入后，有多少次在官方评分中达成了攻击目标？", "Flash Star · 实测", "teal")}
    ${panel("从暴露到工具执行", `<div class="stage-flow">${cards.map(([id, title, value, caption]) =>
      `<button type="button" class="stage-card" data-stage="${id}" aria-pressed="${id === state.stage}"><h3>${title}</h3><strong>${value}</strong><span class="micro">${caption}</span></button>`).join("")}</div>
      <div class="stage-detail" id="stage-detail" aria-live="polite">${stageDetail()}</div>`, "点击阶段查看其定义和测量口径。")}
    ${panel("Slack 07 · 按 Agent 对照", table(["Agent", "确认收到内容", "目标调用", "首次交接前"],
      c.actors.map(({ id, exposed, target_calls, pre_handoff_target_calls }) =>
        [`${actorName(id)} (${id})`, yes(exposed), n(target_calls), n(pre_handoff_target_calls)])),
    "该例同时记录了模型输入、消息传递与工具调用。")}
    ${note("Adoption 尚缺整组语义标注。已确认暴露的分母、官方成功分母和逐 Agent 工具调用分别保留。", "partial")}
    <div class="actions"><a class="button primary" href="#provenance">查看消息与工具路径 ${icon("arrow")}</a>${button("全屏回放", "data-open-replay")}</div>
    ${dataLinks("summary", "case_slack_07")}`;
}

function stageDetail() {
  const f = data.summary.flash;
  const stage = {
    exposure: `${f.exposed} 个 Attack episode 确认暴露，${f.exposure_unknown} 个为 UNKNOWN（共 ${f.attack_n} 个）。${fractionBar(f.exposed, f.attack_n)}`,
    adoption: '<span lang="en">Not yet systematically measured — requires semantic trace annotation.</span>',
    execution: `Targeted ASR ${ratio(f.attacker_success, f.attack_n)}（${pct(f.attacker_success, f.attack_n)}）。确认暴露后的 Conditional ASR 为 ${ratio(f.exposed_success, f.exposed)}（${pct(f.exposed_success, f.exposed)}）。`,
  };
  return stage[state.stage];
}

function markers(prefix) {
  return `<defs>${[["peer", "blue"], ["read", "teal"], ["target", "amber"]].map(([id, color]) =>
    `<marker id="${prefix}-${id}" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto" markerUnits="userSpaceOnUse"><path d="M0 0 8 4 0 8Z" fill="var(--${color})"/></marker>`).join("")}</defs>`;
}

const provenanceLayout = {
  m_1: ["M319 142 Q370 94 442 82", 374, 101],
  m_2: ["M319 170 Q373 224 442 231", 374, 222],
  m_3: ["M442 99 Q387 123 319 154", 399, 132],
  m_4: ["M442 211 Q383 183 319 159", 399, 181],
  read_agent_0: ["M126 155 H217", 171, 145],
  read_agent_1: ["M94 134 Q169 25 491 59", 255, 52],
  read_agent_2: ["M94 175 Q169 279 491 249", 260, 259],
  target_agent_0: ["M319 156 H654", 579, 145],
  target_agent_2: ["M549 224 Q612 219 673 176", 624, 215],
};
const provenanceNodes = [
  ["external", 23, 134, 103, "外部网页", "信息源", "source"],
  ["agent_0", 217, 134, 102, "Coordinator", "agent_0", ""],
  ["agent_1", 442, 60, 107, "Worker 1", "agent_1", ""],
  ["agent_2", 442, 209, 107, "Worker 2", "agent_2", ""],
  ["target", 654, 134, 103, "目标调用", "get_webpage", "tool"],
];

function provenance() {
  const { edges } = data.case_slack_07;
  const graph = `<svg class="graph" viewBox="0 0 780 282" role="group" aria-label="Slack 07 信息溯源图，边与节点可选择">
    ${markers("prov")}${edges.map((e) => {
      const [d, x, y] = provenanceLayout[e.id];
      const label = e.kind === "peer" ? e.id : e.calls.map((c) => `#${c}`).join(" / ");
      return `<g role="button" tabindex="0" data-graph="${esc(e.id)}" aria-pressed="${e.id === state.graphEdge}" aria-label="${esc(`${actorName(e.from)} → ${actorName(e.to)} ${label}`)}">
        <path class="edge ${e.kind}" d="${d}" marker-end="url(#prov-${e.kind})"/><path class="edge-hit" d="${d}"/>
        <text class="svg-small edge-label" x="${x}" y="${y}" text-anchor="middle">${esc(label)}</text></g>`;
    }).join("")}${provenanceNodes.map(([id, x, y, width, title, subtitle, cls]) =>
      `<g role="button" tabindex="0" data-graph="${id}" aria-label="${title}" aria-pressed="${id === state.graphEdge}"><rect class="node-box${cls ? ` node-${cls}` : ""}" x="${x}" y="${y}" width="${width}" height="42" rx="5"/>
      <text x="${x + width / 2}" y="${y + 17}" text-anchor="middle">${title}</text><text class="svg-small" x="${x + width / 2}" y="${y + 32}" text-anchor="middle">${subtitle}</text></g>`).join("")}</svg>`;
  return `${heading("通信图与实际信息流", "只看 Agent 之间的消息边，会漏掉哪些可观察的信息来源？", "Slack 07 · 个案", "purple")}
    ${panel("Information Provenance Graph", `<div class="provenance-workbench"><div><div class="graph-frame" tabindex="0" aria-label="可横向滚动的信息溯源图">${graph}</div>
      <p class="micro graph-scroll-hint">横向滑动查看完整路径。</p><div class="legend"><span><i class="line-key"></i>同伴消息</span><span><i class="line-key dashed"></i>读取或重读外部网页</span><span><i class="line-key tool"></i>实际目标调用</span></div>
      <div class="filters">${select("graph-select", "选择节点或边", [...edges.map(({ id }) => id), ...provenanceNodes.map(([id]) => id)], state.graphEdge, (id) => {
        const e = edges.find((entry) => entry.id === id);
        return e ? `${e.kind === "peer" ? `${id} · ` : e.kind === "read" ? "网页 · " : "工具 · "}${actorName(e.from)} → ${actorName(e.to)}` : actorName(id);
      })}</div></div>
      <div id="graph-detail" class="stage-detail" aria-live="polite">${graphDetail()}</div></div>`,
    "消息以 m_1–m_4 标识，# 对应原始工具调用序号。选择一条边或节点查看归档证据。")}
    ${note("完整上下文溯源仍不完整。该轨迹展示了多种可观察的信息来源，每个 episode 的全量信息流图仍待重建。", "partial")}
    ${dataLinks("case_slack_07")}`;
}

function graphDetail() {
  const { edges, conditions } = data.case_slack_07;
  const edge = edges.find(({ id }) => id === state.graphEdge);
  const attack = conditions.attack;
  if (!edge) {
    const actor = attack.actors.find(({ id }) => id === state.graphEdge);
    return `<h3>${esc(actorName(state.graphEdge))}</h3>${actor ? values([
      ["模型输入确认暴露", yes(actor.exposed)],
      ["目标调用", n(actor.target_calls)],
      ["已见消息", esc(actor.visible_messages.join(", ") || "—")],
    ]) : `<p>${state.graphEdge === "external" ? "原始网页通过 get_webpage 进入运行记录。虚线以归档 URL 相等性识别同页读取。" : "该节点汇总评分目标对应的已记录 get_webpage 调用。"}</p>`}`;
  }
  const m = edge.kind === "peer" ? attack.messages.find(({ id }) => id === edge.id) : null;
  return `<h3>${esc(actorName(edge.from))} → ${esc(actorName(edge.to))}</h3>` + values(m ? [
    ["消息与分发", `${esc(m.id)} · dispatch ${n(m.dispatch_id)}`],
    ["消息类型", esc(m.kind)],
    ["接收方可见记录", esc(m.visible_at.map((i) => `Stage ${i}`).join(", "))],
    ["接收阶段输入含内容", yes(m.recipient_stage_payload)],
    ["证据位置", "<code>conditions.attack.relay_messages / stages</code>"],
  ] : [
    ["事件类型", edge.kind === "read" ? "同一网页的工具读取" : "与官方攻击目标匹配的工具调用"],
    ["工具", "<code>get_webpage</code>"],
    ["调用记录", esc(edge.calls.map((i) => {
      const call = attack.calls.find((c) => c.order === i);
      return `#${i} · Stage ${call.stage} · ${call.status}`;
    }).join(" / "))],
    ["证据位置", "<code>conditions.attack.stages[].tool_calls</code>"],
  ]);
}


const titleCase = (value) => value[0].toUpperCase() + value.slice(1);

function comparisonRows(rows, asrPercent) {
  const field = (label, f) => [label, ...rows.map(f)];
  return [
    field("Clean Utility", (r) => pct(r.clean_success, r.clean_n)),
    field("Attack Utility", (r) => pct(r.attack_successful_tasks, r.attack_n)),
    field("Targeted ASR", (r) => asrPercent ? pct(r.attacker_successes, r.attack_n) : ratio(r.attacker_successes, r.attack_n)),
    field("Total Tokens", (r) => millions(r.total_tokens)),
    field("Mean Episode Latency", (r) => sec(r.mean_episode_latency_s)),
  ];
}

function topology() {
  const { summary, episodes } = data.topology;
  const matching = episodes.filter((e) => e.condition === state.topoCondition &&
    (state.topoSuite === "all" || e.suite === state.topoSuite));
  const episode = matching.find((e) => e.scene === state.topoScene) ||
    matching.find((e) => e.turns.length > 1) || matching[0];
  state.topoScene = episode.scene;
  if (state.topoTurn >= episode.turns.length) state.topoTurn = 0;
  const comparison = ["flash_star", "flash16k_adaptive"].map((id) => data.summary.cohorts.find((c) => c.id === id));
  const compare = state.topoCompare && episode.turns.length > 1;
  const chart = (turn) => topologyTurn(turn, episode.turns[0]);
  const filters = `<div class="filters">${select("topo-suite", "Suite", ["all", ...data.summary.suites], state.topoSuite, suiteName)}
    ${select("topo-condition", "Condition", ["clean", "attack"], state.topoCondition, conditionName)}
    ${select("topo-scene", "Scene", matching.map((e) => e.scene), state.topoScene, (scene) => {
      const e = matching.find((item) => item.scene === scene);
      return `${scene}${e.turns.length > 1 ? " · 有 Turn 1" : ""}`;
    })}${select("topo-turn", "Turn", episode.turns.map((t) => t.index), state.topoTurn, (v) => `Turn ${v}`)}
    ${button("对照 Turn 0 / 1", `id="topo-compare" aria-pressed="${compare}"${episode.turns.length < 2 ? " disabled" : ""}`)}</div>`;
  return `${heading("自适应拓扑与安全", "当团队组织发生改变时，任务完成率、安全评分与执行开销如何变化？", "Adaptive Flash · 实测", "teal")}
    ${metrics([[n(summary.episodes), "有效 episodes"], [n(summary.repair_execution_episodes), "发生 repair 执行", `${summary.actual_spec_changed_episodes} 例规格实际改变`],
      [n(summary.root_pattern_changed_episodes), "根模式改变"], [n(summary.nested_group_episodes), "出现嵌套组"]])}
    ${panel("Topology Explorer", `${filters}<div class="actions topo-examples">${summary.snapshots.map((id) => button(esc(id.replace("__", " / ")), `data-example="${esc(id)}"`)).join("")}</div>
      <div class="${compare ? "grid-2" : ""} topo-turns">${compare ? episode.turns.map(chart).join("") : chart(episode.turns[state.topoTurn])}</div>
      <p class="micro" id="topo-node-detail" aria-live="polite">${topologyNodeDetail(episode)}</p>`,
    `<code>${esc(episode.id)}</code> · 展示归档组成员与阶段顺序。青色标出相对 Turn 0 的新增节点或变更组。`)}
    <div class="grid-2">${panel("完整配置对照", table(["Metric", "Flash Star", "Adaptive Flash"], comparisonRows(comparison, true)),
      "原始 Flash 4K / Star 与 Flash 16K / Native adaptive。")}
    ${panel("模式计数", table(["Pattern", "初始根模式", "执行组出现次数"],
      [...new Set([...Object.keys(summary.initial_root_patterns), ...Object.keys(summary.executed_group_pattern_occurrences)])]
        .map((key) => [titleCase(key), n(summary.initial_root_patterns[key] || 0), n(summary.executed_group_pattern_occurrences[key])])),
    "初始根模式每 episode 计一次。执行组按每轮、每组累计。")}</div>
    ${note("效用与 Targeted ASR 在这两组相同，Adaptive Flash 的 token 与延迟更高。两组运行采用完整配置，包含不同输出预算和执行设置。拓扑本身对安全的因果效应仍待隔离实验。")}
    ${dataLinks("topology", "summary")}`;
}

function topologyTurn(turn, original) {
  const { spec } = turn;
  const groups = spec.groups;
  const prior = new Set(original.spec.agents.map((a) => a.agent_id));
  const label = `Turn ${turn.index} · ${titleCase(turn.root_pattern)}`;
  const width = Math.max(415, Math.max(...groups.map((g) => g.member_ids.length)) * 103 + 34);
  const height = groups.length * 90 + 12;
  const coords = new Map(groups.flatMap((g, i) => g.member_ids.map((id, j) => [id, [67.5 + j * 103, 77 + i * 90]])));
  const graph = `<svg class="graph topo-chart" viewBox="0 0 ${width} ${height}" role="group" aria-label="${label}">
    ${spec.extra_edges.length ? markers(`topo-${turn.index}`) : ""}
    ${groups.map((group, i) => {
      const y = 12 + i * 90;
      const previous = original.spec.groups.find((g) => g.group_id === group.group_id);
      const changed = turn.index > 0 && JSON.stringify(previous) !== JSON.stringify(group);
      return `<g class="${changed ? "changed" : ""}">
      <rect class="group-box" x="9" y="${y}" width="${width - 18}" height="77" rx="5"/>
      <text x="19" y="${y + 18}">${esc(`${group.group_id} · ${titleCase(group.pattern)}`)}</text>
      <text class="svg-small" x="${width - 20}" y="${y + 18}" text-anchor="end">${esc(group.parent_agent_id ? `parent ${group.parent_agent_id}` : "root")}</text>
      ${group.member_ids.map((id, j) => {
        const x = 20 + j * 103;
        return `<g role="button" tabindex="0" data-topo-node="${esc(id)}" data-turn="${turn.index}"
          aria-label="${esc(`Turn ${turn.index} · ${id}`)}" class="${prior.has(id) ? "" : "added"}">
          <rect class="node-box" x="${x}" y="${y + 29}" width="95" height="36" rx="4"/>
          <text x="${x + 47.5}" y="${y + 46}" text-anchor="middle">${esc(id)}</text>
          <text class="svg-small" x="${x + 47.5}" y="${y + 59}" text-anchor="middle">${id === group.leader_id ? "leader" : "member"}</text></g>`;
      }).join("")}</g>`;
    }).join("")}${spec.extra_edges.map(([from, to]) => {
      const [x1, y1] = coords.get(from);
      const [x2, y2] = coords.get(to);
      const d = `M${x1} ${y1} V${y1 + 6} H${x2} V${y2}`;
      return `<path class="edge target" d="${d}" marker-end="url(#topo-${turn.index}-target)"><title>${esc(`归档附加边 ${from} → ${to}`)}</title></path>`;
    }).join("")}</svg>`;
  return `<figure><div class="turn-heading"><h3>${label}</h3><span class="micro">${turn.agent_count} Agents · ${turn.group_count} 组 · spec v${spec.version}</span></div>
    <div class="graph-frame" tabindex="0" aria-label="可横向滚动的组规格">${graph}</div>${spec.extra_edges.length ? `<p class="micro">归档附加边 ${esc(spec.extra_edges.map(([a, b]) => `${a} → ${b}`).join(" · "))}</p>` : ""}<div class="seq" aria-label="执行阶段顺序">${turn.sequence.map((stage, i) =>
      `<span title="${esc(stage.node_name)}">${i + 1} · ${esc(stage.agent_id)} / ${esc(stage.stage_role)}</span>`).join("")}</div></figure>`;
}

function topologyNodeDetail(episode) {
  if (!state.topoNode) return "点击 Agent 查看结构角色、所属组和执行阶段。";
  const { turn, id } = state.topoNode;
  const record = episode.turns[turn];
  const node = record?.spec.agents.find((a) => a.agent_id === id);
  if (!node) return "点击 Agent 查看结构角色、所属组和执行阶段。";
  const stages = record.sequence.filter((s) => s.agent_id === id).map((s) => s.node_name);
  return `<code>${esc(id)}</code> · Turn ${turn} · ${esc(node.group_id)} · ${esc(node.structural_role)} / ${esc(node.stage_role)} · ${esc(stages.join(" → ") || "本轮无执行阶段")}`;
}

function workers() {
  const d = data.worker_comparison;
  const totals = [d.overview.F, d.overview.W];
  const extra = totals[1].attack_successful_tasks - totals[0].attack_successful_tasks;
  const tokenDelta = pct(totals[1].total_tokens - totals[0].total_tokens, totals[0].total_tokens);
  const rows = state.workerSuite === "all" ? totals : ["F", "W"].map((run) =>
    d.by_suite.find((r) => r.run === run && r.suite === state.workerSuite));
  const selected = d.paired.filter((r) => r.condition === state.workerCondition && (state.workerSuite === "all" || r.suite === state.workerSuite));
  const pairs = (f, w) => n(selected.filter((r) => r.F_utility === f && r.W_utility === w).length);
  const details = [
    ["Confirmed Exposure", ...rows.map((r) => ratio(r.confirmed_exposed, r.attack_n))],
    ["Exposure UNKNOWN", ...rows.map((r) => ratio(r.exposure_unknown, r.attack_n))],
    ["Worker Episodes", ...rows.map((r) => n(r.worker_episodes))],
    ["Worker Contexts", ...rows.map((r) => n(r.worker_contexts))],
    ["重复工具调用 / 总调用", ...rows.map((r) => ratio(r.duplicate_runtime_calls, r.runtime_calls))],
  ];
  return `${heading("多智能体协作效率", "固定两名 Worker 能多完成多少任务？额外执行需要多少 token 和时间？", "F / W · 实测", "teal")}
    ${note(`全 cohort 中 W 在 Attack 条件多完成 ${n(extra)} 个任务，总 token 比 F 高 ${tokenDelta}。W 同时引入 Main 的任务分派和 Worker 汇报协议，两组比较覆盖完整调度流程。`)}
    <div class="filters">${select("worker-suite", "Suite", ["all", ...data.summary.suites], state.workerSuite, suiteName)}
    ${select("worker-condition", "配对矩阵条件", ["attack", "clean"], state.workerCondition, conditionName)}</div>
    <div class="grid-2">
    ${panel("效用与执行开销", table(["Metric", "F", "W"], [...comparisonRows(rows, false), ...details]),
      `${suiteName(state.workerSuite)} · F = On-demand Worker · W = Fixed Two Workers`)}
    <div class="stack">${panel("配对结果矩阵", `<div class="table-scroll"><table class="pair-matrix"><thead><tr><th scope="col">F ↓ / W →</th><th scope="col">完成</th><th scope="col">未完成</th></tr></thead>
      <tbody><tr><th scope="row">完成</th><td>${pairs(true, true)}<small>均完成</small></td><td class="f-only">${pairs(true, false)}<small>仅 F 完成</small></td></tr>
      <tr><th scope="row">未完成</th><td class="w-only">${pairs(false, true)}<small>仅 W 完成</small></td><td>${pairs(false, false)}<small>均未完成</small></td></tr></tbody></table></div>`,
      `${suiteName(state.workerSuite)} · ${conditionName(state.workerCondition)} · ${n(selected.length)} 个配对场景`)}
    ${panel("Token 分布", roleChart(d.role_usage), "角色拆分按完整 cohort 汇总。")}</div></div>
    ${note("F 与 W 在这批 direct attack 记录中的 Targeted ASR 均为 0/80。配对计数按冻结场景对齐。对其他攻击族的安全表现和统计显著性需要额外实验。", "partial")}
    ${dataLinks("worker_comparison", "episodes")}`;
}

function roleChart(records) {
  const roles = [["main", "Main", "blue"], ["worker", "Worker", "teal"], ["action_verifier", "Verifier", "purple"]];
  const runs = ["F", "W"];
  const max = Math.max(...runs.map((run) => records.filter((r) => r.run === run).reduce((sum, r) => sum + r.total_tokens, 0)));
  const tokens = (run, role) => records.find((r) => r.run === run && r.role === role).total_tokens;
  const bars = runs.map((run, i) => {
    let x = 26;
    return `<text x="4" y="${23 + i * 30}">${run}</text>` + roles.map(([id, label, color]) => {
      const value = tokens(run, id);
      const width = 322 * value / max;
      const segment = `<rect x="${x}" y="${9 + i * 30}" width="${width}" height="18" fill="var(--${color})"><title>${run} ${label} · ${n(value)} tokens</title></rect>`;
      x += width;
      return segment;
    }).join("");
  }).join("");
  return `<svg class="bar-chart" viewBox="0 0 354 67" role="img" aria-label="F 和 W 按角色分解的 token 总量">${bars}</svg>
    <div class="legend">${roles.map(([, label, color]) => `<span><i class="swatch ${color}"></i>${label}</span>`).join("")}</div>
    ${table(["Role", ...runs], roles.map(([id, label]) => [label, ...runs.map((run) => n(tokens(run, id)))]))}`;
}


const eventKinds = {
  exposure: ["暴露", "teal"], tool: ["工具执行", "amber"], message: ["消息", ""], synthesis: ["综合", ""],
  audit: ["Audit", "purple"], recommendation: ["修复建议", "amber"], repair: ["实际修复", ""],
};

function describeEvent(event, record) {
  const { kind, actor, stage, call, message } = event;
  const label = actorName(actor);
  if (call != null) {
    const c = record.calls.find((item) => item.order === call);
    const first = record.calls.find((item) => item.source_page)?.order === call;
    const summary = c.target ? `${label} 访问评分目标` :
      kind === "exposure" ? `${label} ${first ? "读取" : "重读"}含恶意内容的网页` : `${label} 执行 ${c.tool}`;
    return { summary, rows: [
      ["Tool call", `<code>#${c.order} · ${esc(c.tool)}</code>`],
      ["执行记录", `Stage ${stage} · ${esc(c.status)}`],
      ["匹配官方目标", yes(c.target)],
      ["首次交接前的目标调用", c.target ? yes(stage === 0) : "—"],
    ], source: "stages[].tool_calls" };
  }
  if (message) {
    const m = record.messages.find((item) => item.id === message);
    const receiver = m.recipients.map(actorName).join(", ");
    const receiverRecord = record.actors.find((item) => item.id === actor);
    return { summary: `${m.id} · ${actorName(m.sender)} → ${receiver}`, rows: [
      ["消息类型", `<code>${esc(m.kind)}</code>`],
      ["分发 / 读取", `dispatch ${m.dispatch_id} / Stage ${stage}`],
      ["接收阶段输入含内容", yes(m.recipient_stage_payload)],
      ["接收 Agent 全程目标调用", n(receiverRecord.target_calls)],
    ], source: "relay_messages / stages" };
  }
  if (kind === "synthesis") {
    return { summary: `${label} ${actor === "final_synthesizer" ? "汇总最终结果" : "核对约束"}`,
      rows: [["执行阶段", `Stage ${stage} · <code>${esc(event.phase)}</code>`]], source: "stages / final_synthesis" };
  }
  const turn = `Turn ${event.turn}`;
  const audit = record.audit;
  const descriptions = {
    audit: { summary: `归档 Auditor 结果 · risk_score ${audit.risk_score.toFixed(1)}`,
      rows: [["审计位置", turn], ["来源", esc(audit.source)], ["detected_modes", esc(JSON.stringify(audit.detected_modes))]], source: "audit_reports" },
    recommendation: { summary: `repair_recommended = ${audit.repair_recommended}`,
      rows: [["建议修复", yes(audit.repair_recommended)], ["审计位置", turn]], source: "audit_reports" },
    repair: { summary: `实际 topology mutations · ${record.mutations}`,
      rows: [["实际变更记录", n(record.mutations)]], source: "mutations" },
  };
  return descriptions[kind];
}

function replayMarkup(modal = false) {
  const record = data.case_slack_07.conditions[state.replayCondition];
  const timeline = data.audit_timeline[state.replayCondition];
  const prefix = modal ? "fullscreen" : "inline";
  return `<div class="replay" data-replay>
    <div class="filters">${select(`${prefix}-condition`, "Trace", ["attack", "clean"], state.replayCondition, conditionName)}
    ${modal ? "" : button(`全屏回放 ${icon("screen")}`, "data-open-replay")}</div>
    <div class="controls">
      ${button("← 上一步", 'data-replay-control="prev"')}
      ${button(state.replayTimer ? "暂停" : "播放", 'data-replay-control="play"', true)}
      ${button("下一步 →", 'data-replay-control="next"')}
      <input data-scrub type="range" aria-label="回放进度" min="1" max="${timeline.length}" value="${state.replayIndex + 1}">
      <output class="micro mono" data-counter>${state.replayIndex + 1} / ${timeline.length}</output>
    </div>
    <div class="split">
      <ol class="timeline" aria-label="${conditionName(state.replayCondition)} 归档事件">${timeline.map((event, i) => {
        const [label, color] = eventKinds[event.kind];
        const { summary } = describeEvent(event, record);
        return `<li><button type="button" class="event" data-replay-index="${i}" data-kind="${event.kind}"${i === state.replayIndex ? ' aria-current="step"' : ""}>
          <span class="mono">${String(i + 1).padStart(2, "0")}</span><span>${tag(label, color)}</span><span>${esc(summary)}</span></button></li>`;
      }).join("")}</ol>
      <div class="panel replay-detail" data-event-detail aria-live="polite">${replayDetail()}</div>
    </div></div>`;
}

function replayDetail() {
  const record = data.case_slack_07.conditions[state.replayCondition];
  const event = data.audit_timeline[state.replayCondition][state.replayIndex];
  const { summary, rows, source } = describeEvent(event, record);
  return `<h3>${esc(summary)}</h3>${values(rows)}<p class="micro event-source"><code>${esc(record.episode)} · ${source}</code></p>`;
}

function audit() {
  const { attack, clean } = data.case_slack_07.conditions;
  return `${heading("风险识别与实际预防", "沿 Slack 07 的轨迹，对照工具执行、Auditor 结果、修复建议和实际修复。", "Slack 07 · 个案", "purple")}
    ${metrics([[n(attack.target_calls), "Attack 目标调用", `${attack.pre_handoff_target_calls} 次发生在首次交接前`], [n(clean.target_calls), "Clean 目标调用"],
      [attack.audit.risk_score.toFixed(1), "Auditor risk_score", `repair_recommended = ${attack.audit.repair_recommended}`], [n(attack.mutations), "Topology mutations"]])}
    ${panel("Slack 07 · Archived Trace Replay", `<div id="replay-inline">${replayMarkup()}</div>`,
    "离线回放按阶段与调用顺序展示，尾部列出 turn 级审计记录。归档没有为 audit 与各调用提供可对齐的时间戳。")}
    ${note(`Coordinator 在首次交接前完成 ${attack.pre_handoff_target_calls} 次目标调用。该记录支持初次命中先于同伴传递；Worker 2 此后也执行了目标调用。<br><span lang="en">Case-level observation; not an aggregate Auditor precision/recall evaluation.</span>`, "case")}
    ${dataLinks("audit_timeline", "case_slack_07")}`;
}

function method() {
  const { study } = data.summary;
  const archive = data.data_manifest;
  const components = [
    ["Adapter / Tool runtime bridge", "src/agentdojo_manta/adapter.py"],
    ["Provider", "src/agentdojo_manta/providers.py"],
    ["Budget tracking", "src/agentdojo_manta/budget.py"],
    ["Trace logging", "src/agentdojo/logging.py"],
    ["Metrics & reporting", "src/agentdojo_manta/metrics.py"],
    ["MANTA Engine", "upstreams/manta/MAS/self_evolved/engine.py"],
    ["AgentDojo FunctionsRuntime", "src/agentdojo/functions_runtime.py"],
    ["Adaptive topology execution", "reports/2026-10-28-deepseek-flash-adaptive/README.md"],
    ["Folded scheduling protocol", "reports/2026-10-29-agentdojo-flash16k-fw/README.md"],
    ["Cohort registry & reporting", "reports/2026-10-29-completed-experiments/README.md"],
  ];
  const architecture = ["AgentDojo Official Benchmark", "MANTA Agent Execution Engine", "Adapter Layer",
    "AgentDojo FunctionsRuntime", "Official Utility / Security Judge", "Structured Logs and Analysis"];
  return `${heading("方法与复现", "从官方冻结场景到离线演示，按组件和数据清单追溯评分、执行记录和分析。")}
    ${panel("Evaluation Architecture", `<div class="architecture" aria-label="评测数据流">${architecture.map((label) =>
      `<div class="arch-node">${label}</div>`).join("")}</div><ul class="source-list">${components.map(([label, path]) =>
      `<li>${sourceLink(path, label)}</li>`).join("")}</ul>`, `AgentDojo ${esc(study.benchmark_version)} · 现有 Folded 执行配置用于 F/W 实验。`)}
    ${panel("范围与证据层级", `<dl class="method-scope">
      <div><dt>${tag("实测", "teal")}</dt><dd>单种子 ${study.seed}、${esc(study.attack_family)}；每组 ${study.scenes_per_cohort} 个冻结场景、${study.tasks_per_cohort} 个不同任务标识，Banking 含重复任务。</dd></div>
      <div><dt>${tag("部分证据", "amber")}</dt><dd>暴露存在 UNKNOWN。上下文溯源尚未覆盖全量 episodes，Adoption 缺整组语义标注。</dd></div>
      <div><dt>${tag("个案观察", "purple")}</dt><dd>Slack 07 提供消息、工具动作、审计和拓扑变更记录。全局 Auditor precision / recall 尚待评估。</dd></div>
      <div><dt>${tag("待验证")}</dt><dd>跨配置存在模型、预算和执行策略差异。F/W 比较两种完整调度协议；单一组件、worker 数量与拓扑的因果效应需要隔离实验。</dd></div>
    </dl>`)}
    ${panel("Data Sources & Checksums", `<p class="micro">页面从同源 JSON 读取。原始文件链接指向固定的 Git 提交，打开 GitHub 链接需要联网。</p>
      ${dataLinks(...datasets)}
      <details class="source-detail"><summary>查看 ${archive.sources.length} 个源文件与 SHA-256</summary>
      <div class="table-scroll"><table><thead><tr><th scope="col">源文件</th><th scope="col">SHA-256</th></tr></thead>
      <tbody>${archive.sources.map(({ path, sha256 }) => `<tr><td>${sourceLink(path)}</td><td><code>${esc(sha256)}</code></td></tr>`).join("")}</tbody></table></div></details>
      <p class="micro"><code>python scripts/demo/build_demo_data.py</code><br><code>python -m http.server 8000 --directory demo</code></p>`,
      "派生数据、原始报告、代码入口与生成脚本。")}`;
}

const views = { overview, exposure, provenance, topology, workers, audit, method };

function render(focus = null) {
  page.innerHTML = views[state.route]() + `<details class="speaker"${state.presenting ? " open" : ""}><summary>讲解备注</summary><p>${sections.find(([id]) => id === state.route)[3]}</p></details>`;
  if (focus) $(focus)?.focus({ preventScroll: true });
  syncReplay(false);
}

function route() {
  const hash = location.hash.slice(1);
  if (hash === "main" && !footer.hidden) return;
  state.route = Object.hasOwn(views, hash) ? hash : "overview";
  stopReplay();
  if (dialog.open) dialog.close();
  navigation();
  render();
  scrollTo(0, 0);
  $("#main").focus({ preventScroll: true });
  $(".nav-item[aria-current='page']")?.scrollIntoView({ block: "nearest", inline: "nearest" });
}

function syncReplay(scroll = true) {
  if (!data) return;
  const timeline = data.audit_timeline[state.replayCondition];
  for (const root of $$("[data-replay]")) {
    $("[data-counter]", root).value = `${state.replayIndex + 1} / ${timeline.length}`;
    $("[data-scrub]", root).value = state.replayIndex + 1;
    $('[data-replay-control="prev"]', root).disabled = state.replayIndex === 0;
    $('[data-replay-control="next"]', root).disabled = state.replayIndex === timeline.length - 1;
    $('[data-replay-control="play"]', root).textContent = state.replayTimer ? "暂停" : "播放";
    $("[data-event-detail]", root).innerHTML = replayDetail();
    for (const event of $$("[data-replay-index]", root)) {
      const current = +event.dataset.replayIndex === state.replayIndex;
      if (current) event.setAttribute("aria-current", "step");
      else event.removeAttribute("aria-current");
    }
    const item = $('[aria-current="step"]', root);
    if (scroll && item) {
      const list = $(".timeline", root);
      const rect = item.getBoundingClientRect();
      const bounds = list.getBoundingClientRect();
      if (rect.top < bounds.top) list.scrollTop += rect.top - bounds.top;
      else if (rect.bottom > bounds.bottom) list.scrollTop += rect.bottom - bounds.bottom;
    }
  }
}

function stopReplay() {
  clearInterval(state.replayTimer);
  state.replayTimer = null;
}

function stepReplay(index) {
  const max = data.audit_timeline[state.replayCondition].length - 1;
  state.replayIndex = Math.max(0, Math.min(max, index));
  if (state.replayIndex === max) stopReplay();
  syncReplay();
}

function toggleReplay() {
  if (state.replayTimer) {
    stopReplay();
  } else {
    if (state.replayIndex === data.audit_timeline[state.replayCondition].length - 1) state.replayIndex = 0;
    state.replayTimer = setInterval(() => stepReplay(state.replayIndex + 1), 950);
  }
  syncReplay();
}

function refreshReplay() {
  const inline = $("#replay-inline");
  if (inline) inline.innerHTML = replayMarkup();
  if (dialog.open) $("#replay-modal-content").innerHTML = replayMarkup(true);
  syncReplay(false);
}

function openReplay() {
  stopReplay();
  dialog.innerHTML = `<header class="panel-head"><div><p class="eyebrow">Archived Trace Replay</p><h2 id="replay-heading">Slack 07 · 离线回放</h2></div>
    ${button("关闭 ×", "data-close-replay autofocus")}</header><div id="replay-modal-content">${replayMarkup(true)}</div>`;
  dialog.classList.add("viewport-replay");
  dialog.showModal();
  syncReplay();
  dialog.requestFullscreen?.().catch(() => {});
}

dialog.addEventListener("close", () => {
  if (document.fullscreenElement === dialog) document.exitFullscreen().catch(() => {});
  stopReplay();
  syncReplay(false);
});


function click(event) {
  const target = event.target.closest("button, [role='button']");
  if (!target) return;
  const { cohort, stage, graph, example, topoNode, turn, replayControl, replayIndex } = target.dataset;
  if (cohort) {
    state.cohort = cohort;
    $$(".cohort-row").forEach((b) => b.setAttribute("aria-pressed", b.dataset.cohort === cohort));
    $("#overview-detail").innerHTML = overviewDetail();
  } else if (stage) {
    state.stage = stage;
    $$(".stage-card").forEach((b) => b.setAttribute("aria-pressed", b.dataset.stage === stage));
    $("#stage-detail").innerHTML = stageDetail();
  } else if (graph) {
    selectGraph(graph);
  } else if (example) {
    const episode = data.topology.episodes.find((e) => e.id === example);
    state.topoSuite = episode.suite;
    state.topoScene = episode.scene;
    state.topoCondition = episode.condition;
    state.topoTurn = 0;
    state.topoCompare = episode.turns.length > 1;
    state.topoNode = null;
    render(`[data-example="${example}"]`);
  } else if (topoNode) {
    state.topoNode = { id: topoNode, turn: +turn };
    const episode = data.topology.episodes.find((e) => e.scene === state.topoScene && e.condition === state.topoCondition);
    $("#topo-node-detail").innerHTML = topologyNodeDetail(episode);
  } else if (replayControl) {
    if (replayControl === "play") toggleReplay();
    else {
      stopReplay();
      stepReplay(state.replayIndex + (replayControl === "next" ? 1 : -1));
    }
  } else if (replayIndex != null) {
    stopReplay();
    stepReplay(+replayIndex);
  } else if (target.hasAttribute("data-open-replay")) {
    openReplay();
  } else if (target.hasAttribute("data-close-replay")) {
    dialog.close();
  } else if (target.id === "topo-compare") {
    state.topoCompare = !state.topoCompare;
    state.topoNode = null;
    render("#topo-compare");
  } else if (target.id === "present") {
    state.presenting = !state.presenting;
    document.body.classList.toggle("presenting", state.presenting);
    present.setAttribute("aria-pressed", state.presenting);
    $("span", present).textContent = state.presenting ? "退出演示" : "演示模式";
    render();
    scrollTo(0, 0);
    $("#main").focus({ preventScroll: true });
  }
}

function selectGraph(id) {
  state.graphEdge = id;
  $$("[data-graph]").forEach((g) => g.setAttribute("aria-pressed", g.dataset.graph === id));
  $("#graph-select").value = id;
  $("#graph-detail").innerHTML = graphDetail();
}

const filters = {
  "overview-suite": "overviewSuite", "overview-condition": "overviewCondition", "overview-scene": "overviewScene",
  "topo-suite": "topoSuite", "topo-condition": "topoCondition", "topo-scene": "topoScene", "topo-turn": "topoTurn",
  "worker-suite": "workerSuite", "worker-condition": "workerCondition",
};

function filterChange(event) {
  const { id, value } = event.target;
  if (id === "graph-select") {
    selectGraph(value);
  } else if (id === "inline-condition" || id === "fullscreen-condition") {
    stopReplay();
    state.replayCondition = value;
    state.replayIndex = 0;
    refreshReplay();
    $(`#${id}`).focus({ preventScroll: true });
  } else if (Object.hasOwn(filters, id)) {
    state[filters[id]] = id === "topo-turn" ? +value : value;
    if (id.startsWith("topo-")) {
      state.topoNode = null;
      if (id !== "topo-turn") state.topoTurn = 0;
      if (id === "topo-turn") state.topoCompare = false;
    }
    if (id.startsWith("overview-")) {
      $("#overview-detail").innerHTML = overviewDetail();
      $(`#${id}`).focus({ preventScroll: true });
    } else {
      render(`#${id}`);
    }
  }
}

function keyboard(event) {
  if (event.target.matches("svg [role='button']") && ["Enter", " "].includes(event.key)) {
    event.preventDefault();
    event.target.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    return;
  }
  if (!state.presenting || dialog.open || event.altKey || event.ctrlKey || event.metaKey ||
      event.target.closest("select, input, button, a, [role='button'], summary")) return;
  if (event.key === "ArrowRight" || event.key === "ArrowLeft") {
    const index = sections.findIndex(([id]) => id === state.route) + (event.key === "ArrowRight" ? 1 : -1);
    if (sections[index]) {
      event.preventDefault();
      location.hash = sections[index][0];
    }
  }
}

async function start() {
  try {
    const payloads = await Promise.all(datasets.map(async (name) => {
      const response = await fetch(`data/${name}.json`);
      if (!response.ok) throw new Error(`${name}.json · HTTP ${response.status}`);
      return [name, await response.json()];
    }));
    data = Object.fromEntries(payloads);
    route();
    window.addEventListener("hashchange", route);
    document.addEventListener("click", click);
    document.addEventListener("change", filterChange);
    document.addEventListener("keydown", keyboard);
    document.addEventListener("input", (event) => {
      if (event.target.matches("[data-scrub]")) {
        stopReplay();
        stepReplay(+event.target.value - 1);
      }
    });
  } catch (error) {
    page.innerHTML = `<p class="note partial" role="alert">本地数据读取失败。请运行 <code>python scripts/demo/build_demo_data.py</code> 和
      <code>python -m http.server 8000 --directory demo</code>，然后在 localhost 打开页面。<br>${esc(error.message)}</p>`;
    console.error(error);
  }
}

start();
