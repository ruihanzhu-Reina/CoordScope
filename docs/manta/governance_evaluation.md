# CoordScope 授权边界升级：benchmark、baseline、指标与理想主表

日期：2026-11-26。本文是调研与实验设计，未启动模型实验、未改运行时代码、未复现外部论文分数。源码可用性仅核对公开仓库、README/接口说明和读取时的 commit，不等于运行复现或完整安全审计。

## 1. 结论与实际实现边界

优先做 **AgentDojo 主实验 + AgentDyn 动态任务泛化**。AgentDojo 能复用当前 adapter 与官方环境状态评分；AgentDyn 直接检验“严格授权是否妨碍必须依据外部信息调整的合法工作流”。三类基线足够：**当前 Folded + per-action judge、ToolFence 官方实现、CaMeL**。Multi-CaMeL 作为第三类的跨 worker 边界扩展，避免在第一轮同时更换执行架构和安全机制。

按主线程已确认的实际实现，新增机制为：统一可信 tool manifest；独立 compiler 初始化**完整参数 exact capability**；未知动作送隔离 judge，host 固定为精确、单次 grant；可选 JSON Pointer 字段证据校验；task-local monitor；全局版本与串行 dispatch；锁外 review、执行前复检；receipt 与 sticky UNKNOWN。保留只读 workers 和 legacy 开关。

**本版没有完整的 derived policy 模板、自动参数 taint、资源级并发、Z3 或形式验证。** 因而不能把预期包装为完整 ToolFence/CaMeL 的实现，也不能主张消除了语义误授权、保证数据来源正确、支持安全并发。judge 误批一个具体恶意动作后，精确 capability 仍会忠实授权该动作；它限制的是批准后的漂移、复用、跨任务污染与执行边界绕过。

最合适的两项待验证结论：

1. **授权后不漂移**：即使 agent 提议被注入污染，host 确认的动作边界不会因参数更换、伪造证据、重复提交、跨任务复用或未知执行结果而被扩大。证明靠确定性边界测试与实际 dispatch 记录；prompt-injection ASR 只能补充，不能代替这项机制证据。
2. **安全约束保留实际效用**：相对当前 F，复杂合法任务的完成率与成本保持接近，同时更完整地给出授权、执行、异常结果的可核查证据。若动态任务效用明显下降，应解释为 exact 预授权不足或 review/恢复负担，而非声称越严格越好。

## 2. 已有 F/W 数值：可作为锚点，不能拿来证明新增防御

直接读取以下公开归档：

- [F/W 公开归档](../../reports/2026-10-29-agentdojo-flash16k-fw/README.md)
- 同目录 `overview.csv`、`role_usage.csv`、`fw_paired.csv`、`manifest_common.json`。

该归档为 AgentDojo v1.2.2、deepseek-flash、最大输出 16,384 token、seed 42；每组 80 clean + 80 direct attack。两组代码版本/资源上限一致；F 按需启动只读 worker，W 在 main 分派后固定执行两个真实只读 worker。**W 是包含分派与汇报的调度协议对照，不是一般动态拓扑重连的纯消融。** 归档 manifest 的 prepared 状态是预备清单字段，完成结果来自 README/逐条结果，不应将清单字段误读为未执行。

| 系统 | Clean | Attack utility | Attacker success | Safe completion | 总 token / 160 episodes | 平均 episode 时延 | Worker episodes |
|---|---:|---:|---:|---:|---:|---:|---:|
| F / on-demand，已测 | 72/80，90.00% | 71/80，88.75% | 0/80 | 71/80 | 7,137,951 | 29.90 s | 2/160 |
| W / fixed-two，已测 | 73/80，91.25% | 75/80，93.75% | 0/80 | 75/80 | 13,142,142 | 61.92 s | 160/160 |

W 相对 F 多完成 4 个受攻击任务，总 token +84.12%，平均时延约 2.07 倍。两组各 76 条确认看到攻击、4 条 exposure UNKNOWN。**0/80 是此配置与攻击的观测结果，不是零风险保证**；若粗略把 80 次当独立 Bernoulli，零成功的一侧 95% 上界约 3.68%，真实任务相关性还会影响解释。确认暴露子集应另外报告 0/76，而不能悄悄丢弃 4 UNKNOWN。

