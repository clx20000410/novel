# AI-Novel 深度优化功能报告

## 概述

本次优化实现了六大核心功能，将 AI 小说创作系统从"能用"提升到"好用"的级别。所有功能已集成到统一的 `UltimateWritingFlow` 服务中。

---

## 一、新增功能清单

### 1. 记忆层架构（Memory Layer）

**解决的问题**：AI 无法主动追踪角色状态，导致角色"瞬移"、情绪断层、物品凭空出现等一致性问题。

**核心组件**：

| 组件 | 职责 | 文件 |
|------|------|------|
| 角色状态表 | 追踪每个角色在每章结束时的状态（位置、情绪、物品、关系等） | `memory_layer.py` |
| 时间线 | 追踪故事内的时间流逝和关键事件 | `memory_layer.py` |
| 因果链 | 追踪事件之间的因果关系，确保逻辑自洽 | `memory_layer.py` |
| 记忆层服务 | 提取、更新、查询记忆层数据 | `memory_layer_service.py` |

**工作流程**：
```
章节生成前 → 获取记忆层上下文 → 注入到写作提示词
章节生成后 → 自动提取角色状态变化 → 更新记忆层
```

---

### 2. 情绪曲线算法（Emotion Curve）

**解决的问题**：节奏失控，每章都是高潮或每章都是铺垫，缺乏"呼吸感"。

**核心特性**：

| 特性 | 说明 |
|------|------|
| 多种弧线类型 | 标准三幕式、慢热型、快节奏、波浪式 |
| 动态情绪目标 | 根据章节位置自动计算目标情绪强度（1-100） |
| 节奏参数 | 自动计算场景长度、过渡风格、动作密度 |
| 爽点密度 | 自动计算每章应有的爽点数量 |
| 内容比例 | 自动建议对话/动作/描写/内心戏的比例 |

**情绪曲线示例（标准三幕式）**：
```
位置        情绪强度    阶段
0-10%      30-50      铺垫期
10-25%     50-70      上升期
25-35%     70-90      第一高潮
35-50%     50-70      发展期
50-60%     40-60      低谷期
60-75%     60-80      反转期
75-90%     75-95      最终上升
90-100%    85-100     大高潮
```

---

### 3. 读者模拟器（Reader Simulator）

**解决的问题**：缺乏"读者视角"的反馈，不知道读者会在哪里感到"爽"或想"弃书"。

**核心特性**：

| 读者类型 | 特征 | 弃书触发点 |
|---------|------|-----------|
| 休闲读者 | 追求轻松愉快 | 太无聊、看不懂、太压抑 |
| 硬核读者 | 追求逻辑严密 | 逻辑崩坏、人设崩塌、烂尾迹象 |
| 情感读者 | 追求情感共鸣 | 感情线崩、角色OOC、太冷血 |
| 爽点读者 | 追求爽感 | 连续三章没爽点、主角被虐太惨 |
| 挑剔读者 | 追求文笔质量 | 文笔太差、太多废话、明显AI生成 |

**输出内容**：
- 爽点检测（类型、强度、位置）
- 各类读者满意度评分
- 弃书风险评估
- 章节结尾钩子强度

---

### 4. 预演-正式两阶段生成（Preview Generation）

**解决的问题**：直接生成正文，如果方向错了就浪费了大量 token。

**工作流程**：
```
阶段 1：生成 500 字预览
  ├── 开场设定（时间、地点、人物状态）
  ├── 3-5 个关键情节点
  ├── 章节结尾钩子设计
  └── 预期读者情绪变化

阶段 2：评估预览质量
  ├── 大纲符合度
  ├── 情节安排合理性
  ├── 情绪节奏符合度
  └── 钩子有效性

阶段 3：扩写成完整章节
  └── 严格按照预览中的情节点顺序扩写
```

**优势**：
- 早期发现问题，避免浪费
- 可以生成多个预览供选择
- 预览通过后再扩写，方向更准确

---

### 5. 自我批评-修正循环（Self Critique）

**解决的问题**：一次性生成质量不稳定，缺乏迭代优化。

**批评维度**：

| 维度 | 权重 | 检查重点 |
|------|------|---------|
| 逻辑一致性 | 1.5 | 事件因果、时间线、行为动机 |
| 人设一致性 | 1.3 | 性格、说话方式、价值观 |
| 文笔质量 | 1.0 | AI词汇、重复啰嗦、描写质量 |
| 节奏控制 | 1.0 | 场景转换、高低潮分布 |
| 情感表达 | 0.8 | 情感真实性、共鸣度 |
| 对话质量 | 0.9 | 自然度、角色区分度 |

**工作流程**：
```
生成 → 批评（找出问题）→ 修正 → 再批评 → 再修正
最多 3 轮，达到目标分数后停止
```

---

### 6. 章节回顾机制（Chapter Review）

**解决的问题**：每章独立生成，缺乏对整体的"回顾"，导致长篇一致性差。

**触发条件**：每 5 章（可配置）触发一次回顾。

**回顾内容**：

