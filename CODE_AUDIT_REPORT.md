# AI-Novel 代码审计报告

**审计日期**: 2026-01-13  
**审计范围**: 提示词、服务层、路由层  
**提交 ID**: 8d7b903

---

## 一、提示词审计结果

### 1.1 已修复问题

| 问题 | 修复方案 | 状态 |
|------|---------|------|
| `outline.md` 与代码引用 `outline_generation` 不一致 | 重命名为 `outline_generation.md` | ✅ |
| `editor_review.md` 未被代码调用 | 新增 `ai_review_service.py` 集成 | ✅ |
| `writing_enhanced.md` 未被使用 | 已删除 | ✅ |
| `writing_original.md` 未被使用 | 已删除 | ✅ |

### 1.2 当前提示词使用情况

| 提示词名称 | 引用位置 | 用途 |
|-----------|---------|------|
| `chapter_plan` | writer.py L118 | L2 导演脚本生成 |
| `concept` | novels.py L172 | 概念阶段对话 |
| `editor_review` | ai_review_service.py | 多版本评审 |
| `evaluation` | writer.py L622 | 章节评审 |
| `extraction` | llm_service.py L69 | 信息提取 |
| `import_analysis` | import_service.py L387 | 导入分析 |
| `optimize_dialogue` | optimizer.py | 对话优化 |
| `optimize_environment` | optimizer.py | 环境优化 |
| `optimize_psychology` | optimizer.py | 心理优化 |
| `optimize_rhythm` | optimizer.py | 节奏优化 |
| `outline_generation` | writer.py L756 | 大纲生成 |
| `rewrite_guardrails` | writer.py L173 | 违规修复 |
| `screenwriting` | novels.py L261 | 剧本模式 |
| `writing` | writer.py L363 | 写作（fallback） |
| `writing_v2` | writer.py L361 | 写作（主） |

### 1.3 保留但低频使用的提示词

| 提示词名称 | 说明 |
|-----------|------|
| `character_dna_guide.md` | 被 optimizer.py 间接使用，用于角色 DNA 构建 |

---

## 二、服务层审计结果

### 2.1 服务引用统计

| 服务 | 引用次数 | 状态 |
|------|---------|------|
| `novel_service` | 88 | 核心服务 |
| `llm_service` | 45 | 核心服务 |
| `prompt_service` | 39 | 核心服务 |
| `cache_service` | 18 | 活跃 |
| `auth_service` | 12 | 活跃 |
| `config_service` | 12 | 活跃 |
| `update_log_service` | 9 | 活跃 |
| `admin_setting_service` | 7 | 活跃 |
| `user_service` | 7 | 活跃 |
| `llm_config_service` | 5 | 活跃 |
| `character_knowledge_manager` | 3 | 低频 |
| `emotion_service` | 3 | 低频 |
| `import_service` | 3 | 低频 |
| `outline_rewriter` | 3 | 低频 |
| `pacing_controller` | 3 | 低频 |
| `usage_service` | 3 | 低频 |
| `vector_store_service` | 3 | 低频 |
| `foreshadowing_service` | 2 | 低频 |
| `chapter_context_service` | 1 | 低频 |
| `chapter_guardrails` | 1 | 新增 |
| `chapter_ingest_service` | 1 | 低频 |
| `creative_guidance_system` | 1 | 低频 |
| `emotion_analyzer_enhanced` | 1 | 低频 |
| `prompt_templates_optimized` | 1 | 仅测试引用 |
| `story_trajectory_analyzer` | 1 | 低频 |
| `writer_context_builder` | 1 | 新增 |
| `ai_review_service` | 1 | 新增 |

### 2.2 新增服务

| 服务 | 职责 |
|------|------|
| `writer_context_builder.py` | 信息可见性过滤，防止主角全知 |
| `chapter_guardrails.py` | 后置一致性检查，检测违规内容 |
| `ai_review_service.py` | 多版本自动评审，选出最佳版本 |

---

## 三、路由层审计结果

### 3.1 已清理的未使用导入

| 文件 | 清理内容 |
|------|---------|
| `writer.py` | `Body`, `ChapterOutline` |
| `analytics_enhanced.py` | `json`, `Any` |

### 3.2 保留的未使用导入（暂不处理）

| 文件 | 未使用导入 | 原因 |
|------|-----------|------|
| `admin.py` | `Optional` | 可能用于类型注解 |
| `analytics.py` | `PromptService` | 可能预留扩展 |
| `auth.py` | `settings`, `timedelta`, `Optional` | 可能用于配置 |
| `foreshadowing.py` | 多个模型类 | 可能用于类型注解 |

---

## 四、结构化改进

### 4.1 写作流程优化

```
原流程：
  生成 N 个版本 → 直接返回给用户

新流程：
  生成 N 个版本 → AI Review 评审 → 标记最佳版本 → 返回给用户
```

### 4.2 新增的流程节点

| 节点 | 服务 | 提示词 |
|------|------|--------|
| L2 导演脚本 | writer.py | `chapter_plan` |
| 信息可见性过滤 | `writer_context_builder.py` | - |
| 后置护栏检查 | `chapter_guardrails.py` | - |
| 违规自动修复 | writer.py | `rewrite_guardrails` |
| AI 评审 | `ai_review_service.py` | `editor_review` |

---

## 五、部署注意事项

### 5.1 数据库迁移
```sql
ALTER TABLE chapter_outlines ADD COLUMN metadata JSON NULL;
```

### 5.2 新增提示词初始化

需要在后台管理界面添加以下提示词：
- `chapter_plan`
- `writing_v2`
- `rewrite_guardrails`
- `editor_review`
- `outline_generation`（原 `outline`）

### 5.3 Docker 重新部署
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## 六、后续优化建议

1. **低频服务评估**：`creative_guidance_system`、`emotion_analyzer_enhanced`、`story_trajectory_analyzer` 等服务引用次数极低，建议评估是否需要保留或重构。

2. **测试文件清理**：`test_phase4_integration.py` 位于 services 目录下，建议移至专门的 tests 目录。

3. **提示词版本管理**：建议建立提示词版本控制机制，避免直接修改导致的回归问题。