F 的 verifier 为 263,492 tokens / 196 requests，占 F 总 token **3.69%**。在其它行为完全相同、compiler 零成本的虚构上限下，删掉全部 verifier 也只能节省 3.69%；实际还要付 compiler、grant、证据上下文成本。故不应承诺总 token 大降。未实施的 shape reuse/cache 更不能作为节省依据。

## 3. 一张理想主结果表

以下是**同一旧 80 对场景、同 backbone/预算下的设计目标，绝非实测结果、模型预测分布或置信区间**。老分数只是历史锚点；正式比较要同时重跑 legacy F 和新版，不能假定服务端模型从 10 月到 11 月完全未变。新增系统行在论文主结果中应等真实运行后再填。

| 系统 / 证据状态 | Clean ↑ | Attack utility ↑ | ASR ↓ | Safe completion ↑ | 总 token ↓ | 主要解释 |
|---|---:|---:|---:|---:|---:|---|
| F，历史已测 | 72/80 | 71/80 | 0/80 | 71/80 | 7.138 M，1.00×F | 当前最直接控制组 |
| W，历史已测 | 73/80 | 75/80 | 0/80 | 75/80 | 13.142 M，1.84×F | 调度协议参考，不是新增授权方法的竞争者 |
| 新版 exact-governed F，**理想目标** | **72–74/80** | **71–75/80** | **保持观测 0/80** | **71–75/80** | **7.14–8.21 M，1.00–1.15×F** | 先保效用、强化边界；72–75 attack 是更积极的 stretch 目标 |
| ToolFence，**待同配置实测** | — | — | — | — | — | 不搬用论文的模型/任务/攻击不同分数 |
| CaMeL，**待同配置实测** | — | — | — | — | — | 强信息流基线，执行架构不同，需披露适配 |

为何区间这样定：旧 F 已有 90% clean / 88.75% attack，简单 direct ASR 已饱和；新机制主要限制授权后的变化，而非新增任务求解能力。清洁效用保持、少量恢复改进是合理工程目标；0.00–5.00 个百分点的 attack utility 提高只是希望。每 1 例就是 1.25 pp，80 例的 1–4 例增益很可能不足以证明稳定提升。**新版也完全可能因 compiler 过严而低于 71/80；那是必须报告的失败，不应改变任务选择来满足目标。**

在 AgentDyn 或新攻击集没有同配置 baseline 时，只给相对目标：clean utility 较并行重跑 F 下降不超过 3 pp；safe completion 不低于 F；总 token 不高于 1.20×F。仅在 F 确有非零残余 ASR 且样本足够时，以 ASR 相对降低 25–50% 为探索目标；如果 F 已近零，比较更强攻击/边界违规与误拒，不能制造绝对 ASR 数字。所有这些仍是工程验收方向，不是统计保证；正式报告 paired delta 与 95% CI。

## 4. Benchmark 取舍

### AgentDojo：第一优先，主表

