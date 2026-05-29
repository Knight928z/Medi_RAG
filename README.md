# Medi_RAG

本项目是一个面向生产的本地医疗报告解读多智能体系统，采用 FastAPI + LangGraph + PostgreSQL(pgvector) + Redis，支持结构化状态传递、可追踪工作流、RAG 检索与校验。

## 主要特性

- 多智能体协作（Planner/Parser/Retriever/Reasoning/Validator/Memory）
- 结构化 JSON 状态传递（可持久化）
- PostgreSQL + pgvector 持久化与向量检索
- Redis 短期记忆与状态缓存
- 本地模型推理（Ollama/vLLM）

## 目录结构

详见 `apps/`, `agents/`, `workflows/`, `storage/`, `retrieval/`, `llm/` 等模块。

## 快速开始（本地）

> 需要提前准备本地模型服务（Ollama 或 vLLM）。

- 初始化数据库表：
  - 使用 `python scripts/init_db.py`

- 启动 FastAPI：
  - 使用 `uvicorn apps.api.main:app --reload`

## 容器化部署

- 使用 `docker-compose.yml` 启动 PostgreSQL + Redis + API 服务。

## 说明

当前为增量构建的基础骨架，后续将逐步完善 LangGraph 工作流与持久化逻辑。

`/data` 目录用于放置知识库文件，已在 `.gitignore` 中忽略。
