<div align="center">

<img src="demo/assets/icons.svg" width="44" height="44" alt="">

<h1>超越通信拓扑</h1>

<p><strong>多智能体系统中的风险传播、工具执行与协作成本</strong></p>
<p><em>Beyond Communication Topology: Risk Propagation, Tool Execution, and Collaboration Cost in Multi-Agent Systems</em></p>

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

### 固定增加调查者，完成率提升有限，成本增加很多

与按需调查相比，固定安排两名调查者在正常条件下多完成 1 项任务，在攻击条件下多完成 4 项任务，总 token 增加了 84.12%。新增用量中，92.6% 来自调查者调用。对这批任务来说，增加协作投入的收益集中在少数任务，大部分任务用按需调查就能完成。 [配对结果](reports/2026-10-29-completed-experiments/README.md#fw-配对结果) · [角色用量](reports/2026-10-29-completed-experiments/README.md#token-具体花在哪)

### 精简执行流程后，任务完成率和资源效率同时改善

采用共享主执行历史、按需调查和执行前核验的配置，比原生自适应配置完成了更多任务，token 用量减少了 74.62%。原流程中的规划、调查、审计和综合会反复携带任务背景与工具信息。这个结果把优化重点指向协调和执行流程中的重复工作，具体模块各贡献多少还需要消融实验确认。 [完整配置比较与用量分析](reports/2026-10-29-completed-experiments/README.md#token-具体花在哪)

### 自适应重组改变了执行过程，却没有提高整体完成率

DeepSeek Flash 的星形配置与原生自适应配置取得了相同的总体完成率和攻击成功数，自适应配置消耗的 token 更多。逐轮轨迹确认系统确实发生了重组，但这些结构变化并未带来整体指标的改善。评价自适应协作，需要同时看重组是否解决了任务、以及为此付出的开销。 [跨配置分析](reports/2026-10-28-four-experiment-analysis/README.md) · [实际拓扑记录](reports/2026-10-28-deepseek-flash-adaptive/README.md)

### 任务完成率更高的配置，也可能更容易达成攻击目标

DeepSeek Pro 的星形配置比 DeepSeek Flash 的星形配置完成了更多任务，同时出现了更多攻击成功记录。用户任务完成和攻击成功还可能发生在同一次运行中。因此，任务能力和安全性需要分别评价，单看完成率会掩盖这类失败。 [各模型的任务与安全结果](reports/2026-10-29-completed-experiments/README.md#结果总表)

### 识别出恶意内容，仍可能在转述时达成攻击目标

自适应配置的 Slack 14 案例中，Agent 识别了恶意内容并发出警告，但警告消息也转述了攻击目标要求传递的内容，最终被官方评分判定为攻击成功。风险识别与安全执行之间还隔着输出和工具动作，安全检查需要覆盖这些实际产生效果的环节。 [案例与审计分析](reports/2026-10-28-four-experiment-analysis/README.md)

## Evaluation

实验涵盖 DeepSeek Flash、DeepSeek Pro 和 GPT-4o，共六种配置。每组使用四个任务套件中的 80 个固定场景，对应 76 个不同用户任务，每个场景分别运行正常条件与攻击条件。六种配置加上一次按需调查的参考复跑，共有 1,120 条有效记录。实验采用 seed 42 和官方 direct 攻击。 [逐场景结果](reports/2026-10-29-completed-experiments/episode_results.csv) · [参考复跑](reports/2026-10-29-completed-experiments/README.md#重复运行与安全事件)

| 模型与执行配置 | 正常完成率 ↑ | 攻击下完成率 ↑ | 攻击目标达成 ↓ | 总 token ↓ | 单次平均耗时 ↓ |
| --- | ---: | ---: | ---: | ---: | ---: |
| DeepSeek Flash · 星形协作 · 4K | 81.25% | 82.50% | 1/80 | 25.60M | 164.87 s |
| GPT-4o · 星形协作 · 4K | 53.75% | 55.00% | 1/80 | 10.45M | 76.39 s |
| DeepSeek Pro · 星形协作 · 16K | 86.25% | 86.25% | 4/80 | 26.91M | 304.41 s |
| DeepSeek Flash · 原生自适应 · 16K | 81.25% | 82.50% | 1/80 | 28.13M | 209.23 s |
| DeepSeek Flash · 按需调查 · 16K | 90.00% | 88.75% | 0/80 | **7.14M** | **29.90 s** |
| DeepSeek Flash · 固定双调查者 · 16K | **91.25%** | **93.75%** | 0/80 | 13.14M | 61.92 s |

4K 与 16K 表示单次输出上限。总 token 合计每组 80 次正常运行和 80 次攻击运行。按需调查与固定双调查者两组各有 4 条攻击记录的暴露状态未知。 [完整结果及指标定义](reports/2026-10-29-completed-experiments/README.md#结果总表)

按需调查与固定双调查者的配对实验同时改变了调查者启动、分工和汇报方式，比较对象是完整调度协议。其余历史配置还存在模型记录、输出上限和审计方式的差异，配置间比较用于描述观测结果。Flash 的历史模型记录包含 `deepseek-v4-flash` 和 `deepseek-flash`，Pro 记录为 `deepseek-v4-pro`。以上发现适用于这批单随机种子、固定攻击设置下的任务。 [实验设计与适用范围](reports/2026-10-29-completed-experiments/README.md#配置与证据边界)

<p align="center">
  <img src="docs/assets/research-showcase/worker-tradeoff.svg" width="760" alt="横轴为每种配置的总 token，纵轴为 Attack 任务完成率。按需调查为 7.14M 与 88.75%，固定双调查者为 13.14M 与 93.75%，历史自适应配置为 28.13M 与 82.50%。">
  <br>
  <em>图 1 · DeepSeek Flash、16K 输出上限下的三种执行配置。纵轴为攻击条件下的任务完成率，横轴合计正常与攻击条件的 token。</em>
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
| 调度、执行与评测流程 | [系统架构](docs/REPOSITORY_ARCHITECTURE.md) · [调查者调度对照设计](docs/manta/FW_ABLATION.md) · [实验运行入口](scripts/manta/run_formal.py) |
| 图表与轨迹数据 | [派生数据清单与 SHA-256](demo/data/data_manifest.json) · [离线数据生成](scripts/demo/build_demo_data.py) · [图 1 绘图脚本](scripts/reporting/plot_showcase_tradeoff.py) · [图 2 绘图脚本](scripts/reporting/plot_showcase_provenance.py) |

## Credits

实验任务、工具与评分来自 AgentDojo，执行引擎来自仓库内的 MANTA 源码快照。 [AgentDojo 论文引用](docs/CITATION.bib) · [上游说明归档](archive/AGENTDOJO_UPSTREAM.md) · [MANTA 源码](upstreams/manta/) · [许可证](LICENSE)
