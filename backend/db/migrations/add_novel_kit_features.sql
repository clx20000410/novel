-- Novel-Kit 功能融合数据库迁移
-- 执行时间: 2025-01-13
-- 功能: 小说宪法、Writer 人格、势力关系网络、伏笔追踪增强

-- ===== 1. 小说宪法表 =====
CREATE TABLE IF NOT EXISTS novel_constitutions (
    project_id VARCHAR(255) PRIMARY KEY,
    
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
    
    -- 风格基调
    overall_tone VARCHAR(128),
    realism_level VARCHAR(128),
    language_style VARCHAR(128),
    
    -- 世界观约束
    world_type VARCHAR(128),
    power_system TEXT,
    world_rules JSON,
    forbidden_content JSON,
    
    -- 角色约束
    allowed_character_types JSON,
    character_power_limits TEXT,
    allowed_relationship_types JSON,
    
    -- 剧情约束
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
    
    FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE
);

-- ===== 2. Writer 人格表 =====
CREATE TABLE IF NOT EXISTS writer_personas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id VARCHAR(255) NOT NULL,
    
    -- 基础信息
    name VARCHAR(128) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- 身份定位
    identity TEXT,
    experience_years INT,
    expertise_areas JSON,
    
    -- 目标受众
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
    
    -- 对话风格
    dialogue_style TEXT,
    dialogue_tags TEXT,
    
    -- 描写风格
    description_style TEXT,
    show_vs_tell_ratio VARCHAR(64),
    sensory_focus JSON,
    
    -- 人类化特征
    catchphrases JSON,
    personal_quirks JSON,
    imperfection_patterns JSON,
    thinking_pauses JSON,
    filler_words JSON,
    regional_expressions JSON,
    
    -- 反 AI 检测规则
    avoid_patterns JSON,
    variation_rules JSON,
    
    -- 元数据
    extra JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_project_id (project_id),
    FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE
);

-- ===== 3. 势力表 =====
CREATE TABLE IF NOT EXISTS factions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id VARCHAR(255) NOT NULL,
    
    -- 基础信息
    name VARCHAR(255) NOT NULL,
    faction_type VARCHAR(64),
    description LONGTEXT,
    
    -- 势力属性
    power_level VARCHAR(64),
    territory TEXT,
    resources JSON,
    
    -- 组织结构
    leader VARCHAR(255),
    hierarchy JSON,
    member_count VARCHAR(64),
    
    -- 目标与现状
    goals JSON,
    current_status TEXT,
    recent_events JSON,
    
    -- 文化特征
    culture TEXT,
    rules JSON,
    traditions JSON,
    
    -- 元数据
    extra JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_project_id (project_id),
    FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE
);

-- ===== 4. 势力关系表 =====
CREATE TABLE IF NOT EXISTS faction_relationships (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id VARCHAR(255) NOT NULL,
    
    -- 关系双方
    faction_from_id INT NOT NULL,
    faction_to_id INT NOT NULL,
    
    -- 关系属性
    relationship_type VARCHAR(64) NOT NULL,
    strength INT,
    description TEXT,
    terms JSON,
    
    -- 历史记录
    established_at VARCHAR(255),
    reason TEXT,
    
    -- 元数据
    extra JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_project_id (project_id),
    FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (faction_from_id) REFERENCES factions(id) ON DELETE CASCADE,
    FOREIGN KEY (faction_to_id) REFERENCES factions(id) ON DELETE CASCADE
);

-- ===== 5. 势力成员表 =====
CREATE TABLE IF NOT EXISTS faction_members (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id VARCHAR(255) NOT NULL,
    
    faction_id INT NOT NULL,
    character_id BIGINT NOT NULL,
    
    -- 成员属性
    role VARCHAR(128),
    `rank` VARCHAR(64),
    loyalty INT,
    joined_at VARCHAR(255),
    
    -- 元数据
    extra JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_project_id (project_id),
    FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (faction_id) REFERENCES factions(id) ON DELETE CASCADE,
    FOREIGN KEY (character_id) REFERENCES blueprint_characters(id) ON DELETE CASCADE
);

-- ===== 6. 势力关系变更历史表 =====
CREATE TABLE IF NOT EXISTS faction_relationship_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    relationship_id INT NOT NULL,
    
    -- 变更内容
    old_type VARCHAR(64),
    new_type VARCHAR(64) NOT NULL,
    old_strength INT,
    new_strength INT,
    
    -- 变更原因
    reason TEXT,
    chapter_number INT,
    story_time VARCHAR(255),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (relationship_id) REFERENCES faction_relationships(id) ON DELETE CASCADE
);

-- ===== 7. 伏笔表增强字段 =====
ALTER TABLE foreshadowings
    ADD COLUMN IF NOT EXISTS name VARCHAR(255),
    ADD COLUMN IF NOT EXISTS target_reveal_chapter INT,
    ADD COLUMN IF NOT EXISTS reveal_method TEXT,
    ADD COLUMN IF NOT EXISTS reveal_impact TEXT,
    ADD COLUMN IF NOT EXISTS related_characters JSON,
    ADD COLUMN IF NOT EXISTS related_plots JSON,
    ADD COLUMN IF NOT EXISTS related_foreshadowings JSON,
    ADD COLUMN IF NOT EXISTS importance VARCHAR(32),
    ADD COLUMN IF NOT EXISTS urgency INT;

-- 更新伏笔状态默认值
ALTER TABLE foreshadowings
    MODIFY COLUMN status VARCHAR(32) DEFAULT 'planted';

-- ===== 8. 伏笔状态变更历史表 =====
CREATE TABLE IF NOT EXISTS foreshadowing_status_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    foreshadowing_id BIGINT NOT NULL,
    
    -- 变更内容
    old_status VARCHAR(32),
    new_status VARCHAR(32) NOT NULL,
    
    -- 变更上下文
    chapter_number INT,
    reason TEXT,
    action_taken TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (foreshadowing_id) REFERENCES foreshadowings(id) ON DELETE CASCADE
);

-- ===== 索引优化 =====
CREATE INDEX IF NOT EXISTS idx_foreshadowings_status ON foreshadowings(status);
CREATE INDEX IF NOT EXISTS idx_foreshadowings_urgency ON foreshadowings(urgency);
CREATE INDEX IF NOT EXISTS idx_writer_personas_active ON writer_personas(project_id, is_active);
