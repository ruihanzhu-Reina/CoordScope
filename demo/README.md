# MANTA × AgentDojo Research Demo

**超越通信拓扑：多智能体系统的信息流与执行动态研究**

用中文展示多智能体 AgentDojo 实验的评分、可观察信息来源、逐轮拓扑与执行成本。完整演示只需 Python 标准库和本机浏览器。

## 本地运行

在仓库根目录使用 Python 3.11 或更新版本运行。

```bash
python scripts/demo/build_demo_data.py
python -m http.server 8000 --directory demo
```

打开 [http://localhost:8000](http://localhost:8000)。预生成的 `demo/data/` 随分支提供，可以直接启动服务器。断开外网后可继续浏览全部页面和回放。

## 组会操作

- **总览**。点击 cohort 柱条，再按 Suite、Condition 和 Scene 筛选。参考复跑保留独立条目。
- **Insight 01–02**。点击 Exposure、Adoption、Execution 查看分母和定义。进入 Slack 07 图后，选择消息、网页读取、目标调用或 Agent 查看证据位置。
- **Insight 03**。选择 Suite、Condition、Scene 与 Turn。示例 `travel_15 / clean` 打开嵌套组对照。点击 Agent 查看结构角色与阶段。
- **Insight 04**。按 Suite 查看效用与资源，按 Clean 或 Attack 切换配对矩阵。角色 token 图使用完整 cohort 的角色汇总。
- **Insight 05**。播放、暂停、单步或拖动进度。全屏回放内可切换 Clean 与 Attack。
- **演示模式**。隐藏侧栏并展开讲解备注。使用页面底部按钮或正文获得焦点时的左右方向键切换章节。

## 数据与复现

| 页面 | 派生数据 | 归档来源 |
| --- | --- | --- |
| 总览与 Insight 01 | `summary.json`、`episodes.json` | [已完成实验汇总](../reports/2026-10-29-completed-experiments/README.md)、[原始 Flash/Star manifest](../reports/2026-10-19-manta-agentdojo/manifest.json)、[原始评分汇总](../reports/2026-10-19-manta-agentdojo/summary.json) |
| Insight 02 / 05 | `case_slack_07.json`、`audit_timeline.json` | [Slack 07 结构化证据](../reports/2026-10-19-manta-agentdojo/case_slack_07_evidence.json)、[工具调用表](../reports/2026-10-19-manta-agentdojo/case_slack_07_tool_calls.csv) |
| Insight 03 | `topology.json` | [Adaptive 报告](../reports/2026-10-28-deepseek-flash-adaptive/README.md)、[执行轮表](../reports/2026-10-28-deepseek-flash-adaptive/execution_graphs.csv)、[拓扑汇总](../reports/2026-10-28-deepseek-flash-adaptive/topology_summary.json)、[示例规格](../reports/2026-10-28-deepseek-flash-adaptive/topology_cases.json) 与四套件公开归档 |
| Insight 04 | `worker_comparison.json` | [F/W 报告](../reports/2026-10-29-agentdojo-flash16k-fw/README.md)、[概览](../reports/2026-10-29-agentdojo-flash16k-fw/overview.csv)、[分 suite](../reports/2026-10-29-agentdojo-flash16k-fw/by_suite.csv)、[配对](../reports/2026-10-29-agentdojo-flash16k-fw/fw_paired.csv)、[角色用量](../reports/2026-10-29-agentdojo-flash16k-fw/role_usage.csv) |

[`data_manifest.json`](data/data_manifest.json) 将每个派生数据集映射到仓库内的源文件及其 SHA-256。拓扑规格按归档的 job ID、selected attempt 和 turn 对齐。构建器从公开压缩归档读取结构字段，网页只加载派生 JSON。原始报告与代码链接在站内指向固定提交，查阅这些链接需要联网，仓库检出中的同路径文件也可离线打开。

```bash
python -m unittest discover -s tests/demo -v
```

测试涵盖 cohort 分母、暴露与未知值、逐轮拓扑、F/W 配对与成本、Slack 07 的消息和工具顺序，以及源文件哈希与派生数据的确定性复现。

## 证据边界

- 1,120 条有效记录来自七次运行的相同 80 个场景，其中有 76 个不同的 `(suite, task_id)`，含重复 Banking 任务。实验范围为 seed 42 和官方 direct attack。
- Exposure UNKNOWN 保持为 `null`。Adoption 缺整组语义标注，因此无聚合采纳率。Slack 07 展示可观察的来源和调用，完整上下文溯源仍待补齐。
- 审计结果来自 Slack 07 的 turn 级归档。审计与工具事件缺可对齐的时间戳，尾部的审计结果用于对照。全局 Auditor 准确率和 repair 成功率尚待评估。
- Adaptive 与 Star 采用不同完整配置。F/W 同时改变 Worker 调度和任务分派、汇报协议。拓扑、worker 数量及 Folded 内部组件的单独因果效果仍待隔离评估。
