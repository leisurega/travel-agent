#!/bin/bash

echo "🔍 检查记账分摊功能状态..."

echo ""
echo "📊 后端状态检查:"
echo "=================="

# 检查后端是否运行
if curl --noproxy localhost -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "✅ 后端服务运行正常 (http://localhost:8000)"
else
    echo "❌ 后端服务未运行"
    exit 1
fi

# 检查记账API
if curl --noproxy localhost -s -X GET http://localhost:8000/trips/2/expenses/summary/ -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiZXhwIjoxNzU5NTM5NzYyfQ.9TvbZwKDWZeFpd801NEyHzslCRsG8Xlyh4fE2kRsNVE" > /dev/null 2>&1; then
    echo "✅ 记账API响应正常"
else
    echo "❌ 记账API无响应"
fi

echo ""
echo "📊 前端状态检查:"
echo "=================="

# 检查前端是否运行
if curl --noproxy localhost -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ 前端服务运行正常 (http://localhost:3000)"
else
    echo "❌ 前端服务未运行"
    exit 1
fi

echo ""
echo "📊 功能测试:"
echo "============="

# 获取当前支出汇总
SUMMARY=$(curl --noproxy localhost -s -X GET http://localhost:8000/trips/2/expenses/summary/ -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiZXhwIjoxNzU5NTM5NzYyfQ.9TvbZwKDWZeFpd801NEyHzslCRsG8Xlyh4fE2kRsNVE")

if [ $? -eq 0 ]; then
    TOTAL_EXPENSES=$(echo $SUMMARY | grep -o '"total_expenses":[0-9.]*' | cut -d':' -f2)
    echo "✅ 当前总支出: ¥$TOTAL_EXPENSES"
    
    SETTLEMENTS=$(echo $SUMMARY | grep -o '"settlements":\[[^]]*\]')
    if [ ! -z "$SETTLEMENTS" ]; then
        echo "✅ 结算方案已生成"
    else
        echo "ℹ️  暂无结算方案"
    fi
else
    echo "❌ 无法获取支出汇总"
fi

echo ""
echo "🎉 记账分摊功能状态检查完成!"
echo ""
echo "📝 访问地址:"
echo "   前端: http://localhost:3000"
echo "   记账页面: http://localhost:3000/trips/2/expenses"
echo "   后端API: http://localhost:8000"

