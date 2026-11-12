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

外部内容进入多智能体系统后，风险在哪个环节转化为工具动作？额外的协作又在哪些场景值得付出成本？本研究在同一批场景上比较调度协议，并用逐轮轨迹追踪工具动作和实际执行结构。

## Findings

### 只审计智能体之间的消息，会漏掉委派前的工具动作

Slack 07 的轨迹显示，协调者在首次委派前就执行了攻击目标对应的工具动作。委派之后，两名调查者都接触了相关内容，其中一名执行了目标调用。审计应从协调者首次读取外部内容开始，分别追踪内容接触、实际调用和攻击目标是否达成。 [Slack 07 轨迹](demo/data/case_slack_07.json) · [案例分析](reports/2026-10-19-manta-agentdojo/README.md)

### 根拓扑标签会漏掉多数运行中的重组

在自适应配置实际重组的记录中，多数仍保留原来的根拓扑模式。只按「星形」或「链式」归类，会把重组前后的执行规格归到同一类。按轮对比组成员、执行顺序和子组结构，可以定位实际执行发生了哪些变化。 [自适应实验报告](reports/2026-10-28-deepseek-flash-adaptive/README.md) · [逐轮拓扑数据](demo/data/topology.json)

### 固定调查每次都要付出成本，完成收益集中在少数场景

固定调度为每次运行安排两名调查者，新增 token 主要花在调查者调用上。在这批配对场景中，按需调度已经完成了固定调度能完成的绝大多数任务。选择协议时，应看新增完成的是哪些任务，以及这些任务是否值得为每次运行增加调查开销。 [配对结果](reports/2026-10-29-completed-experiments/README.md#fw-配对结果) · [开销分解](reports/2026-10-29-completed-experiments/README.md#token-具体花在哪)

## Evaluation

评测覆盖 80 个冻结场景、四个套件和 76 个不同用户任务。每个场景分别运行正常和攻击条件。六种配置和一次参考复跑共得到 1,120 条有效记录，采用单一随机种子和同一种官方攻击。调度对照比较完整协议，固定方案同时改变了调查者启动、分工和汇报方式。 [结果总表](reports/2026-10-29-completed-experiments/README.md#结果总表) · [场景级结果](reports/2026-10-29-completed-experiments/episode_results.csv) · [实验范围](reports/2026-10-29-completed-experiments/README.md#配置与证据边界)

<p align="center">
  <img src="docs/assets/research-showcase/worker-tradeoff.svg" width="760" alt="横轴为每种配置的总 token，纵轴为 Attack 任务完成率。按需 F 为 7.14M 与 88.75%，固定双 Worker W 为 13.14M 与 93.75%，历史自适应配置为 28.13M 与 82.50%。">
  <br>
  <em>图 1 · 各配置在 80 条 Attack 记录上的任务完成率，以及 160 条 Clean 和 Attack 记录的总 token。</em>
</p>

## Demo

在离线演示中可以点选消息、网页读取和目标调用，查看对应的发送方、接收方或工具记录。完整演示还支持按场景筛选、对照拓扑回合，以及切换 Clean 和 Attack 逐步回放。 [演示说明](demo/README.md)

<p align="center">
  <img src="docs/assets/research-showcase/provenance-preview.png" width="880" alt="Slack 07 信息溯源图，区分 Agent 消息、网页读取和工具目标调用。右侧显示选中消息的证据。">
  <br>
  <em>图 2 · Slack 07 的执行轨迹与来源证据。</em>
</p>

## Reproducibility

| 复核内容 | 入口 |
| --- | --- |
| 配置、样本与指标 | [完整实验报告](reports/2026-10-29-completed-experiments/README.md) · [逐场景结果](reports/2026-10-29-completed-experiments/episode_results.csv) · [公开日志索引](reports/LOGS.md) |
| 调度、执行与评测流程 | [系统架构](docs/REPOSITORY_ARCHITECTURE.md) · [F/W 对照设计](docs/manta/FW_ABLATION.md) · [实验运行入口](scripts/manta/run_formal.py) |
| 图表与轨迹数据 | [派生数据清单与 SHA-256](demo/data/data_manifest.json) · [离线数据生成](scripts/demo/build_demo_data.py) · [图 1 复现脚本](scripts/reporting/plot_showcase_tradeoff.py) |

## Credits

实验任务、工具与评分来自 AgentDojo，执行引擎来自仓库内的 MANTA 源码快照。 [AgentDojo 论文引用](docs/CITATION.bib) · [上游说明归档](archive/AGENTDOJO_UPSTREAM.md) · [MANTA 源码](upstreams/manta/) · [许可证](LICENSE)
