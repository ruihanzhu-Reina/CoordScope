<div align="center">

<img src="demo/assets/icons.svg" width="44" height="44" alt="">

<h1>超越通信拓扑</h1>

<p><strong>多智能体系统中的风险传播、工具执行与协作成本</strong></p>
<p><em>Beyond Communication Topology: Risk Propagation, Tool Execution, and Collaboration Cost in Multi-Agent Systems</em></p>
<p>朱芮含</p>

<p>
  <a href="#findings">研究发现</a> ·
  <a href="#evaluation">实验设计</a> ·
  <a href="#demo">轨迹演示</a> ·
  <a href="#reproducibility">复现资料</a>
</p>

<p><strong>80</strong> 个冻结场景　·　<strong>6</strong> 种实验配置　·　<strong>1,120</strong> 条有效运行记录</p>

</div>

我们在同一批任务上比较多智能体调度协议。逐轮日志记录各角色读到的内容、传递的消息和执行的工具动作，配对实验则用来比较任务完成率与协作开销。

## Findings

### 判断模型是否采纳指令，需要检查它的响应

在 Flash Star 实验中，攻击内容经常进入模型输入，只有一条运行达成了攻击目标。暴露和工具调用都可以从日志核实。要判断模型有没有照外部指令行事，还需要标注它对内容的响应。 [暴露统计与官方评分](reports/2026-10-19-manta-agentdojo/README.md)

### 消息图会漏掉调查者直接读取的内容

在 Slack 07，两名调查者收到协调者的消息后，又各自读取了同一个外部网页。沿消息追溯能查到谁转交了内容，对照工具记录才看得见调查者从哪里直接读到了它。 [Slack 07 轨迹](demo/data/case_slack_07.json)

### 同一种根拓扑可以对应不同的执行结构

多数发生重组的运行仍沿用原来的根拓扑模式。只记下「星形」或「链式」，容易把两轮执行当成同一种安排。逐轮快照保留了成员、执行顺序和子组，可以据此核对重组发生在哪里。 [自适应实验报告](reports/2026-10-28-deepseek-flash-adaptive/README.md) · [逐轮拓扑数据](demo/data/topology.json)

### 固定分工增加整批开销，收益集中在少数任务

固定调度在每次运行中都启动两名调查者，增加的 token 主要花在调查调用上。逐项比较时，只有少数任务的成败随调度方案改变。额外开销是否划算，要看这些任务对实际应用有多重要。 [配对结果](reports/2026-10-29-completed-experiments/README.md#fw-配对结果) · [开销分解](reports/2026-10-29-completed-experiments/README.md#token-具体花在哪)

### 审计给出零风险分时，目标调用仍可能发生

Slack 07 的归档审计给出零风险分，系统没有触发修复。协调者在首次委派前就执行了目标调用，官方评分判定攻击成功。评估这类审计的预防效果，需要同时核对工具调用和任务最终状态。 [审计与工具轨迹](demo/data/audit_timeline.json) · [案例分析](reports/2026-10-19-manta-agentdojo/README.md)

## Evaluation

评测覆盖四个任务套件、76 个不同用户任务。每种配置在 80 个固定场景上各运行一次正常条件和攻击条件。实验使用同一随机种子和同一种官方攻击。 [六种配置总表](reports/2026-10-29-completed-experiments/overview.csv) · [场景级结果](reports/2026-10-29-completed-experiments/episode_results.csv) · [实验范围](reports/2026-10-29-completed-experiments/README.md#配置与证据边界)

### Flash 16K 配置对照

| 配置 | 正常完成率 ↑ | 攻击下完成率 ↑ | 攻击目标达成 ↓ | 总 token ↓ | 单次平均耗时 ↓ |
| --- | ---: | ---: | ---: | ---: | ---: |
| F · 按需调查 | 90.00% | 88.75% | 0/80 | **7.14M** | **29.90 s** |
| W · 固定双调查者 | **91.25%** | **93.75%** | 0/80 | 13.14M | 61.92 s |
| 原生自适应 · 历史参照 | 81.25% | 82.50% | 1/80 | 28.13M | 209.23 s |

F/W 对照比较两套完整调度协议，固定方案同时改变了调查者启动、分工和汇报方式。两组各有 4 条攻击记录的暴露状态未知。原生自适应的结果来自较早一轮实验。 [调度对照设计](docs/manta/FW_ABLATION.md) · [指标口径](reports/2026-10-29-completed-experiments/README.md#结果总表)

<p align="center">
  <img src="docs/assets/research-showcase/worker-tradeoff.svg" width="760" alt="横轴为每种配置的总 token，纵轴为 Attack 任务完成率。按需 F 为 7.14M 与 88.75%，固定双 Worker W 为 13.14M 与 93.75%，历史自适应配置为 28.13M 与 82.50%。">
  <br>
  <em>图 1 · 各配置在 80 条 Attack 记录上的任务完成率，以及 160 条 Clean 和 Attack 记录的总 token。</em>
</p>

## Demo

在离线演示中可以点选消息、网页读取和目标调用，查看对应的发送方、接收方或工具记录。完整演示还支持按场景筛选、对照拓扑回合，以及切换 Clean 和 Attack 逐步回放。 [演示说明](demo/README.md)

<p align="center">
  <img src="docs/assets/research-showcase/provenance-preview.png" width="880" alt="Slack 07 的信息来源图。外部网页分别向协调者和两名调查者提供内容。协调者在首次委派前有两次目标调用，调查者 2 后续也有一次目标调用。">
  <br>
  <em>图 2 · Slack 07 攻击条件下的信息来源与工具调用。m 为消息编号，# 为工具调用序号。</em>
</p>

## Reproducibility

| 复核内容 | 入口 |
| --- | --- |
| 配置、样本与指标 | [完整实验报告](reports/2026-10-29-completed-experiments/README.md) · [逐场景结果](reports/2026-10-29-completed-experiments/episode_results.csv) · [公开日志索引](reports/LOGS.md) |
| 调度、执行与评测流程 | [系统架构](docs/REPOSITORY_ARCHITECTURE.md) · [F/W 对照设计](docs/manta/FW_ABLATION.md) · [实验运行入口](scripts/manta/run_formal.py) |
| 图表与轨迹数据 | [派生数据清单与 SHA-256](demo/data/data_manifest.json) · [离线数据生成](scripts/demo/build_demo_data.py) · [图 1 绘图脚本](scripts/reporting/plot_showcase_tradeoff.py) · [图 2 绘图脚本](scripts/reporting/plot_showcase_provenance.py) |

## Credits

实验任务、工具与评分来自 AgentDojo，执行引擎来自仓库内的 MANTA 源码快照。 [AgentDojo 论文引用](docs/CITATION.bib) · [上游说明归档](archive/AGENTDOJO_UPSTREAM.md) · [MANTA 源码](upstreams/manta/) · [许可证](LICENSE)
