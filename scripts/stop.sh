#!/bin/bash

echo "🛑 停止 Travel Agent 项目..."

# 停止后端服务（如果运行中）
echo "🛑 停止后端服务..."
pkill -f "uvicorn app.main:app" || true

# 停止数据库服务
echo "🛑 停止数据库服务..."
docker-compose down

echo "✅ 所有服务已停止"
