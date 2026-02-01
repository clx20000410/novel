-- 深度优化功能数据库迁移
-- 包含：记忆层、情绪曲线、读者模拟、周期回顾等功能所需的表

-- ===== 记忆层相关表 =====

-- 角色状态表
CREATE TABLE IF NOT EXISTS character_states (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_id VARCHAR(255) NOT NULL,
    character_id BIGINT,
    character_name VARCHAR(255) NOT NULL,
    chapter_number INT NOT NULL,
    
    -- 位置状态
    location VARCHAR(255),
    location_detail TEXT,
    
    -- 情绪状态
    emotion VARCHAR(64),
    emotion_intensity INT,
    emotion_reason TEXT,
    
    -- 健康状态
    health_status VARCHAR(64) DEFAULT 'healthy',
    injuries JSON,
    
    -- 持有物品
    inventory JSON,
    inventory_changes JSON,
    
    -- 关系变化
    relationship_changes JSON,
    
    -- 能力/实力
    power_level VARCHAR(64),
    power_changes JSON,
    
    -- 知识/信息
    known_secrets JSON,
    new_knowledge JSON,
    
    -- 目标
    current_goals JSON,
    goal_progress JSON,
    
    -- 元数据
    extra JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_project_chapter (project_id, chapter_number),
    INDEX idx_character (project_id, character_name),
    FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 时间线事件表
CREATE TABLE IF NOT EXISTS timeline_events (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_id VARCHAR(255) NOT NULL,
    
    -- 时间信息
    chapter_number INT NOT NULL,
    story_time VARCHAR(255),
    story_date VARCHAR(64),
    time_elapsed VARCHAR(128),
    
    -- 事件信息
    event_type VARCHAR(64) DEFAULT 'minor',
    event_title VARCHAR(255) NOT NULL,
    event_description TEXT,
    
    -- 关联信息
    involved_characters JSON,
    location VARCHAR(255),
    
    -- 因果关系
    caused_by_event_id BIGINT,
    leads_to_event_ids JSON,
    
    -- 元数据
    importance INT DEFAULT 5,
    is_turning_point BOOLEAN DEFAULT FALSE,
    extra JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_project_chapter (project_id, chapter_number),
    INDEX idx_importance (project_id, importance),
    FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (caused_by_event_id) REFERENCES timeline_events(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 因果链表
CREATE TABLE IF NOT EXISTS causal_chains (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_id VARCHAR(255) NOT NULL,
    
    -- 因果关系
    cause_type VARCHAR(64),
    cause_description TEXT NOT NULL,
    cause_chapter INT NOT NULL,
    
    effect_type VARCHAR(64),
    effect_description TEXT NOT NULL,
    effect_chapter INT,
    
    -- 关联信息
    involved_characters JSON,
    cause_event_id BIGINT,
    effect_event_id BIGINT,
    
    -- 状态
    status VARCHAR(32) DEFAULT 'pending',
    resolution_description TEXT,
    
    -- 元数据
    importance INT DEFAULT 5,
    extra JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_project_status (project_id, status),
    INDEX idx_cause_chapter (project_id, cause_chapter),
    FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (cause_event_id) REFERENCES timeline_events(id) ON DELETE SET NULL,
    FOREIGN KEY (effect_event_id) REFERENCES timeline_events(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 故事时间追踪器表
CREATE TABLE IF NOT EXISTS story_time_trackers (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_id VARCHAR(255) NOT NULL UNIQUE,
    
    -- 时间设定
    time_system VARCHAR(64) DEFAULT 'modern',
    start_date VARCHAR(64),
    current_date VARCHAR(64),
    current_time VARCHAR(64),
    
    -- 时间流速
    default_chapter_duration VARCHAR(64) DEFAULT '1 day',
    
    -- 章节时间映射
    chapter_time_map JSON,
    
    -- 元数据
    extra JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===== 周期回顾相关表 =====

-- 周期回顾记录表
CREATE TABLE IF NOT EXISTS periodic_reviews (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_id VARCHAR(255) NOT NULL,
    
    -- 回顾范围
    start_chapter INT NOT NULL,
    end_chapter INT NOT NULL,
    
    -- 评分
    pacing_score INT,
    consistency_score INT,
    overall_score INT,
    
    -- 分析结果
    pacing_analysis JSON,
    character_analysis JSON,
    foreshadowing_analysis JSON,
    consistency_check JSON,
    
    -- 建议和行动
    recommendations JSON,
    priority_actions JSON,
    adjustment_plan JSON,
    
    -- 元数据
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_project_chapter (project_id, end_chapter),
    FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===== 读者模拟相关表 =====

-- 读者反馈记录表
CREATE TABLE IF NOT EXISTS reader_feedbacks (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_id VARCHAR(255) NOT NULL,
    chapter_number INT NOT NULL,
    version_index INT DEFAULT 0,
    
    -- 整体评分
    overall_score INT,
    
    -- 爽点检测
    thrill_points JSON,
    thrill_count INT DEFAULT 0,
    
    -- 各类读者反馈
    reader_feedbacks JSON,
    
    -- 弃书风险
    abandon_risks JSON,
    max_abandon_risk INT,
    
    -- 钩子强度
    hook_strength INT,
    hook_type VARCHAR(64),
    
    -- 建议
    recommendations JSON,
    
    -- 元数据
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_project_chapter (project_id, chapter_number),
    FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===== 自我批评相关表 =====

-- 批评记录表
CREATE TABLE IF NOT EXISTS critique_records (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_id VARCHAR(255) NOT NULL,
    chapter_number INT NOT NULL,
    version_index INT DEFAULT 0,
    
    -- 批评维度
    dimension VARCHAR(64) NOT NULL,
    
    -- 评分
    score INT,
    
    -- 问题列表
    issues JSON,
    issue_count INT DEFAULT 0,
    critical_count INT DEFAULT 0,
    major_count INT DEFAULT 0,
    
    -- 优点
    strengths JSON,
    
    -- 元数据
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_project_chapter (project_id, chapter_number),
    FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 修订历史表
CREATE TABLE IF NOT EXISTS revision_histories (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_id VARCHAR(255) NOT NULL,
    chapter_number INT NOT NULL,
    version_index INT DEFAULT 0,
    
    -- 修订信息
    iteration INT NOT NULL,
    score_before INT,
    score_after INT,
    improvement INT,
    
    -- 修复的问题
    fixed_issues JSON,
    
    -- 状态
    status VARCHAR(32),
    
    -- 元数据
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_project_chapter (project_id, chapter_number),
    FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===== 情绪曲线配置表 =====

-- 项目情绪曲线配置
CREATE TABLE IF NOT EXISTS emotion_curve_configs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_id VARCHAR(255) NOT NULL UNIQUE,
    
    -- 弧线类型
    arc_type VARCHAR(64) DEFAULT 'standard',
    
    -- 自定义曲线点
    custom_curve JSON,
    
    -- 分卷配置
    volume_configs JSON,
    
    -- 元数据
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===== 添加索引优化查询性能 =====

-- 为 chapter_versions 表添加索引（如果不存在）
-- ALTER TABLE chapter_versions ADD INDEX idx_project_chapter (project_id, chapter_number);

-- 为 chapter_outlines 表添加索引（如果不存在）
-- ALTER TABLE chapter_outlines ADD INDEX idx_project_chapter (project_id, chapter_number);

-- ===== 完成 =====
-- 执行完成后，请重启后端服务
