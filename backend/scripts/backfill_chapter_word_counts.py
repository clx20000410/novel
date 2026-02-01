"""
Backfill chapter word_count.

Purpose:
  Populate word_count for legacy chapters using selected_version.content,
  or fall back to the latest version when no selected_version exists.

Usage:
  cd backend
  python -m scripts.backfill_chapter_word_counts --dry-run
  python -m scripts.backfill_chapter_word_counts --apply

Options:
  --project-id <ID>   Only process a specific project
  --limit <N>         Limit number of records (debug)
  --verbose           Print per-row updates

Notes:
  - Back up your database first
  - Default is dry-run (no write)
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Optional

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import exists, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, selectinload

from app.core.config import settings
from app.models.novel import Chapter, ChapterVersion


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill chapter word_count")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write changes to DB (default is dry-run)",
    )
    parser.add_argument(
        "--project-id",
        type=str,
        default=None,
        help="Only process the given project_id",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit records (debug)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print verbose updates",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Explicit dry-run (default)",
    )
    return parser.parse_args()


def _compute_word_count(content: Optional[str]) -> int:
    if not content:
        return 0
    return len(content)

def _pick_best_content(chapter: Chapter) -> Optional[str]:
    if chapter.selected_version and chapter.selected_version.content:
        return chapter.selected_version.content
    if chapter.versions:
        for version in reversed(chapter.versions):
            if version.content and version.content.strip():
                return version.content
    return None


async def _backfill(
    session: AsyncSession,
    *,
    project_id: Optional[str],
    limit: Optional[int],
    apply_changes: bool,
    verbose: bool,
) -> None:
    version_exists = exists(select(1).select_from(ChapterVersion).where(ChapterVersion.chapter_id == Chapter.id))
    stmt = (
        select(Chapter)
        .options(
            selectinload(Chapter.selected_version),
            selectinload(Chapter.versions),
        )
        .where(or_(Chapter.word_count == 0, Chapter.word_count.is_(None)))
        .where(or_(Chapter.selected_version_id.isnot(None), version_exists))
        .order_by(Chapter.project_id, Chapter.chapter_number)
    )
    if project_id:
        stmt = stmt.where(Chapter.project_id == project_id)
    if limit:
        stmt = stmt.limit(limit)

    result = await session.execute(stmt)
    chapters = result.scalars().all()

    total = len(chapters)
    updated = 0
    skipped_empty = 0

    for chapter in chapters:
        content = _pick_best_content(chapter)
        new_count = _compute_word_count(content)
        if new_count == 0:
            skipped_empty += 1
            continue
        if chapter.word_count == new_count:
            continue
        if verbose:
            print(
                f"Update: project={chapter.project_id} chapter={chapter.chapter_number} "
                f"{chapter.word_count} -> {new_count}"
            )
        chapter.word_count = new_count
        updated += 1

    if apply_changes:
        await session.commit()
    else:
        await session.rollback()

    print("")
    print("=" * 60)
    print("Backfill complete")
    print(f"Candidates: {total}")
    print(f"Updated: {updated}")
    print(f"Skipped (empty content): {skipped_empty}")
    print(f"Mode: {'APPLY' if apply_changes else 'DRY-RUN'}")
    print("=" * 60)


async def main() -> None:
    args = _parse_args()
    apply_changes = bool(args.apply)

    print("=" * 60)
    print("Chapter word_count backfill")
    print("=" * 60)
    print(f"DB: {settings.sqlalchemy_database_uri}")
    if args.project_id:
        print(f"Project: {args.project_id}")
    if args.limit:
        print(f"Limit: {args.limit}")
    print(f"Mode: {'APPLY' if apply_changes else 'DRY-RUN'}")

    engine = create_async_engine(settings.sqlalchemy_database_uri, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        await _backfill(
            session,
            project_id=args.project_id,
            limit=args.limit,
            apply_changes=apply_changes,
            verbose=bool(args.verbose),
        )

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
