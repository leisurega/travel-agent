# AI旅游聊天机器人集成说明

## 功能概述

在旅行页面集成了AI旅游聊天机器人，具有以下特性：

### 🤖 AI能力
- 使用**通义千问Plus**模型提供智能对话
- 基于**Mem0**实现记忆功能，能记住用户偏好和历史对话
- 专业的旅游领域知识和建议

### 🎯 主要功能
- **个性化推荐**：基于用户历史偏好推荐旅游目的地
- **智能规划**：协助制定详细的旅行计划
- **记忆功能**：记住用户的喜好、预算、旅行风格等
- **实时对话**：流畅的聊天体验，支持多轮对话

## 技术实现

### 后端架构
- **服务文件**：`backend/app/services/ai_chatbot.py`
- **API接口**：
  - `POST /chat/` - 发送消息给AI
  - `GET /chat/memories/` - 获取用户聊天记忆

### 前端组件
- **聊天组件**：`frontend/src/components/AI/Chatbot.tsx`
- **集成位置**：旅行列表页面 (`TripsPage.tsx`)

### 依赖项
```txt
# 后端依赖
mem0ai==0.0.11        # 记忆管理
dashscope==1.14.0     # 通义千问API
qdrant-client==1.7.0  # 向量数据库
```

## 使用方式

### 1. 启动聊天机器人
- 在旅行页面点击 **"AI旅游助手"** 按钮
- 或点击右下角的聊天图标

### 2. 对话功能
- 输入旅游相关问题
- AI会基于历史对话提供个性化建议
- 支持最小化/最大化窗口

### 3. 记忆功能
- 自动记住用户的旅行偏好
- 保存历史对话内容
- 基于记忆提供更精准的建议

## 配置说明

### 环境变量
```bash
# 通义千问API密钥
DASHSCOPE_API_KEY=your_api_key_here
```

### Qdrant配置
```python
config = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "host": "localhost",
            "port": 6333,
        }
    },
}
```

## API接口详情

### POST /chat/
发送消息给AI聊天机器人

**请求体：**
```json
{
  "message": "我想去北京旅游，有什么推荐吗？"
}
```

**响应：**
```json
{
  "message": "对话成功",
  "data": {
    "user_message": "我想去北京旅游，有什么推荐吗？",
    "ai_response": "北京是一个历史悠久的城市...",
    "timestamp": "2024-01-01T12:00:00.000Z"
  }
}
```

### GET /chat/memories/
获取用户的聊天记忆

**响应：**
```json
{
  "message": "获取记忆成功",
  "data": [
    {
      "memory": "用户喜欢历史文化类景点",
      "metadata": {"role": "user"}
    }
  ]
}
```

## 前端组件使用

```tsx
import { Chatbot } from 'components/AI';

// 在组件中使用
<Chatbot 
  isOpen={isChatbotOpen} 
  onToggle={() => setIsChatbotOpen(!isChatbotOpen)} 
/>
```

## 注意事项

1. **API密钥**：确保配置了有效的DASHSCOPE_API_KEY
2. **Qdrant服务**：需要启动Qdrant向量数据库服务
3. **网络连接**：需要能访问通义千问API服务
4. **用户认证**：聊天功能需要用户登录状态

## 扩展功能

可以进一步扩展的功能：
- 支持语音输入/输出
- 集成地图显示推荐位置
- 支持图片识别和推荐
- 多语言支持
- 群组聊天功能
