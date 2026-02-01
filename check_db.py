import asyncio
from app.core.database import get_session
from app.models.novel import Chapter, ChapterEvaluation
from sqlalchemy import select

async def check_chapter_6():
    async for session in get_session():
        # 查询第6章
        result = await session.execute(
            select(Chapter).where(Chapter.chapter_number == 6).limit(1)
        )
        chapter = result.scalar_one_or_none()
        
        if not chapter:
            print("未找到第6章")
            return
        
        print(f"章节ID: {chapter.id}")
        print(f"章节号: {chapter.chapter_number}")
        print(f"状态: {chapter.status}")
        print(f"选中版本ID: {chapter.selected_version_id}")
        print(f"字数: {chapter.word_count}")
        print(f"版本数量: {len(chapter.versions)}")
        
        # 查询评审记录
        eval_result = await session.execute(
            select(ChapterEvaluation)
            .where(ChapterEvaluation.chapter_id == chapter.id)
            .order_by(ChapterEvaluation.created_at.desc())
        )
        evaluations = eval_result.scalars().all()
        
        print(f"\n评审记录数量: {len(evaluations)}")
        for i, evaluation in enumerate(evaluations):
            print(f"\n评审记录 {i+1}:")
            print(f"  ID: {evaluation.id}")
            print(f"  版本ID: {evaluation.version_id}")
            print(f"  决策: {evaluation.decision}")
            print(f"  反馈: {evaluation.feedback[:100] if evaluation.feedback else 'None'}...")
            print(f"  评分: {evaluation.score}")
            print(f"  创建时间: {evaluation.created_at}")
        
        break

if __name__ == "__main__":
    asyncio.run(check_chapter_6())
