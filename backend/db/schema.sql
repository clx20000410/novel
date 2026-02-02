-- ==============================================================================
-- Arboris Novel 全量数据库建表脚本
-- 适用于 MySQL 8.x / MariaDB 10.5+
-- 生成日期: 2026-02-02
-- 表数量: 37
-- ==============================================================================
-- 如需重建，请先根据需要执行 DROP TABLE，再运行本脚本
-- 注意：表的创建顺序考虑了外键依赖关系
-- ==============================================================================

-- ============================================
-- 第一部分：基础用户与配置表
-- ============================================

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(64) NOT NULL UNIQUE,
    email VARCHAR(128) UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    external_id VARCHAR(255) UNIQUE,
    is_admin TINYINT(1) DEFAULT 0,
    is_active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_username (username)
);

-- 用户 LLM 配置表（多配置模式）
CREATE TABLE IF NOT EXISTS llm_configs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(64) NOT NULL DEFAULT '默认配置',
    is_active TINYINT(1) DEFAULT 0,
    api_format VARCHAR(32) NOT NULL DEFAULT 'openai_chat',
    llm_provider_url TEXT,
    llm_provider_api_key TEXT,
    llm_provider_model TEXT,
    blueprint_batch_size INT NOT NULL DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_llm_configs_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_llm_configs_user_id (user_id)
);

-- 系统配置表
CREATE TABLE IF NOT EXISTS system_configs (
    `key` VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    description VARCHAR(255)
);

-- 管理员设置表
CREATE TABLE IF NOT EXISTS admin_settings (
    `key` VARCHAR(64) PRIMARY KEY,
    value TEXT NOT NULL
);

-- 使用指标表
CREATE TABLE IF NOT EXISTS usage_metrics (
    `key` VARCHAR(64) PRIMARY KEY,
    value INT NOT NULL DEFAULT 0
);

-- 用户每日请求统计表
CREATE TABLE IF NOT EXISTS user_daily_requests (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    request_date DATE NOT NULL,
    request_count INT DEFAULT 0,
    UNIQUE KEY uq_user_daily (user_id, request_date),
    CONSTRAINT fk_daily_requests_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_daily_requests_user_id (user_id)
);

-- 更新日志表
CREATE TABLE IF NOT EXISTS update_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(64),
    is_pinned TINYINT(1) DEFAULT 0
);

-- 提示词模板表
CREATE TABLE IF NOT EXISTS prompts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    title VARCHAR(255),
    content LONGTEXT NOT NULL,
    tags VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_prompts_name (name)
);

-- 邮箱验证码表
CREATE TABLE IF NOT EXISTS email_verification_codes (
    email VARCHAR(255) PRIMARY KEY,
    code_hash VARCHAR(64) NOT NULL,
    expires_at DATETIME NOT NULL,
    last_sent_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ============================================
-- 第二部分：小说项目核心表
-- ============================================

-- 小说项目主表
CREATE TABLE IF NOT EXISTS novel_projects (
    id CHAR(36) PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    initial_prompt TEXT,
    status VARCHAR(32) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_novel_projects_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_novel_projects_user_id (user_id)
);

-- 小说对话记录表
CREATE TABLE IF NOT EXISTS novel_conversations (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_id CHAR(36) NOT NULL,
    seq INT NOT NULL,
    role VARCHAR(32) NOT NULL,
    content LONGTEXT NOT NULL,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_conversations_project FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE,
    UNIQUE KEY uq_conversations_project_seq (project_id, seq)
);

-- 小说蓝图表
CREATE TABLE IF NOT EXISTS novel_blueprints (
    project_id CHAR(36) PRIMARY KEY,
    title VARCHAR(255),
    target_audience VARCHAR(255),
    genre VARCHAR(128),
    style VARCHAR(128),
    tone VARCHAR(128),
    one_sentence_summary TEXT,
    full_synopsis LONGTEXT,
    world_setting JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_blueprints_project FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE
);

-- 蓝图角色表
CREATE TABLE IF NOT EXISTS blueprint_characters (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_id CHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL,
    identity VARCHAR(255),
    personality TEXT,
    goals TEXT,
    abilities TEXT,
    relationship_to_protagonist TEXT,
    extra JSON,
    position INT DEFAULT 0,
    CONSTRAINT fk_characters_project FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE,
    INDEX idx_blueprint_characters_project_id (project_id)
);

-- 蓝图关系表
CREATE TABLE IF NOT EXISTS blueprint_relationships (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_id CHAR(36) NOT NULL,
    character_from VARCHAR(255) NOT NULL,
    character_to VARCHAR(255) NOT NULL,
    description TEXT,
    position INT DEFAULT 0,
    CONSTRAINT fk_relationships_project FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE,
    INDEX idx_blueprint_relationships_project_id (project_id)
);

-- 章节大纲表
CREATE TABLE IF NOT EXISTS chapter_outlines (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_id CHAR(36) NOT NULL,
    chapter_number INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    summary TEXT,
    metadata JSON,
    CONSTRAINT fk_outlines_project FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE,
    UNIQUE KEY uq_outline_project_chapter (project_id, chapter_number)
);

-- 章节表
CREATE TABLE IF NOT EXISTS chapters (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_id CHAR(36) NOT NULL,
    chapter_number INT NOT NULL,
    real_summary TEXT,
    status VARCHAR(32) DEFAULT 'not_generated',
    word_count INT DEFAULT 0,
    selected_version_id BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_chapters_project FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE,
    UNIQUE KEY uq_chapter_project_number (project_id, chapter_number)
);

-- 章节版本表
CREATE TABLE IF NOT EXISTS chapter_versions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    chapter_id BIGINT NOT NULL,
    version_label VARCHAR(64),
    provider VARCHAR(64),
    content LONGTEXT NOT NULL,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_versions_chapter FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE,
    INDEX idx_chapter_versions_chapter_id (chapter_id)
);

