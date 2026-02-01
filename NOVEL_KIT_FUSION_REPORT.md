# Novel-Kit 功能融合报告

> 本报告记录了从 [novel-kit](https://github.com/t59688/novel-kit) 项目中提取并融合到 AI-Novel 系统的全部优势功能。

---

## 一、融合概览

| 功能模块 | 原 AI-Novel | Novel-Kit 优势 | 融合后状态 |
|----------|-------------|----------------|------------|
| 创作规则 | 无 | 小说宪法系统 | ✅ 已实现 |
| 文本风格 | 基础提示词 | Writer 人格系统 | ✅ 已实现 |
| 质量审查 | 单维度评审 | 六维度审查 | ✅ 已实现 |
| 伏笔管理 | 基础记录 | 状态追踪+提醒 | ✅ 已增强 |
| 势力系统 | 无 | 完整关系网络 | ✅ 已实现 |

---

## 二、新增功能详解

### 2.1 小说宪法系统 (Constitution)

**核心价值**：通过 28+ 维度的规则定义，确保长篇小说创作的一致性。

**文件清单**：
- `backend/app/models/constitution.py` - 数据模型
- `backend/app/services/constitution_service.py` - 服务层
- `backend/prompts/constitution_check.md` - 合规检查提示词

**宪法维度**：

| 类别 | 维度 |
|------|------|
| 故事基础 | 核心主题、类型、核心冲突、故事走向、核心价值观 |
| 叙事视角 | POV 类型、POV 角色、视角限制 |
| 目标受众 | 年龄层、阅读水平、暴力分级、言情分级 |
| 风格基调 | 整体基调、现实程度、语言风格 |
| 世界观约束 | 世界类型、力量体系、世界规则、禁忌内容 |
| 角色约束 | 允许角色类型、角色能力上限、允许关系类型 |
| 剧情约束 | 允许剧情类型、反转频率、伏笔规则 |
| 时空约束 | 时间跨度、地理范围、时间流速 |

**使用示例**：
```python
from app.services.constitution_service import ConstitutionService

# 创建宪法
constitution = await constitution_service.create_constitution(
    project_id="xxx",
    core_theme="逆袭与成长",
    genre="都市异能",
    pov_type="limited_third",
    violence_rating="moderate",
    ...
)

# 合规检查
result = await constitution_service.check_compliance(
    project_id="xxx",
    chapter_content="..."
)
# result.overall_compliance: True/False
# result.violations: [...]
```

---

### 2.2 Writer 人格系统 (反 AI 检测)

**核心价值**：通过定义 Writer 的"人格特征"，让生成的文本更具"人味"，可通过 AI 检测。

**文件清单**：
- `backend/app/models/writer_persona.py` - 数据模型
- `backend/app/services/writer_persona_service.py` - 服务层
- `backend/prompts/writer_persona.md` - 人格提示词

**人格特征维度**：

| 类别 | 特征 |
|------|------|
| 身份定位 | 身份描述、从业年限、擅长领域 |
| 语言特征 | 词汇水平、句式节奏、偏好词汇、独特表达、正式程度 |
| 内容结构 | 开篇风格、过渡风格、结尾风格 |
| 对话风格 | 对话特点、对话标签 |
| 描写风格 | 描写特点、展示vs叙述比例、感官侧重 |
| 人类化特征 | 口头禅、个人怪癖、不完美模式、思考停顿、填充词、地域表达 |
| 反 AI 检测 | 避免模式、变化规则 |

**默认人格（起点中文网风格）**：
```python
DEFAULT_QIDIAN_PERSONA = {
    "name": "起点老司机",
    "identity": "网文老作者，擅长都市/玄幻/系统流",
    "vocabulary_level": "colloquial",  # 口语化
    "sentence_rhythm": "短句为主，偶尔长句抒情",
    "catchphrases": ["卧槽", "这波稳了", "血赚"],
    "avoid_patterns": [
        "值得注意的是",
        "总而言之",
        "综上所述",
        "首先...其次...最后"
    ],
    ...
}
```

**反 AI 检测规则**：
1. 非对称句式结构
2. 个性化口头禅和偏好词汇
3. 适度"不完美"（口语化、情绪化）
4. 避免 AI 典型模式（过度对称、机械过渡词）
5. 自然填充词和思考停顿

---

### 2.3 六维度审查系统

**核心价值**：从六个维度全面审查章节质量，确保内容一致性和专业性。

**文件清单**：
- `backend/app/services/six_dimension_review_service.py` - 服务层
- `backend/prompts/six_dimension_review.md` - 审查提示词

**六个维度**：

| 维度 | 检查内容 | 权重 |
|------|---------|------|
| 宪法合规 | 是否违反小说宪法中的任何规则 | 20% |
| 内部一致性 | 章节内部的逻辑、时间、空间一致性 | 20% |
| 跨章一致性 | 与前文的人设、剧情、世界观一致性 | 20% |
| 计划合规 | 是否完成章节大纲/导演脚本的目标 | 15% |
| 风格合规 | 是否符合 Writer 人格的风格要求 | 15% |
| 冲突检测 | 是否存在未解决的逻辑冲突 | 10% |

**输出格式**：
```json
{
  "dimensions": {
    "constitution_compliance": {"score": 85, "issues": [...]},
    "internal_consistency": {"score": 90, "issues": [...]},
    "cross_chapter_consistency": {"score": 80, "issues": [...]},
    "plan_compliance": {"score": 95, "issues": [...]},
    "style_compliance": {"score": 88, "issues": [...]},
    "conflict_detection": {"score": 92, "issues": [...]}
  },
  "overall_score": 88,
  "critical_issues_count": 1,
  "priority_fixes": ["..."]
}
```

---

### 2.4 伏笔状态追踪增强

**核心价值**：将伏笔从简单记录升级为完整的状态机，支持自动提醒和发展建议。

**文件清单**：
- `backend/app/models/foreshadowing.py` - 数据模型（增强）
- `backend/app/services/foreshadowing_tracker_service.py` - 服务层
- `backend/prompts/foreshadowing_reminder.md` - 提醒提示词

**状态机**：
```
planted (已埋设)
    ↓
developing (发展中)
    ↓
revealed (已揭示) / abandoned (已放弃) / red_herring (红鲱鱼)
```

**新增字段**：
- `name`: 伏笔名称
- `target_reveal_chapter`: 目标揭示章节
- `reveal_method`: 揭示方式
- `reveal_impact`: 揭示影响
- `related_characters`: 关联角色
- `related_plots`: 关联剧情
- `importance`: 重要性（major/minor/subtle）
- `urgency`: 紧迫度（1-10）

**自动提醒逻辑**：
- 紧迫度 ≥ 8：必须处理
- 距离目标揭示章节 ≤ 3 章：即将到期
- 埋下后超过 20 章未处理：超期警告

---

### 2.5 势力关系网络系统

**核心价值**：完整的势力管理系统，支持势力档案、关系网络、成员管理和历史追踪。

**文件清单**：
- `backend/app/models/faction.py` - 数据模型
- `backend/app/services/faction_service.py` - 服务层
- `backend/prompts/faction_context.md` - 上下文提示词

**数据结构**：

**势力 (Faction)**：
- 基础信息：名称、类型、描述
- 势力属性：实力等级、领地、资源
- 组织结构：领袖、层级、成员数量
- 目标与现状：目标、当前状态、近期事件
- 文化特征：文化、规则、传统

**势力关系 (FactionRelationship)**：
- 关系类型：ally/enemy/rival/neutral/vassal/overlord/trade_partner/at_war
- 关系强度：1-10
- 关系描述和条款
- 建立时间和原因

**关系变更历史**：
- 自动记录每次关系变更
- 记录变更原因和章节号

---

### 2.6 增强型写作流程

**核心价值**：将所有新功能集成到统一的写作流程中。

**文件清单**：
- `backend/app/services/enhanced_writing_flow.py` - 集成服务

**流程图**：
```
┌─────────────────────────────────────────────────────────────┐
│                    准备写作上下文                            │
│  1. 获取小说宪法上下文                                       │
│  2. 获取 Writer 人格上下文                                   │
│  3. 获取伏笔提醒                                            │
│  4. 获取势力关系上下文                                       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    构建增强提示词                            │
│  - 注入宪法约束                                             │
│  - 注入人格风格                                             │
│  - 注入伏笔提醒                                             │
│  - 注入势力关系                                             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    生成章节正文                              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    生成后审查                                │
│  1. 六维度审查                                              │
│  2. 宪法合规检查                                            │
│  3. 风格合规检查                                            │
│  4. 自动更新伏笔状态                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 三、数据库迁移

**迁移文件**：`backend/db/migrations/add_novel_kit_features.sql`

**新增表**：
1. `novel_constitutions` - 小说宪法
2. `writer_personas` - Writer 人格
3. `factions` - 势力
4. `faction_relationships` - 势力关系
5. `faction_members` - 势力成员
6. `faction_relationship_history` - 势力关系变更历史
7. `foreshadowing_status_history` - 伏笔状态变更历史

**执行方式**：
```bash
mysql -u root -p your_database < backend/db/migrations/add_novel_kit_features.sql
```

---

## 四、提示词清单

| 提示词文件 | 用途 |
|-----------|------|
| `constitution_check.md` | 小说宪法合规检查 |
| `writer_persona.md` | Writer 人格风格指导 |
| `six_dimension_review.md` | 六维度审查 |
| `foreshadowing_reminder.md` | 伏笔提醒和发展建议 |
| `faction_context.md` | 势力关系上下文生成 |

---

## 五、使用建议

### 5.1 初始化顺序

1. **执行数据库迁移**
2. **配置小说宪法**：在项目创建后，通过 API 或后台配置宪法
3. **配置 Writer 人格**：可使用默认的"起点老司机"人格，或自定义
4. **配置势力**：如果小说涉及多势力，提前配置势力档案和关系

### 5.2 最佳实践

1. **宪法配置**：在开始写作前完成，避免中途修改导致前后不一致
2. **人格选择**：根据目标平台选择合适的人格（起点/番茄/知乎）
3. **伏笔管理**：每章写完后检查伏笔状态，及时处理超期伏笔
4. **势力更新**：剧情涉及势力变化时，及时更新关系状态

---

## 六、后续优化建议

1. **前端界面**：为宪法配置、人格管理、势力网络可视化开发前端界面
2. **自动化**：实现伏笔状态的自动检测和更新
3. **模板库**：积累不同类型小说的宪法模板和人格模板
4. **数据分析**：基于审查结果进行写作质量趋势分析

---

*报告生成时间：2025-01-13*
*融合来源：https://github.com/t59688/novel-kit*
