#!/usr/bin/env python3
"""
测试旅行计划数据显示
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_trip_plan_display():
    """测试旅行计划数据显示"""
    
    print("🧪 测试旅行计划数据显示...")
    
    # 测试数据
    trip_id = 2
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiZXhwIjoxNzU5NTM5NzYyfQ.9TvbZwKDWZeFpd801NEyHzslCRsG8Xlyh4fE2kRsNVE"
    headers = {"Authorization": f"Bearer {token}"}
    
    # 获取旅行详情
    print(f"\n1️⃣ 获取旅行 {trip_id} 详情...")
    try:
        response = requests.get(f"{BASE_URL}/trips/{trip_id}", headers=headers)
        if response.status_code == 200:
            trip_data = response.json()["data"]
            print(f"✅ 旅行详情获取成功")
            print(f"   标题: {trip_data['title']}")
            print(f"   目的地: {trip_data['destination']}")
            print(f"   天数: {trip_data['days']}")
            
            # 检查计划数据
            if 'plans' in trip_data and trip_data['plans']:
                print(f"   计划数量: {len(trip_data['plans'])}")
                for i, plan in enumerate(trip_data['plans']):
                    print(f"   第{plan['day']}天: {plan['plan_data']['activities'][0]['activity']}")
            else:
                print(f"   ⚠️  没有找到计划数据")
                
            if 'itinerary' in trip_data:
                print(f"   AI行程: {'有' if trip_data['itinerary'] else '无'}")
        else:
            print(f"❌ 获取旅行详情失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 获取旅行详情异常: {e}")
    
    print("\n📝 前端访问地址:")
    print(f"   http://localhost:3000/trips/{trip_id}")
    print(f"   请检查旅行计划标签页是否显示计划内容")

if __name__ == "__main__":
    test_trip_plan_display()

