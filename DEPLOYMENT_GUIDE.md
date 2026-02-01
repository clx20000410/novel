# 人类化起点长篇写作系统 - 部署指南

## 版本信息
- **提交 ID**: d5213c4
- **更新日期**: 2026-01-13
- **核心改进**: 三层架构重构，解决单章 1234 闭环、主角全知、角色突兀等问题

---

## 一、数据库迁移（必须执行）

在部署新版本前，需要执行以下 SQL 迁移脚本：

```sql
-- 给 chapter_outlines 表添加 metadata 字段
ALTER TABLE chapter_outlines ADD COLUMN metadata JSON NULL;
```

**执行方式**：
```bash
# 进入数据库容器
docker exec -it <mysql_container_name> mysql -u root -p

# 选择数据库
USE ai_novel;

# 执行迁移
ALTER TABLE chapter_outlines ADD COLUMN metadata JSON NULL;
```

---

## 二、Docker 重新部署

```bash
# 1. 拉取最新代码
cd /path/to/AI-novel
git pull origin main

# 2. 重新构建并启动容器
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# 3. 验证服务状态
docker-compose ps
docker-compose logs -f backend
```

---

## 三、新增提示词初始化

系统会自动在 `init_db` 时插入新的提示词，但如果数据库中已存在同名提示词，不会自动覆盖。

**建议手动检查并更新以下提示词**：

| 提示词名称 | 文件路径 | 用途 |
|-----------|---------|------|
| `chapter_plan` | `backend/prompts/chapter_plan.md` | L2 导演脚本生成 |
| `writing_v2` | `backend/prompts/writing_v2.md` | 精简硬约束写作提示词 |
| `rewrite_guardrails` | `backend/prompts/rewrite_guardrails.md` | 违规内容自动修复 |
| `editor_review` | `backend/prompts/editor_review.md` | AI Review 评审标准 |

**手动更新方式**：
1. 进入后台管理界面
2. 找到「提示词管理」
3. 新增或更新上述提示词，内容从对应文件复制

---

## 四、配置项说明

### 4.1 章节版本数量
现在支持以下配置方式（按优先级排序）：

1. **数据库配置**（推荐）：
   - 键名：`writer.chapter_versions`（新）或 `writer.version_count`（旧，兼容）
   - 值：整数，如 `2`

2. **环境变量**：
   - `WRITER_CHAPTER_VERSION_COUNT`
   - `WRITER_CHAPTER_VERSIONS`
   - `WRITER_VERSION_COUNT`（旧，兼容）

3. **默认值**：`settings.writer_chapter_versions`（默认 2）

---

## 五、新增文件清单

| 文件路径 | 类型 | 说明 |
|---------|------|------|
| `backend/app/services/writer_context_builder.py` | 服务 | 信息可见性过滤 |
| `backend/app/services/chapter_guardrails.py` | 服务 | 后置一致性检查 |
| `backend/prompts/chapter_plan.md` | 提示词 | L2 导演脚本 |
| `backend/prompts/writing_v2.md` | 提示词 | 精简硬约束 |
| `backend/prompts/rewrite_guardrails.md` | 提示词 | 自动修复 |
| `backend/prompts/editor_review.md` | 提示词 | AI Review |
| `backend/db/migrations/add_chapter_outline_metadata.sql` | 迁移 | 数据库结构变更 |

---

## 六、验收标准

部署完成后，请验证以下功能：

### 6.1 配置生效
- 后台设置 `writer.chapter_versions=2`，生成章节时应只产生 2 个版本

### 6.2 导演脚本生成
- 生成章节时，日志中应出现「成功生成章节导演脚本: macro_beat=X」

### 6.3 信息可见性
- 日志中应出现「信息可见性: 已登场=X, 允许新登场=X, 禁止=X」

### 6.4 护栏检查
- 如果正文中出现禁止角色名，日志中应出现「检测到 X 个违规」

---

## 七、回滚方案

如果新版本出现问题，可以回滚到上一个版本：

```bash
cd /path/to/AI-novel
git checkout 794a304  # 上一个稳定版本
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

**注意**：回滚后需要手动删除 `chapter_outlines.metadata` 列（如果已添加）。

---

## 八、常见问题

### Q1: 生成章节时报错「缺少写作提示词」
**A**: 系统优先使用 `writing_v2`，如果不存在则 fallback 到 `writing`。请确保至少有一个提示词存在。

### Q2: 导演脚本生成失败
**A**: 检查是否已添加 `chapter_plan` 提示词。如果未配置，系统会跳过导演脚本生成，使用默认模式。

### Q3: 护栏检查没有触发
**A**: 护栏检查需要 `forbidden_characters` 列表非空。如果所有角色都已登场，则不会触发禁止角色检测。
