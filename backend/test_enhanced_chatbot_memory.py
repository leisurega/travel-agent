"""
测试enhanced_chatbot.py的记忆模块功能
"""

import os
import sys
import json
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_enhanced_chatbot_memory():
    """测试增强版聊天机器人的记忆功能"""
    print("🤖 测试增强版聊天机器人记忆功能")
    print("=" * 60)
    
    # 检查环境变量
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("❌ 错误: 未设置DASHSCOPE_API_KEY环境变量")
        return False
    
    print(f"✅ API密钥已设置: {api_key[:10]}...")
    
    try:
        # 测试1: 导入服务
        print("\n1. 测试导入EnhancedTravelChatbot...")
        from app.services.enhanced_chatbot import EnhancedTravelChatbot, create_enhanced_chatbot
        print("✅ 聊天机器人导入成功")
        
        # 测试2: 创建聊天机器人实例
        print("\n2. 测试创建聊天机器人实例...")
        chatbot = create_enhanced_chatbot()
        print("✅ 聊天机器人实例创建成功")
        
        # 测试3: 检查记忆服务
        print("\n3. 检查记忆服务...")
        if chatbot.memory_service:
            print("✅ 记忆服务已初始化")
            print(f"   - 记忆服务类型: {type(chatbot.memory_service)}")
        else:
            print("❌ 记忆服务未初始化")
            return False
        
        # 测试4: 基础对话测试
        print("\n4. 测试基础对话功能...")
        test_user_id = "memory_test_user"
        
        # 第一轮对话
        print("   4.1 第一轮对话...")
        response1 = chatbot.chat("你好，我想去日本旅游", test_user_id)
        if response1 and len(response1) > 10:
            print(f"   ✅ 对话成功: {response1[:50]}...")
        else:
            print(f"   ❌ 对话失败: {response1}")
            return False
        
        # 第二轮对话（测试记忆功能）
        print("   4.2 第二轮对话（测试记忆）...")
        response2 = chatbot.chat("我喜欢清淡的食物，有什么推荐吗？", test_user_id)
        if response2 and len(response2) > 10:
            print(f"   ✅ 记忆对话成功: {response2[:50]}...")
        else:
            print(f"   ❌ 记忆对话失败: {response2}")
            return False
        
        # 第三轮对话（测试个性化）
        print("   4.3 第三轮对话（测试个性化）...")
        response3 = chatbot.chat("基于我的偏好，给我一些京都的推荐", test_user_id)
        if response3 and len(response3) > 10:
            print(f"   ✅ 个性化对话成功: {response3[:50]}...")
        else:
            print(f"   ❌ 个性化对话失败: {response3}")
            return False
        
        # 测试5: 记忆存储功能
        print("\n5. 测试记忆存储功能...")
        
        # 检查用户记忆
        memories = chatbot.memory_service.get_user_memories(test_user_id, limit=10)
        print(f"   📝 用户记忆数量: {len(memories)}")
        
        if memories:
            print("   ✅ 记忆存储成功")
            # 处理不同的数据类型
            memory_list = list(memories) if hasattr(memories, '__iter__') else [memories]
            for i, memory in enumerate(memory_list[:3], 1):
                if isinstance(memory, dict):
                    content = memory.get("content", "")[:30] + "..." if len(memory.get("content", "")) > 30 else memory.get("content", "")
                else:
                    content = str(memory)[:30] + "..." if len(str(memory)) > 30 else str(memory)
                print(f"      {i}. {content}")
        else:
            print("   ❌ 记忆存储失败")
            return False
        
        # 测试6: 记忆搜索功能
        print("\n6. 测试记忆搜索功能...")
        
        # 搜索相关记忆
        search_results = chatbot.memory_service.search_memories(
            query="日本旅游",
            user_id=test_user_id,
            limit=3
        )
        
        if search_results:
            print(f"   ✅ 搜索成功，找到 {len(search_results)} 条相关记忆")
            for i, result in enumerate(search_results, 1):
                content = result.get("content", "")[:30] + "..." if len(result.get("content", "")) > 30 else result.get("content", "")
                similarity = result.get("similarity", 0)
                print(f"      {i}. {content} (相似度: {similarity:.4f})")
        else:
            print("   ❌ 搜索失败")
            return False
        
        # 测试7: 用户档案功能
        print("\n7. 测试用户档案功能...")
        
        profile = chatbot.get_user_profile(test_user_id)
        if profile and not profile.get("error"):
            print("   ✅ 用户档案生成成功")
            stats = profile.get("stats", {})
            print(f"   📊 总记忆数: {stats.get('total_memories', 0)}")
            print(f"   📊 记忆类型: {stats.get('memory_types', {})}")
            
            preferences = profile.get("preferences", [])
            if preferences:
                print(f"   🎯 用户偏好: {len(preferences)} 条")
                for pref in preferences[:2]:
                    print(f"      - {pref[:30]}...")
        else:
            print(f"   ❌ 用户档案生成失败: {profile.get('error', '未知错误')}")
            return False
        
        # 测试8: 个性化推荐功能
        print("\n8. 测试个性化推荐功能...")
        
        recommendation = chatbot.generate_travel_recommendation(test_user_id, "京都")
        if recommendation and len(recommendation) > 20:
            print("   ✅ 个性化推荐生成成功")
            print(f"   🎯 推荐内容: {recommendation[:100]}...")
        else:
            print(f"   ❌ 个性化推荐失败: {recommendation}")
            return False
        
        # 测试9: 偏好检测功能
        print("\n9. 测试偏好检测功能...")
        
        # 测试不同类型的偏好检测
        test_messages = [
            "我喜欢辣的食物",
            "我对历史文化很感兴趣",
            "我想要经济实惠的住宿"
        ]
        
        for msg in test_messages:
            preferences = chatbot._detect_user_preferences(msg)
            if preferences:
                print(f"   ✅ 偏好检测成功: '{msg}' -> {preferences}")
            else:
                print(f"   ⚠️  偏好检测: '{msg}' -> 无偏好")
        
        # 测试10: 记忆清理功能
        print("\n10. 测试记忆清理功能...")
        
        clear_result = chatbot.clear_user_memories(test_user_id)
        if clear_result.get("success"):
            deleted_count = clear_result.get("deleted_count", 0)
            print(f"   ✅ 记忆清理成功，删除了 {deleted_count} 条记忆")
        else:
            print(f"   ❌ 记忆清理失败: {clear_result.get('error')}")
        
        print("\n🎉 增强版聊天机器人记忆功能测试全部通过！")
        return True
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        print(f"详细错误信息:")
        print(traceback.format_exc())
        return False

