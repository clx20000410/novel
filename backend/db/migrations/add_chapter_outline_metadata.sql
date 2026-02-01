-- 迁移脚本：给 chapter_outlines 表添加 metadata 字段
-- 用于存储导演脚本、节拍状态、角色登场计划等信息

ALTER TABLE chapter_outlines ADD COLUMN metadata JSON NULL;
