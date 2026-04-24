"""
基于Qwen模型的mem0记忆功能服务
提供智能记忆存储、检索和管理功能
"""

import os
import json
import logging
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from dotenv import load_dotenv
from mem0 import Memory
import requests

# 加载环境变量
load_dotenv(override=True)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QwenMem0Service:
    """基于Qwen模型的mem0记忆服务"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化Qwen mem0服务
        
        Args:
            config: 自定义配置，如果为None则使用默认配置
        """
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY 环境变量未设置")
        
        # 默认配置
        self.default_config = {
            "llm": {
                "provider": "openai",
                "config": {
                    "api_key": self.api_key,
                    "openai_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                    "model": "qwen-plus",
                    "temperature": 0.7,
                    "max_tokens": 200
                }
            },
            "embedder": {
                "provider": "openai",
                "config": {
                    "api_key": self.api_key,
                    "openai_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                    "model": "text-embedding-v2"
                }
            },
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "url": "http://localhost:6333",
                    "collection_name": "mem0_memories"
                }
            }
        }
        
        # 使用自定义配置或默认配置
        self.config = config or self.default_config
        
        # 初始化mem0实例
        try:
            self.memory = Memory.from_config(self.config)
            logger.info("Qwen mem0服务初始化成功")
        except Exception as e:
            logger.error(f"mem0初始化失败: {e}")
            raise
    
    def add_memory(
        self, 
        content: str, 
        user_id: str, 
        metadata: Optional[Dict] = None,
        memory_type: str = "conversation"
    ) -> Dict[str, Any]:
        """
        添加记忆
        
        Args:
            content: 记忆内容
            user_id: 用户ID
            metadata: 元数据
            memory_type: 记忆类型 (conversation, preference, fact, etc.)
            
        Returns:
            添加结果
        """
        try:
            # 构建元数据
            full_metadata = {
                "type": memory_type,
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id
            }
            if metadata:
                full_metadata.update(metadata)
            
            # 添加记忆
            result = self.memory.add(
                messages=content,
                user_id=user_id,
                metadata=full_metadata
            )
            
            logger.info(f"成功添加记忆 - 用户: {user_id}, 类型: {memory_type}")
            return {
                "success": True,
                "memory_id": result.get("id"),
                "content": content,
                "metadata": full_metadata
            }
            
        except Exception as e:
            logger.error(f"添加记忆失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def search_memories(
        self, 
        query: str, 
        user_id: str, 
        limit: int = 5,
        memory_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索相关记忆
        
        Args:
            query: 搜索查询
            user_id: 用户ID
            limit: 返回结果数量限制
            memory_type: 记忆类型过滤
            
        Returns:
            相关记忆列表
        """
        try:
            # 执行搜索
            search_response = self.memory.search(
                query=query,
                user_id=user_id,
                limit=limit
            )
            
            # 解析搜索结果
            if isinstance(search_response, dict) and 'results' in search_response:
                results = search_response['results']
            else:
                results = search_response if isinstance(search_response, list) else []
            
            # 如果指定了记忆类型，进行过滤
            if memory_type and results:
                filtered_results = []
                for result in results:
                    if isinstance(result, dict) and result.get("metadata", {}).get("type") == memory_type:
                        filtered_results.append(result)
                results = filtered_results
            
            logger.info(f"搜索记忆 - 查询: {query}, 用户: {user_id}, 结果数: {len(results)}")
            return results
            
        except Exception as e:
            logger.error(f"搜索记忆失败: {e}")
            return []
    
    def get_user_memories(
        self, 
        user_id: str, 
        limit: int = 50,
        memory_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取用户的所有记忆
        
        Args:
            user_id: 用户ID
            limit: 返回结果数量限制
            memory_type: 记忆类型过滤
            
        Returns:
            用户记忆列表
        """
        try:
            # 使用空查询获取所有记忆
            search_response = self.memory.search(
                query="",
                user_id=user_id,
                limit=limit
            )
            
            # 解析搜索结果
            if isinstance(search_response, dict) and 'results' in search_response:
                results = search_response['results']
            else:
                results = search_response if isinstance(search_response, list) else []
            
            # 如果指定了记忆类型，进行过滤
            if memory_type and results:
                filtered_results = []
                for result in results:
                    if isinstance(result, dict) and result.get("metadata", {}).get("type") == memory_type:
                        filtered_results.append(result)
                results = filtered_results
            
            logger.info(f"获取用户记忆 - 用户: {user_id}, 数量: {len(results)}")
            return results
            
        except Exception as e:
            logger.error(f"获取用户记忆失败: {e}")
            return []
    
    def update_memory(
        self, 
        memory_id: str, 
        content: str, 
        user_id: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        更新记忆
        
        Args:
            memory_id: 记忆ID
            content: 新的记忆内容
            user_id: 用户ID
            metadata: 新的元数据
            
        Returns:
            更新结果
        """
        try:
            # mem0的更新方法
            result = self.memory.update(
                memory_id=memory_id,
                messages=content,
                user_id=user_id,
                metadata=metadata
            )
            
            logger.info(f"成功更新记忆 - ID: {memory_id}, 用户: {user_id}")
            return {
                "success": True,
                "memory_id": memory_id,
                "content": content,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"更新记忆失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_memory(
        self, 
        memory_id: str, 
        user_id: str
    ) -> Dict[str, Any]:
        """
        删除记忆
        
        Args:
            memory_id: 记忆ID
            user_id: 用户ID
            
        Returns:
            删除结果
        """
        try:
            # mem0的删除方法
            result = self.memory.delete(
                memory_id=memory_id,
                user_id=user_id
            )
            
            logger.info(f"成功删除记忆 - ID: {memory_id}, 用户: {user_id}")
            return {
                "success": True,
                "memory_id": memory_id
            }
            
        except Exception as e:
            logger.error(f"删除记忆失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_memory_summary(
        self, 
        user_id: str,
        memory_type: Optional[str] = None
    ) -> str:
        """
        生成用户记忆摘要
        
        Args:
            user_id: 用户ID
            memory_type: 记忆类型过滤
            
        Returns:
            记忆摘要
        """
        try:
            # 获取用户记忆
            memories = self.get_user_memories(user_id, limit=100, memory_type=memory_type)
            
            if not memories:
                return f"用户 {user_id} 暂无记忆记录"
            
            # 按类型分组统计
            type_counts = {}
            for memory in memories:
                mem_type = memory.get("metadata", {}).get("type", "unknown")
                type_counts[mem_type] = type_counts.get(mem_type, 0) + 1
            
            # 生成摘要
            summary_parts = [f"用户 {user_id} 共有 {len(memories)} 条记忆记录:"]
            for mem_type, count in type_counts.items():
                summary_parts.append(f"- {mem_type}: {count} 条")
            
            # 添加最近记忆示例
            recent_memories = memories[:3]
            if recent_memories:
                summary_parts.append("\n最近的记忆:")
                for i, memory in enumerate(recent_memories, 1):
                    content = memory.get("content", "")[:50] + "..." if len(memory.get("content", "")) > 50 else memory.get("content", "")
                    summary_parts.append(f"{i}. {content}")
            
            summary = "\n".join(summary_parts)
            logger.info(f"生成记忆摘要 - 用户: {user_id}")
            return summary
            
        except Exception as e:
            logger.error(f"生成记忆摘要失败: {e}")
            return f"无法生成用户 {user_id} 的记忆摘要"
    
    def clear_user_memories(
        self, 
        user_id: str,
        memory_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        清空用户记忆
        
        Args:
            user_id: 用户ID
            memory_type: 记忆类型过滤，如果指定则只清空该类型的记忆
            
        Returns:
            清空结果
        """
        try:
            # 获取用户记忆
            memories = self.get_user_memories(user_id, limit=1000)
            
            if not memories:
                return {
                    "success": True,
                    "message": f"用户 {user_id} 没有记忆需要清空",
                    "deleted_count": 0
                }
            
            # 过滤要删除的记忆
            memories_to_delete = memories
            if memory_type:
                memories_to_delete = [
                    mem for mem in memories 
                    if mem.get("metadata", {}).get("type") == memory_type
                ]
            
            # 删除记忆
            deleted_count = 0
            for memory in memories_to_delete:
                memory_id = memory.get("id")
                if memory_id:
                    delete_result = self.delete_memory(memory_id, user_id)
                    if delete_result.get("success"):
                        deleted_count += 1
            
            logger.info(f"清空用户记忆 - 用户: {user_id}, 删除数量: {deleted_count}")
            return {
                "success": True,
                "message": f"成功清空用户 {user_id} 的记忆",
                "deleted_count": deleted_count
            }
            
        except Exception as e:
            logger.error(f"清空用户记忆失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户记忆统计信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            统计信息
        """
        try:
            memories = self.get_user_memories(user_id, limit=1000)
            
            if not memories:
                return {
                    "total_memories": 0,
                    "memory_types": {},
                    "oldest_memory": None,
                    "newest_memory": None
                }
            
            # 统计记忆类型
            type_counts = {}
            timestamps = []
            
            for memory in memories:
                mem_type = memory.get("metadata", {}).get("type", "unknown")
                type_counts[mem_type] = type_counts.get(mem_type, 0) + 1
                
                timestamp = memory.get("metadata", {}).get("timestamp")
                if timestamp:
                    timestamps.append(timestamp)
            
            # 排序时间戳
            timestamps.sort()
            
            stats = {
                "total_memories": len(memories),
                "memory_types": type_counts,
                "oldest_memory": timestamps[0] if timestamps else None,
                "newest_memory": timestamps[-1] if timestamps else None
            }
            
            logger.info(f"获取记忆统计 - 用户: {user_id}, 总数: {len(memories)}")
            return stats
            
        except Exception as e:
            logger.error(f"获取记忆统计失败: {e}")
            return {
                "error": str(e)
            }
    
    def export_memories(
        self, 
        user_id: str,
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        导出用户记忆到文件
        
        Args:
            user_id: 用户ID
            file_path: 导出文件路径，如果为None则使用默认路径
            
        Returns:
            导出结果
        """
        try:
            memories = self.get_user_memories(user_id, limit=1000)
            
            if not memories:
                return {
                    "success": False,
                    "message": f"用户 {user_id} 没有记忆可导出"
                }
            
            # 构建导出数据
            export_data = {
                "user_id": user_id,
                "export_time": datetime.now().isoformat(),
                "total_memories": len(memories),
                "memories": memories
            }
            
            # 确定文件路径
            if not file_path:
                file_path = f"./memories_export_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"导出记忆成功 - 用户: {user_id}, 文件: {file_path}")
            return {
                "success": True,
                "file_path": file_path,
                "total_memories": len(memories)
            }
            
        except Exception as e:
            logger.error(f"导出记忆失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def import_memories(
        self, 
        file_path: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        从文件导入记忆
        
        Args:
            file_path: 导入文件路径
            user_id: 目标用户ID，如果为None则使用文件中的用户ID
            
        Returns:
            导入结果
        """
        try:
            # 读取文件
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # 确定用户ID
            target_user_id = user_id or import_data.get("user_id")
            if not target_user_id:
                return {
                    "success": False,
                    "error": "无法确定目标用户ID"
                }
            
            memories = import_data.get("memories", [])
            if not memories:
                return {
                    "success": False,
                    "message": "文件中没有记忆数据"
                }
            
            # 导入记忆
            imported_count = 0
            for memory in memories:
                content = memory.get("content", "")
                metadata = memory.get("metadata", {})
                
                if content:
                    result = self.add_memory(
                        content=content,
                        user_id=target_user_id,
                        metadata=metadata
                    )
                    if result.get("success"):
                        imported_count += 1
            
            logger.info(f"导入记忆成功 - 用户: {target_user_id}, 数量: {imported_count}")
            return {
                "success": True,
                "imported_count": imported_count,
                "total_count": len(memories)
            }
            
        except Exception as e:
            logger.error(f"导入记忆失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# 创建全局实例
def create_qwen_mem0_service(config: Optional[Dict] = None) -> QwenMem0Service:
    """
    创建Qwen mem0服务实例
    
    Args:
        config: 自定义配置
        
    Returns:
        QwenMem0Service实例
    """
    return QwenMem0Service(config)


# 示例用法
if __name__ == "__main__":
    # 创建服务实例
    service = create_qwen_mem0_service()
    
    # 测试用户ID
    test_user_id = "test_user_001"
    
    # 添加一些测试记忆
    print("=== 添加测试记忆 ===")
    service.add_memory(
        content="用户喜欢清淡口味的食物，不喜欢太辣",
        user_id=test_user_id,
        memory_type="preference",
        metadata={"category": "food", "preference": "light"}
    )
    
    service.add_memory(
        content="用户计划去日本旅游，对传统文化很感兴趣",
        user_id=test_user_id,
        memory_type="plan",
        metadata={"destination": "Japan", "interest": "culture"}
    )
    
    service.add_memory(
        content="用户询问了关于京都的旅游景点推荐",
        user_id=test_user_id,
        memory_type="conversation",
        metadata={"topic": "travel", "location": "Kyoto"}
    )
    
    # 搜索记忆
    print("\n=== 搜索记忆 ===")
    results = service.search_memories("日本旅游", test_user_id, limit=3)
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.get('content', '')}")
        print(f"   相似度: {result.get('similarity', 0):.4f}")
        print(f"   元数据: {result.get('metadata', {})}")
        print()
    
    # 获取记忆统计
    print("=== 记忆统计 ===")
    stats = service.get_memory_stats(test_user_id)
    print(f"总记忆数: {stats.get('total_memories', 0)}")
    print(f"记忆类型: {stats.get('memory_types', {})}")
    
    # 生成摘要
    print("\n=== 记忆摘要 ===")
    summary = service.generate_memory_summary(test_user_id)
    print(summary)
