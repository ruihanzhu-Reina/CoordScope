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

用配对实验与执行轨迹，研究多智能体如何协调、消耗多少资源，以及何时出现安全失败。

<a name="findings"></a>

## <img src="docs/assets/research-showcase/sparkles.svg" width="28" height="28" alt=""> Findings

在这批固定任务中，我们观察到：

- **增加 Agent 的收益有限。** 固定双辅助 Agent 只帮助少数任务，总 token 却增加了 84%。[配对分析](reports/2026-10-29-completed-experiments/README.md#fw-配对结果)
- **协调流程值得优先优化。** 精简后的完整执行协议完成更多任务，token 用量比原生自适应配置减少了 75%。[用量分析](reports/2026-10-29-completed-experiments/README.md#token-具体花在哪)
- **动态重组不保证更好的结果。** Flash 自适应配置确实改变了拓扑，但整体完成率与星形配置相同，开销更高。[拓扑分析](reports/2026-10-28-four-experiment-analysis/README.md)
- **完成率更高，不代表更安全。** Pro 星形配置完成更多任务，也出现了更多攻击成功记录。[结果对照](reports/2026-10-29-completed-experiments/README.md#结果总表)
- **识别攻击后仍可能执行攻击。** Slack 14 中，Agent 在警告中转述恶意内容，最终达成了攻击目标。[案例分析](reports/2026-10-28-four-experiment-analysis/README.md)

<a name="evaluation"></a>

## <img src="docs/assets/research-showcase/chart.svg" width="28" height="28" alt=""> Evaluation

每种配置使用相同的 80 个场景，分别评测正常与攻击条件。

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

加粗为最优观测值；↑ 越高越好，↓ 越低越好。结果仅覆盖本批固定任务与攻击设置。

GPT-6 Luna 名称按项目方向服务商核实后的反馈更正；原始请求标识为 `gpt-4o`。

<details>
<summary>实验设置与比较范围</summary>

实验涵盖 DeepSeek Flash、DeepSeek Pro 和 GPT-6 Luna，共六种配置。每组使用四个任务套件中的 80 个固定场景，对应 76 个不同用户任务，每个场景分别运行正常条件与攻击条件。六种配置加上一次按需调用方案的参考复跑，共有 1,120 条有效记录。实验采用 seed 42 和官方 direct 攻击。 [逐场景结果](reports/2026-10-29-completed-experiments/episode_results.csv) · [参考复跑](reports/2026-10-29-completed-experiments/README.md#重复运行与安全事件)

输出上限：DeepSeek Flash 和 GPT-6 Luna 的星形配置为每次请求 4,096 token（4K），其余配置为 16,384 token（16K）。表中的「总 token」则合计每组 80 次正常运行和 80 次攻击运行的用量。按需调用与固定调用两个辅助 Agent 的两组各有 4 条攻击记录的暴露状态未知。 [完整结果及指标定义](reports/2026-10-29-completed-experiments/README.md#结果总表)

两种辅助 Agent 调用方案的配对实验同时改变了辅助 Agent 启动、分工和汇报方式，比较对象是完整调度协议。其余历史配置还存在模型记录、输出上限和审计方式的差异，配置间比较用于描述观测结果。Flash 的历史模型记录包含 `deepseek-v4-flash` 和 `deepseek-flash`，Pro 记录为 `deepseek-v4-pro`。以上发现适用于这批单随机种子、固定攻击设置下的任务。 [实验设计与适用范围](reports/2026-10-29-completed-experiments/README.md#配置与证据边界)

</details>

<p align="center">
  <img src="docs/assets/research-showcase/worker-tradeoff.svg" width="760" alt="横轴为每种配置的总 token，纵轴为 Attack 任务完成率。按需调用辅助 Agent 为 7.14M 与 88.75%，固定调用两个辅助 Agent 为 13.14M 与 93.75%，历史自适应配置为 28.13M 与 82.50%。">
  <br>
  <em>图 1 · DeepSeek Flash 的三种执行配置：任务完成率与 token 开销（均为 16K 输出上限）。</em>
</p>

<a name="demo"></a>

## <img src="docs/assets/research-showcase/robot.svg" width="28" height="28" alt=""> Demo

按场景回放消息、网页读取与工具调用，对照正常和攻击轨迹。[打开演示说明](demo/README.md)

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
