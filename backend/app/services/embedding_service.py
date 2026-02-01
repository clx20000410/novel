# AIMETA P=嵌入服务_文本向量化|R=文本嵌入_向量生成|NR=不含存储逻辑|E=EmbeddingService|X=internal|A=嵌入生成|D=openai|S=none|RD=./README.ai
"""
嵌入服务 (EmbeddingService)

提供文本向量化功能，支持：
1. OpenAI 嵌入模型
2. 本地嵌入模型（可选）
3. 批量嵌入生成

用于支持向量检索功能。
"""
import logging
from typing import List, Optional, Sequence
import hashlib

from ..core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    嵌入服务
    
    负责将文本转换为向量表示。
    """
    
    def __init__(self):
        self._client = None
        self._model = settings.embedding_model if hasattr(settings, 'embedding_model') else "text-embedding-3-small"
        self._cache = {}  # 简单的内存缓存
        self._init_client()
    
    def _init_client(self):
        """初始化 OpenAI 客户端"""
        try:
            from openai import AsyncOpenAI
            api_key = settings.openai_api_key if hasattr(settings, 'openai_api_key') else None
            if api_key:
                self._client = AsyncOpenAI(api_key=api_key)
                logger.info("嵌入服务初始化成功")
            else:
                logger.warning("未配置 OpenAI API Key，嵌入服务不可用")
        except ImportError:
            logger.warning("未安装 openai 包，嵌入服务不可用")
        except Exception as e:
            logger.error(f"初始化嵌入服务失败: {e}")
    
    async def get_embedding(
        self,
        text: str,
        use_cache: bool = True
    ) -> Optional[List[float]]:
        """
        获取文本的嵌入向量
        
        Args:
            text: 输入文本
            use_cache: 是否使用缓存
            
        Returns:
            嵌入向量，如果失败返回 None
        """
        if not text or not self._client:
            return None
        
        # 检查缓存
        if use_cache:
            cache_key = self._get_cache_key(text)
            if cache_key in self._cache:
                return self._cache[cache_key]
        
        try:
            response = await self._client.embeddings.create(
                model=self._model,
                input=text[:8000]  # 限制长度
            )
            embedding = response.data[0].embedding
            
            # 存入缓存
            if use_cache:
                self._cache[cache_key] = embedding
            
            return embedding
        
        except Exception as e:
            logger.error(f"生成嵌入向量失败: {e}")
            return None
    
    async def get_embeddings_batch(
        self,
        texts: Sequence[str],
        use_cache: bool = True
    ) -> List[Optional[List[float]]]:
        """
        批量获取文本的嵌入向量
        
        Args:
            texts: 输入文本列表
            use_cache: 是否使用缓存
            
        Returns:
            嵌入向量列表
        """
        if not texts or not self._client:
            return [None] * len(texts)
        
        results = []
        uncached_indices = []
        uncached_texts = []
        
        # 检查缓存
        for i, text in enumerate(texts):
            if use_cache:
                cache_key = self._get_cache_key(text)
                if cache_key in self._cache:
                    results.append(self._cache[cache_key])
                    continue
            
            results.append(None)
            uncached_indices.append(i)
            uncached_texts.append(text[:8000])
        
        # 批量请求未缓存的文本
        if uncached_texts:
            try:
                response = await self._client.embeddings.create(
                    model=self._model,
                    input=uncached_texts
                )
                
                for j, embedding_data in enumerate(response.data):
                    idx = uncached_indices[j]
                    embedding = embedding_data.embedding
                    results[idx] = embedding
                    
                    # 存入缓存
                    if use_cache:
                        cache_key = self._get_cache_key(texts[idx])
                        self._cache[cache_key] = embedding
            
            except Exception as e:
                logger.error(f"批量生成嵌入向量失败: {e}")
        
        return results
    
    def _get_cache_key(self, text: str) -> str:
        """生成缓存键"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
    
    @property
    def is_available(self) -> bool:
        """检查服务是否可用"""
        return self._client is not None


__all__ = ["EmbeddingService"]
