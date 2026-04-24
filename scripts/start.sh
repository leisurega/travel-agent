#!/bin/bash

echo "🚀 启动 Travel Agent 项目..."

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker 未运行，请先启动 Docker"
    exit 1
fi

# 启动数据库服务
echo "📦 启动数据库服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose ps

# 生成JWT密钥（如果不存在）
if [ ! -f "backend/.env" ]; then
    echo "🔑 生成JWT密钥..."
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    
    # 复制环境变量文件
    cp backend/env.example backend/.env
    
    # 更新密钥
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/your_secret_key_here/$SECRET_KEY/" backend/.env
    else
        # Linux
        sed -i "s/your_secret_key_here/$SECRET_KEY/" backend/.env
    fi
    
    echo "✅ JWT密钥已生成并保存到 backend/.env"
fi

# 安装Python依赖
echo "📦 安装Python依赖..."
cd backend
pip install -r requirements.txt

# 初始化数据库
echo "🗄️ 初始化数据库..."
python3 ../scripts/init_db.py

# 启动后端服务
echo "🚀 启动后端服务..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
