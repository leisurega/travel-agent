import React, { useState, useRef, useEffect } from 'react';
import { Send, MessageCircle, X, Minimize2, Maximize2, Bot, User } from 'lucide-react';
import Button from 'components/UI/Button';
import Input from 'components/UI/Input';
import Card from 'components/UI/Card';
import LoadingSpinner from 'components/UI/LoadingSpinner';
import apiService from 'services/api';

interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: string;
}

interface ChatbotProps {
  isOpen: boolean;
  onToggle: () => void;
}

const Chatbot: React.FC<ChatbotProps> = ({ isOpen, onToggle }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 初始化欢迎消息
  useEffect(() => {
    if (isOpen && messages.length === 0) {
      setMessages([
        {
          id: '1',
          content: '您好！我是您的专属旅游助手🧳 我可以帮您：\n\n• 推荐旅游目的地\n• 制定旅行计划\n• 提供当地攻略\n• 记住您的偏好\n\n请问有什么可以帮助您的吗？',
          role: 'assistant',
          timestamp: new Date().toISOString()
        }
      ]);
    }
  }, [isOpen, messages.length]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputMessage.trim(),
      role: 'user',
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      console.log('=== 开始发送消息 ===');
      console.log('发送消息:', inputMessage.trim());
      console.log('调用API服务...');
      
      const response = await apiService.chatWithAI(inputMessage.trim());
      
      console.log('=== API调用成功 ===');
      console.log('API响应:', response);
      console.log('响应数据类型:', typeof response);
      console.log('响应数据内容:', response.data);
      console.log('response.data.data:', response.data?.data);
      console.log('ai_response字段:', response.data?.data?.ai_response);
      console.log('timestamp字段:', response.data?.data?.timestamp);
      console.log('=== 开始解析响应 ===');
      
      // 检查响应结构
      if (!response || !response.data) {
        throw new Error('响应结构异常: 缺少data字段');
      }
      
      // 后端返回的数据结构是 { success: true, message: "...", data: { ai_response: "...", timestamp: "..." } }
      const responseData = response.data.data;
      
      if (!responseData || !responseData.ai_response) {
        throw new Error('响应中缺少ai_response字段');
      }
      
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: responseData.ai_response,
        role: 'assistant',
        timestamp: responseData.timestamp || new Date().toISOString()
      };

      console.log('AI消息:', aiMessage);
      setMessages(prev => [...prev, aiMessage]);
    } catch (error: any) {
      console.error('=== 聊天失败 ===');
      console.error('完整错误信息:', error);
      console.error('错误类型:', typeof error);
      console.error('错误消息:', error.message);
      console.error('错误堆栈:', error.stack);
      console.error('错误响应:', error.response);
      console.error('错误状态:', error.response?.status);
      console.error('错误数据:', error.response?.data);
      console.error('错误配置:', error.config);
      console.error('=== 错误详情结束 ===');
      
      // 更详细的错误信息
      let errorText = '未知错误';
      if (error.message) {
        if (error.message.includes('timeout')) {
          errorText = 'AI响应超时，请稍后再试';
        } else {
          errorText = error.message;
        }
      } else if (error.response?.status) {
        errorText = `HTTP ${error.response.status}: ${error.response.statusText || '请求失败'}`;
      } else if (error.code) {
        if (error.code === 'ECONNABORTED') {
          errorText = '请求超时，AI正在思考中，请稍后再试';
        } else {
          errorText = `网络错误: ${error.code}`;
        }
      }
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: `抱歉，我暂时无法回答您的问题。错误信息: ${errorText}`,
        role: 'assistant',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (!isOpen) {
    return (
      <div className="fixed bottom-4 right-4 z-50">
        <Button
          onClick={onToggle}
          className="rounded-full w-14 h-14 shadow-lg hover:shadow-xl transition-shadow"
        >
          <MessageCircle className="w-6 h-6" />
        </Button>
      </div>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 z-50">
      <Card className={`w-96 ${isMinimized ? 'h-14' : 'h-96'} shadow-xl transition-all duration-300`}>
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-primary-50 rounded-t-lg">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">AI旅游助手</h3>
              <p className="text-xs text-gray-500">在线</p>
            </div>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setIsMinimized(!isMinimized)}
              className="p-1 hover:bg-gray-200 rounded transition-colors"
            >
              {isMinimized ? <Maximize2 className="w-4 h-4" /> : <Minimize2 className="w-4 h-4" />}
            </button>
            <button
              onClick={onToggle}
              className="p-1 hover:bg-gray-200 rounded transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {!isMinimized && (
          <>
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 h-64">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-xs lg:max-w-md px-3 py-2 rounded-lg ${
                      message.role === 'user'
                        ? 'bg-primary-600 text-white'
                        : 'bg-gray-100 text-gray-900'
                    }`}
                  >
                    <div className="flex items-start gap-2">
                      {message.role === 'assistant' && (
                        <Bot className="w-4 h-4 mt-0.5 flex-shrink-0" />
                      )}
                      {message.role === 'user' && (
                        <User className="w-4 h-4 mt-0.5 flex-shrink-0" />
                      )}
                      <div className="text-sm whitespace-pre-wrap">{message.content}</div>
                    </div>
                    <div className={`text-xs mt-1 ${
                      message.role === 'user' ? 'text-primary-100' : 'text-gray-500'
                    }`}>
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}
              
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 text-gray-900 max-w-xs lg:max-w-md px-3 py-2 rounded-lg">
                    <div className="flex items-center gap-2">
                      <Bot className="w-4 h-4" />
                      <LoadingSpinner size="sm" />
                      <span className="text-sm">AI正在思考中，请耐心等待...</span>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      这可能需要10-30秒，请勿关闭页面
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-4 border-t border-gray-200">
              <div className="flex gap-2">
                <Input
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="请输入您的问题..."
                  disabled={isLoading}
                  className="flex-1"
                />
                <Button
                  onClick={handleSendMessage}
                  disabled={!inputMessage.trim() || isLoading}
                  size="sm"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </>
        )}
      </Card>
    </div>
  );
};

export default Chatbot;
