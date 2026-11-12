<div align="center">

<h1>超越通信拓扑<br>多智能体系统的信息流与执行动态研究</h1>

<p><em>Beyond Communication Topology: Understanding Information Flow and Execution Dynamics in Multi-Agent Systems</em></p>

<p><strong>朱芮含</strong> · MANTA × AgentDojo</p>

<p>
  <a href="#demo"><strong>交互演示</strong></a> ·
  <a href="#results"><strong>实验结果</strong></a> ·
  <a href="reports/2026-10-29-completed-experiments/README.md"><strong>完整报告</strong></a> ·
  <a href="docs/REPOSITORY_ARCHITECTURE.md"><strong>仓库架构</strong></a>
</p>

<p><strong>4</strong> 个任务套件　 ·　 <strong>80</strong> 个冻结场景　 ·　 <strong>1,120</strong> 条有效 episode 记录</p>

</div>

## Abstract

当外部内容进入多智能体系统，安全风险取决于 Agent **看到了什么、如何传递信息、最后执行了什么**。这个项目将 MANTA 的多智能体执行层接入 AgentDojo，在官方任务环境与评分下比较静态、自适应和不同 Worker 调度配置，并用归档轨迹重建可观察的信息来源和工具动作。在归档案例中，协调者在交接前已执行目标调用；在配对评测中，固定双 Worker 带来更多攻击下的任务完成，同时增加了 token 开销。

## Contributions

| 我的项目工作 | 实现与产出 |
| --- | --- |
| **系统适配** | 将 MANTA 的规划、交接和工具调用接入 AgentDojo 的官方任务环境、`FunctionsRuntime` 与 utility/security 评分，统一记录执行轨迹。 [适配层](src/agentdojo_manta/adapter.py) · [接口说明](docs/manta/GPT4O_ADAPTER.md) |
| **可复现评测** | 建立冻结场景、配对运行、失败与续跑管理、预算记账和离线核算流程。以共同的 Clean/Attack 场景比较六种配置，并单列一次参考复跑。 [运行入口](scripts/manta/run_formal.py) · [逐场景结果](reports/2026-10-29-completed-experiments/episode_results.csv) |
| **机制与效率分析** | 从消息、网页重读和工具调用对齐 Slack 07 轨迹，重建实际拓扑变化，并用 F/W 配对比较按需与固定双 Worker 调度。 [案例证据](demo/data/case_slack_07.json) · [拓扑记录](reports/2026-10-28-deepseek-flash-adaptive/execution_graphs.csv) · [F/W 配对](reports/2026-10-29-completed-experiments/fw_paired.csv) |
| **研究演示** | 将归档结果做成可筛选、可单步回放的离线网页。派生数据附有源文件和 SHA-256，支持从图表回查证据。 [演示说明](demo/README.md) · [数据清单](demo/data/data_manifest.json) |

## Results

**一次暴露如何演变成攻击成功？** 原始 Flash Star 的 80 条 Attack episode 中，74 条确认暴露、6 条状态未知，官方评分记录到 1 次攻击目标达成。在 Slack 07，协调者首次命中发生在跨 Agent 交接前；两名 Worker 此后都收到相关内容并重读网页，只有一名 Worker 调用了攻击目标。这个案例把**消息传递、工具重读和实际执行**对齐到同一条轨迹。Agent 是否采纳攻击意图仍需逐条语义标注。 [Flash Star 报告](reports/2026-10-19-manta-agentdojo/README.md) · [结构化案例](demo/data/case_slack_07.json)

**额外协作带来多少收益？** 在配对的 Attack 场景中，W（固定双 Worker）比 F（按需 Worker）多完成 **4 项任务**，按 Clean 和 Attack 两组合计，W 的总 token 比 F 高 **84.12%**。原 Flash 16K 自适应配置提供历史参照。 [完整结果](reports/2026-10-29-completed-experiments/README.md) · [F/W 协议](docs/manta/FW_ABLATION.md)