-- 章节选中版本外键（在 chapter_versions 创建后添加）
ALTER TABLE chapters
    ADD CONSTRAINT fk_chapter_selected_version
    FOREIGN KEY (selected_version_id) REFERENCES chapter_versions(id)
    ON DELETE SET NULL;

-- 章节评估表
CREATE TABLE IF NOT EXISTS chapter_evaluations (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    chapter_id BIGINT NOT NULL,
    version_id BIGINT,
    decision VARCHAR(32),
    feedback TEXT,
    score DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_evaluations_chapter FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE,
    CONSTRAINT fk_evaluations_version FOREIGN KEY (version_id) REFERENCES chapter_versions(id) ON DELETE CASCADE,
    INDEX idx_chapter_evaluations_chapter_id (chapter_id)
);

-- ============================================
-- 第三部分：章节蓝图与模板系统
-- ============================================

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
    CONSTRAINT fk_chapter_blueprints_project FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE,
    INDEX idx_chapter_blueprints_project_id (project_id),
    INDEX idx_chapter_blueprints_chapter_number (chapter_number)
);

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
);

-- ============================================
-- 第四部分：小说宪法与写作人格系统
-- ============================================

-- 小说宪法表
CREATE TABLE IF NOT EXISTS novel_constitutions (
    project_id CHAR(36) PRIMARY KEY,
    -- 故事基础
    core_theme VARCHAR(255),
    genre VARCHAR(128),
    core_conflict VARCHAR(255),
    story_direction VARCHAR(255),
    core_values TEXT,
    -- 叙事视角
    pov_type VARCHAR(64),
    pov_character VARCHAR(255),
    pov_restrictions TEXT,
    -- 目标受众
    target_age_group VARCHAR(64),
    reading_level VARCHAR(64),
    violence_rating VARCHAR(64),
    romance_rating VARCHAR(64),
    -- 风格与基调
    overall_tone VARCHAR(128),
    realism_level VARCHAR(128),
    language_style VARCHAR(128),
    -- 世界约束
    world_type VARCHAR(128),
    power_system TEXT,
    world_rules JSON,
    forbidden_content JSON,
    -- 角色约束
    allowed_character_types JSON,
    character_power_limits TEXT,
    allowed_relationship_types JSON,
    -- 情节约束
    allowed_plot_types JSON,
    twist_frequency VARCHAR(128),
    foreshadowing_rules TEXT,
    -- 时空约束
    time_span VARCHAR(128),
    geographical_scope VARCHAR(128),
    time_flow VARCHAR(128),
    -- 元数据
    extra JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_novel_constitutions_project FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE
);

-- 写作人格表
CREATE TABLE IF NOT EXISTS writer_personas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id CHAR(36) NOT NULL,
    name VARCHAR(128) NOT NULL,
    is_active TINYINT(1) DEFAULT 1,
    -- 身份
    identity TEXT,
    experience_years INT,
    expertise_areas JSON,
    target_audience TEXT,
    -- 语言特征
    vocabulary_level VARCHAR(64),
    sentence_rhythm TEXT,
    vocabulary_preferences JSON,
    unique_expressions JSON,
    formality_level VARCHAR(64),
    -- 内容结构
    opening_style TEXT,
    transition_style TEXT,
    ending_style TEXT,
    -- 对话与描写
    dialogue_style TEXT,
    dialogue_tags TEXT,
    description_style TEXT,
    show_vs_tell_ratio VARCHAR(64),
    sensory_focus JSON,
    -- 人性化/反AI检测
    catchphrases JSON,
    personal_quirks JSON,
    imperfection_patterns JSON,
    thinking_pauses JSON,
    filler_words JSON,
    regional_expressions JSON,
    avoid_patterns JSON,
    variation_rules JSON,
    -- 元数据
    extra JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_writer_personas_project FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE,
    INDEX idx_writer_personas_project_id (project_id)
);

