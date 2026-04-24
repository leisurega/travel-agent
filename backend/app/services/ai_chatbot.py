import os
import requests
import json
from typing import List, Dict, Optional
from dotenv import load_dotenv
from mem0 import Memory
from .qwen_mem0_service import QwenMem0Service, create_qwen_mem0_service

# 加载.env文件，强制覆盖环境变量
load_dotenv(override=True)

class TravelChatbot:
    def __init__(self):
        # Initialize Qwen API
        self.api_key = os.getenv("DASHSCOPE_API_KEY", "your_dashscope_api_key")
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        
        # 初始化 Qwen mem0 记忆系统
        try:
            # 使用 QwenMem0Service 进行记忆管理
            self.mem0_service = create_qwen_mem0_service()
            print(f"[DEBUG] Qwen mem0 记忆系统初始化成功")
            
        except Exception as e:
            print(f"[DEBUG] Qwen mem0 memory 初始化失败: {e}")
            print(f"[DEBUG] 将使用简单内存存储作为备用方案")
            self.mem0_service = None
        
        # 简单的内存存储（备用）
        self.user_memories = {}
    
    def get_relevant_memories(self, query: str, user_id: str) -> str:
        """获取相关的记忆上下文（使用 QwenMem0Service 语义搜索）"""
        try:
            print(f"[DEBUG] 获取记忆 - 用户ID: {user_id}")
            print(f"[DEBUG] 查询内容: {query}")
            
            # 优先使用 QwenMem0Service 进行语义搜索
            if self.mem0_service is not None:
                result = self._get_relevant_memories_qwen_mem0(query, user_id)
                if result:  # 如果 mem0 搜索成功
                    return result
                else:  # 如果 mem0 搜索失败，使用备用方案
                    print(f"[DEBUG] mem0 搜索失败，使用备用关键词匹配")
                    return self._get_relevant_memories_improved(query, user_id)
            else:
                # 回退到关键词匹配
                return self._get_relevant_memories_improved(query, user_id)
                
        except Exception as e:
            print(f"获取记忆失败: {e}")
            # 发生异常时使用备用方案
            return self._get_relevant_memories_improved(query, user_id)
    
    def _get_relevant_memories_qwen_mem0(self, query: str, user_id: str) -> str:
        """使用 QwenMem0Service 进行语义搜索获取相关记忆"""
        try:
            print(f"[DEBUG] 使用 QwenMem0Service 搜索记忆 - 用户ID: {user_id}, 查询: {query}")
            
            # 使用 QwenMem0Service 搜索记忆
            results = self.mem0_service.search_memories(
                query=query,
                user_id=user_id,
                limit=5
            )
            
            print(f"[DEBUG] 搜索结果: {results}")
            
            if not results:
                print(f"[DEBUG] QwenMem0Service 未找到相关记忆")
                return ""
            
            print(f"[DEBUG] QwenMem0Service 找到 {len(results)} 条相关记忆")
            
            # 构建上下文
            context = "相关的历史信息:\n"
            for i, result in enumerate(results, 1):
                print(f"[DEBUG] 原始搜索结果 {i}: {result}")
                content = result.get('content', result.get('memory', ''))
                similarity = result.get('similarity', result.get('score', 0))
                print(f"[DEBUG] 记忆 {i}: {content} (相似度: {similarity:.4f})")
                context += f"- {content}\n"
            
            print(f"[DEBUG] 生成的上下文: {context}")
            return context
            
        except Exception as e:
            print(f"[DEBUG] QwenMem0Service 搜索失败: {e}")
            # 回退到关键词匹配
            return self._get_relevant_memories_improved(query, user_id)
    
    def _get_relevant_memories_mem0(self, query: str, user_id: str) -> str:
        """使用 mem0 进行语义搜索获取相关记忆"""
        try:
            print(f"[DEBUG] 使用 mem0 搜索记忆 - 用户ID: {user_id}")
            
            # 参考 mem0_qwen_integration.py 的搜索方式
            results = self.memory.search(query, user_id=user_id, limit=3)
            
            if not results:
                print(f"[DEBUG] mem0 未找到相关记忆")
                return ""
            
            print(f"[DEBUG] mem0 找到 {len(results)} 条相关记忆")
            
            # 构建上下文
            context = "相关的历史信息:\n"
            for i, result in enumerate(results, 1):
                content = result.get('content', '')
                similarity = result.get('similarity', 0)
                print(f"[DEBUG] 记忆 {i}: {content} (相似度: {similarity:.4f})")
                context += f"- {content}\n"
            
            print(f"[DEBUG] 生成的上下文: {context}")
            return context
            
        except Exception as e:
            print(f"[DEBUG] mem0 搜索失败: {e}")
            # 回退到关键词匹配
            return self._get_relevant_memories_improved(query, user_id)
    
    def _get_relevant_memories_improved(self, query: str, user_id: str) -> str:
        """改进的关键词匹配"""
        try:
            # 首先尝试从 mem0 服务获取用户记忆
            if self.mem0_service is not None:
                try:
                    all_memories = self.mem0_service.get_user_memories(user_id, limit=10)
                    print(f"[DEBUG] 从 mem0 获取到 {len(all_memories)} 条记忆")
                    user_memories = [mem.get('memory', mem.get('content', '')) for mem in all_memories if mem.get('memory') or mem.get('content')]
                except Exception as e:
                    print(f"[DEBUG] 从 mem0 获取记忆失败: {e}")
                    user_memories = self.user_memories.get(user_id, [])
            else:
                user_memories = self.user_memories.get(user_id, [])
            
            print(f"[DEBUG] 用户 {user_id} 的记忆: {user_memories}")
            
            if not user_memories:
                print(f"[DEBUG] 用户 {user_id} 没有记忆")
                return ""
            
            relevant = []
            query_lower = query.lower()
            print(f"[DEBUG] 查询内容: {query_lower}")
            
            # 定义更全面的关键词映射
            keyword_mapping = {
                '口味': ['口味', '味道', '清淡', '辣', '甜', '咸', '酸', '偏好', '喜欢'],
                '美食': ['美食', '食物', '菜', '吃', '餐厅', '料理', '菜系'],
                '旅游': ['旅游', '旅行', '景点', '地方', '城市', '国家', '目的地', '巴厘岛', '喜欢'],
                '推荐': ['推荐', '建议', '介绍', '什么', '哪些', '如何'],
                '喜欢': ['喜欢', '爱好', '偏好', '爱', '钟爱', '偏爱']
            }
            
            # 扩展查询关键词
            expanded_keywords = [query_lower]
            for key, values in keyword_mapping.items():
                if key in query_lower:
                    expanded_keywords.extend(values)
            
            print(f"[DEBUG] 扩展后的关键词: {expanded_keywords}")
            
            # 优先匹配包含"喜欢"的记忆
            for memory in user_memories:
                print(f"[DEBUG] 检查记忆: {memory}")
                memory_lower = memory.lower()
                
                # 优先匹配包含"喜欢"的记忆
                if '喜欢' in memory_lower and any(keyword in memory_lower for keyword in ['巴厘岛', '地方', '旅游', '旅行']):
                    relevant.insert(0, memory)  # 插入到列表开头
                    print(f"[DEBUG] 优先匹配的记忆: {memory}")
                # 然后匹配其他相关记忆
                elif any(keyword in memory_lower for keyword in expanded_keywords):
                    relevant.append(memory)
                    print(f"[DEBUG] 匹配的记忆: {memory}")
            
            if relevant:
                context = "相关的历史信息:\n"
                for memory in relevant:
                    context += f"- {memory}\n"
                print(f"[DEBUG] 生成的上下文: {context}")
                return context
            print(f"[DEBUG] 没有找到相关记忆")
            return ""
        except Exception as e:
            print(f"改进记忆匹配失败: {e}")
            return ""
    
    def _get_relevant_memories_simple(self, query: str, user_id: str) -> str:
        """简单的关键词匹配（备用方法）"""
        try:
            user_memories = self.user_memories.get(user_id, [])
            print(f"[DEBUG] 用户 {user_id} 的记忆: {user_memories}")
            
            if not user_memories:
                print(f"[DEBUG] 用户 {user_id} 没有记忆")
                return ""
            
            # 改进的关键词匹配
            relevant = []
            query_lower = query.lower()
            print(f"[DEBUG] 查询内容: {query_lower}")
            
            # 定义关键词映射，提高匹配准确性
            keyword_mapping = {
                '口味': ['口味', '味道', '清淡', '辣', '甜', '咸', '酸'],
                '美食': ['美食', '食物', '菜', '吃', '餐厅', '料理'],
                '旅游': ['旅游', '旅行', '景点', '地方', '城市', '国家'],
                '推荐': ['推荐', '建议', '介绍', '什么']
            }
            
            # 扩展查询关键词
            expanded_keywords = [query_lower]
            for key, values in keyword_mapping.items():
                if key in query_lower:
                    expanded_keywords.extend(values)
            
            print(f"[DEBUG] 扩展后的关键词: {expanded_keywords}")
            
            for memory in user_memories[-5:]:  # 只取最近5条记忆
                print(f"[DEBUG] 检查记忆: {memory}")
                memory_lower = memory.lower()
                
                # 检查是否有任何扩展关键词匹配
                if any(keyword in memory_lower for keyword in expanded_keywords):
                    relevant.append(memory)
                    print(f"[DEBUG] 匹配的记忆: {memory}")
            
            if relevant:
                context = "相关的历史信息:\n"
                for memory in relevant:
                    context += f"- {memory}\n"
                print(f"[DEBUG] 生成的上下文: {context}")
                return context
            print(f"[DEBUG] 没有找到相关记忆")
            return ""
        except Exception as e:
            print(f"简单记忆匹配失败: {e}")
            return ""
    
    def chat_with_qwen(self, message: str, user_id: str) -> str:
        """使用通义千问进行对话"""
        try:
            # 获取相关记忆
            context = self.get_relevant_memories(message, user_id)
            print(f"[DEBUG] 获取到的context: '{context}'")

            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            }
            
            # 构建system content
            system_content = f"""你是一个专业的旅游助手，具有以下特点：
1. 能够记住用户的偏好和历史对话
2. 提供个性化的旅游建议和规划
3. 友好、专业、简洁，有帮助
4. 如果没找到相关记忆，请根据用户的问题，提供有用的旅游建议。不要编造记忆。
4. 回答字数不超过100字

{context}

请基于用户的历史信息和当前问题，提供有用的旅游建议。"""
            
            print(f"[DEBUG] 完整的system content: {system_content}")
            
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
     
            print(f"[DEBUG] 发送请求到: {self.base_url}")
            print(f"[DEBUG] API密钥: {self.api_key[:20]}...")
            print(f"[DEBUG] 请求数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            response = requests.post(self.base_url, headers=headers, json=data)
            
            print(f"[DEBUG] 响应状态码: {response.status_code}")
            print(f"[DEBUG] 响应头: {dict(response.headers)}")
            print(f"[DEBUG] 响应内容: {response.text}")
            
            if response.status_code == 400:
                error_data = response.json()
                print(f"[DEBUG] 错误数据: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
                if error_data.get("code") == "Arrearage":
                    return "抱歉，AI服务暂时不可用（账户余额不足）。不过我可以基于您的历史对话为您提供一些建议。请稍后再试或联系管理员。"
                else:
                    return f"抱歉，AI服务暂时不可用。错误信息：{error_data.get('message', '未知错误')}"
            
            response.raise_for_status()
            
            result = response.json()
            print(f"[DEBUG] 成功响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            if result.get("output") and result["output"].get("text"):
                answer = result["output"]["text"]
                print(f"[DEBUG] AI回答: {answer}")
                
                # 存储对话到记忆中
                self.store_conversation(message, answer, user_id)
                
                return answer
            elif result.get("output") and result["output"].get("choices"):
                answer = result["output"]["choices"][0]["message"]["content"]
                print(f"[DEBUG] AI回答: {answer}")
                
                # 存储对话到记忆中
                self.store_conversation(message, answer, user_id)
                
                return answer
            else:
                print(f"[DEBUG] 响应格式异常: {result}")
                return "抱歉，我现在无法回答您的问题，请稍后再试。"
                
        except Exception as e:
            print(f"[DEBUG] 调用通义千问API失败: {e}")
            import traceback
            print(f"[DEBUG] 完整错误信息: {traceback.format_exc()}")
            return "抱歉，服务暂时不可用，请稍后再试。"
    
    def store_conversation(self, user_message: str, ai_response: str, user_id: str):
        """存储对话到记忆中（使用 mem0）"""
        try:
            print(f"[DEBUG] 存储对话 - 用户ID: {user_id}")
            print(f"[DEBUG] 用户消息: {user_message}")
            print(f"[DEBUG] AI回复: {ai_response}")
            
            # 优先使用 QwenMem0Service 存储记忆
            if self.mem0_service is not None:
                try:
                    # 存储用户偏好信息（更智能的检测）
                    preference_keywords = ['喜欢', '偏好', '口味', '美食', '旅游', '地方', '推荐', '建议', '想要', '希望']
                    if any(keyword in user_message.lower() for keyword in preference_keywords):
                        print(f"[DEBUG] 检测到用户偏好关键词，准备存储: {user_message}")
                        result = self.mem0_service.add_memory(
                            content=f"用户偏好: {user_message}",
                            user_id=user_id,
                            memory_type="preference",
                            metadata={"category": "user_preference"}
                        )
                        print(f"[DEBUG] 存储用户偏好结果: {result}")
                        if result.get("success"):
                            print(f"[DEBUG] 使用 QwenMem0Service 存储用户偏好成功: {user_message}")
                        else:
                            print(f"[DEBUG] 使用 QwenMem0Service 存储用户偏好失败: {result}")
                    
                    # 存储用户问题
                    result = self.mem0_service.add_memory(
                        content=f"用户问题: {user_message}",
                        user_id=user_id,
                        memory_type="conversation",
                        metadata={"category": "question"}
                    )
                    
                    # 存储AI回复
                    result = self.mem0_service.add_memory(
                        content=f"AI回复: {ai_response}",
                        user_id=user_id,
                        memory_type="conversation",
                        metadata={"category": "answer"}
                    )
                    
                    print(f"[DEBUG] 使用 QwenMem0Service 存储对话成功")
                    
                except Exception as e:
                    print(f"[DEBUG] QwenMem0Service 存储失败: {e}")
                    # 回退到简单存储
                    self._store_simple(user_message, ai_response, user_id)
            else:
                # 回退到简单存储
                self._store_simple(user_message, ai_response, user_id)
                
        except Exception as e:
            print(f"存储对话记忆失败: {e}")
    
    def _store_simple(self, user_message: str, ai_response: str, user_id: str):
        """简单的内存存储（备用方法）"""
        try:
            if user_id not in self.user_memories:
                self.user_memories[user_id] = []
                print(f"[DEBUG] 为新用户 {user_id} 创建记忆列表")
            
            # 存储用户消息和AI回复
            self.user_memories[user_id].append(f"用户: {user_message}")
            self.user_memories[user_id].append(f"AI: {ai_response}")
            
            print(f"[DEBUG] 存储后的记忆: {self.user_memories[user_id]}")
            
            # 限制记忆数量，避免内存过大
            if len(self.user_memories[user_id]) > 20:
                self.user_memories[user_id] = self.user_memories[user_id][-20:]
                print(f"[DEBUG] 记忆数量超过20，已截取最近20条")
                
        except Exception as e:
            print(f"简单存储失败: {e}")
    
    def get_user_memories(self, user_id: str) -> List[Dict]:
        """获取用户的所有记忆（使用 QwenMem0Service）"""
        try:
            if self.mem0_service is not None:
                # 使用 QwenMem0Service 获取用户记忆
                memories = self.mem0_service.get_user_memories(user_id, limit=100)
                print(f"[DEBUG] QwenMem0Service 获取到 {len(memories)} 条记忆")
                return memories
            else:
                # 回退到简单存储
                memories = self.user_memories.get(user_id, [])
                return [{"memory": memory} for memory in memories]
        except Exception as e:
            print(f"获取用户记忆失败: {e}")
            # 回退到简单存储
            memories = self.user_memories.get(user_id, [])
            return [{"memory": memory} for memory in memories]
    
    def generate_memory_summary(self, user_id: str) -> str:
        """生成用户记忆摘要（使用 QwenMem0Service）"""
        try:
            if self.mem0_service is not None:
                # 使用 QwenMem0Service 生成记忆摘要
                summary = self.mem0_service.generate_memory_summary(user_id)
                print(f"[DEBUG] QwenMem0Service 生成记忆摘要: {summary}")
                return summary
            else:
                # 回退到简单摘要
                memories = self.user_memories.get(user_id, [])
                if memories:
                    return f"用户共有 {len(memories)} 条对话记录"
                else:
                    return "用户暂无对话记录"
        except Exception as e:
            print(f"生成记忆摘要失败: {e}")
            return "无法生成记忆摘要"
