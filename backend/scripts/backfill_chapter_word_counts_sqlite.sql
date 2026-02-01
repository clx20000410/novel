-- Backfill chapter word_count (SQLite)
-- 1) Use selected_version.content when available
-- 2) If no selected_version, use latest version by created_at/id

BEGIN TRANSACTION;

UPDATE chapters
SET word_count = (
  SELECT LENGTH(content)
  FROM chapter_versions
  WHERE chapter_versions.id = chapters.selected_version_id
)
WHERE (word_count IS NULL OR word_count = 0)
  AND selected_version_id IS NOT NULL;

UPDATE chapters
SET word_count = (
  SELECT LENGTH(content)
  FROM chapter_versions
  WHERE chapter_versions.chapter_id = chapters.id
  ORDER BY created_at DESC, id DESC
  LIMIT 1
)
WHERE (word_count IS NULL OR word_count = 0)
  AND selected_version_id IS NULL
  AND EXISTS (
    SELECT 1 FROM chapter_versions WHERE chapter_versions.chapter_id = chapters.id
  );

COMMIT;
