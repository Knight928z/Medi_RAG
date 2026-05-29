# 操作日志

> 说明：记录本地操作与变更，时间戳精确到秒。

## 2026-05-29

- 2026-05-29 10:25:10：初始化操作日志文件 `operation_log.md`。
- 2026-05-29 10:26:05：新增 `.gitignore`，忽略 `/data/` 与本地环境文件。
- 2026-05-29 10:26:20：删除 `data/.gitkeep`，确保知识库目录不被跟踪。
- 2026-05-29 10:26:45：实现 `workflows/graph.py` 的 LangGraph 编排与节点调用。
- 2026-05-29 10:27:10：更新 `apps/api/routers/reports.py`，接入同步工作流执行。
- 2026-05-29 10:27:25：新增 `tests/test_workflow.py` 的工作流执行测试。
- 2026-05-29 10:28:05：尝试执行工作流烟雾测试，系统 Python 缺少 `langgraph` 依赖，待统一环境后补测。
- 2026-05-29 10:29:40：提交变更（feat: wire minimal workflow and ops log）。
- 2026-05-29 10:29:55：推送提交到远程 `origin/main`。
