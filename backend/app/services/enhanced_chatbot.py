"""
增强版AI聊天机器人，集成Qwen模型和mem0记忆功能
"""

import os
import requests
import json
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from dotenv import load_dotenv

from .qwen_mem0_service import QwenMem0Service

# 加载环境变量
load_dotenv()

# 配置日志
logger = logging.getLogger(__name__)

class EnhancedTravelChatbot:
    """增强版旅游聊天机器人，集成mem0记忆功能"""
    
    def __init__(self, memory_service: Optional[QwenMem0Service] = None):
        """
        初始化增强版聊天机器人
        
        Args:
            memory_service: 记忆服务实例，如果为None则创建新实例
        """
        # 初始化Qwen API
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY 环境变量未设置")
        
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        
        # 初始化记忆服务
        if memory_service:
            self.memory_service = memory_service
        else:
            try:
                self.memory_service = QwenMem0Service()
                logger.info("记忆服务初始化成功")
            except Exception as e:
                logger.error(f"记忆服务初始化失败: {e}")
                self.memory_service = None
        
        # 系统提示词模板
        self.system_prompt_template = """你是一个专业的旅游助手AI，具有以下特点：

1. **记忆能力**：能够记住用户的偏好、历史对话和重要信息
2. **个性化服务**：基于用户的历史信息提供个性化建议
3. **专业建议**：提供准确、实用的旅游建议和规划
4. **友好交流**：保持友好、专业、简洁的交流风格
5. **智能推荐**：根据用户偏好推荐合适的景点、美食、住宿等

**重要原则**：
- 如果找到相关记忆，请基于历史信息提供个性化建议
- 如果没有相关记忆，请根据用户问题提供有用的旅游建议
- 不要编造记忆，诚实回答
- 回答要简洁明了，不超过200字
- 主动询问用户偏好以提供更好的服务

**用户历史信息**：
{context}

请基于用户的历史信息和当前问题，提供有用的旅游建议。"""
    
    def _get_relevant_context(self, query: str, user_id: str) -> str:
        """
        获取相关上下文信息
        
        Args:
            query: 用户查询
            user_id: 用户ID
            
        Returns:
            相关上下文信息
        """
        if not self.memory_service:
            return ""
        
        try:
            # 搜索相关记忆
            memories = self.memory_service.search_memories(
                query=query,
                user_id=user_id,
                limit=5
            )
            
            if not memories:
                return ""
            
            # 构建上下文
            context_parts = []
            for memory in memories:
                # 处理不同的返回格式
                if isinstance(memory, dict):
                    content = memory.get("content", "")
                    memory_type = memory.get("metadata", {}).get("type", "unknown")
                    similarity = memory.get("similarity", 0)
                elif isinstance(memory, str):
                    content = memory
                    memory_type = "unknown"
                    similarity = 0.5  # 默认相似度
                else:
                    continue
                
                if similarity > 0.3:  # 只包含相似度较高的记忆
                    context_parts.append(f"- {content}")
            
            if context_parts:
                return "\n".join(context_parts)
            else:
                return ""
                
        except Exception as e:
            logger.error(f"获取相关上下文失败: {e}")
            return ""
    
    def _detect_user_preferences(self, message: str) -> Dict[str, Any]:
        """
        检测用户偏好信息
        
        Args:
            message: 用户消息
            
        Returns:
            检测到的偏好信息
        """
        preferences = {}
        message_lower = message.lower()
        
        # 检测食物偏好
        food_keywords = {
            "清淡": "light",
            "辣": "spicy", 
            "甜": "sweet",
            "咸": "salty",
            "酸": "sour",
            "素食": "vegetarian",
            "海鲜": "seafood"
        }
        
        for keyword, preference in food_keywords.items():
            if keyword in message_lower:
                preferences["food_preference"] = preference
                break
        
        # 检测旅游偏好
        travel_keywords = {
            "文化": "culture",
            "自然": "nature",
            "历史": "history",
            "购物": "shopping",
            "美食": "food",
            "冒险": "adventure",
            "休闲": "relaxation"
        }
        
        for keyword, preference in travel_keywords.items():
            if keyword in message_lower:
                preferences["travel_preference"] = preference
                break
        
        # 检测预算偏好
        budget_keywords = {
            "便宜": "budget",
            "经济": "budget",
            "中等": "mid-range",
            "豪华": "luxury",
            "高端": "luxury"
        }
        
        for keyword, preference in budget_keywords.items():
            if keyword in message_lower:
                preferences["budget_preference"] = preference
                break
        
        return preferences
    
    def _store_conversation(self, user_message: str, ai_response: str, user_id: str):
        """
        存储对话到记忆中
        
        Args:
            user_message: 用户消息
            ai_response: AI回复
            user_id: 用户ID
        """
        if not self.memory_service:
            return
        
        try:
            # 检测用户偏好
            preferences = self._detect_user_preferences(user_message)
            
            # 存储用户消息
            user_metadata = {
                "timestamp": datetime.now().isoformat(),
                "message_type": "user_input"
            }
            if preferences:
                user_metadata["preferences"] = preferences
            
            self.memory_service.add_memory(
                content=f"用户询问: {user_message}",
                user_id=user_id,
                memory_type="conversation",
                metadata=user_metadata
            )
            
            # 存储AI回复
            self.memory_service.add_memory(
                content=f"AI回复: {ai_response}",
                user_id=user_id,
                memory_type="conversation",
                metadata={
                    "timestamp": datetime.now().isoformat(),
                    "message_type": "ai_response"
                }
            )
            
            # 如果有检测到的偏好，单独存储
            if preferences:
                for pref_type, pref_value in preferences.items():
                    self.memory_service.add_memory(
                        content=f"用户偏好: {pref_type} = {pref_value}",
                        user_id=user_id,
                        memory_type="preference",
                        metadata={
                            "preference_type": pref_type,
                            "preference_value": pref_value,
                            "timestamp": datetime.now().isoformat()
                        }
                    )
            
            logger.info(f"对话存储成功 - 用户: {user_id}")
            
        except Exception as e:
            logger.error(f"存储对话失败: {e}")
    
    def chat(self, message: str, user_id: str) -> str:
        """
        与用户聊天
        
        Args:
            message: 用户消息
            user_id: 用户ID
            
        Returns:
            AI回复
        """
        try:
            # 获取相关上下文
            context = self._get_relevant_context(message, user_id)
            
            # 构建系统提示词
            system_content = self.system_prompt_template.format(context=context)
            
            # 准备API请求
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            }
            
            data = {
                "model": "qwen-plus",
                "input": {
                    "messages": [
                        {
                            "role": "system",
                            "content": system_content
                        },
                        {
                            "role": "user",
                            "content": message
                        }
                    ]
                },
                "parameters": {
                    "temperature": 0.7,
                    "max_tokens": 500
                }
            }
            
            logger.info(f"发送请求到Qwen API - 用户: {user_id}")
            
            # 发送请求
            response = requests.post(self.base_url, headers=headers, json=data)
            
            if response.status_code == 400:
                error_data = response.json()
                if error_data.get("code") == "Arrearage":
                    return "抱歉，AI服务暂时不可用（账户余额不足）。不过我可以基于您的历史对话为您提供一些建议。请稍后再试或联系管理员。"
                else:
                    return f"抱歉，AI服务暂时不可用。错误信息：{error_data.get('message', '未知错误')}"
            
            response.raise_for_status()
            result = response.json()
            
            # 提取回复
            if result.get("output") and result["output"].get("text"):
                ai_response = result["output"]["text"]
            elif result.get("output") and result["output"].get("choices"):
                ai_response = result["output"]["choices"][0]["message"]["content"]
            else:
                ai_response = "抱歉，我现在无法回答您的问题，请稍后再试。"
            
            # 存储对话
            self._store_conversation(message, ai_response, user_id)
            
            logger.info(f"聊天完成 - 用户: {user_id}")
            return ai_response
            
        except Exception as e:
            logger.error(f"聊天失败: {e}")
            return "抱歉，服务暂时不可用，请稍后再试。"
    
    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户档案信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户档案信息
        """
        if not self.memory_service:
            return {"error": "记忆服务不可用"}
        
        try:
            # 获取用户记忆统计
            stats = self.memory_service.get_memory_stats(user_id)
            
            # 获取用户偏好
            preferences = self.memory_service.search_memories(
                query="偏好",
                user_id=user_id,
                memory_type="preference",
                limit=10
            )
            
            # 获取最近对话
            recent_conversations = self.memory_service.search_memories(
                query="",
                user_id=user_id,
                memory_type="conversation",
                limit=5
            )
            
            # 构建用户档案
            profile = {
                "user_id": user_id,
                "stats": stats,
                "preferences": [p.get("content", "") if isinstance(p, dict) else str(p) for p in preferences],
                "recent_conversations": [c.get("content", "") if isinstance(c, dict) else str(c) for c in recent_conversations],
                "generated_at": datetime.now().isoformat()
            }
            
            return profile
            
        except Exception as e:
            logger.error(f"获取用户档案失败: {e}")
            return {"error": str(e)}
    
    def generate_travel_recommendation(self, user_id: str, destination: str) -> str:
        """
        基于用户偏好生成旅游推荐
        
        Args:
            user_id: 用户ID
            destination: 目的地
            
        Returns:
            个性化旅游推荐
        """
        if not self.memory_service:
            return "记忆服务不可用，无法提供个性化推荐。"
        
        try:
            # 获取用户偏好
            preferences = self.memory_service.search_memories(
                query="偏好",
                user_id=user_id,
                memory_type="preference",
                limit=10
            )
            
            # 获取相关历史对话
            relevant_memories = self.memory_service.search_memories(
                query=destination,
                user_id=user_id,
                limit=5
            )
            
            # 构建推荐请求
            context_parts = []
            if preferences:
                context_parts.append("用户偏好:")
                for pref in preferences:
                    content = pref.get('content', '') if isinstance(pref, dict) else str(pref)
                    context_parts.append(f"- {content}")
            
            if relevant_memories:
                context_parts.append("相关历史:")
                for memory in relevant_memories:
                    content = memory.get('content', '') if isinstance(memory, dict) else str(memory)
                    context_parts.append(f"- {content}")
            
            context = "\n".join(context_parts) if context_parts else "暂无相关历史信息"
            
            # 生成推荐
            recommendation_prompt = f"""基于以下用户信息和目的地，生成个性化旅游推荐：

