from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from qdrant_client.http.exceptions import UnexpectedResponse
from typing import List, Dict, Any
import numpy as np
from ..config import settings

class RAGService:
    def __init__(self):
        # 暂时禁用 RAG 服务初始化，避免 Qdrant 冲突
        print("RAG服务已禁用，跳过初始化")
        self.client = None
        self.collection_name = None
        return
        
        try:
            self.client = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT
            )
            self.collection_name = "travel_knowledge"
            self._init_collection()
        except Exception as e:
            print(f"RAG服务初始化失败: {e}")
            # 如果初始化失败，设置为 None，避免后续调用出错
            self.client = None
            self.collection_name = None
    
    def _init_collection(self):
        """初始化向量集合"""
        if not self.client:
            return
            
        try:
            # 检查集合是否存在
            self.client.get_collection(self.collection_name)
            print(f"集合 {self.collection_name} 已存在")
        except Exception as e:
            # 集合不存在，创建新集合
            try:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
                )
                print(f"成功创建集合 {self.collection_name}")
            except UnexpectedResponse as create_error:
                # 处理 Qdrant 的 409 冲突错误
                if create_error.status_code == 409 and "already exists" in str(create_error):
                    print(f"集合 {self.collection_name} 已存在，继续使用")
                else:
                    print(f"创建集合失败: {create_error}")
                    raise create_error
            except Exception as create_error:
                print(f"创建集合失败: {create_error}")
                # 如果是集合已存在的错误，忽略
                if "already exists" in str(create_error):
                    print(f"集合 {self.collection_name} 已存在，继续使用")
                else:
                    raise create_error
    
    async def add_knowledge(self, text: str, metadata: Dict[str, Any], vector: List[float]):
        """添加知识到向量数据库"""
        if not self.client:
            print("RAG服务未初始化，跳过添加知识")
            return
            
        point = PointStruct(
            id=hash(text) % (2**63 - 1),
            vector=vector,
            payload={
                "text": text,
                "metadata": metadata
            }
        )
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )
    
    async def search_knowledge(self, query_vector: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """搜索相关知识"""
        if not self.client:
            print("RAG服务未初始化，返回空结果")
            return []
            
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit
        )
        
        return [
            {
                "text": result.payload["text"],
                "metadata": result.payload["metadata"],
                "score": result.score
            }
            for result in search_result
        ]
    
    async def add_trip_memory(self, memory: Dict[str, Any], vector: List[float]):
        """添加旅行记忆到向量数据库"""
        if not self.client:
            print("RAG服务未初始化，跳过添加旅行记忆")
            return
            
        collection_name = f"trip_{memory['trip_id']}_memories"
        
        try:
            self.client.get_collection(collection_name)
        except Exception as e:
            try:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
                )
            except UnexpectedResponse as create_error:
                # 处理 Qdrant 的 409 冲突错误
                if create_error.status_code == 409 and "already exists" in str(create_error):
                    pass
                else:
                    raise create_error
            except Exception as create_error:
                # 如果是集合已存在的错误，忽略
                if "already exists" in str(create_error):
                    pass
                else:
                    raise create_error
        
        point = PointStruct(
            id=memory["id"],
            vector=vector,
            payload=memory
        )
        
        self.client.upsert(
            collection_name=collection_name,
            points=[point]
        )
