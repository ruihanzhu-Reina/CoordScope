<div align="center">

<img src="docs/assets/research-showcase/coordscope-mark.svg" width="168" height="72" alt="机器人、协作节点与星星组成的 CoordScope 标志">

<h1>CoordScope</h1>

<p><strong>多智能体系统中的协调、成本与安全</strong></p>
<p><em>Coordination, Cost, and Security in Multi-Agent Systems</em></p>

<p>
  <a href="#findings">研究发现</a> ·
  <a href="#evaluation">实验设计</a> ·
  <a href="#demo">轨迹演示</a> ·
  <a href="#reproducibility">复现资料</a>
</p>

<p><strong>80</strong> 个冻结场景　·　<strong>6</strong> 种实验配置　·　<strong>1,120</strong> 条有效运行记录</p>

</div>

我们在同一批任务上比较多智能体调度协议。逐轮日志记录各角色读到的内容、传递的消息和执行的工具动作，配对实验则用来比较任务完成率与协作开销。

<a name="findings"></a>

## <img src="docs/assets/research-showcase/sparkles.svg" width="28" height="28" alt=""> Findings

### 固定增加辅助 Agent，完成率提升有限，成本增加很多

与按需调用方案相比，固定安排两个辅助 Agent 在正常条件下多完成 1 项任务，在攻击条件下多完成 4 项任务，总 token 增加了 84.12%。新增用量中，92.6% 来自辅助 Agent 调用。对这批任务来说，增加协作投入的收益集中在少数任务，大部分任务按需调用辅助 Agent 就能完成。 [配对结果](reports/2026-10-29-completed-experiments/README.md#fw-配对结果) · [角色用量](reports/2026-10-29-completed-experiments/README.md#token-具体花在哪)

### 精简执行流程后，任务完成率和资源效率同时改善

采用共享主执行历史、按需调用辅助 Agent 和执行前核验的配置，比原生自适应配置完成了更多任务，token 用量减少了 74.62%。原流程中的规划、调查、审计和综合会反复携带任务背景与工具信息。这个结果把优化重点指向协调和执行流程中的重复工作，具体模块各贡献多少还需要消融实验确认。 [完整配置比较与用量分析](reports/2026-10-29-completed-experiments/README.md#token-具体花在哪)

### 自适应重组改变了执行过程，却没有提高整体完成率

DeepSeek Flash 的星形配置与原生自适应配置取得了相同的总体完成率和攻击成功数，自适应配置消耗的 token 更多。逐轮轨迹确认系统确实发生了重组，但这些结构变化并未带来整体指标的改善。评价自适应协作，需要同时看重组是否解决了任务、以及为此付出的开销。 [跨配置分析](reports/2026-10-28-four-experiment-analysis/README.md) · [实际拓扑记录](reports/2026-10-28-deepseek-flash-adaptive/README.md)

### 任务完成率更高的配置，也可能更容易达成攻击目标

DeepSeek Pro 的星形配置比 DeepSeek Flash 的星形配置完成了更多任务，同时出现了更多攻击成功记录。用户任务完成和攻击成功还可能发生在同一次运行中。因此，任务能力和安全性需要分别评价，单看完成率会掩盖这类失败。 [各模型的任务与安全结果](reports/2026-10-29-completed-experiments/README.md#结果总表)

### 识别出恶意内容，仍可能在转述时达成攻击目标

自适应配置的 Slack 14 案例中，Agent 识别了恶意内容并发出警告，但警告消息也转述了攻击目标要求传递的内容，最终被官方评分判定为攻击成功。风险识别与安全执行之间还隔着输出和工具动作，安全检查需要覆盖这些实际产生效果的环节。 [案例与审计分析](reports/2026-10-28-four-experiment-analysis/README.md)

<a name="evaluation"></a>

## <img src="docs/assets/research-showcase/chart.svg" width="28" height="28" alt=""> Evaluation

实验涵盖 DeepSeek Flash、DeepSeek Pro 和 GPT-6 Luna，共六种配置。每组使用四个任务套件中的 80 个固定场景，对应 76 个不同用户任务，每个场景分别运行正常条件与攻击条件。六种配置加上一次按需调用方案的参考复跑，共有 1,120 条有效记录。实验采用 seed 42 和官方 direct 攻击。 [逐场景结果](reports/2026-10-29-completed-experiments/episode_results.csv) · [参考复跑](reports/2026-10-29-completed-experiments/README.md#重复运行与安全事件)

<p><strong>表 1 · 六种配置的任务表现与运行开销</strong></p>

<table>
  <thead>
    <tr>
      <th rowspan="2" align="left">模型</th>
      <th rowspan="2" align="left">执行方式</th>
      <th colspan="2" align="center">任务完成率 ↑</th>
      <th rowspan="2" align="center">攻击目标<br>达成数 ↓</th>
      <th colspan="2" align="center">资源开销 ↓</th>
    </tr>
    <tr>
      <th align="center">正常条件</th>
      <th align="center">攻击条件</th>
      <th align="center">总 token<br>（百万）</th>
      <th align="center">平均耗时<br>（秒 / 次）</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>DeepSeek<br>Flash</td>
      <td>星形协作</td>
      <td align="right">81.25%</td>
      <td align="right">82.50%</td>
      <td align="right">1/80</td>
      <td align="right">25.60</td>
      <td align="right">164.87</td>
    </tr>
    <tr>
      <td>GPT-6 Luna</td>
      <td>星形协作</td>
      <td align="right">53.75%</td>
      <td align="right">55.00%</td>
      <td align="right">1/80</td>
      <td align="right">10.45</td>
      <td align="right">76.39</td>
    </tr>
    <tr>
      <td>DeepSeek<br>Pro</td>
      <td>星形协作</td>
      <td align="right">86.25%</td>
      <td align="right">86.25%</td>
      <td align="right">4/80</td>
      <td align="right">26.91</td>
      <td align="right">304.41</td>
    </tr>
    <tr>
      <td>DeepSeek<br>Flash</td>
      <td>原生自适应</td>
      <td align="right">81.25%</td>
      <td align="right">82.50%</td>
      <td align="right">1/80</td>
      <td align="right">28.13</td>
      <td align="right">209.23</td>
    </tr>
    <tr>
      <td>DeepSeek<br>Flash</td>
      <td>按需调用辅助 Agent</td>
      <td align="right">90.00%</td>
      <td align="right">88.75%</td>
      <td align="right"><strong>0/80</strong></td>
      <td align="right"><strong>7.14</strong></td>
      <td align="right"><strong>29.90</strong></td>
    </tr>
    <tr>
      <td>DeepSeek<br>Flash</td>
      <td>固定调用两个辅助 Agent</td>
      <td align="right"><strong>91.25%</strong></td>
      <td align="right"><strong>93.75%</strong></td>
      <td align="right"><strong>0/80</strong></td>
      <td align="right">13.14</td>
      <td align="right">61.92</td>
    </tr>
  </tbody>
</table>

加粗表示本表中的最优观测值（含并列）；↑ 越高越好，↓ 越低越好。

GPT-6 Luna 的名称依据项目方向服务商核实后的反馈更正，原始运行记录中的请求标识为 `gpt-4o`。

输出上限：DeepSeek Flash 和 GPT-6 Luna 的星形配置为每次请求 4,096 token（4K），其余配置为 16,384 token（16K）。Token 是模型处理文本的计量单位，不能直接等同于字数；实际输出可以短于这个上限。表中的「总 token」则合计每组 80 次正常运行和 80 次攻击运行的用量。按需调用与固定调用两个辅助 Agent 的两组各有 4 条攻击记录的暴露状态未知。 [完整结果及指标定义](reports/2026-10-29-completed-experiments/README.md#结果总表)

两种辅助 Agent 调用方案的配对实验同时改变了辅助 Agent 启动、分工和汇报方式，比较对象是完整调度协议。其余历史配置还存在模型记录、输出上限和审计方式的差异，配置间比较用于描述观测结果。Flash 的历史模型记录包含 `deepseek-v4-flash` 和 `deepseek-flash`，Pro 记录为 `deepseek-v4-pro`。以上发现适用于这批单随机种子、固定攻击设置下的任务。 [实验设计与适用范围](reports/2026-10-29-completed-experiments/README.md#配置与证据边界)

<p align="center">
  <img src="docs/assets/research-showcase/worker-tradeoff.svg" width="760" alt="横轴为每种配置的总 token，纵轴为 Attack 任务完成率。按需调用辅助 Agent 为 7.14M 与 88.75%，固定调用两个辅助 Agent 为 13.14M 与 93.75%，历史自适应配置为 28.13M 与 82.50%。">
  <br>
  <em>图 1 · DeepSeek Flash、16K 输出上限下的三种执行配置。纵轴为攻击条件下的任务完成率，横轴合计正常与攻击条件的 token。</em>
</p>

<a name="demo"></a>

## <img src="docs/assets/research-showcase/robot.svg" width="28" height="28" alt=""> Demo

在离线演示中可以点选消息、网页读取和目标调用，查看对应的发送方、接收方或工具记录。完整演示还支持按场景筛选、对照拓扑回合，以及切换 Clean 和 Attack 逐步回放。 [演示说明](demo/README.md)

<p align="center">
  <img src="docs/assets/research-showcase/provenance-preview.png" width="880" alt="Slack 07 的信息来源图。外部网页分别向协调者和两个辅助 Agent 提供内容。协调者在首次委派前有两次目标调用，辅助 Agent 2 后续也有一次目标调用。">
  <br>
  <em>图 2 · Slack 07 攻击条件下的信息来源与工具调用。m 为消息编号，# 为工具调用序号。</em>
</p>

<a name="reproducibility"></a>

## <img src="docs/assets/research-showcase/records.svg" width="28" height="28" alt=""> Reproducibility

| 复核内容 | 入口 |
| --- | --- |
| 配置、样本与指标 | [完整实验报告](reports/2026-10-29-completed-experiments/README.md) · [逐场景结果](reports/2026-10-29-completed-experiments/episode_results.csv) · [公开日志索引](reports/LOGS.md) |
| 调度、执行与评测流程 | [系统架构](docs/REPOSITORY_ARCHITECTURE.md) · [辅助 Agent 调度对照设计](docs/manta/FW_ABLATION.md) · [实验运行入口](scripts/manta/run_formal.py) |
| 图表与轨迹数据 | [图表与轨迹数据清单](demo/data/data_manifest.json) · [离线数据生成](scripts/demo/build_demo_data.py) · [图 1 绘图脚本](scripts/reporting/plot_showcase_tradeoff.py) · [图 2 绘图脚本](scripts/reporting/plot_showcase_provenance.py) |

## Credits

实验任务、工具与评分来自 AgentDojo，执行引擎来自仓库内的 MANTA 源码快照。 [AgentDojo 论文引用](docs/CITATION.bib) · [上游说明归档](archive/AGENTDOJO_UPSTREAM.md) · [MANTA 源码](upstreams/manta/) · [许可证](LICENSE)