<p align="center">
  <img src="docs/assets/research-showcase/worker-tradeoff.svg" width="760" alt="Flash 16K 的三种配置在总 token 与攻击下任务完成率上的对照。按需 F 为 7.14M 与 88.75%，固定双 Worker W 为 13.14M 与 93.75%，原自适应配置为 28.13M 与 82.50%。">
  <br>
  <em>图 1 · 横轴汇总每个配置的 160 条 Clean + Attack episode 的 token，纵轴以 80 条 Attack episode 为分母计算官方任务完成率。</em>
</p>

| Flash 16K 配置 | Clean Utility ↑ | Attack Utility ↑ | Targeted ASR ↓ | 总 token ↓ | 平均每条耗时 ↓ |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原自适应（历史参照） | 81.25% | 82.50% | 1/80 | 28.13M | 209.23 s |
| F · 按需 Worker | 90.00% | 88.75% | 0/80 | **7.14M** | **29.90 s** |
| W · 固定双 Worker | **91.25%** | **93.75%** | 0/80 | 13.14M | 61.92 s |

每次完整运行使用同一组 80 个冻结场景，涵盖 76 个不同用户任务，分别执行 Clean 与 Attack。F/W 比较的是两种完整调度协议，其中 W 同时引入分派和汇报步骤。结果适用于 seed 42 下的官方 direct 攻击；F/W 各有 4 条 Attack episode 的暴露状态未知。历史参照和 F/W 配置之间的差异属于描述性比较。 [完整配置与证据边界](reports/2026-10-29-completed-experiments/README.md#配置与证据边界)

## Demo

从总览筛选配置，或进入 **Slack 07 信息溯源图**，点击消息、网页读取路径或工具调用查看证据。自适应拓扑页支持逐轮对照，F/W 页可按套件比较成本与完成率，回放页可在 Clean 和 Attack 之间切换。

<p align="center">
  <img src="docs/assets/research-showcase/provenance-preview.png" width="880" alt="Slack 07 信息溯源演示。实线标出 Agent 消息与工具调用，虚线标出网页读取，右侧显示选中消息的来源证据。">
  <br>
  <em>图 2 · 离线演示的 Slack 07 信息溯源页。</em>
</p>

在仓库根目录使用 Python 3.11+ 启动演示。预生成数据已随仓库提供。

```bash
python -m http.server 8000 --bind 127.0.0.1 --directory demo
```

打开 [http://localhost:8000](http://localhost:8000)。重建数据、运行验证和查看来源的步骤见 [演示 README](demo/README.md)。

## Reproducibility

| 阅读路线 | 入口 |
| --- | --- |
| 复核完整实验设置和分项结果 | [结果汇总](reports/2026-10-29-completed-experiments/README.md) · [配置总表](reports/2026-10-29-completed-experiments/overview.csv) · [公开日志索引](reports/LOGS.md) |
| 查看系统实现与评测边界 | [仓库架构](docs/REPOSITORY_ARCHITECTURE.md) · [Folded 配置](docs/manta/FOLDED_FLASH_16K.md) · [F/W 对照设计](docs/manta/FW_ABLATION.md) |
| 重新生成展示数据和图表 | [离线数据脚本](scripts/demo/build_demo_data.py) · [数据测试](tests/demo/test_demo_data.py) · [图 1 脚本（Matplotlib）](scripts/reporting/plot_showcase_tradeoff.py) |

## Credits

本项目使用 Debenedetti 等人的 [AgentDojo](https://github.com/ethz-spylab/agentdojo) 作为任务、工具和评分基准，并基于仓库内的 [MANTA 源码快照](upstreams/manta/) 进行适配。参见 [AgentDojo 论文引用](CITATION.bib)、[仓库许可证](LICENSE)和 [MANTA 许可证](upstreams/manta/LICENSE)。

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