-- ============================================
-- 第五部分：势力系统
-- ============================================

-- 势力表
CREATE TABLE IF NOT EXISTS factions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id CHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL,
    faction_type VARCHAR(64),
    description LONGTEXT,
    power_level VARCHAR(64),
    territory TEXT,
    resources JSON,
    leader VARCHAR(255),
    hierarchy JSON,
    member_count VARCHAR(64),
    goals JSON,
    current_status TEXT,
    recent_events JSON,
    culture TEXT,
    rules JSON,
    traditions JSON,
    extra JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_factions_project FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE,
    INDEX idx_factions_project_id (project_id)
);

-- 势力关系表
CREATE TABLE IF NOT EXISTS faction_relationships (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id CHAR(36) NOT NULL,
    faction_from_id INT NOT NULL,
    faction_to_id INT NOT NULL,
    relationship_type VARCHAR(64) NOT NULL COMMENT 'ally, enemy, rival, neutral, vassal, overlord, trade_partner, at_war',
    strength INT COMMENT '1-10',
    description TEXT,
    terms JSON,
    established_at VARCHAR(255) COMMENT 'story time',
    reason TEXT,
    extra JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_faction_relationships_project FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_faction_relationships_from FOREIGN KEY (faction_from_id) REFERENCES factions(id) ON DELETE CASCADE,
    CONSTRAINT fk_faction_relationships_to FOREIGN KEY (faction_to_id) REFERENCES factions(id) ON DELETE CASCADE,
    INDEX idx_faction_relationships_project_id (project_id)
);

-- 势力成员表
CREATE TABLE IF NOT EXISTS faction_members (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id CHAR(36) NOT NULL,
    faction_id INT NOT NULL,
    character_id BIGINT NOT NULL,
    role VARCHAR(128),
    `rank` VARCHAR(64),
    loyalty INT COMMENT '1-10',
    joined_at VARCHAR(255) COMMENT 'story time',
    extra JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_faction_members_project FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_faction_members_faction FOREIGN KEY (faction_id) REFERENCES factions(id) ON DELETE CASCADE,
    CONSTRAINT fk_faction_members_character FOREIGN KEY (character_id) REFERENCES blueprint_characters(id) ON DELETE CASCADE,
    INDEX idx_faction_members_project_id (project_id)
);

-- 势力关系历史表
CREATE TABLE IF NOT EXISTS faction_relationship_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    relationship_id INT NOT NULL,
    old_type VARCHAR(64),
    new_type VARCHAR(64) NOT NULL,
    old_strength INT,
    new_strength INT,
    reason TEXT,
    chapter_number INT,
    story_time VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_faction_relationship_history_rel FOREIGN KEY (relationship_id) REFERENCES faction_relationships(id) ON DELETE CASCADE
);

-- ============================================
-- 第六部分：伏笔系统
-- ============================================

-- 伏笔表
CREATE TABLE IF NOT EXISTS foreshadowings (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_id CHAR(36) NOT NULL,
    chapter_id BIGINT NOT NULL,
    chapter_number INT NOT NULL,
    content LONGTEXT NOT NULL,
    type VARCHAR(32) NOT NULL COMMENT 'question, mystery, hint, clue, setup',
    keywords JSON,
    status VARCHAR(32) DEFAULT 'planted' COMMENT 'planted, developing, revealed, abandoned, partial',
    resolved_chapter_id BIGINT,
    resolved_chapter_number INT,
    -- Novel-Kit 增强字段
    name VARCHAR(255),
    target_reveal_chapter INT,
    reveal_method TEXT,
    reveal_impact TEXT,
    related_characters JSON,
    related_plots JSON,
    related_foreshadowings JSON,
    importance VARCHAR(32) COMMENT 'major, minor, subtle',
    urgency INT COMMENT '1-10',
    -- 元数据
    is_manual TINYINT(1) DEFAULT 0,
    ai_confidence DECIMAL(5,4),
    author_note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_foreshadowings_project FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_foreshadowings_chapter FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE,
    CONSTRAINT fk_foreshadowings_resolved_chapter FOREIGN KEY (resolved_chapter_id) REFERENCES chapters(id) ON DELETE SET NULL,
    INDEX idx_foreshadowings_project_id (project_id),
    INDEX idx_foreshadowings_status (status)
);

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
);

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
    CONSTRAINT fk_foreshadowing_reminders_project FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_foreshadowing_reminders_foreshadowing FOREIGN KEY (foreshadowing_id) REFERENCES foreshadowings(id) ON DELETE CASCADE,
    INDEX idx_foreshadowing_reminders_project_id (project_id),
    INDEX idx_foreshadowing_reminders_status (status)
);

