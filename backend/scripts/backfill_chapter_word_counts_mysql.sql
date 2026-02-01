-- Backfill chapter word_count (MySQL)
-- 1) Use selected_version.content when available
-- 2) If no selected_version, use latest version by created_at/id

START TRANSACTION;

UPDATE chapters c
JOIN chapter_versions v ON v.id = c.selected_version_id
SET c.word_count = CHAR_LENGTH(v.content)
WHERE (c.word_count IS NULL OR c.word_count = 0);

UPDATE chapters c
SET c.word_count = (
  SELECT CHAR_LENGTH(cv.content)
  FROM chapter_versions cv
  WHERE cv.chapter_id = c.id
  ORDER BY cv.created_at DESC, cv.id DESC
  LIMIT 1
)
WHERE c.selected_version_id IS NULL
  AND (c.word_count IS NULL OR c.word_count = 0)
  AND EXISTS (SELECT 1 FROM chapter_versions cv WHERE cv.chapter_id = c.id);

COMMIT;
