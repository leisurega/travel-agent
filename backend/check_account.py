import os
import requests
import json

def check_account_status():
    api_key = os.getenv("DASHSCOPE_API_KEY", "sk-d0d268abb7874f8f934782ccdb40ccfd")
    
    # 尝试获取账户信息或可用模型列表
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    
    # 测试不同的API端点
    endpoints = [
        "https://dashscope.aliyuncs.com/api/v1/models",
        "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
        "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    ]
    
    for i, endpoint in enumerate(endpoints, 1):
        print(f"\n=== 测试端点 {i} ===")
        print(f"URL: {endpoint}")
        
        try:
            if "models" in endpoint:
                response = requests.get(endpoint, headers=headers)
            else:
                data = {
                    "model": "qwen-turbo",  # 尝试使用更便宜的模型
                    "input": {
                        "messages": [
                            {"role": "user", "content": "你好"}
                        ]
                    },
                    "parameters": {"max_tokens": 50}
                }
                response = requests.post(endpoint, headers=headers, json=data)
            
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.text[:200]}...")
            
        except Exception as e:
            print(f"异常: {e}")

if __name__ == "__main__":
    check_account_status()
