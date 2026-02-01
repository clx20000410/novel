# AIMETA P=向量存储服务扩展_章节写入和搜索|R=章节分块_向量化_搜索|NR=不含核心向量逻辑|E=VectorStoreServiceExt|X=internal|A=服务扩展|D=vector_store_service_embedding_service|S=none|RD=./README.ai
"""
向量存储服务扩展 (VectorStoreServiceExt)

为 VectorStoreService 添加高层封装方法，简化章节内容的写入和搜索：
1. add_chapter_to_store: 将章节内容分块并写入向量库
2. search: 基于文本查询进行向量检索

这些方法被 FinalizeService 和 KnowledgeRetrievalService 调用。
"""
import logging
import re
from typing import Any, Dict, List, Optional

from .vector_store_service import VectorStoreService
from .embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class VectorStoreServiceExt(VectorStoreService):
    """
    向量存储服务扩展
    
    在基础 VectorStoreService 上添加高层封装方法。
    """
    
    def __init__(self, embedding_service: Optional[EmbeddingService] = None):
        super().__init__()
        self._embedding_service = embedding_service
    
    async def add_chapter_to_store(
        self,
        project_id: str,
        chapter_number: int,
        content: str,
        chapter_title: Optional[str] = None,
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ) -> int:
        """
        将章节内容分块并写入向量库
        
        Args:
            project_id: 项目ID
            chapter_number: 章节号
            content: 章节内容
            chapter_title: 章节标题
            chunk_size: 分块大小（字符数）
            chunk_overlap: 分块重叠（字符数）
            
        Returns:
            写入的分块数量
        """
        if not self._embedding_service:
            logger.warning("未配置嵌入服务，跳过向量库写入")
            return 0
        
        # 先删除该章节的旧数据
        await self.delete_by_chapters(project_id, [chapter_number])
        
        # 分块
        chunks = self._split_text(content, chunk_size, chunk_overlap)
        
        if not chunks:
            return 0
        
        # 生成嵌入向量并写入
        records = []
        for idx, chunk in enumerate(chunks):
            try:
                embedding = await self._embedding_service.get_embedding(chunk)
                if embedding:
                    records.append({
                        "id": f"{project_id}_{chapter_number}_{idx}",
                        "project_id": project_id,
                        "chapter_number": chapter_number,
                        "chunk_index": idx,
                        "chapter_title": chapter_title,
                        "content": chunk,
                        "embedding": embedding,
                        "metadata": {
                            "source": "chapter",
                            "chunk_index": idx,
                            "total_chunks": len(chunks)
                        }
                    })
            except Exception as e:
                logger.error(f"生成嵌入向量失败: {e}")
        
        if records:
            await self.upsert_chunks(records=records)
        
        logger.info(f"已写入章节向量: project={project_id}, chapter={chapter_number}, chunks={len(records)}")
        return len(records)
    
    async def search(
        self,
        project_id: str,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        基于文本查询进行向量检索
        
        Args:
            project_id: 项目ID
            query: 查询文本
            top_k: 返回数量
            
        Returns:
            检索结果列表
        """
        if not self._embedding_service:
            logger.warning("未配置嵌入服务，跳过向量检索")
            return []
        
        try:
            # 生成查询向量
            query_embedding = await self._embedding_service.get_embedding(query)
            if not query_embedding:
                return []
            
            # 执行检索
            chunks = await self.query_chunks(
                project_id=project_id,
                embedding=query_embedding,
                top_k=top_k
            )
            
            # 转换为字典格式
            return [
                {
                    "content": chunk.content,
                    "source": "chapter",
                    "chapter_number": chunk.chapter_number,
                    "score": 1.0 - chunk.score,  # 转换为相似度
                    "metadata": chunk.metadata
                }
                for chunk in chunks
            ]
        
        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            return []
    
    async def search_summaries(
        self,
        project_id: str,
        query: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        基于文本查询检索章节摘要
        
        Args:
            project_id: 项目ID
            query: 查询文本
            top_k: 返回数量
            
        Returns:
            检索结果列表
        """
        if not self._embedding_service:
            logger.warning("未配置嵌入服务，跳过摘要检索")
            return []
        
        try:
            query_embedding = await self._embedding_service.get_embedding(query)
            if not query_embedding:
                return []
            
            summaries = await self.query_summaries(
                project_id=project_id,
                embedding=query_embedding,
                top_k=top_k
            )
            
            return [
                {
                    "chapter_number": s.chapter_number,
                    "title": s.title,
                    "summary": s.summary,
                    "score": 1.0 - s.score
                }
                for s in summaries
            ]
        
        except Exception as e:
            logger.error(f"摘要检索失败: {e}")
            return []
    
    async def add_summary_to_store(
        self,
        project_id: str,
        chapter_number: int,
        title: str,
        summary: str
    ) -> bool:
        """
        将章节摘要写入向量库
        
        Args:
            project_id: 项目ID
            chapter_number: 章节号
            title: 章节标题
            summary: 章节摘要
            
        Returns:
            是否成功
        """
        if not self._embedding_service:
            logger.warning("未配置嵌入服务，跳过摘要写入")
            return False
        
        try:
            embedding = await self._embedding_service.get_embedding(summary)
            if not embedding:
                return False
            
            await self.upsert_summaries(records=[{
                "id": f"{project_id}_summary_{chapter_number}",
                "project_id": project_id,
                "chapter_number": chapter_number,
                "title": title,
                "summary": summary,
                "embedding": embedding
            }])
            
            logger.info(f"已写入章节摘要: project={project_id}, chapter={chapter_number}")
            return True
        
        except Exception as e:
            logger.error(f"写入章节摘要失败: {e}")
            return False
    
    def _split_text(
        self,
        text: str,
        chunk_size: int,
        chunk_overlap: int
    ) -> List[str]:
        """
        将文本分块
        
        优先按段落分割，保持语义完整性。
        """
        if not text:
            return []
        
        # 按段落分割
        paragraphs = re.split(r'\n\s*\n', text)
        
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # 如果当前段落加上已有内容超过 chunk_size
            if len(current_chunk) + len(para) > chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                
                # 如果单个段落就超过 chunk_size，需要进一步分割
                if len(para) > chunk_size:
                    # 按句子分割
                    sentences = re.split(r'([。！？.!?])', para)
                    temp_chunk = ""
                    for i in range(0, len(sentences), 2):
                        sentence = sentences[i]
                        if i + 1 < len(sentences):
                            sentence += sentences[i + 1]
                        
                        if len(temp_chunk) + len(sentence) > chunk_size:
                            if temp_chunk:
                                chunks.append(temp_chunk)
                            temp_chunk = sentence
                        else:
                            temp_chunk += sentence
                    
                    current_chunk = temp_chunk
                else:
                    current_chunk = para
            else:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
        
        if current_chunk:
            chunks.append(current_chunk)
        
        # 添加重叠
        if chunk_overlap > 0 and len(chunks) > 1:
            overlapped_chunks = []
            for i, chunk in enumerate(chunks):
                if i > 0:
                    # 从前一个 chunk 取重叠部分
                    prev_chunk = chunks[i - 1]
                    overlap_text = prev_chunk[-chunk_overlap:] if len(prev_chunk) > chunk_overlap else prev_chunk
                    chunk = overlap_text + "..." + chunk
                overlapped_chunks.append(chunk)
            return overlapped_chunks
        
        return chunks


__all__ = ["VectorStoreServiceExt"]
