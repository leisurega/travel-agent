# Qwen mem0记忆功能使用指南

## 概述

本项目实现了一个基于Qwen模型的mem0记忆功能，为旅游AI助手提供智能记忆存储、检索和管理能力。系统能够记住用户的偏好、历史对话和重要信息，从而提供个性化的旅游建议。

## 功能特性

### 🧠 核心功能
- **智能记忆存储**: 自动存储用户对话和偏好信息
- **语义搜索**: 基于Qwen模型进行智能记忆检索
- **个性化推荐**: 基于历史信息提供个性化旅游建议
- **记忆管理**: 支持记忆的增删改查、导出导入
- **用户档案**: 自动生成用户偏好档案

### 🔧 技术特性
- **Qwen模型集成**: 使用通义千问作为LLM和嵌入模型
- **mem0框架**: 基于mem0ai框架实现记忆功能
- **RESTful API**: 提供完整的REST API接口
- **类型化支持**: 支持不同类型的记忆分类
- **容错机制**: 具备完善的错误处理和回退机制

## 安装和配置

### 1. 环境要求
- Python 3.8+
- 通义千问API密钥

### 2. 安装依赖
```bash
cd backend
pip install -r requirements.txt
```

### 3. 环境配置
创建`.env`文件并配置：
```env
DASHSCOPE_API_KEY=your_dashscope_api_key
```

### 4. 初始化服务
```python
from app.services.qwen_mem0_service import create_qwen_mem0_service

# 创建记忆服务
memory_service = create_qwen_mem0_service()
```

## 使用方法

### 1. 基础记忆操作

#### 添加记忆
```python
# 添加用户偏好
result = memory_service.add_memory(
    content="用户喜欢清淡口味的食物",
    user_id="user_001",
    memory_type="preference",
    metadata={"category": "food", "preference": "light"}
)

# 添加对话记录
result = memory_service.add_memory(
    content="用户询问了关于京都的旅游景点",
    user_id="user_001",
    memory_type="conversation",
    metadata={"topic": "travel", "location": "Kyoto"}
)
```

#### 搜索记忆
```python
# 搜索相关记忆
results = memory_service.search_memories(
    query="日本旅游",
    user_id="user_001",
    limit=5
)

for result in results:
    print(f"内容: {result['content']}")
    print(f"相似度: {result['similarity']:.4f}")
```

#### 获取用户记忆
```python
# 获取用户所有记忆
memories = memory_service.get_user_memories(
    user_id="user_001",
    limit=50
)

# 按类型过滤
preferences = memory_service.get_user_memories(
    user_id="user_001",
    memory_type="preference"
)
```

### 2. 记忆管理

#### 更新记忆
```python
result = memory_service.update_memory(
    memory_id="memory_id_123",
    content="更新后的记忆内容",
    user_id="user_001",
    metadata={"updated": True}
)
```

#### 删除记忆
```python
result = memory_service.delete_memory(
    memory_id="memory_id_123",
    user_id="user_001"
)
```

#### 清空记忆
```python
# 清空所有记忆
result = memory_service.clear_user_memories("user_001")

# 清空特定类型记忆
result = memory_service.clear_user_memories(
    user_id="user_001",
    memory_type="conversation"
)
```

### 3. 高级功能

#### 生成记忆摘要
```python
summary = memory_service.generate_memory_summary("user_001")
print(summary)
```

#### 获取记忆统计
```python
stats = memory_service.get_memory_stats("user_001")
print(f"总记忆数: {stats['total_memories']}")
print(f"记忆类型: {stats['memory_types']}")
```

#### 导出导入记忆
```python
# 导出记忆
export_result = memory_service.export_memories(
    user_id="user_001",
    file_path="./user_memories.json"
)

# 导入记忆
import_result = memory_service.import_memories(
    file_path="./user_memories.json",
    user_id="user_002"
)
```

### 4. 增强版聊天机器人

#### 基础对话
```python
from app.services.enhanced_chatbot import create_enhanced_chatbot

# 创建聊天机器人
chatbot = create_enhanced_chatbot(memory_service)

# 进行对话
response = chatbot.chat("我想去日本旅游，有什么推荐吗？", "user_001")
print(response)
```

#### 获取用户档案
```python
profile = chatbot.get_user_profile("user_001")
print(f"用户偏好: {profile['preferences']}")
print(f"最近对话: {profile['recent_conversations']}")
```

#### 生成个性化推荐
```python
recommendation = chatbot.generate_travel_recommendation(
    user_id="user_001",
    destination="京都"
)
print(recommendation)
```

## API接口

### 记忆管理API