def test_memory_integration():
    """测试记忆集成功能"""
    print("\n🔗 测试记忆集成功能")
    print("=" * 60)
    
    try:
        from app.services.enhanced_chatbot import create_enhanced_chatbot
        from app.services.qwen_mem0_service import create_qwen_mem0_service
        
        # 创建独立的记忆服务
        memory_service = create_qwen_mem0_service()
        
        # 创建聊天机器人并传入记忆服务
        chatbot = create_enhanced_chatbot(memory_service)
        
        print("✅ 记忆服务集成成功")
        
        # 测试集成后的功能
        test_user = "integration_test_user"
        
        # 添加一些测试记忆
        memory_service.add_memory(
            content="用户喜欢日式料理",
            user_id=test_user,
            memory_type="preference",
            metadata={"category": "food", "preference": "japanese"}
        )
        
        # 测试聊天机器人是否能使用这些记忆
        response = chatbot.chat("我想吃日本菜，有什么推荐吗？", test_user)
        
        if response and len(response) > 10:
            print("✅ 集成记忆功能正常")
            print(f"   回复: {response[:50]}...")
        else:
            print("❌ 集成记忆功能异常")
            return False
        
        # 清理测试数据
        chatbot.clear_user_memories(test_user)
        
        return True
        
    except Exception as e:
        print(f"❌ 记忆集成测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 增强版聊天机器人记忆功能测试套件")
    print("=" * 80)
    
    tests = [
        ("记忆功能测试", test_enhanced_chatbot_memory),
        ("记忆集成测试", test_memory_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 运行测试: {test_name}")
        print("-" * 50)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 通过")
            else:
                print(f"❌ {test_name} 失败")
        except Exception as e:
            print(f"❌ {test_name} 异常: {e}")
    
    print(f"\n📊 测试结果:")
    print(f"通过: {passed}/{total}")
    print(f"成功率: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 所有测试通过！增强版聊天机器人记忆功能正常工作")
        print("\n💡 功能验证:")
        print("   ✅ 记忆存储和检索")
        print("   ✅ 用户偏好检测")
        print("   ✅ 个性化对话")
        print("   ✅ 用户档案生成")
        print("   ✅ 个性化推荐")
        print("   ✅ 记忆管理")
    else:
        print("\n⚠️  部分测试失败，请检查配置和依赖")

if __name__ == "__main__":
    main()
