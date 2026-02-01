# Arboris 长篇小说自动化流水线说明

本文档描述 Arboris 在「从概念到章节成稿」过程中的完整自动化流程、涉及的提示词、上下文载荷与模型参数。

---

## 1. 总体流程概览

```
项目创建 → 概念对话 → 蓝图生成/编辑 → 章节生成 → 版本评审/选择
     ↑                                            ↓
  （持续迭代） ← 手动编辑 ← 向量入库 ← 摘要提取 ← RAG 检索支撑下一章
```

关键能力由以下组件协作完成：

| 阶段 | 主要接口 | 提示词 ID | 模型温度 | 说明 |
|------|----------|-----------|----------|------|
| 概念对话 | `POST /api/novels/{id}/concept/converse` | `concept`（附带 JSON schema 指令） | 0.8 | 引导用户梳理世界观与剧情要素 |
| 蓝图生成 | `POST /api/novels/{id}/blueprint/generate` | `screenwriting` | 0.3 | 基于概念对话整理正式蓝图 |
| 章节生成 | `POST /api/writer/novels/{id}/chapters/generate` | `writing` | 0.9 | 结合蓝图、前情摘要与 RAG 结果生成章节草稿 |
| 章节评审 | `POST /api/writer/novels/{id}/chapters/evaluate` | `evaluation` | 0.3 | 对全部候选版本给出改进建议 |
| 摘要提取 | 调用 `LLMService.get_summary`（生成/编辑/选择时触发） | `extraction` | 0.15 | 对最终正文提炼真实摘要 |

所有提示词原文保存在 `backend/prompts/` 目录，可由 Prompt 管理界面动态更新。

---

## 2. 阶段详解

### 2.1 概念阶段（Concept Converse）

- **入口**：`POST /api/novels/{project_id}/concept/converse`
- **上下文**：
  - 历史概念对话（数据库 `NovelConversation` 表）
  - 用户本轮输入（JSON）
- **提示词**：`concept` + `JSON_RESPONSE_INSTRUCTION`（强制返回结构化 JSON）
- **LLM 参数**：温度 0.8，超时 240 秒
- **输出**：`ConverseResponse`，包含 AI 建议、UI 控件描述以及对话状态；当 `is_complete` 为真时，允许进入蓝图阶段。

### 2.2 蓝图生成（Blueprint）

- **入口**：`POST /api/novels/{project_id}/blueprint/generate`
- **上下文**：
  - 概念对话中成功解析的用户/助手消息（提取自存档 JSON）
- **提示词**：`screenwriting`
- **LLM 参数**：温度 0.3，超时 480 秒
- **输出**：结构化蓝图 JSON，映射到 `NovelBlueprint`（世界观、角色、章节纲要等）
- **后续**：
  - `PATCH /api/novels/{project_id}/blueprint` 可局部修改蓝图
  - `save_blueprint` 路径用于手动覆盖生成结果

### 2.3 章节生成（Writer.GenerateChapter）

- **入口**：`POST /api/writer/novels/{project_id}/chapters/generate`，请求体 `GenerateChapterRequest`
- **上下文组装**：
  1. **蓝图**：剔除章节细节字段（章节摘要、对话、角色动态等），仅保留世界观框架。
  2. ~~**已完成章节摘要**：逐章真实摘要；若缺失则调用 `get_summary` 以 `extraction` 提示词生成。~~
  3. **上一章桥接**：上一章真实摘要 + 正文末尾 500 字。
  4. **RAG 检索结果**（由 `ChapterContextService` 提供）：
     - 查询向量来源：章节标题 + 纲要摘要 + 可选写作指令 → `LLMService.get_embedding`
     - 文本来源：`VectorStoreService.query_chunks/query_summaries`（若数据库不支持向量函数，则回退到应用层余弦距离排序）
     - 默认 Top-K：正文片段 5 条、章节摘要 3 条（可通过环境变量调整）
  5. **写作提示词**：`writing`
- **LLM 参数**：温度 0.9，超时 600 秒，候选版本数默认为 3（可通过系统配置或环境变量覆盖）
- **输出**：章节候选版本数组（JSON），写入 `ChapterVersion`；`Chapter` 状态设置为 `generating`。

> **注意**：章节上下文生成失败（如无向量库）时，流程会降级为“蓝图 + 历史摘要”模式继续执行。

### 2.4 章节版本选择 / 手动编辑