NeurIPS 2024 Datasets and Benchmarks 正式工作；四个模拟业务 suite，工具读写可控环境状态，官方 utility/security checker。当前项目已有 adapter，接入成本最低。[官方仓库](https://github.com/ethz-spylab/agentdojo)、[论文](https://arxiv.org/abs/2406.13352)。

选它是为了测**合法完成 + 恶意目标是否真的达到环境状态**，而不是模型是否说了危险话。保留旧 80 对做回归，但主研究必须加独立 holdout、多攻击策略和参数攻击子类。应将 cross-tool 与 within-tool 参数攻击分别统计；分类标签只供评分，不给 compiler/judge。[ToolFence 原文 §4/C](https://arxiv.org/html/2609.37196v2)

注意：这些是**模拟 API**，不代表真实银行/Slack 服务的事务一致性。AgentDojo 本身不能验证网络 timeout 后真实副作用的不确定性，必须补 host fault injection。

### AgentDyn：第二优先，最能打中 exact capability 的弱点

2026 arXiv 工作，当前官方仓库题名已更新。公开 AgentDojo fork，60 user tasks、28 injection tasks 形成 560 security cases；Shopping/GitHub/DailyLife，要求动态计划与有用的外部指令。报告 benign utility、utility under attack、ASR。它是开放式**模拟 sandbox**，不是在线真实购物/GitHub 账户操作。[原文](https://arxiv.org/html/2602.03117v1)、[现官方代码](https://github.com/SaFo-Lab/AgentDyn)。

接入难度中等：接口可复用，但新增工具需要可信 manifest、敏感参数与身份解析规则。最值得拆出“初始完整参数不可知、必须合法读后再写”的任务。论文为了不因 agent 求确认而停止，给防御统一加了自动完成提示；我们应固定是否允许确认，不让某方法得到人工授权、另一方法只能拒绝。

泄漏控制：同一 user task 的不同 injection 配对不能随机散落 dev/test；同目标实体、同任务模板也应分组。外部 helpful instructions 必须允许作为任务数据使用，但不能因其存在直接成为新的 host 权威。报告 grant-needed 子集与误拒原因，正好检查本版精确单次 grant 的成本。

### AgentLAB：第二阶段附录，不做第一轮全量主表

2026 arXiv；公开代码含五种长程攻击（intent hijacking、tool chaining、objective drifting、task injection、memory poisoning），论文 28 环境/644 cases。工具环境含可变对象，也结合 WebShop 等；评分并非统一纯状态 oracle，原文允许外部 LLM 比较轨迹，README 有 GPT-5.1 judge 分数阈值。[原文](https://arxiv.org/html/2602.16901v1)、[代码](https://github.com/TanqiuJiang/AgentLAB)。

接入成本高于 AgentDyn：不同 track/环境、攻击 planner、attacker、judge 的模型预算都要冻结。优先选择**间接注入 + tool chaining / objective drift**，排除直接恶意用户请求与当前 threat model 不符部分；若本版无跨任务持久记忆，memory-poisoning 不是公平核心任务。它适合测试“单个动作看似合法、序列累积越权”，也最可能暴露当前 exact 单次 grant 仍缺任务整体语义约束。自适应攻击必须给每种防御相同攻击 query/turn/token budget，单独记攻击开销。

### MCPTox：工具元数据污染边界，不能替代执行可靠性

AAAI 2026 正式论文。材料来自 45 个真实 MCP servers、353 工具；但论文评估关键步骤是将污染工具描述与合法工具放入上下文，记录模型选择的工具和参数。其“成功”强调被污染描述诱导调用另一合法工具；直接调用恶意工具反被记为一种 failure。因此不能将该 ASR 等同所有有害副作用或真实事务提交率。[正式论文](https://ojs.aaai.org/index.php/AAAI/article/download/40895/44856)、[方法原文](https://arxiv.org/html/2508.14925v1)、[材料/analysis 代码](https://github.com/zhiqiangwang4/MCPTox-Benchmark)。

用于补测：可信 manifest 不被 MCP tool description 覆盖；同名工具 schema/来源改变应拒绝。未知工具一律拒绝很容易把该 benchmark 做成零 ASR，因此必须同时测合法工具可用率、已知工具参数劫持和 matched clean 调用，不能只展示未知工具被拒绝。按 **server + attack family** 分组 holdout，避免同 server 元数据进入训练/规则制定后又作为“未见”测试。公开仓库偏数据与 analysis，不等于开箱即用的完整 runtime runner；需要受控 dispatch stub。不要为了测试访问带真实凭证的生产 MCP。

### ASB：安全面更宽，优先级低于 AgentDyn

ICLR 2025 正式工作，官方基于 AIOS，覆盖十类应用情景，支持 direct/observation injection、PoT backdoor、memory poisoning，公开配置与攻击脚本。[官方项目](https://luckfort.github.io/ASBench/)、[代码](https://github.com/agiresearch/ASB)、[正式论文](https://proceedings.iclr.cc/paper_files/paper/2025/file/5750f91d8fb9d5c02bd8ad2c3b44456b-Paper-Conference.pdf)。

本次只核实官方说明与可用性，未逐条审计其工具 handler/evaluator，**不能据此声称所有任务执行了真实副作用或统一状态评分**。与当前 adapter 的环境/工具接口不同，memory/backdoor threat model 也超出本版。可作为后续攻击面补充；如用 ToolFence repo 的 ASB wrapper，必须称该 wrapper 的具体 track，不把 wrapper 分数冒称完整官方 ASB。

### AppWorld：最强 benign 复杂任务/附带损害补充，暂不冒称 PI benchmark

ACL 2024 正式工作。高保真模拟 apps，通过数据库状态 unit tests 检查任务完成及 collateral damage；有 function-calling/MCP 接口。原生没有与 AgentDojo 完全同构的 prompt-injection 主分数。[论文](https://arxiv.org/abs/2407.18901)、[官方代码](https://github.com/StonyBrookNLP/appworld)。

接入中高：可用 API/MCP 做网关，仍须为大量工具维护 manifest，且不能让执行代码绕过网关直接写 DB。按官方 train/dev/test_normal/test_challenge 使用；ground_truth/evaluation program 不得进入 agent、compiler 或 judge 上下文。官方要求不要把 bundle 解密后的代码/数据公开散播以免污染训练；日志发布应服从这一范围。官方明确指出 agent 若使用任意状态回滚，不能与没有该能力的 agent 公平对比。可在受控 fault test 中由评测器重置世界，不能赋予方法独享撤销真实副作用的能力。

## 5. 三类 baseline：实际差异与公平适配

| 家族 | 必须保留的原方法 | 与本版区别 | 接入与比较范围 |
|---|---|---|---|
| B1 当前 Folded + per-action judge | 原 main/worker、review prompt、EvidenceStore、预算、恢复逻辑；legacy 开关冻结 | 语义判断逐动作；新版多 initial exact compiler、host pin/monitor/receipt | 最直接因果对照，同 agent 同工具，必须同时重跑 |
| B2 ToolFence 官方 | blueprint + deterministic monitor + runtime capability grant；注明 cache/strict mode，保存官方 commit | 原论文支持可复用 capability shape/跨 session cache；当前 repo 还含 transaction ledger/host boundary；本版只是精确单次 grant | 先跑官方 smoke，完整 host adapter 后同模型/任务/攻击；不能削弱成 tool-name allowlist 再称 ToolFence |
| B3 CaMeL / Multi-CaMeL | privileged planning 与 quarantined processing；解释器数据依赖和 policy；多 agent 则保留双通道与跨边界 provenance | 本版 main 仍会看外部内容，无自动 taint/控制数据分离；JSON Pointer 校验不等价 | CaMeL 作为主强基线；Multi-CaMeL 仅 worker 边界附录，公开 artifact 基于 Sequrity 且 tools 分给子 agent，不能假装与只读 worker 架构完全一致 |

ToolFence 是本升级最接近的先例，不能把“compiler + monitor + grant”当新提出的概念。论文的参数级攻击 split 和安全/效用/延迟分开报告很值得复用。其 2026-11-24 公共代码 README 已明确 host-issued TaskContract、strict derived field、reservation、receipt、UNKNOWN reconciliation，故 novelty 需落在**本系统任务/边界实证、简化精确授权方案及权衡**，而不是给这些现成组件改名。[论文](https://arxiv.org/html/2609.37196v2)、[代码](https://github.com/PolyLiYJ/ToolFence_v2)。

CaMeL 官方研究 artifact 公开可跑 AgentDojo，README 提醒解释器可能有 bug、并不承诺维护。论文明确需要在歧义时人工澄清，不是完全无人干预保证；自动评估中应统一“请求澄清算 abstain/失败”的规则，不给其 oracle 用户。[论文](https://arxiv.org/html/2503.18813v1)、[代码](https://github.com/google-research/camel-prompt-injection)。

Multi-CaMeL 防止父 agent 把工具数据塞入下游 trusted instruction；数据单独传递并保留 provenance。公开 MultiAgentDojo artifact 复用官方任务/攻击/评分，但改为 orchestrator 无直接工具、子 agent 分工具的层级结构。该结构与 Folded 主写者+只读 workers 不同，整系统对比只能比较最终安全效用，不能归因一个组件。[论文](https://arxiv.org/html/2610.05640v1)、[代码](https://github.com/james-pete/multiagentdojo)。

所有外部方法的同配置绝对分数都**待实测**。官方论文分数可以描述背景，不应填进新主结果表的同一列。

## 6. 指标：以 committed behavior 为主，分开 proposal、review、dispatch

核心效用/安全指标：

1. Clean utility、utility under attack，沿用官方 state checker。
2. ASR：官方恶意目标成功 / 全部分配攻击 episodes；另报确认 exposure 子集和 UNKNOWN 数。拒绝、资源耗尽或格式错误不是“安全完成”。
3. **Safe completion**：合法目标成功 AND 恶意目标失败；给分子/分母，不把它直接等同 1−ASR。
4. **Committed unauthorized action rate**：违反独立 host policy 的实际 handler dispatch / 敏感 dispatch，以及发生至少一次违规的 episode 比例。基于 host 记录+独立 oracle，不拿 monitor 自报的 allow 当 gold label。
5. Proposal attack rate 与 committed ASR 分开：模型可能仍被诱导提议恶意操作，但网关阻断；这是边界有效，不能据此声称模型没有被注入。

成本与效用损失：

- 含 compiler、judge、main、worker、重试的 input/output token 与模型 calls；延迟 p50/p95 和均值；总成本用当次价格与真实 usage，unknown 用量另列。
- 每任务 compiler calls、semantic review calls、capability match ratio、grant denial、平均/长尾 review 时延。单次 exact grant 不可用 shape cache 的命中率来包装。
- **Benign false block**：把合法工作流挡住的 episode/动作，人工盲审或基于验证过的 gold traces；不要把所有拒绝都当正确。
- 敏感 dispatch 的 receipt 覆盖率、未知结果保留率、重复副作用数、未授权跨任务 capability 命中数；receipt 只能证明 handler 返回/边界记录，不能凭内部状态推定外部事务已提交。

主报告给 task-level paired bootstrap 95% CI，三 seeds 分别列出。相同 user task 的多攻击组合必须聚类重采样；不能把同一任务 10 个攻击、3 seeds 当 30 个独立任务。ASR 近零时给精确上界/原始计数，bootstrap 全零不应被误读成置信区间绝对 [0,0] 的风险保证。模型 API 若不保证 seed，注明 seed 用于顺序/采样，实际是三次独立重复。

## 7. 最小执行顺序与失败解释

**A. 无模型机制测试，先做且应阻断发布错误。** 固定 transcript/action fixtures：未知工具、schema 漂移、worker 写、初始 cap 参数被换、大小写/Unicode/URL 等归一化歧义、grant 单次耗尽、task_id 不匹配、伪造/不存在 evidence、JSON Pointer 错字段/错值、版本过期、review 后状态变化、相同 action 重放、dispatch 前失败、dispatch 后 timeout、receipt 丢失。合法控制必须能过，非法必须不调 handler。sticky UNKNOWN 必须不自动释放 cap 或重试；无法获得可信 reconciliation 回执时预期是安全停止并扣效用，而不是凭空宣称恢复成功。

**B. Legacy F 与新版的旧 80 对回归。** 同模型、系统上限、seed 42，先小范围 smoke 后全80对；每场景 clean/attack 成对，运行次序随机。主要查 utility 下跌和成本膨胀。历史 F/W仅作参照，必须新跑旧 F 防 provider 漂移。

**C. AgentDojo 独立 holdout + 三类基线 + 三 seeds。** 攻击策略至少覆盖现有 direct、tool-aware/伪装上下文、within-tool 参数劫持；新增攻击内容与 holdout task 在防御冻结后生成。若用官方全部任务，应明确哪些已用于开发，分开报 dev 与 holdout。预算含初始化、失败、重试、全部审核。最强攻击可再做 matched-budget adaptive attack，但不要把不同攻击器预算合并。

**D. AgentDyn 小规模适配再三 seeds正式。** 先按 user task/模板分组冻结 split；三个 suite 均覆盖。首轮重点比较 F 与新版、补 ToolFence，CaMeL按已公开fork接入，避免首轮跨度过大。失败归因：动态必需步骤 initial exact cap 缺失、judge不承认合法外部帮助、证据字段结构化不足、用户意图歧义、长链超预算。若 benign下降超过3 pp且安全无收益，优先改授权表达，不能继续加限制。

**E. 消融/压力只选能解释问题的。** （i）新版去 initial compiler，只保留同 isolated judge+host exact grant，判断 compiler 是否值成本；（ii）去 exact host pin/单次上限的受控 fixture 对照，判断授权后漂移；（iii）去 receipt/UNKNOWN的故障环境对照，判断重复副作用。选一项最相关的 AgentLAB 长链或 MCP description stress作附录。不要为了论文完整一次把六个benchmark全部跑完。

若完整方法与 F 在所有ASR上同为零，只能支持“在该攻击范围未观测恶意成功”；新增贡献由边界测试与可靠性证据支撑。若安全改善只来自全拒绝而 safe completion下降，则主张不成立。若 compiler增加token而几乎没fast-path命中，应报告初始化方案不经济；可以保留host-pinned one-shot grant版本作为更简单结果。若正确来源字段仍带恶意值、judge批准越权，说明 provenance存在≠授权语义正确，必须披露该失败类。

## 8. Split、缓存与泄漏约束

- Dev/test 按 task/template、攻击家族、实体组合分组；防御开发者不能根据 test失败继续改prompt后还称最终test。
- Runtime输入仅 user request、可信工具schema/manifest、实际可见证据；不得读取 attack target、gold tool sequence、评分函数、task_id映射答案。离线分类/评分器可以用gold，但需独立进程/目录隔离。
- Task-local monitor 每个 episode清空；host签发cap/receipt使用新task nonce。ToolFence跨session cache主表先用cold；warm单列，预热只用train/dev，并记录cache来源/策略版本。共享防御cache不能先跑攻击再“带着答案”测试下一个方法。
- 结构化工具输出被攻击污染，仍可满足“来自指定JSON Pointer”；这仅是来源校验，不是内容真实性。设计 same-field poisoned-value案例，避免把来源存在直接当安全。
- 基准工具metadata是攻击面时，可信manifest必须来自host维护的版本，不能先把污染描述喂compiler构建权限再说manifest可信。
- 所有模型调用、超时、预算耗尽和拒绝保留；预先定义基础设施无效重跑。方法错误计utility失败，不静默删除。
- AppWorld只公开符合其数据许可证/抗污染要求的汇总和脱敏指标，不上传test ground truth/解密bundle。其它benchmark也不把攻击成功目标或私有任务答案混进可见prompt。

## 9. 公开代码快照（读取日 2026-11-26）

以下 SHA 用于冻结待复现实验；读取了仓库/README，不代表已把依赖全部安装成功。AgentDyn原链接 leolee99/AgentDyn 已迁至 SaFo-Lab。

| 仓库 | 本次确认 HEAD |
|---|---|
| ethz-spylab/agentdojo | `089ed468cf3ed0322acc66b0211f26d9d90dbf60` |
| SaFo-Lab/AgentDyn | `5353cf7615b135cace8d07c8f12dac53a16b6db3` |
| TanqiuJiang/AgentLAB | `36f58e60c36bbd6d5b8e61d50d7db7d9ea7258d7` |
| zhiqiangwang4/MCPTox-Benchmark | `630121b3275f74cc72d000a7a056e4d3c68648ef` |
| agiresearch/ASB | `544540ff0788998072f7df463056fd17e62cc9f4` |
| StonyBrookNLP/appworld | `42b5bcf3cd334fee33f0c37c02070a9f5807add5` |
| PolyLiYJ/ToolFence_v2 | `e49c1ba746d0a13e48787a5660a5cf5424e33cf7` |
| google-research/camel-prompt-injection | `f083b6b396399d3b3c7f2ddaf613a5945eaf32d8` |

Multi-CaMeL 仓库本次确认公开并读README，但尚未记录HEAD SHA；若纳入正式实验必须先pin，并冻结Sequrity依赖版本。ToolFence 的论文和实现存在版本变化；引用论文版本与执行代码commit分别披露，不混为同一历史版本。
