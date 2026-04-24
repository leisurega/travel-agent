from dashscope import Generation
from typing import List, Dict, Any
import json
from ..config import settings

class AIService:
    def __init__(self):
        # DashScope SDK 会读取环境变量 DASHSCOPE_API_KEY
        # 这里不再调用不存在的 set_api_key，避免启动时崩溃
        self.api_key = settings.DASHSCOPE_API_KEY
    
    async def generate_trip_plan(self, destination: str, days: int, preferences: List[str]) -> Dict[str, Any]:
        """生成旅行计划"""
        prompt = f"""
        请为{destination}的{days}天旅行生成详细计划。
        用户偏好：{', '.join(preferences)}
        
        请按以下格式返回JSON：
        {{
            "daily_plans": [
                {{
                    "day": 1,
                    "morning": "上午活动",
                    "afternoon": "下午活动", 
                    "evening": "晚上活动",
                    "accommodation": "住宿建议",
                    "transportation": "交通建议",
                    "estimated_cost": "预估费用"
                }}
            ],
            "total_estimated_cost": "总预估费用",
            "tips": "旅行小贴士"
        }}
        """
        
        try:
            response = Generation.call(
                model='qwen-max',
                prompt=prompt,
                max_tokens=2000,
                temperature=0.7
            )
            return json.loads(response.output.text)
        except Exception:
            # 返回一个合理的占位结果，保证接口可用
            return {
                "daily_plans": [
                    {
                        "day": 1,
                        "morning": "待生成",
                        "afternoon": "待生成",
                        "evening": "待生成",
                        "accommodation": "待生成",
                        "transportation": "待生成",
                        "estimated_cost": "待估算"
                    }
                ],
                "total_estimated_cost": "待估算",
                "tips": "AI服务暂不可用，已返回占位结果"
            }
    
    async def answer_question(self, question: str, context: str = "") -> str:
        """AI问答助手"""
        prompt = f"""
        上下文：{context}
        
        问题：{question}
        
        请提供详细、准确的回答。
        """
        
        try:
            response = Generation.call(
                model='qwen-max',
                prompt=prompt,
                max_tokens=1000,
                temperature=0.5
            )
            return response.output.text
        except Exception:
            return "AI服务暂不可用，请稍后再试。"
    
    async def analyze_memories(self, memories: List[Dict]) -> Dict[str, Any]:
        """分析时光记录，生成洞察"""
        prompt = f"""
        请分析以下旅行记录，生成洞察报告：
        
        {json.dumps(memories, ensure_ascii=False)}
        
        请按以下格式返回JSON：
        {{
            "mood_analysis": "心情分析",
            "highlight_places": "重点地点",
            "recommendations": "建议",
            "statistics": {{
                "total_memories": "总记录数",
                "most_active_user": "最活跃用户",
                "favorite_locations": "最受欢迎地点"
            }}
        }}
        """
        
        try:
            response = Generation.call(
                model='qwen-max',
                prompt=prompt,
                max_tokens=1500,
                temperature=0.3
            )
            return json.loads(response.output.text)
        except Exception:
            return {
                "mood_analysis": "暂不可用",
                "highlight_places": [],
                "recommendations": [],
                "statistics": {
                    "total_memories": 0,
                    "most_active_user": "",
                    "favorite_locations": []
                }
            }
