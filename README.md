<div align="center">

<img src="demo/assets/icons.svg" width="44" height="44" alt="">

<h1>超越通信拓扑</h1>

<p><strong>多智能体系统的信息流与执行动态研究</strong></p>
<p><em>Beyond Communication Topology: Understanding Information Flow and Execution Dynamics in Multi-Agent Systems</em></p>
<p>朱芮含 · MANTA × AgentDojo</p>

<p>
  <a href="#contributions">我的工作</a> ·
  <a href="#results">研究发现</a> ·
  <a href="#demo">演示预览</a> ·
  <a href="#reproducibility">实验与代码</a>
</p>

<p><strong>80</strong> 个冻结场景　·　<strong>6</strong> 种配置　·　<strong>1,120</strong> 条有效运行记录</p>

</div>

## Abstract

多智能体系统里，同一段外部内容可以经由同伴消息和工具读取进入不同 Agent 的输入。我把 MANTA 接入 AgentDojo 的官方任务环境、工具和评分，沿执行轨迹检查信息何时被看到、传递并转化为动作，再比较不同拓扑与 Worker 调度下的任务完成率、攻击成功率和资源开销。

## Contributions

- **接入执行引擎。** 我用适配层衔接 MANTA 的规划、调度和交接与 AgentDojo 的官方工具执行，将执行结果交回原有的 utility/security 评分。 [适配层](src/agentdojo_manta/adapter.py) · [系统架构](docs/REPOSITORY_ARCHITECTURE.md)
- **建立配对实验。** 我冻结场景和注入配置，记录运行状态与预算，支持失败续跑，并按场景对齐 Clean 和 Attack 的结果。 [运行入口](scripts/manta/run_formal.py) · [逐场景数据](reports/2026-10-29-completed-experiments/episode_results.csv)
- **重建实际执行。** 我将 Agent 消息、工具调用和拓扑快照对齐，核对信息到达路径、目标动作和调度成本。 [Slack 07 证据](demo/data/case_slack_07.json) · [逐轮拓扑](reports/2026-10-28-deepseek-flash-adaptive/execution_graphs.csv)
- **制作研究演示。** 我将归档数据做成可筛选的图表和逐步回放，给派生数据附上源文件位置和 SHA-256 校验值。 [演示说明](demo/README.md) · [数据清单](demo/data/data_manifest.json)

## Demo

演示可以按场景筛选，点击 Slack 07 的图边回查消息或工具事件，逐轮对照自适应拓扑，或切换 Clean 和 Attack 逐步回放。 [演示说明与操作路线](demo/README.md)

<p align="center">
  <img src="docs/assets/research-showcase/provenance-preview.png" width="880" alt="Slack 07 信息溯源图。蓝线表示 Agent 消息，虚线表示网页读取，橙线表示工具目标调用。右侧显示选中消息的发送和接收证据。">
  <br>
  <em>图 1 · Slack 07 的消息、网页读取和目标调用。右侧显示选中消息的证据。</em>
</p>

## Results

### 交接前已经发生目标调用

原始 Flash Star 的 80 条 Attack 记录中，74 条确认暴露、6 条暴露状态未知，官方评分记录到 1 次攻击成功。在这次成功案例 Slack 07 中，协调者在首次跨 Agent 交接前已发出两次目标调用。之后，两名 Worker 都收到相关内容并重读网页，其中一名发出了目标调用。Agent 是否采纳了攻击意图仍需逐条语义标注。 [Flash Star 报告](reports/2026-10-19-manta-agentdojo/README.md) · [结构化案例](demo/data/case_slack_07.json)

### 从运行轨迹重建拓扑变化

原生自适应配置的 160 条记录中，50 条执行了第二轮并改变了拓扑规格，其中 19 条改变了根拓扑模式。逐轮快照保留实际组成员和阶段顺序，可用来追踪结构变化。 [自适应实验报告](reports/2026-10-28-deepseek-flash-adaptive/README.md) · [逐轮快照](demo/data/topology.json)

### 固定双 Worker 多完成 4 项攻击场景任务

配对的 80 个 Attack 场景里，固定双 Worker（W）完成 **75 项**，按需 Worker（F）完成 **71 项**。Clean 与 Attack 两组合计，W 的总 token 比 F 高 **84.12%**。W 同时采用固定双 Worker 和相应的任务分派、汇报协议。 [F/W 配对结果](reports/2026-10-29-completed-experiments/fw_paired.csv) · [协议设计](docs/manta/FW_ABLATION.md)

<p align="center">
  <img src="docs/assets/research-showcase/worker-tradeoff.svg" width="760" alt="Flash 16K 配置对比。F 的总 token 为 7.14M，攻击下完成率 88.75%。W 为 13.14M 与 93.75%。原生自适应配置为 28.13M 与 82.50%。">
  <br>
  <em>图 2 · 横轴汇总每个配置的 160 条 Clean 与 Attack 记录的 token，纵轴按 80 条 Attack 记录计算任务完成率。</em>
</p>

| Flash 16K 配置 | Clean 完成率 ↑ | Attack 完成率 ↑ | 攻击成功数 ↓ | 总 token ↓ | 平均每条耗时 ↓ |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原生自适应（历史参照） | 81.25% | 82.50% | 1/80 | 28.13M | 209.23 s |
| F · 按需 Worker | 90.00% | 88.75% | 0/80 | **7.14M** | **29.90 s** |
| W · 固定双 Worker | **91.25%** | **93.75%** | 0/80 | 13.14M | 61.92 s |