- **选择版本**：`POST /api/writer/novels/{project_id}/chapters/select`
  - 选定后调用 `get_summary`（温度 0.15）生成真实摘要
  - 触发 `ChapterIngestionService.ingest_chapter` 切分正文、摘要并写入向量库

- **手动编辑**：`POST /api/writer/novels/{project_id}/chapters/edit`
  - 更新正文、重算摘要
  - 同样触发向量入库，以覆盖旧 chunk

### 2.5 章节评审（Evaluation）

- **入口**：`POST /api/writer/novels/{project_id}/chapters/evaluate`
- **上下文**：
  - 蓝图（完整结构）
  - 当前章节全部版本内容（按创建时间排序）
- **提示词**：`evaluation`
- **LLM 参数**：温度 0.3，超时 360 秒
- **输出**：评审报告文本，写入 `ChapterEvaluation`。

### 2.6 摘要提取（Summary Extraction）

- **触发点**：
  - 章节自动生成阶段（“前情摘要缺失”场景）
  - 章节版本确认
  - 手动编辑保存
- **调用**：`LLMService.get_summary`
- **提示词**：`extraction`
- **LLM 参数**：温度 0.15（默认 0.2，在调用处覆盖），超时 180 秒
- **目标**：为后续章节生成提供真实摘要，避免使用纲要内容。

---

## 3. 向量化与 RAG 细节

### 3.1 切分策略

- 默认使用 **LangChain `RecursiveCharacterTextSplitter`**：
  - `chunk_size = settings.vector_chunk_size`（默认 480）
  - `chunk_overlap = min(settings.vector_chunk_overlap, chunk_size // 2)`（默认 120）
  - 分隔符优先级：双换行 > 单换行 > 句号/问号/感叹号 > 逗号 > 空格 ➜ 确保靠近语义边界
- 若未安装对应依赖，则回退到内置段落 + 标点切分算法，配合日志提示。
- 摘要文本也使用同一套流程（通常为单条向量）。

### 3.2 向量存储

- **后端服务**：`VectorStoreService`
- **存储实现**：libsql（可本地 `file:`，亦可云端），需手动配置 `VECTOR_DB_URL`
- **表结构**：
  - `rag_chunks`（正文分块）：`id`、`project_id`、`chapter_number`、`chunk_index`、`chapter_title`、`content`、`embedding`、`metadata`
  - `rag_summaries`（章节摘要）：`id`、`project_id`、`chapter_number`、`title`、`summary`、`embedding`
- **检索策略**：
  - 优先使用 libsql 的 `vector_distance_cosine`；若未启用，回退到 Python 端计算余弦距离（排序后截取 Top-K）。
  - 查询向量由 `LLMService.get_embedding` 生成，支持 OpenAI 与 Ollama（通过 `EMBEDDING_PROVIDER` 切换）。

### 3.3 向量生命周期

- **插入/更新**：章节版本被确认或编辑保存后，先删除旧向量，再批量写入最新正文/摘要分块。
- **删除**：`delete_chapters` 接口会同步清理向量库，防止后续 RAG 读到过期内容。
- **日志**：向量 service 与 ingestion service 会在关键阶段输出日志（初始化、切分数量、写入成功/失败），便于排查。

---

## 4. 运行依赖与配置总览

| 配置项 | 说明 | 默认/来源 |
|--------|------|-----------|
| `OPENAI_*` | 默认生成模型配置 | `.env` 或系统配置表 |
| `EMBEDDING_PROVIDER` | 嵌入提供方（`openai` / `ollama`） | `.env` |
| `EMBEDDING_MODEL` / `OLLAMA_EMBEDDING_MODEL` | 具体嵌入模型名 | `.env` |
| `VECTOR_DB_URL` | libsql 数据库地址（支持 `file:`） | `.env` |
| `VECTOR_TOP_K_CHUNKS` / `VECTOR_TOP_K_SUMMARIES` | 检索数量 | `.env` / 系统配置 |
| `WRITER_CHAPTER_VERSION_COUNT` | 章节候选版本数 | 系统配置 / 环境变量 |

确保在部署环境中提前安装新依赖：

```bash
pip install -r backend/requirements.txt
```

---

如需进一步开发，请配合此文档查看对应模块的实现文件（`backend/app/services/*`、`backend/app/api/routers/*`、`backend/prompts/*`），保持提示词与代码逻辑的一致性。