#### 添加记忆
```http
POST /api/memory/add
Content-Type: application/json

{
    "content": "用户喜欢清淡口味的食物",
    "user_id": "user_001",
    "memory_type": "preference",
    "metadata": {"category": "food"}
}
```

#### 搜索记忆
```http
POST /api/memory/search
Content-Type: application/json

{
    "query": "日本旅游",
    "user_id": "user_001",
    "limit": 5
}
```

#### 获取用户记忆
```http
GET /api/memory/user/{user_id}?limit=50&memory_type=preference
```

#### 获取记忆摘要
```http
GET /api/memory/summary/{user_id}
```

#### 获取记忆统计
```http
GET /api/memory/stats/{user_id}
```

#### 清空记忆
```http
POST /api/memory/clear
Content-Type: application/json

{
    "user_id": "user_001",
    "memory_type": "conversation"
}
```

#### 导出记忆
```http
POST /api/memory/export
Content-Type: application/json

{
    "user_id": "user_001",
    "file_path": "./export.json"
}
```

#### 导入记忆
```http
POST /api/memory/import
Content-Type: application/json

{
    "file_path": "./import.json",
    "user_id": "user_002"
}
```

## 测试

### 运行测试套件
```bash
cd backend
python test_mem0_functionality.py
```

测试套件包含以下测试：
- 记忆添加测试
- 记忆搜索测试
- 记忆管理测试
- 聊天机器人集成测试
- 记忆导出导入测试
- 记忆清理测试

### 测试结果
测试完成后会生成详细的测试报告，包括：
- 测试通过率
- 详细测试结果
- 性能指标
- 错误日志

## 配置选项

### 记忆服务配置
```python
config = {
    "llm": {
        "provider": "openai",
        "config": {
            "api_key": "your_api_key",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "model": "qwen-plus",
            "temperature": 0.7,
            "max_tokens": 2000
        }
    },
    "embedder": {
        "provider": "openai",
        "config": {
            "api_key": "your_api_key",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "model": "text-embedding-v2"
        }
    },
    "storage": {
        "provider": "local",
        "config": {
            "file_path": "./memories.json"
        }
    }
}

memory_service = QwenMem0Service(config)
```

### 支持的存储后端
- **local**: 本地文件存储（默认）
- **qdrant**: Qdrant向量数据库
- **chroma**: ChromaDB向量数据库
- **redis**: Redis存储

## 最佳实践

### 1. 记忆类型分类
- `conversation`: 对话记录
- `preference`: 用户偏好
- `plan`: 旅游计划
- `fact`: 事实信息
- `feedback`: 用户反馈

### 2. 元数据设计
```python
metadata = {
    "category": "food",           # 分类
    "preference": "light",        # 偏好值
    "timestamp": "2024-01-01",   # 时间戳
    "confidence": 0.9,           # 置信度
    "source": "user_input"       # 来源
}
```

### 3. 搜索优化
- 使用具体的查询词
- 合理设置limit参数
- 利用memory_type过滤
- 定期清理过期记忆

### 4. 性能优化
- 批量操作记忆
- 使用异步API
- 定期导出备份
- 监控存储使用量

## 故障排除

### 常见问题

#### 1. API密钥错误
```
错误: DASHSCOPE_API_KEY 环境变量未设置
解决: 检查.env文件中的API密钥配置
```

#### 2. 记忆服务初始化失败
```
错误: mem0初始化失败
解决: 检查依赖安装和网络连接
```

#### 3. 搜索无结果
```
错误: 搜索未找到相关记忆
解决: 检查用户ID和查询词，尝试更宽泛的搜索
```

#### 4. 存储空间不足
```
错误: 存储空间不足
解决: 清理过期记忆或增加存储空间
```

### 调试模式
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 启用详细日志
memory_service = create_qwen_mem0_service()
```

## 扩展开发

### 自定义记忆类型
```python
class CustomMemoryService(QwenMem0Service):
    def add_custom_memory(self, data, user_id):
        # 自定义记忆处理逻辑
        pass
```

### 集成其他LLM
```python
config = {
    "llm": {
        "provider": "openai",
        "config": {
            "api_key": "your_key",
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-4"
        }
    }
}
```

### 添加新的存储后端
```python
config = {
    "storage": {
        "provider": "custom",
        "config": {
            "connection_string": "your_connection"
        }
    }
}
```

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 贡献

欢迎提交Issue和Pull Request来改进项目。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交GitHub Issue
- 发送邮件至项目维护者

---

**注意**: 使用前请确保已正确配置通义千问API密钥，并遵守相关使用条款。
