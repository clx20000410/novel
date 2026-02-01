# AI-Novel 架构融合文档

## 概述

本文档描述了从 [AI_NovelGenerator](https://github.com/YILING0013/AI_NovelGenerator) 项目融合的核心功能和设计理念。

## 融合内容

### P1 优先级（核心功能）

#### 1. 章节蓝图元数据 (ChapterBlueprint)

**来源**: `AI_NovelGenerator/novel_generator/blueprint.py`

**新增模型**: `backend/app/models/chapter_blueprint.py`

**核心字段**:
- `suspense_density`: 悬念密度（compact/gradual/explosive/relaxed）
- `foreshadowing_ops`: 伏笔操作（plant/reinforce/payoff/none）
- `cognitive_twist_level`: 认知颠覆等级（1-5）
- `chapter_function`: 章节功能（progression/turning/revelation/buildup/climax/resolution/interlude）

**用途**: 指导 L2 Director 生成章节任务，实现"慢节奏 + 跨章起承转合"。

---

#### 2. 项目记忆 (ProjectMemory)

**来源**: `AI_NovelGenerator/novel_generator/finalization.py`

**新增模型**: `backend/app/models/project_memory.py`

**核心字段**:
- `global_summary`: 全局摘要，每章定稿后更新，控制在2000字以内
- `plot_arcs`: 剧情线追踪（未回收伏笔、主线矛盾、角色弧线）
- `story_timeline_summary`: 故事时间线摘要

**用途**: 提供跨章节的长程记忆，解决"上下文太长塞不进 prompt"的问题。

---

#### 3. 知识检索服务 (KnowledgeRetrievalService)

**来源**: `AI_NovelGenerator/novel_generator/knowledge.py`

**新增服务**: `backend/app/services/knowledge_retrieval_service.py`

**核心功能**:
1. **检索关键词生成**: 基于章节蓝图生成检索词
2. **向量检索**: topK 相关内容检索
3. **知识过滤**: 冲突检测/价值分级/结构化整理
4. **POV可见性裁剪**: 配合有限视角，只保留POV角色能知道的信息

**输出结构**:
```python
FilteredContext(
    plot_fuel=[...],        # 情节燃料
    character_info=[...],   # 人物维度
    world_fragments=[...],  # 世界碎片
    narrative_techniques=[...],  # 叙事技法
    warnings=[...]          # 冲突警告
)
```

---

#### 4. 一致性检查服务 (ConsistencyService)

**来源**: `AI_NovelGenerator/consistency_checker.py`

**新增服务**: `backend/app/services/consistency_service.py`

**检查维度**:
1. **设定一致性**: 世界观规则、魔法/科技体系
2. **角色状态一致性**: 位置、能力、知识、性格
3. **剧情逻辑一致性**: 因果关系、时间线
4. **伏笔一致性**: 已埋伏笔的引用和回收

**冲突等级**:
- `critical`: 严重冲突，自动触发重写
- `major`: 主要问题，生成修订版本供选择
- `minor`: 轻微问题，仅标注提示

---

### P2 优先级（增强功能）

#### 5. 章节扩写服务 (EnrichmentService)

**来源**: `AI_NovelGenerator/novel_generator/enrich_chapter_text`

**新增服务**: `backend/app/services/enrichment_service.py`

**核心功能**:
1. **字数检测**: 检查是否低于目标字数的70%
2. **智能扩写**: 加戏不加线
   - 感官描写（视觉、听觉、触觉、嗅觉、味觉）
   - 对话潜台词（人物内心活动、言外之意）
   - 余波Sequel（事件发生后的情绪反应、思考）
   - 环境氛围（场景细节、天气、光影）
   - 动作细节（肢体语言、微表情）

**用途**: 稳定保持每章2k~4k字，适合起点风格的网文。

---

#### 6. 定稿服务 (FinalizeService)

**来源**: `AI_NovelGenerator/novel_generator/finalization.py`

**新增服务**: `backend/app/services/finalize_service.py`

**定稿流程**:
1. 更新全局摘要 (global_summary)
2. 更新角色状态 (character_state)
3. 更新剧情线追踪 (plot_arcs)
4. 写入向量库 (vectorstore)
5. 创建章节快照 (chapter_snapshot)

**用途**: "生成后闭环"的核心服务，确保长程一致性。

---

#### 7. 章节蓝图服务 (BlueprintService)

**新增服务**: `backend/app/services/blueprint_service.py`

**核心功能**:
1. **蓝图CRUD**: 章节蓝图的增删改查
2. **自动生成**: 从大纲自动生成蓝图元数据
3. **模板管理**: 预设模板（高潮章节、铺垫章节、过渡章节、转折章节）
4. **节奏分析**: 分析项目的节奏分布，给出优化建议

---

## 数据库变更

### 新增表

| 表名 | 说明 |
|------|------|
| `project_memories` | 项目记忆表，存储全局摘要和剧情线 |
| `chapter_snapshots` | 章节快照表，存储每章定稿时的状态 |
| `chapter_blueprints` | 章节蓝图表，存储节奏控制元数据 |
| `blueprint_templates` | 蓝图模板表，存储预设模板 |

### 迁移命令

```bash
cd backend
alembic revision --autogenerate -m "Add fusion models"
alembic upgrade head
```

---

## 服务依赖关系

```
KnowledgeRetrievalService
    ├── LLMService
    ├── VectorStoreServiceExt
    └── ChapterBlueprint (model)

ConsistencyService
    ├── LLMService
    ├── ProjectMemory (model)
    └── Foreshadowing (model)

FinalizeService
    ├── LLMService
    ├── VectorStoreServiceExt
    ├── ProjectMemory (model)
    ├── ChapterSnapshot (model)
    └── CharacterState (model)

EnrichmentService
    └── LLMService

BlueprintService
    ├── LLMService
    ├── ChapterBlueprint (model)
    └── BlueprintTemplate (model)
```

---

## 使用示例

### 1. 章节生成前获取上下文

```python
from app.services import KnowledgeRetrievalService

service = KnowledgeRetrievalService(db, llm_service, vector_store_service)

# 获取完整上下文
context = await service.get_chapter_context(
    project_id="xxx",
    chapter_number=5,
    user_id=1,
    pov_character="主角名"
)

# context 包含:
# - global_summary: 全局摘要
# - plot_arcs: 剧情线追踪
# - blueprint: 章节蓝图
# - recent_chapters: 前几章摘要
# - filtered_knowledge: 过滤后的知识
# - character_state: 角色状态
```

### 2. 章节定稿

```python
from app.services import FinalizeService

service = FinalizeService(db, llm_service, vector_store_service)

result = await service.finalize_chapter(
    project_id="xxx",
    chapter_number=5,
    chapter_text="章节正文...",
    user_id=1
)

# result 包含:
# - success: 是否成功
# - updates: 更新了哪些内容
```

### 3. 一致性检查

```python
from app.services import ConsistencyService

service = ConsistencyService(db, llm_service)

result = await service.check_and_fix(
    project_id="xxx",
    chapter_text="章节正文...",
    user_id=1,
    auto_fix_threshold=ViolationSeverity.CRITICAL
)

# result 包含:
# - check_result: 检查结果
# - fixed_content: 修复后的内容（如果有）
# - needs_manual_review: 是否需要人工审核
```

### 4. 字数扩写

```python
from app.services import EnrichmentService

service = EnrichmentService(db, llm_service)

result = await service.check_and_enrich(
    chapter_text="章节正文...",
    target_word_count=3000,
    user_id=1
)

if result:
    print(f"扩写完成: {result.original_word_count} -> {result.enriched_word_count}")
```

---

## 后续计划

1. **API 路由**: 为新服务添加 REST API 端点
2. **前端集成**: 在前端添加蓝图编辑、一致性检查等功能
3. **性能优化**: 添加缓存、批量处理等优化
4. **测试覆盖**: 为新服务添加单元测试和集成测试