-- 伏笔状态历史表
CREATE TABLE IF NOT EXISTS foreshadowing_status_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    foreshadowing_id BIGINT NOT NULL,
    old_status VARCHAR(32),
    new_status VARCHAR(32) NOT NULL,
    chapter_number INT,
    reason TEXT,
    action_taken TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_foreshadowing_status_history_foreshadowing FOREIGN KEY (foreshadowing_id) REFERENCES foreshadowings(id) ON DELETE CASCADE
);

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
);

-- ============================================
-- 第七部分：记忆层与上下文系统
-- ============================================

-- 角色状态表
CREATE TABLE IF NOT EXISTS character_states (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_id CHAR(36) NOT NULL,
    character_id BIGINT NOT NULL,
    character_name VARCHAR(255) NOT NULL,
    chapter_number INT NOT NULL,
    -- 位置
    location VARCHAR(255),
    location_detail TEXT,
    -- 情绪
    emotion VARCHAR(64),
    emotion_intensity INT COMMENT '1-10',
    emotion_reason TEXT,
    -- 健康状态
    health_status VARCHAR(64) COMMENT 'healthy, injured, critical, dead',
    injuries JSON,
    -- 物品
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
    CONSTRAINT fk_character_states_project FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_character_states_character FOREIGN KEY (character_id) REFERENCES blueprint_characters(id) ON DELETE CASCADE,
    INDEX idx_character_states_project_id (project_id),
    INDEX idx_character_states_character_id (character_id),
    INDEX idx_character_states_chapter_number (chapter_number)
);

-- 时间线事件表
CREATE TABLE IF NOT EXISTS timeline_events (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_id CHAR(36) NOT NULL,
    chapter_number INT NOT NULL,
    story_time VARCHAR(255),
    story_date VARCHAR(64),
    time_elapsed VARCHAR(128),
    event_type VARCHAR(64) COMMENT 'major, minor, background',
    event_title VARCHAR(255) NOT NULL,
    event_description TEXT,
    involved_characters JSON,
    location VARCHAR(255),
    caused_by_event_id BIGINT,
    leads_to_event_ids JSON,
    importance INT DEFAULT 5 COMMENT '1-10',
    is_turning_point TINYINT(1) DEFAULT 0,
    extra JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_timeline_events_project FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_timeline_events_caused_by FOREIGN KEY (caused_by_event_id) REFERENCES timeline_events(id) ON DELETE SET NULL,
    INDEX idx_timeline_events_project_id (project_id),
    INDEX idx_timeline_events_chapter_number (chapter_number)
);

-- 因果链表
CREATE TABLE IF NOT EXISTS causal_chains (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_id CHAR(36) NOT NULL,
    cause_type VARCHAR(64) COMMENT 'event, action, decision, external',
    cause_description TEXT NOT NULL,
    cause_chapter INT NOT NULL,
    effect_type VARCHAR(64) COMMENT 'event, state_change, relationship_change',
    effect_description TEXT NOT NULL,
    effect_chapter INT,
    involved_characters JSON,
    cause_event_id BIGINT,
    effect_event_id BIGINT,
    status VARCHAR(32) DEFAULT 'pending' COMMENT 'pending, resolved, abandoned',
    resolution_description TEXT,
    importance INT DEFAULT 5 COMMENT '1-10',
    extra JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_causal_chains_project FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_causal_chains_cause_event FOREIGN KEY (cause_event_id) REFERENCES timeline_events(id) ON DELETE SET NULL,
    CONSTRAINT fk_causal_chains_effect_event FOREIGN KEY (effect_event_id) REFERENCES timeline_events(id) ON DELETE SET NULL,
    INDEX idx_causal_chains_project_id (project_id)
);

-- 故事时间追踪表
CREATE TABLE IF NOT EXISTS story_time_trackers (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_id CHAR(36) NOT NULL UNIQUE,
    time_system VARCHAR(64) DEFAULT 'modern' COMMENT 'modern, ancient, fantasy, scifi',
    start_date VARCHAR(64),
    current_date VARCHAR(64),
    current_time VARCHAR(64),
    default_chapter_duration VARCHAR(64) DEFAULT '1 day',
    chapter_time_map JSON,
    extra JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_story_time_trackers_project FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE
);

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
    CONSTRAINT fk_project_memories_project FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE,
    INDEX idx_project_memories_project_id (project_id)
);

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
    CONSTRAINT fk_chapter_snapshots_project FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE,
    INDEX idx_chapter_snapshots_project_id (project_id),
    INDEX idx_chapter_snapshots_chapter_number (chapter_number)
);

-- ============================================
-- 完成
-- ============================================
-- 全部 37 个表已创建
-- 包含所有索引和外键约束
