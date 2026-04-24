# Travel Agent 旅游微信小程序

基于AI的智能旅游规划和管理应用，支持多人协作、智能记账分摊、时光记录和AI问答助手。

## 功能特性

- 🚀 AI智能旅行规划
- 👥 多人协作编辑
- 💰 智能记账分摊
- 📝 时光记录
- 🤖 AI问答助手
- 📊 数据仪表盘
- 🔍 RAG知识检索

## 技术栈

### 后端
- **框架**: FastAPI
- **数据库**: PostgreSQL + Qdrant
- **AI模型**: Qwen (通义千问)
- **缓存**: Redis
- **部署**: Docker

### 前端
- **框架**: 微信小程序
- **样式**: WXSS
- **状态管理**: 页面级状态

## 快速开始

### 方式1：使用启动脚本（推荐）
```bash
# 启动所有服务
./scripts/start.sh

# 停止所有服务
./scripts/stop.sh
```

### 方式2：手动启动
```bash
# 1. 启动数据库服务
docker-compose up -d

# 2. 生成JWT密钥
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 3. 配置环境变量
cp backend/env.example backend/.env
# 编辑 backend/.env 文件，填入你的配置

# 4. 安装依赖并启动
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 数据库配置
1. 使用Docker Compose启动PostgreSQL、Redis、Qdrant
2. 自动生成JWT密钥
3. 自动初始化数据库表

### 环境变量
创建 `.env` 文件：
```env
DATABASE_URL=postgresql://user:password@localhost/travel_agent
REDIS_URL=redis://localhost:6379
QDRANT_HOST=localhost
QDRANT_PORT=6333
DASHSCOPE_API_KEY=your_api_key
SECRET_KEY=your_secret_key
```

## API文档

启动后端服务后访问：http://localhost:8000/docs

## 部署

使用Docker部署：
```bash
docker build -t travel-agent .
docker run -p 8000:8000 travel-agent
```

## 项目结构

```
travel-agent/
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── models/         # 数据模型
│   │   ├── services/       # 业务服务
│   │   ├── api/            # API接口
│   │   └── utils/          # 工具函数
│   ├── requirements.txt    # Python依赖
│   └── Dockerfile         # Docker配置
├── frontend/               # 前端代码
│   ├── pages/             # 页面文件
│   ├── components/        # 组件
│   ├── utils/             # 工具函数
│   └── app.wxss           # 全局样式
└── README.md              # 项目说明
```

## 核心功能说明

### 1. **AI旅行规划**
- 使用Qwen大模型生成个性化旅行计划
- 考虑用户偏好、目的地、天数等因素
- 自动优化行程安排

### 2. **多人协作**
- 实时同步旅行计划更新
- 多人同时编辑记账分摊
- WebSocket实时通信

### 3. **智能记账分摊**
- 支持多种分摊方式（平均、按比例、自定义）
- 自动计算每人应付金额
- 实时同步分摊状态

### 4. **时光记录**
- 记录每个地点的经历和感受
- 支持照片上传和位置标记
- 集成天气信息

### 5. **AI问答助手**
- 基于RAG的知识检索
- 旅行相关问题智能回答
- 上下文感知对话

### 6. **数据仪表盘**
- 个人关注点分析
- 活跃用户统计
- 消费分析和预算管理

### 7. **用户隔离**
- 个人数据隐私保护
- 共享数据权限控制
- 基于角色的访问控制
