-- 深度优化功能数据库迁移
-- 更新日期: 2026-02-02
-- 包含：记忆层、项目记忆、章节蓝图、伏笔增强等功能所需的表
-- 注意：本脚本仅包含 ORM 模型中实际定义的表

-- ===== 记忆层相关表 =====

-- 角色状态表
CREATE TABLE IF NOT EXISTS character_states (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_id CHAR(36) NOT NULL,
    character_id BIGINT NOT NULL,
    character_name VARCHAR(255) NOT NULL,
    chapter_number INT NOT NULL,

    -- 位置状态
    location VARCHAR(255),
    location_detail TEXT,

    -- 情绪状态
    emotion VARCHAR(64),
    emotion_intensity INT COMMENT '1-10',
    emotion_reason TEXT,

    -- 健康状态
    health_status VARCHAR(64) COMMENT 'healthy, injured, critical, dead',
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

    INDEX idx_character_states_project_id (project_id),
    INDEX idx_character_states_character_id (character_id),
    INDEX idx_character_states_chapter_number (chapter_number),
    CONSTRAINT fk_character_states_project FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_character_states_character FOREIGN KEY (character_id) REFERENCES blueprint_characters(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 时间线事件表
CREATE TABLE IF NOT EXISTS timeline_events (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_id CHAR(36) NOT NULL,

    -- 时间信息
    chapter_number INT NOT NULL,
    story_time VARCHAR(255),
    story_date VARCHAR(64),
    time_elapsed VARCHAR(128),

    -- 事件信息
    event_type VARCHAR(64) COMMENT 'major, minor, background',
    event_title VARCHAR(255) NOT NULL,
    event_description TEXT,

    -- 关联信息
    involved_characters JSON,
    location VARCHAR(255),

    -- 因果关系
    caused_by_event_id BIGINT,
    leads_to_event_ids JSON,

    -- 元数据
    importance INT DEFAULT 5 COMMENT '1-10',
    is_turning_point TINYINT(1) DEFAULT 0,
    extra JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_timeline_events_project_id (project_id),
    INDEX idx_timeline_events_chapter_number (chapter_number),
    CONSTRAINT fk_timeline_events_project FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_timeline_events_caused_by FOREIGN KEY (caused_by_event_id) REFERENCES timeline_events(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 因果链表
CREATE TABLE IF NOT EXISTS causal_chains (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_id CHAR(36) NOT NULL,

    -- 因果关系
    cause_type VARCHAR(64) COMMENT 'event, action, decision, external',
    cause_description TEXT NOT NULL,
    cause_chapter INT NOT NULL,

    effect_type VARCHAR(64) COMMENT 'event, state_change, relationship_change',
    effect_description TEXT NOT NULL,
    effect_chapter INT,

    -- 关联信息
    involved_characters JSON,
    cause_event_id BIGINT,
    effect_event_id BIGINT,

    -- 状态
    status VARCHAR(32) DEFAULT 'pending' COMMENT 'pending, resolved, abandoned',
    resolution_description TEXT,

    -- 元数据
    importance INT DEFAULT 5 COMMENT '1-10',
    extra JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_causal_chains_project_id (project_id),
    CONSTRAINT fk_causal_chains_project FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_causal_chains_cause_event FOREIGN KEY (cause_event_id) REFERENCES timeline_events(id) ON DELETE SET NULL,
    CONSTRAINT fk_causal_chains_effect_event FOREIGN KEY (effect_event_id) REFERENCES timeline_events(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 故事时间追踪器表
CREATE TABLE IF NOT EXISTS story_time_trackers (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_id CHAR(36) NOT NULL UNIQUE,

    -- 时间设定
    time_system VARCHAR(64) DEFAULT 'modern' COMMENT 'modern, ancient, fantasy, scifi',
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

    CONSTRAINT fk_story_time_trackers_project FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===== 项目记忆相关表 =====

-- 项目记忆表
CREATE TABLE IF NOT EXISTS project_memories (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_id CHAR(36) NOT NULL UNIQUE,
    global_summary LONGTEXT,
    plot_arcs JSON,
    story_timeline_summary TEXT,
    last_updated_chapter INT DEFAULT 0,
    version INT DEFAULT 1 COMMENT 'optimistic lock',
    extra JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_project_memories_project_id (project_id),
    CONSTRAINT fk_project_memories_project FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 章节快照表
CREATE TABLE IF NOT EXISTS chapter_snapshots (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_id CHAR(36) NOT NULL,
    chapter_number INT NOT NULL,
    global_summary_snapshot LONGTEXT,
    character_states_snapshot JSON,
    plot_arcs_snapshot JSON,
    chapter_summary TEXT,
    word_count INT DEFAULT 0,
    extra JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_chapter_snapshots_project_id (project_id),
    INDEX idx_chapter_snapshots_chapter_number (chapter_number),
    CONSTRAINT fk_chapter_snapshots_project FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===== 章节蓝图系统 =====

-- 章节蓝图表
CREATE TABLE IF NOT EXISTS chapter_blueprints (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_id CHAR(36) NOT NULL,
    chapter_number INT NOT NULL,
    suspense_density VARCHAR(32) DEFAULT 'gradual',
    foreshadowing_ops VARCHAR(128),
    cognitive_twist_level INT DEFAULT 1,
    chapter_function VARCHAR(32) DEFAULT 'progression',
    chapter_focus VARCHAR(255),
    suspense_type VARCHAR(128),
    emotional_arc VARCHAR(255),
    involved_foreshadowings JSON,
    mission_constraints JSON,
    brief_summary TEXT,
    director_script LONGTEXT,
    beat_sheet JSON,
    is_generated TINYINT(1) DEFAULT 0,
    is_finalized TINYINT(1) DEFAULT 0,
    quality_score DECIMAL(5,2),
    extra JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_chapter_blueprints_project_id (project_id),
    INDEX idx_chapter_blueprints_chapter_number (chapter_number),
    CONSTRAINT fk_chapter_blueprints_project FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 蓝图模板表
CREATE TABLE IF NOT EXISTS blueprint_templates (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    description TEXT,
    template_type VARCHAR(32) DEFAULT 'system',
    user_id INT,
    config JSON NOT NULL,
    usage_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_blueprint_templates_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===== 伏笔增强表 =====

-- 伏笔解决记录表
CREATE TABLE IF NOT EXISTS foreshadowing_resolutions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    foreshadowing_id BIGINT NOT NULL,
    resolved_at_chapter_id BIGINT NOT NULL,
    resolved_at_chapter_number INT NOT NULL,
    resolution_text LONGTEXT NOT NULL,
    resolution_type VARCHAR(32) COMMENT 'direct, twist, delayed, etc.',
    quality_score INT COMMENT '1-10',
    reader_satisfaction INT COMMENT '1-10',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_foreshadowing_resolutions_foreshadowing FOREIGN KEY (foreshadowing_id) REFERENCES foreshadowings(id) ON DELETE CASCADE,
    CONSTRAINT fk_foreshadowing_resolutions_chapter FOREIGN KEY (resolved_at_chapter_id) REFERENCES chapters(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 伏笔提醒表
CREATE TABLE IF NOT EXISTS foreshadowing_reminders (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_id CHAR(36) NOT NULL,
    foreshadowing_id BIGINT NOT NULL,
    reminder_type VARCHAR(32) NOT NULL COMMENT 'unresolved, long_time_no_mention, pattern_mismatch',
    message LONGTEXT NOT NULL,
    suggested_chapter_range JSON,
    status VARCHAR(32) DEFAULT 'active' COMMENT 'active, dismissed, resolved',
    dismissed_at DATETIME,
    dismissed_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_foreshadowing_reminders_project_id (project_id),
    INDEX idx_foreshadowing_reminders_status (status),
    CONSTRAINT fk_foreshadowing_reminders_project FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_foreshadowing_reminders_foreshadowing FOREIGN KEY (foreshadowing_id) REFERENCES foreshadowings(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 伏笔分析报告表
CREATE TABLE IF NOT EXISTS foreshadowing_analysis (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_id CHAR(36) NOT NULL UNIQUE,
    total_foreshadowings INT DEFAULT 0,
    resolved_count INT DEFAULT 0,
    unresolved_count INT DEFAULT 0,
    abandoned_count INT DEFAULT 0,
    avg_resolution_distance DECIMAL(10,2),
    unresolved_ratio DECIMAL(5,4),
    pattern_analysis JSON,
    overall_quality_score DECIMAL(5,2),
    recommendations JSON,
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_foreshadowing_analysis_project FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===== 完成 =====
-- 执行完成后，请重启后端服务