> [!NOTE]
> 六种配置与一次参考复跑共用 80 个冻结场景，涵盖四个套件和 76 个不同用户任务。实验使用 seed 42 与 AgentDojo 官方 direct 攻击。F/W 各有 4 条 Attack 记录的暴露状态未知。历史配置间的结果用于描述观察到的差异。 [完整实验报告](reports/2026-10-29-completed-experiments/README.md)

## Reproducibility

| 查看内容 | 入口 |
| --- | --- |
| 实验配置、逐场景结果与配对统计 | [完整报告](reports/2026-10-29-completed-experiments/README.md) · [配置总表](reports/2026-10-29-completed-experiments/overview.csv) · [公开日志索引](reports/LOGS.md) |
| 适配层与调度设计 | [仓库架构](docs/REPOSITORY_ARCHITECTURE.md) · [Folded 执行配置](docs/manta/FOLDED_FLASH_16K.md) · [F/W 对照](docs/manta/FW_ABLATION.md) |
| 派生数据与图表复现 | [数据生成](scripts/demo/build_demo_data.py) · [数据测试](tests/demo/test_demo_data.py) · [图 2 脚本](scripts/reporting/plot_showcase_tradeoff.py) |

## Credits

AgentDojo 提供实验任务、工具和评分基准，仓库内的 MANTA 源码快照提供执行引擎。 [AgentDojo 项目](https://github.com/ethz-spylab/agentdojo) · [论文引用](CITATION.bib) · [MANTA 源码](upstreams/manta/) · [仓库许可证](LICENSE) · [MANTA 许可证](upstreams/manta/LICENSE)

<details>
<summary>AgentDojo 上游 README 与使用说明</summary>

<center>

# AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents

![GitHub License](https://img.shields.io/github/license/ethz-spylab/agentdojo) ![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/ethz-spylab/agentdojo/lint-docs.yaml)
 ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/agentdojo) ![PyPI - Downloads](https://img.shields.io/pypi/dm/agentdojo) ![PyPI - Version](https://img.shields.io/pypi/v/agentdojo)



[Edoardo Debenedetti](https://edoardo.science)<sup>1</sup>, [Jie Zhang](https://zj-jayzhang.github.io)<sup>1</sup>, [Mislav Balunović](https://www.sri.inf.ethz.ch/people/mislav)<sup>1,2</sup>, [Luca Beurer-Kellner](https://www.sri.inf.ethz.ch/people/luca)<sup>1,2</sup>, [Marc Fischer](https://marcfischer.at)<sup>1,2</sup>, [Florian Tramèr](https://floriantramer.com)<sup>1</sup>

<sup>1</sup>ETH Zurich and <sup>2</sup>Invariant Labs

[Read Paper](https://arxiv.org/abs/2406.13352) | [Inspect Results](https://agentdojo.spylab.ai/results/)
</center>

## Quickstart

```bash
pip install agentdojo
```

## MANTA adapter experiment

This public checkout also contains the V1 MANTA integration used for the
adaptive-topology security experiment. See [`docs/manta/README.md`](docs/manta/README.md)
for the adapter boundary, pinned MANTA snapshot, and one-episode smoke commands.

The completed **MANTA × AgentDojo** experiment (80 scenes, 160 valid paired
episodes, seed 42, official direct attack) is published with the full report,
CSV tables, configuration, checksums and all retained logs in redacted archives:
**[experiment report and logs](reports/2026-10-19-manta-agentdojo/README.md)**.

The follow-up context experiments (24 valid local worker replays and 6 native
graph continuations from 1 eligible checkpoint among 12 capture candidates)
are published separately with reports, configurations, analysis and all retained
redacted logs: **[context mechanism reports and logs](reports/2026-10-19-context-mechanisms/README.md)**.
These are exploratory mechanism studies and do not establish general failure
of graph-based defenses.

> [!IMPORTANT]
> Note that the API of the package is still under development and might change in the future.

If you want to use the prompt injection detector, you need to install the `transformers` extra:

```bash
pip install "agentdojo[transformers]"
```

## Running the benchmark

The benchmark can be run with the [benchmark](src/agentdojo/scripts/benchmark.py) script. Documentation on how to use the script can be obtained with the `--help` flag.

For example, to run the `workspace` suite on the tasks 0 and 1, with `gpt-4o-2024-05-13` as the LLM, the tool filter as a defense, and the attack with tool knowlege, run the following command:

```bash
python -m agentdojo.scripts.benchmark -s workspace -ut user_task_0 \
    -ut user_task_1 --model gpt-4o-2024-05-13 \
    --defense tool_filter --attack tool_knowledge
```

To run the above, but on all suites and tasks, run the following:

```bash
python -m agentdojo.scripts.benchmark --model gpt-4o-2024-05-13 \
    --defense tool_filter --attack tool_knowledge
```

## Inspect the results

To inspect the results, go to the dedicated [results page](https://agentdojo.spylab.ai/results/) of the documentation. AgentDojo results are also listed in the [Invariant Benchmark Registry](https://explorer.invariantlabs.ai/benchmarks/).Agent

## Documentation of the Dojo

Take a look at our [documentation](https://agentdojo.spylab.ai/).

## Development set-up

Take a look at the [development set-up](https://agentdojo.spylab.ai/development/) docs.

## Citing

If you use AgentDojo in your research, please consider citing our paper:

```bibtex
@inproceedings{
 debenedetti2024agentdojo,
 title={AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for {LLM} Agents},
 author={Edoardo Debenedetti and Jie Zhang and Mislav Balunovic and Luca Beurer-Kellner and Marc Fischer and Florian Tram{\`e}r},
 booktitle={The Thirty-eight Conference on Neural Information Processing Systems Datasets and Benchmarks Track},
 year={2024},
 url={https://openreview.net/forum?id=m1YYAQjO3w}
}
```

</details>
