---
layout: post
title: "Agent Infra Daily：模型准入与执行治理开始分层"
date: 2026-11-25 08:00:00 +0800
summary: "Bedrock 可信准入 API 正式商用，Agents SDK 正式版强化安全边界，跨 Worker 恢复仍处于预览。"
tags: [agent-infra, governance, harness, cloud-agent]
---

## 今日核心判断

Agent 平台需要把模型准入、数据留存、工具授权与任务恢复分成独立控制面。过去约24小时核验到两个正式交付信号，但没有证据表明跨厂商统一执行契约已经成熟。

## 重大进展

**AWS Bedrock Trusted Access API（P0 产品信号）。** 官方文章标注11月23日，仓库 RSS 时间为11月24日13:01北京时间，两者日期口径不同，按 RSS 时间纳入本期，不能确认精确上线时刻。API 已 GA，而 Anthropic EFS/EDC 仍为公开预览。准入申请与接受条款分离，可按账户、组织、项目治理。数据保留方案有区域配置要求。其意义在于模型选择不再只是价格和质量排序，还受租户合规约束；预览不能当作正式合规承诺，亦非跨步骤工具授权标准。

**OpenAI Agents SDK v0.26.0（P1 正式版本）。** 北京时间11月24日11:15发布。正式版限制 Docker 存储挂载权限，修复归档路径校验资源边界、Realtime 输出检查以及会话历史脱敏。多个修复共同说明安全边界必须覆盖模型输出、持久化和运行环境，而非只检查工具参数。Release 不提供独立规模测试，不能据此断言隔离完整。

**历史对照：Agents SDK v1.0.0-alpha.2。** 北京时间11月24日04:11发布，略早于观察窗口。支持跨 Worker 恢复会话及待审批状态，要求条件原子写入的会话存储，并明确先升级读取端再升级写入端。新旧快照不双向兼容。这是预发布，不是正式生产承诺。Codex 0.174.0-alpha.4 于25日07:01发布，但说明不足，不推断新增架构。

## 架构路线与取舍

托管路线将模型准入和数据策略交给云平台，降低接入复杂度，但区域、租户资格和供应商条款可能约束故障切换。SDK 路线让应用控制审批、状态存储及运行环境，灵活性更高，却需要自行验证版本迁移、并发与安全隔离。二者互补，不应把模型准入等同于工具调用授权。

## 标准与研究

本次有限独立检索未核验到新的 MCP/A2A 正式标准或足以改变选型的论文；不将预览 API 视为标准。MCP 旧仓库 Release API 返回迁移提示，标准检索覆盖不完整。

## 7/30 天趋势雷达（分析）

| 趋势 | 7天 | 30天 |
|---|---|---|
| 模型与工具治理分层 | 加强：准入 API | 加强：与10月21日 Registry 参考架构互补，但仍缺独立验证 |
| 持久执行 | 加强：SDK 预览恢复契约 | 待证实：跨后端恢复及副作用正确性 |
| Sandbox 可移植性 | 待证实：安全修复不等于可移植 | 待证实：缺统一状态与隔离语义 |
| 单位任务经济性 | 待证实 | 待证实：缺跨厂商可比生产数据 |

## 百万用户 Cloud Agent 工程建议

优先建设 ModelEligibilityPolicy：按租户、区域、模型和数据分类记录允许的留存模式、准入状态及策略版本。路由先做合规过滤，再优化单位成功任务成本；故障切换不得静默放宽留存策略。将策略版本写入任务 Checkpoint，恢复时重新校验。审批记录使用 CAS 防止并发恢复重复消费；外部写入另设幂等账本和对账流程。

验收覆盖跨区域缺失配置、模型资格撤销、旧 Worker 读取新快照、归档异常资源消耗、审批并发恢复。记录拒绝原因、策略版本、重复副作用率和恢复延迟，不记录不必要的敏感原文。

## 情报质量

11月25日快照读取返回404；最新11月24日质量快照：19/19信源健康、35候选、903未核验积压、2个已核验事件。Gold 样本为0，无法计算召回率。两项预测仍开放，未到期，不改条件或概率。今日不修改长期 KG，Delta 四组空数组。独立检索有限，不代表全行业无其他进展。

## 官方 Sources

- [AWS Trusted Access API](https://aws.amazon.com/blogs/machine-learning/introducing-the-amazon-bedrock-trusted-access-api-with-anthropics-enterprise-frontier-safeguards-and-enterprise-data-controls/)
- [AWS 数据留存文档](https://docs.aws.amazon.com/bedrock/latest/userguide/data-retention.html)
- [Agents SDK v0.26.0](https://github.com/openai/openai-agents-python/releases/tag/v0.26.0)
- [Agents SDK v1.0.0-alpha.2](https://github.com/openai/openai-agents-python/releases/tag/v1.0.0-alpha.2)
- [Codex alpha.4](https://github.com/openai/codex/releases/tag/rust-v0.174.0-alpha.4)
