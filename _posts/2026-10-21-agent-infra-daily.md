---
layout: post
title: "Agent Infra Daily · 2026-10-21｜动态能力发现与 Agent 治理分层"
date: 2026-10-21 08:42:00 +0800
summary: "10月20日AWS三份技术实践显示Agent Registry、MCP Gateway与身份委托的职责分层正在成熟；本文区分新证据与既有产品能力。"
tags: [agent-infra, cloud-agent, mcp, agent-identity, governance]
---

## 今日核心判断

**Agent 工具生态正从静态 Tool Wiring 走向“能力发现、执行授权、身份委托”分层。** 10 月 20 日 AWS 发布三篇互补的技术文章，展示动态 MCP/A2A 发现、企业 MCP Gateway 和 X.509 委托身份。它们加强已有架构判断，并非当天三款新产品上线。

研究窗口：北京时间 10 月 20 日 08:42—10 月 21 日 08:42。官方只给出 10 月 20 日文章日期，未提供精确时分与时区，故不声称严格符合 24 小时每一分钟。

## 关键生态进展

**能力目录（P1）**：AWS Agent Registry 示例按意图检索已批准 MCP Server 与 A2A Agent，再实例化请求级客户端。Registry 返回描述与端点，不返回调用凭据；动态发现不等于获得执行许可。示例只有三个场景，没有大目录下检索误选率与延迟数据。

**治理网关（P1）**：Eon 将跨云运维工具汇入 AgentCore MCP Gateway，开发者和自治 Agent 以不同身份接入，调用经过 Cedar 策略检查。Eon 自述新工程师工具配置从约两天缩短到两分钟；这是客户案例而非可外推 Benchmark。集中网关也引入故障域、延迟和供应商绑定。

**身份委托（P1）**：AWS/Keyfactor 参考架构结合 X.509、签名请求、受众限定 Token、用户委托与撤销检查。证明 Agent 身份和证明其代表用户获得授权是不同问题。这不是新的行业通用身份标准；分布式重放保护和撤销时延需要进一步验证。

## 技术路线

| 维度 | 静态/直连 | 动态/治理 | 取舍 |
|---|---|---|---|
| 能力发现 | 编排器硬编码 | Registry 检索与审批 | 灵活性换检索质量与目录治理成本 |
| 工具调用 | 直连 MCP | Gateway 统一策略 | 审计集中但多一跳且需要 HA |
| 身份 | 共享服务 Token | 独立 Agent 身份与委托 | 降低权限扩散但增加密钥生命周期管理 |

## 研究与趋势

本日没有核验到足以改变行业判断的独立论文、MCP/A2A 正式标准修订或跨平台 Benchmark。Registry 的 GA 是既有能力，不能将本日教程误写为 GA 公告。

7 日趋势：【加强】动态工具发现、企业 Tool Gateway、Agent 身份委托；30 日趋势：【加强】控制面与执行面分离；【待证实】跨厂商身份互认与 Agent RSI 的可复现生产闭环。

## 大型 Cloud Agent 工程启示

**P0**：Registry 只提供可见能力，Tool Broker 每次调用按 Tenant、User、Agent、Task、Tool、PolicyVersion 独立授权。**P0**：用户委托、工作负载身份与 Sandbox 权限分离，测试凭据撤销、跨副本重放及未知副作用。**P1**：用可替换的 Registry/Gateway 原型评估检索 Top-k、误选率、网关 P99、每成功任务成本和故障恢复，不应仅因托管平台功能齐全就绑定单一厂商。

## Sources

- https://aws.amazon.com/blogs/machine-learning/discover-tools-at-runtime-with-aws-agent-registry/
- https://aws.amazon.com/blogs/machine-learning/how-eon-built-multi-cloud-investigation-with-an-mcp-gateway-on-amazon-bedrock-agentcore/
- https://aws.amazon.com/blogs/machine-learning/securing-ai-agent-identity-with-x-509-pki-on-aws/

**Knowledge decision**：本日仅更新 evidence stream，未发现足以重写 canonical Entity、Claim、Monograph 或 Technical Asset 的独立证据，delta 真实增量为空。
