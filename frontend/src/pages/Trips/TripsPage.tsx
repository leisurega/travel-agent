import React, { useEffect, useState, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Plus, MapPin, Calendar, Users, Search, Filter, Trash2, MoreVertical, MessageCircle, X, Send, User } from 'lucide-react';
import { useTripStore } from 'store/useTripStore';
import Card from 'components/UI/Card';
import Button from 'components/UI/Button';
import LoadingSpinner from 'components/UI/LoadingSpinner';
import Input from 'components/UI/Input';
import apiService from 'services/api';

interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: string;
}

const TripsPage: React.FC = () => {
  const navigate = useNavigate();
  const { trips, isLoading, fetchTrips, deleteTrip } = useTripStore();
  const [searchTerm, setSearchTerm] = React.useState('');
  const [statusFilter, setStatusFilter] = React.useState<string>('all');
  const [isChatbotOpen, setIsChatbotOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 初始化欢迎消息
  useEffect(() => {
    if (isChatbotOpen && messages.length === 0) {
      setMessages([
        {
          id: '1',
          content: '您好！我是您的专属旅游助手🧳 我可以帮您：\n\n• 推荐旅游目的地\n• 制定旅行计划\n• 提供当地攻略\n• 记住您的偏好\n\n请问有什么可以帮助您的吗？',
          role: 'assistant',
          timestamp: new Date().toISOString()
        }
      ]);
    }
  }, [isChatbotOpen, messages.length]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isChatLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputMessage.trim(),
      role: 'user',
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsChatLoading(true);

    try {
      console.log('TripsPage - 发送消息:', inputMessage.trim());
      const response = await apiService.chatWithAI(inputMessage.trim());
      console.log('TripsPage - API响应:', response);
      console.log('TripsPage - 响应数据类型:', typeof response);
      console.log('TripsPage - 响应数据内容:', response.data);
      console.log('TripsPage - ai_response字段:', response.data?.ai_response);
      console.log('TripsPage - timestamp字段:', response.data?.timestamp);
      
      if (!response.data?.ai_response) {
        throw new Error('响应中缺少ai_response字段');
      }
      
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: response.data.ai_response,
        role: 'assistant',
        timestamp: response.data.timestamp || new Date().toISOString()
      };

      console.log('TripsPage - AI消息:', aiMessage);
      setMessages(prev => [...prev, aiMessage]);
    } catch (error: any) {
      console.error('TripsPage - 聊天失败 - 完整错误信息:', error);
      console.error('TripsPage - 错误响应:', error.response);
      console.error('TripsPage - 错误状态:', error.response?.status);
      console.error('TripsPage - 错误数据:', error.response?.data);
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: `抱歉，我暂时无法回答您的问题。错误信息: ${error.response?.status || '未知错误'}`,
        role: 'assistant',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsChatLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  useEffect(() => {
    fetchTrips();
  }, [fetchTrips]);

  const filteredTrips = trips.filter(trip => {
    if (!trip || !trip.title || !trip.destination) {
      return false;
    }
    const matchesSearch = trip.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         trip.destination.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || trip.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'planning':
        return 'bg-blue-100 text-blue-800';
      case 'completed':
        return 'bg-gray-100 text-gray-800';
      case 'cancelled':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'active':
        return '进行中';
      case 'planning':
        return '规划中';
      case 'completed':
        return '已完成';
      case 'cancelled':
        return '已取消';
      default:
        return status;
    }
  };

  const handleDeleteTrip = async (tripId: number, tripName: string, event: React.MouseEvent) => {
    event.preventDefault(); // 阻止Link的跳转
    event.stopPropagation();
    
    if (!window.confirm(`确定要删除旅行"${tripName}"吗？\n\n此操作将删除该旅行的所有数据，包括：\n• 所有成员信息\n• 所有支出记录\n• 所有时光记录\n• 所有旅行计划\n\n此操作不可恢复！`)) {
      return;
    }

    try {
      await deleteTrip(tripId);
      alert('旅行删除成功！');
    } catch (error: any) {
      console.error('删除旅行失败:', error);
      alert('删除旅行失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner size="lg" text="加载旅行列表..." />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* AI旅游助手区域 */}
      <Card className="bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center">
              <MessageCircle className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">AI旅游助手</h2>
              <p className="text-gray-600">智能规划您的旅行，记住您的偏好</p>
            </div>
          </div>
          <Button
            onClick={() => setIsChatbotOpen(!isChatbotOpen)}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            {isChatbotOpen ? '收起助手' : '开始对话'}
          </Button>
        </div>
      </Card>

      {/* 聊天机器人展开区域 */}
      {isChatbotOpen && (
        <Card className="border-2 border-blue-200">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-200">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                <MessageCircle className="w-4 h-4 text-white" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900">AI旅游助手</h3>
              <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">在线</span>
            </div>
            <button
              onClick={() => setIsChatbotOpen(false)}
              className="p-1 hover:bg-gray-100 rounded-full transition-colors"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>
          
          {/* 聊天区域 */}
          <div className="h-96 flex flex-col">
            {/* 消息列表 */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50 rounded-lg mb-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-xs lg:max-w-md px-4 py-3 rounded-lg ${
                      message.role === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-white text-gray-900 border border-gray-200'
                    }`}
                  >
                    <div className="flex items-start gap-2">
                      {message.role === 'assistant' && (
                        <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                          <MessageCircle className="w-3 h-3 text-white" />
                        </div>
                      )}
                      {message.role === 'user' && (
                        <div className="w-6 h-6 bg-white rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                          <User className="w-3 h-3 text-blue-600" />
                        </div>
                      )}
                      <div className="text-sm whitespace-pre-wrap">{message.content}</div>
                    </div>
                    <div className={`text-xs mt-2 ${
                      message.role === 'user' ? 'text-blue-100' : 'text-gray-500'
                    }`}>
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}
              
              {isChatLoading && (
                <div className="flex justify-start">
                  <div className="bg-white text-gray-900 max-w-xs lg:max-w-md px-4 py-3 rounded-lg border border-gray-200">
                    <div className="flex items-center gap-2">
                      <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center">
                        <MessageCircle className="w-3 h-3 text-white" />
                      </div>
                      <LoadingSpinner size="sm" />
                      <span className="text-sm">AI正在思考...</span>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            {/* 输入区域 */}
            <div className="flex gap-3">
              <Input
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="请输入您的问题，例如：我想去北京旅游有什么推荐？"
                disabled={isChatLoading}
                className="flex-1"
              />
              <Button
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() || isChatLoading}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6"
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">我的旅行</h1>
          <p className="text-gray-600 mt-1">管理你的所有旅行计划</p>
        </div>
        <Link to="/trips/create">
          <Button>
            <Plus className="w-4 h-4 mr-2" />
            创建新旅行
          </Button>
        </Link>
      </div>

      {/* Filters */}
      <Card>
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <Input
              placeholder="搜索旅行名称或目的地..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              leftIcon={<Search className="w-4 h-4" />}
            />
          </div>
          <div className="sm:w-48">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="input"
            >
              <option value="all">所有状态</option>
              <option value="planning">规划中</option>
              <option value="active">进行中</option>
              <option value="completed">已完成</option>
              <option value="cancelled">已取消</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Trips Grid */}
      {filteredTrips.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredTrips.map((trip) => (
            <Card key={trip.id} hover className="h-full">
              {/* 点击区域 */}
              <Link to={`/trips/${trip.id}`} className="block">
                <div className="flex items-start justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900 line-clamp-1 flex-1 pr-2">
                    {trip.title}
                  </h3>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(trip.status)}`}>
                      {getStatusText(trip.status)}
                    </span>
                    {/* 删除按钮 */}
                    <button
                      onClick={(e) => handleDeleteTrip(trip.id, trip.title, e)}
                      className="p-1 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-full transition-colors"
                      title="删除旅行"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                
                <div className="space-y-3 mb-4">
                  <div className="flex items-center text-gray-600">
                    <MapPin className="w-4 h-4 mr-2 flex-shrink-0" />
                    <span className="text-sm truncate">{trip.destination}</span>
                  </div>
                  <div className="flex items-center text-gray-600">
                    <Calendar className="w-4 h-4 mr-2 flex-shrink-0" />
                    <span className="text-sm">
                      {new Date(trip.start_date).toLocaleDateString()} - 
                      {new Date(trip.end_date).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="flex items-center text-gray-600">
                    <Users className="w-4 h-4 mr-2 flex-shrink-0" />
                    <span className="text-sm">{trip.members?.length || 0} 位成员</span>
                  </div>
                </div>

                {trip.description && (
                  <p className="text-gray-600 text-sm line-clamp-2 mb-4">
                    {trip.description}
                  </p>
                )}

                {/* Trip Stats */}
                <div className="pt-4 border-t border-gray-100 space-y-1">
                  <div className="text-sm text-gray-500">
                    {trip.expense_count || 0} 笔支出
                  </div>
                  <div className="text-sm text-gray-500">
                    {trip.memory_count || 0} 条记录
                  </div>
                </div>
              </Link>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="text-center py-12">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <MapPin className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {searchTerm || statusFilter !== 'all' ? '没有找到匹配的旅行' : '还没有旅行计划'}
          </h3>
          <p className="text-gray-600 mb-6">
            {searchTerm || statusFilter !== 'all' 
              ? '尝试调整搜索条件或筛选器'
              : '创建你的第一个旅行计划，开始精彩的旅程！'
            }
          </p>
          <Link to="/trips/create">
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              创建旅行
            </Button>
          </Link>
        </Card>
      )}
    </div>
  );
};

export default TripsPage;