用户信息：
{context}

目的地：{destination}

请提供：
1. 适合的景点推荐
2. 美食建议
3. 住宿建议
4. 注意事项
5. 预算建议

请保持简洁明了，不超过300字。"""
            
            return self.chat(recommendation_prompt, user_id)
            
        except Exception as e:
            logger.error(f"生成旅游推荐失败: {e}")
            return "抱歉，无法生成个性化推荐，请稍后再试。"
    
    def clear_user_memories(self, user_id: str, memory_type: Optional[str] = None) -> Dict[str, Any]:
        """
        清空用户记忆
        
        Args:
            user_id: 用户ID
            memory_type: 记忆类型过滤
            
        Returns:
            清空结果
        """
        if not self.memory_service:
            return {"success": False, "error": "记忆服务不可用"}
        
        try:
            result = self.memory_service.clear_user_memories(
                user_id=user_id,
                memory_type=memory_type
            )
            return result
            
        except Exception as e:
            logger.error(f"清空用户记忆失败: {e}")
            return {"success": False, "error": str(e)}


# 创建全局实例
def create_enhanced_chatbot(memory_service: Optional[QwenMem0Service] = None) -> EnhancedTravelChatbot:
    """
    创建增强版聊天机器人实例
    
    Args:
        memory_service: 记忆服务实例
        
    Returns:
        EnhancedTravelChatbot实例
    """
    return EnhancedTravelChatbot(memory_service)


# 示例用法
if __name__ == "__main__":
    # 创建聊天机器人
    chatbot = create_enhanced_chatbot()
    
    # 测试用户ID
    test_user_id = "test_user_001"
    
    # 测试对话
    print("=== 测试对话 ===")
    
    # 第一轮对话
    response1 = chatbot.chat("我想去日本旅游，有什么推荐吗？", test_user_id)
    print(f"用户: 我想去日本旅游，有什么推荐吗？")
    print(f"AI: {response1}\n")
    
    # 第二轮对话（测试记忆功能）
    response2 = chatbot.chat("我喜欢清淡的食物，有什么美食推荐吗？", test_user_id)
    print(f"用户: 我喜欢清淡的食物，有什么美食推荐吗？")
    print(f"AI: {response2}\n")
    
    # 第三轮对话（测试个性化推荐）
    response3 = chatbot.chat("基于我的偏好，给我一些京都的推荐", test_user_id)
    print(f"用户: 基于我的偏好，给我一些京都的推荐")
    print(f"AI: {response3}\n")
    
    # 获取用户档案
    print("=== 用户档案 ===")
    profile = chatbot.get_user_profile(test_user_id)
    print(json.dumps(profile, ensure_ascii=False, indent=2))
    
    # 生成个性化推荐
    print("\n=== 个性化推荐 ===")
    recommendation = chatbot.generate_travel_recommendation(test_user_id, "京都")
    print(f"京都推荐: {recommendation}")