| 维度 | 分析内容 |
|------|---------|
| 节奏分析 | 情绪起伏、高低潮分布、节奏问题 |
| 角色发展 | 戏份分布、成长合理性、关系发展 |
| 伏笔状态 | 活跃伏笔数、超期伏笔、发展建议 |
| 一致性检查 | 时间线、角色行为、设定矛盾 |

**输出内容**：
- 综合建议（最多 10 条）
- 优先行动（最多 5 个）
- 调整计划（针对接下来几章）

---

## 二、终极写作流程

所有功能已集成到 `UltimateWritingFlow` 服务中：

```python
from app.services.ultimate_writing_flow import UltimateWritingFlow

flow = UltimateWritingFlow(db, llm_service, prompt_service)

result = await flow.generate_chapter_ultimate(
    project_id="xxx",
    chapter_number=10,
    total_chapters=100,
    outline=outline,
    blueprint_context=blueprint,
    character_names=["张三", "李四"],
    character_profiles=profiles,
    arc_type=ArcType.STANDARD,
    target_word_count=3000,
    enable_preview=True,      # 启用预览阶段
    enable_critique=True,     # 启用自我批评
    enable_reader_simulation=True,  # 启用读者模拟
    version_count=2,          # 生成 2 个版本
    user_id=1
)
```

**完整流程**：
```
1. 上下文准备
   ├── 获取记忆层上下文
   ├── 计算情绪曲线目标
   └── 检查是否触发周期回顾

2. 版本生成（可并行）
   ├── 预览生成 → 预览评估 → 扩写正文
   └── 自我批评 → 修正 → 再批评 → 再修正

3. 读者模拟评估
   ├── 爽点检测
   ├── 多类型读者反馈
   └── 钩子强度评估

4. 版本选择
   └── 综合评分 = 批评分数 × 0.4 + 读者分数 × 0.6 + 钩子加分

5. 记忆层更新
   ├── 提取角色状态变化
   ├── 添加时间线事件
   └── 更新因果链
```

---

## 三、数据库迁移

执行以下 SQL 脚本创建新表：

```bash
mysql -u root -p your_database < backend/db/migrations/add_deep_optimization_features.sql
```

新增表：
- `character_states` - 角色状态表
- `timeline_events` - 时间线事件表
- `causal_chains` - 因果链表
- `story_time_trackers` - 故事时间追踪器
- `periodic_reviews` - 周期回顾记录
- `reader_feedbacks` - 读者反馈记录
- `critique_records` - 批评记录
- `revision_histories` - 修订历史
- `emotion_curve_configs` - 情绪曲线配置

---

## 四、部署步骤

1. **拉取最新代码**
   ```bash
   cd /path/to/AI-novel
   git pull origin main
   ```

2. **执行数据库迁移**
   ```bash
   mysql -u root -p your_database < backend/db/migrations/add_deep_optimization_features.sql
   ```

3. **重新部署 Docker**
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

---

## 五、配置选项

可以通过系统配置控制各功能的开关：

| 配置键 | 默认值 | 说明 |
|--------|--------|------|
| `writer.enable_preview` | `true` | 是否启用预览阶段 |
| `writer.enable_critique` | `true` | 是否启用自我批评 |
| `writer.enable_reader_simulation` | `true` | 是否启用读者模拟 |
| `writer.critique_max_iterations` | `2` | 自我批评最大迭代次数 |
| `writer.critique_target_score` | `75` | 自我批评目标分数 |
| `writer.review_interval` | `5` | 周期回顾间隔（章） |
| `writer.arc_type` | `standard` | 情绪曲线类型 |

---

## 六、预期效果

| 指标 | 优化前 | 优化后 |
|------|--------|--------|
| 角色一致性 | 经常出现瞬移、情绪断层 | 通过记忆层追踪，大幅减少 |
| 节奏控制 | 每章都是高潮或铺垫 | 根据情绪曲线动态调节 |
| 爽点密度 | 随机分布 | 根据位置自动计算目标数量 |
| 文笔质量 | 一次性生成，质量不稳定 | 通过批评-修正循环迭代优化 |
| 长篇一致性 | 越写越乱 | 通过周期回顾及时调整 |
| 版本选择 | 人工盲选 | 综合评分自动推荐最佳版本 |

---

## 七、文件清单

| 文件 | 职责 |
|------|------|
| `app/models/memory_layer.py` | 记忆层数据模型 |
| `app/services/memory_layer_service.py` | 记忆层服务 |
| `app/services/emotion_curve_service.py` | 情绪曲线算法 |
| `app/services/reader_simulator_service.py` | 读者模拟器 |
| `app/services/preview_generation_service.py` | 预演-正式两阶段生成 |
| `app/services/self_critique_service.py` | 自我批评-修正循环 |
| `app/services/chapter_review_service.py` | 章节回顾机制 |
| `app/services/ultimate_writing_flow.py` | 终极写作流程集成 |
| `db/migrations/add_deep_optimization_features.sql` | 数据库迁移脚本 |

---

*报告生成时间：2026-01-13*
