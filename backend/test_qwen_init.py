"""
测试Qwen mem0服务初始化
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
load_dotenv(override=True)

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_qwen_mem0_init():
    """测试Qwen mem0服务初始化"""
    print("🧠 测试Qwen mem0服务初始化")
    print("=" * 50)
    
    # 检查环境变量
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("❌ 错误: 未设置DASHSCOPE_API_KEY环境变量")
        print("请在.env文件中设置: DASHSCOPE_API_KEY=your_api_key")
        return False
    
    print(f"✅ API密钥已设置: {api_key[:10]}...")
    
    try:
        # 测试1: 导入服务
        print("\n1. 测试导入QwenMem0Service...")
        from app.services.qwen_mem0_service import QwenMem0Service, create_qwen_mem0_service
        print("✅ 服务导入成功")
        
        # 测试2: 创建服务实例
        print("\n2. 测试创建服务实例...")
        service = create_qwen_mem0_service()
        print("✅ 服务实例创建成功")
        
        # 测试3: 检查服务属性
        print("\n3. 检查服务属性...")
        print(f"   - API密钥: {service.api_key[:10]}...")
        print(f"   - 配置: {type(service.config)}")
        print(f"   - 记忆实例: {type(service.memory)}")
        print("✅ 服务属性检查通过")
        
        # 测试4: 基本功能测试
        print("\n4. 测试基本功能...")
        test_user_id = "init_test_user"
        
        # 添加测试记忆
        print("   4.1 测试添加记忆...")
        result = service.add_memory(
            content="这是一个初始化测试记忆",
            user_id=test_user_id,
            memory_type="test",
            metadata={"test": True, "timestamp": datetime.now().isoformat()}
        )
        
        if result.get("success"):
            print("   ✅ 添加记忆成功")
            memory_id = result.get("memory_id")
            print(f"   📝 记忆ID: {memory_id}")
        else:
            print(f"   ❌ 添加记忆失败: {result.get('error')}")
            return False
        
        # 搜索测试记忆
        print("   4.2 测试搜索记忆...")
        search_results = service.search_memories(
            query="初始化测试",
            user_id=test_user_id,
            limit=1
        )
        
        if search_results:
            print(f"   ✅ 搜索成功，找到 {len(search_results)} 条记忆")
            for i, result in enumerate(search_results, 1):
                print(f"      {i}. {result.get('content', '')}")
                print(f"         相似度: {result.get('similarity', 0):.4f}")
        else:
            print("   ❌ 搜索失败，未找到记忆")
            return False
        
        # 获取用户记忆
        print("   4.3 测试获取用户记忆...")
        user_memories = service.get_user_memories(test_user_id, limit=10)
        print(f"   ✅ 获取成功，共 {len(user_memories)} 条记忆")
        
        # 获取记忆统计
        print("   4.4 测试获取记忆统计...")
        stats = service.get_memory_stats(test_user_id)
        print(f"   ✅ 统计成功: {stats.get('total_memories', 0)} 条记忆")
        print(f"   📊 记忆类型: {stats.get('memory_types', {})}")
        
        # 生成记忆摘要
        print("   4.5 测试生成记忆摘要...")
        summary = service.generate_memory_summary(test_user_id)
        print("   ✅ 摘要生成成功")
        print(f"   📋 摘要: {summary[:100]}...")
        
        # 清理测试数据
        print("\n5. 清理测试数据...")
        clear_result = service.clear_user_memories(test_user_id)
        if clear_result.get("success"):
            print(f"   ✅ 清理成功，删除了 {clear_result.get('deleted_count', 0)} 条记忆")
        else:
            print(f"   ⚠️  清理失败: {clear_result.get('error')}")
        
        print("\n🎉 Qwen mem0服务初始化测试全部通过！")
        return True
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保已安装所有依赖: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ 初始化测试失败: {e}")
        import traceback
        print(f"详细错误信息:")
        print(traceback.format_exc())
        return False

def test_configuration_options():
    """测试不同配置选项"""
    print("\n🔧 测试配置选项")
    print("=" * 50)
    
    try:
        from app.services.qwen_mem0_service import QwenMem0Service
        
        # 测试自定义配置
        print("1. 测试自定义配置...")
        custom_config = {
            "llm": {
                "provider": "openai",
                "config": {
                    "api_key": os.getenv("DASHSCOPE_API_KEY"),
                    "model": "gpt-3.5-turbo",
                    "temperature": 0.5
                }
            },
            "storage": {
                "provider": "local",
                "config": {
                    "file_path": "./custom_test_storage.json"
                }
            }
        }
        
        service = QwenMem0Service(custom_config)
        print("✅ 自定义配置成功")
        
        # 测试服务功能
        test_user = "config_test_user"
        result = service.add_memory(
            content="自定义配置测试",
            user_id=test_user,
            memory_type="config_test"
        )
        
        if result.get("success"):
            print("✅ 自定义配置功能正常")
            # 清理
            service.clear_user_memories(test_user)
        else:
            print(f"❌ 自定义配置功能异常: {result.get('error')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 Qwen mem0服务初始化测试")
    print("=" * 60)
    
    tests = [
        ("服务初始化", test_qwen_mem0_init),
        ("配置选项", test_configuration_options)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 运行测试: {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    print(f"\n📊 测试结果:")
    print(f"通过: {passed}/{total}")
    print(f"成功率: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 所有测试通过！Qwen mem0服务初始化成功")
        print("\n💡 服务已准备就绪，可以开始使用:")
        print("   - 添加记忆: service.add_memory()")
        print("   - 搜索记忆: service.search_memories()")
        print("   - 获取统计: service.get_memory_stats()")
        print("   - 生成摘要: service.generate_memory_summary()")
    else:
        print("\n⚠️  部分测试失败，请检查配置和依赖")

if __name__ == "__main__":
    main()
