# Medi_RAG

本项目是一个面向生产的本地医疗报告解读多智能体系统，采用 FastAPI + LangGraph + PostgreSQL(pgvector) + Redis，支持结构化状态传递、可追踪工作流、RAG 检索与校验。

## 主要特性

- 多智能体协作（Planner/Parser/Retriever/Reasoning/Validator/Memory）
- 结构化 JSON 状态传递（可持久化）
- PostgreSQL + pgvector 持久化与向量检索
- Redis 短期记忆与状态缓存
- 分层记忆：Redis 会话态、PostgreSQL 长期用户/患者历史、pgvector 语义案例与推理链
- 自反思验证：Validator 检测幻觉/引用/schema/一致性，Critic 审查推理链并限次触发重写
- 本地模型推理（Ollama/vLLM）

## 目录结构

详见 `apps/`, `agents/`, `workflows/`, `storage/`, `retrieval/`, `llm/` 等模块。

## 快速开始（本地）

> 需要提前准备本地模型服务（Ollama 或 vLLM）。

- 初始化数据库表：
  - 使用 `python scripts/init_db.py`

- 启动 FastAPI：
  - 使用 `uvicorn apps.api.main:app --reload`

- 录入知识库文档：
  - 使用 `python scripts/ingest_data.py --data-dir ./data`

- 生成迁移脚本（Alembic）：
  - 使用 `alembic revision --autogenerate -m "init"`
  - 使用 `alembic upgrade head`

## 容器化部署

- 使用 `docker-compose.yml` 启动 PostgreSQL + Redis + API 服务。

## 说明

当前为增量构建的基础骨架，后续将逐步完善 LangGraph 工作流与持久化逻辑。

`/data` 目录用于放置知识库文件，已在 `.gitignore` 中忽略。

工作流执行时会记录 `trace` 字段用于审计追踪。

健康检查：`/health`、`/health/db`、`/health/redis`、`/health/ollama`。

检索子系统支持：PDF/TXT/Markdown → 分块 → BGE-M3 向量化 → pgvector 索引 → BM25/向量融合检索。

如需启用检索查询改写（本地中文模型：DeepSeek/Qwen/Llama），设置 `RETRIEVAL_QUERY_REWRITE=true`。

## 记忆子系统

记忆层级：

- 短期工作流记忆：Redis 保存当前请求/会话状态，使用 `MEMORY_SHORT_TTL_SECONDS` 控制过期。
- 长期用户记忆：PostgreSQL 保存历史报告、历史会话、工作流摘要，可通过 `MEMORY_LONG_TTL_DAYS` 配置长期记忆过期策略。
- 语义记忆：`memory_entries.embedding` 使用 pgvector 检索相似历史案例与历史 reasoning trace。

主要接口：

- `GET /memory/context`：聚合短期、长期、语义和历史工作流上下文。
- `GET /memory/semantic`：按 query 做语义记忆搜索。
- `GET /memory/workflows`：按 `user_id` 或 `patient_id` 查历史工作流。

工作流执行 `/reports/interpret` 时会先检索并压缩记忆上下文，再把完成后的工作流摘要写回长期记忆和语义记忆，避免把原始报告、完整 trace 或无界对话历史塞进上下文窗口。

## 验证与自反思子系统

工作流顺序：

`ReasoningAgent → ValidatorAgent → CriticAgent → optional retry ReasoningAgent → SynthesisAgent → MemoryAgent`

Validator 负责：

- 检测幻觉与无依据陈述
- 校验 retrieved citation 是否可追溯
- 检查 reasoning 逻辑一致性
- 验证 parsed_report schema 正确性
- 输出 `validation_score`、`validation_issues`、`validation_passed`

Critic 负责：

- 审查 reasoning chain 是否完整
- 标记弱证据与缺失上下文
- 基于 Validator 结果判断是否需要重写
- 通过 `MAX_REFLECTION_ITERATIONS` 限制自反思重试次数

验证历史会写入 `validation_history`，用于后续评估 dashboard：

- `GET /evaluation/validation-history/{request_id}`
- `GET /evaluation/dashboard`

所有失败都会保留 `code/severity/reason/suggested_action`，便于解释、审计和后续 dashboard 聚合。
