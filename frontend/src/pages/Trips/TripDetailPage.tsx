import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  MapPin, 
  Calendar, 
  Users, 
  DollarSign, 
  Camera, 
  MessageSquare,
  Settings,
  ArrowLeft,
  Plus,
  Check,
  X
} from 'lucide-react';
import { useTripStore } from 'store/useTripStore';
import { useAuthStore } from 'store/useAuthStore';
import Card from 'components/UI/Card';
import Button from 'components/UI/Button';
import LoadingSpinner from 'components/UI/LoadingSpinner';
import Input from 'components/UI/Input';
import apiService from 'services/api';

const TripDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const { 
    currentTrip, 
    expenses, 
    memories, 
    plan, 
    isLoading, 
    error,
    pendingExpenses,
    fetchTrip, 
    fetchExpenses, 
    fetchMemories,
    createMemory,
    updateMemory,
    deleteMemory,
    generateAIItinerary,
    addPendingExpense,
    clearPendingExpenses
  } = useTripStore();
  
  const [activeTab, setActiveTab] = useState<'overview' | 'expenses' | 'memories' | 'plan'>('overview');
  
  // 时光记录相关状态
  const [showAddMemoryForm, setShowAddMemoryForm] = useState(false);
  const [editingMemory, setEditingMemory] = useState<any>(null);
  const [showEditMemoryForm, setShowEditMemoryForm] = useState(false);
  const [newMemory, setNewMemory] = useState({
    title: '',
    content: '',
    location: '',
    date: '',
    tags: [] as string[],
    images: [] as string[]
  });
  const [hasAttemptedFetch, setHasAttemptedFetch] = useState(false);
  const [showAddExpenseForm, setShowAddExpenseForm] = useState(false);
  const [newExpense, setNewExpense] = useState({
    user_id: user?.id || 0,
    type: 'food',
    amount: '',
    currency: 'CNY',
    description: '',
    shares: [] as { user_id: number; amount: number }[]
  });
  const [selectedShareUsers, setSelectedShareUsers] = useState<number[]>([]);
  const [showInviteForm, setShowInviteForm] = useState(false);
  const [allUsers, setAllUsers] = useState<any[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<number>(0);
  
  // 编辑支出相关状态
  const [editingExpense, setEditingExpense] = useState<any>(null);
  const [showEditExpenseForm, setShowEditExpenseForm] = useState(false);
  const [isInitialLoading, setIsInitialLoading] = useState(true);
  
  // 分摊信息显示状态
  const [showSettlements, setShowSettlements] = useState(false);
  const [settlements, setSettlements] = useState<any[]>([]);

  useEffect(() => {
    if (id) {
      const tripId = parseInt(id);
      setHasAttemptedFetch(true);
      setIsInitialLoading(true);
      fetchTrip(tripId);
      fetchExpenses(tripId);
      fetchMemories(tripId);
    }
  }, [id, fetchTrip, fetchExpenses, fetchMemories]);

  // 监听currentTrip变化，当有数据时关闭初始loading
  useEffect(() => {
    if (currentTrip) {
      setIsInitialLoading(false);
      // 如果没有选择分摊人，默认选择所有成员
      if (selectedShareUsers.length === 0 && currentTrip.members) {
        setSelectedShareUsers(currentTrip.members.map(m => m.user_id));
      }
    }
  }, [currentTrip]);

  // 监听error变化，当有错误时也关闭初始loading
  useEffect(() => {
    if (error) {
      setIsInitialLoading(false);
    }
  }, [error]);

  // 加载所有用户
  useEffect(() => {
    const loadUsers = async () => {
      try {
        const response = await apiService.getUsers();
        setAllUsers(response.data);
      } catch (error) {
        console.error('加载用户列表失败:', error);
      }
    };
    loadUsers();
  }, []);

  // 调试信息
  useEffect(() => {
    if (currentTrip) {
      console.log('Current trip members:', currentTrip.members);
      console.log('Current trip members user data:', currentTrip.members?.map(m => ({ user_id: m.user_id, user: m.user })));
    }
  }, [currentTrip]);

  // 调试支出数据
  useEffect(() => {
    if (expenses && expenses.length > 0) {
      console.log('Expenses data:', expenses);
      expenses.forEach((expense, index) => {
        console.log(`Expense ${index}:`, expense);
        console.log(`Expense ${index} shares:`, expense.shares);
        console.log(`Expense ${index} expense_shares:`, (expense as any).expense_shares);
      });
    }
  }, [expenses]);

  // 显示loading状态
  if (isLoading || isInitialLoading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner size="lg" text="加载旅行详情..." />
      </div>
    );
  }

  // 如果已经尝试过获取数据，但没有currentTrip，说明旅行不存在或加载失败
  if (hasAttemptedFetch && !currentTrip && !isInitialLoading) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          {error ? '加载失败' : '旅行不存在'}
        </h2>
        <p className="text-gray-600 mb-6">
          {error || '请检查链接是否正确'}
        </p>
        <Button onClick={() => navigate('/trips')}>
          返回旅行列表
        </Button>
      </div>
    );
  }

  // 确保currentTrip不为null（TypeScript类型保护）
  if (!currentTrip) {
    return null;
  }

  const handleAddExpense = () => {
    if (!newExpense.amount || parseFloat(newExpense.amount) <= 0) {
      alert('请输入有效金额');
      return;
    }

    // 确定分摊用户：如果选择了特定用户，使用选择的用户；否则使用所有成员
    const shareUsers = selectedShareUsers.length > 0 ? selectedShareUsers : 
      currentTrip.members?.map(m => m.user_id) || [];
    
    if (shareUsers.length === 0) {
      alert('请选择至少一个分摊人');
      return;
    }

    const amount = parseFloat(newExpense.amount);
    const shareAmount = amount / shareUsers.length;

    const expense = {
      id: Date.now(), // 临时ID
      user_id: newExpense.user_id,
      type: newExpense.type,
      amount: amount,
      currency: newExpense.currency,
      description: newExpense.description,
      status: 'pending',
      shares: shareUsers.map(userId => ({
        user_id: userId
      }))
    };

    addPendingExpense(expense);
    
    // 重置表单
    setNewExpense({
      user_id: user?.id || 0,
      type: 'food',
      amount: '',
      currency: 'CNY',
      description: '',
      shares: []
    });
    setSelectedShareUsers([]);
    setShowAddExpenseForm(false);
  };

  const handleEditExpense = (expense: any) => {
    setEditingExpense({
      ...expense,
      amount: expense.amount || 0
    });
    setSelectedShareUsers(expense.shares?.map((share: any) => share.user_id) || []);
    setShowEditExpenseForm(true);
  };

  const handleUpdateExpense = async () => {
    if (!editingExpense || !editingExpense.amount || editingExpense.amount <= 0) {
      alert('请输入有效金额');
      return;
    }
    
    // 确定分摊用户：如果选择了特定用户，使用选择的用户；否则使用所有成员
    const shareUsers = selectedShareUsers.length > 0 ? selectedShareUsers : 
      currentTrip.members?.map(m => m.user_id) || [];
    
    if (shareUsers.length === 0) {
      alert('请选择至少一个分摊人');
      return;
    }

    try {
      // 检查是否在pendingExpenses中
      const isPendingExpense = pendingExpenses.some(exp => exp.id === editingExpense.id);
      
      if (isPendingExpense) {
        // 更新pendingExpenses中的支出
        const amount = parseFloat(editingExpense.amount);
        const updatedExpense = {
          ...editingExpense,
          amount: amount,
          shares: shareUsers.map(userId => ({
            user_id: userId
          }))
        };
        
        const updatedPendingExpenses = pendingExpenses.map(exp => 
          exp.id === editingExpense.id ? updatedExpense : exp
        );
        
        // 清空并重新添加更新后的支出
        clearPendingExpenses();
        updatedPendingExpenses.forEach(exp => addPendingExpense(exp));
      } else {
        // 更新后端数据库中的支出
        const updateData = {
          user_id: editingExpense.user_id,
          amount: parseFloat(editingExpense.amount),
          currency: editingExpense.currency,
          category: editingExpense.type,
          description: editingExpense.description,
          status: editingExpense.status,
          shares: shareUsers.map(userId => ({
            user_id: userId
          }))
        };
        
        await apiService.updateExpense(editingExpense.id, updateData);
        
        // 重新加载支出数据
        await fetchExpenses(parseInt(id!));
      }
      
      setEditingExpense(null);
      setSelectedShareUsers([]);
      setShowEditExpenseForm(false);
    } catch (error: any) {
      console.error('更新支出失败:', error);
      alert('更新支出失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleDeleteExpense = async (expenseId: number) => {
    if (window.confirm('确定要删除这条支出记录吗？')) {
      try {
        // 检查是否在pendingExpenses中
        const isPendingExpense = pendingExpenses.some(exp => exp.id === expenseId);
        
        if (isPendingExpense) {
          // 从pendingExpenses中删除
          const updatedPendingExpenses = pendingExpenses.filter(exp => exp.id !== expenseId);
          clearPendingExpenses();
          updatedPendingExpenses.forEach(exp => addPendingExpense(exp));
        } else {
          // 从后端删除
          await apiService.deleteExpense(expenseId);
          // 重新加载支出数据
          await fetchExpenses(parseInt(id!));
        }
      } catch (error: any) {
        console.error('删除支出失败:', error);
        alert('删除支出失败: ' + (error.response?.data?.detail || error.message));
      }
    }
  };

  const handleInviteMember = async () => {
    if (!selectedUserId) {
      alert('请选择要邀请的用户');
      return;
    }

    try {
      await apiService.addTripMember(parseInt(id!), selectedUserId);
      alert('邀请成功！');
      setShowInviteForm(false);
      setSelectedUserId(0);
      // 重新加载trip数据以获取更新后的成员列表
      if (id) {
        fetchTrip(parseInt(id));
      }
    } catch (error: any) {
      alert(error.response?.data?.detail || '邀请失败');
    }
  };

  const calculateSettlements = () => {
    const allPendingExpenses = [...expenses, ...pendingExpenses].filter(e => e.status === 'pending');
    
    console.log('所有待分摊支出:', allPendingExpenses);
    
    // 计算每个用户的净支出
    const userNet: Record<number, number> = {};
    
    allPendingExpenses.forEach((expense: any) => {
      console.log('处理支出:', expense);
      console.log('支出人ID:', expense.user_id, '金额:', expense.amount);
      console.log('分摊信息:', expense.shares);
      
      // 添加支出人支付的金额（支出人实际支付了全额）
      userNet[expense.user_id] = (userNet[expense.user_id] || 0) + expense.amount;
      
      // 减去分摊的金额（每个分摊人应该承担的部分）
      expense.shares?.forEach((share: any) => {
        console.log('分摊人ID:', share.user_id, '分摊金额:', share.amount);
        userNet[share.user_id] = (userNet[share.user_id] || 0) - share.amount;
      });
    });

    console.log('用户净支出:', userNet);

    // 计算结算方案
    const settlements: any[] = [];
    const users = Object.keys(userNet).map(Number);
    const positiveUsers = users.filter(uid => userNet[uid] > 0);
    const negativeUsers = users.filter(uid => userNet[uid] < 0);

    console.log('正余额用户:', positiveUsers);
    console.log('负余额用户:', negativeUsers);

    positiveUsers.forEach(positiveUserId => {
      negativeUsers.forEach(negativeUserId => {
        if (userNet[positiveUserId] > 0 && userNet[negativeUserId] < 0) {
          const amount = Math.min(userNet[positiveUserId], -userNet[negativeUserId]);
          if (amount > 0.01) { // 避免小数点误差
            settlements.push({
              from_user_id: negativeUserId,
              to_user_id: positiveUserId,
              amount: amount
            });
            userNet[positiveUserId] -= amount;
            userNet[negativeUserId] += amount;
          }
        }
      });
    });

    console.log('最终结算方案:', settlements);
    return settlements;
  };

  // 时光记录处理函数
  const handleAddMemory = async () => {
    try {
      const memoryData = {
        ...newMemory,
        date: newMemory.date ? new Date(newMemory.date).toISOString() : new Date().toISOString()
      };
      await createMemory(parseInt(id!), memoryData);
      
      // 重置表单
      setNewMemory({
        title: '',
        content: '',
        location: '',
        date: '',
        tags: [],
        images: []
      });
      setShowAddMemoryForm(false);
      
      // 重新加载时光记录
      await fetchMemories(parseInt(id!));
    } catch (error: any) {
      console.error('添加时光记录失败:', error);
      alert('添加时光记录失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleEditMemory = (memory: any) => {
    setEditingMemory(memory);
    setNewMemory({
      title: memory.title || '',
      content: memory.content || '',
      location: memory.location || '',
      date: memory.date ? new Date(memory.date).toISOString().split('T')[0] : '',
      tags: memory.tags || [],
      images: memory.images || []
    });
    setShowEditMemoryForm(true);
  };

  const handleUpdateMemory = async () => {
    if (!editingMemory) return;
    
    try {
      const memoryData = {
        ...newMemory,
        date: newMemory.date ? new Date(newMemory.date).toISOString() : editingMemory.date
      };
      await updateMemory(editingMemory.id, memoryData);
      
      // 重置表单
      setEditingMemory(null);
      setNewMemory({
        title: '',
        content: '',
        location: '',
        date: '',
        tags: [],
        images: []
      });
      setShowEditMemoryForm(false);
      
      // 重新加载时光记录
      await fetchMemories(parseInt(id!));
    } catch (error: any) {
      console.error('更新时光记录失败:', error);
      alert('更新时光记录失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  // AI行程生成处理函数
  const handleGenerateAIItinerary = async () => {
    if (!id) return;
    
    try {
      await generateAIItinerary(parseInt(id));
      alert('AI行程生成成功！');
    } catch (error: any) {
      console.error('生成AI行程失败:', error);
      alert('生成AI行程失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleDeleteMemory = async (memoryId: number) => {
    if (!window.confirm('确定要删除这条时光记录吗？')) {
      return;
    }
    
    try {
      await deleteMemory(memoryId);
      // 重新加载时光记录
      await fetchMemories(parseInt(id!));
    } catch (error: any) {
      console.error('删除时光记录失败:', error);
      alert('删除时光记录失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  // 图片上传处理函数
  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files) return;

    // 这里是简化版本，实际项目中应该上传到云存储服务
    Array.from(files).forEach(file => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const imageUrl = e.target?.result as string;
        setNewMemory(prev => ({
          ...prev,
          images: [...prev.images, imageUrl]
        }));
      };
      reader.readAsDataURL(file);
    });
  };

  // 删除图片
  const handleImageDelete = (index: number) => {
    setNewMemory(prev => ({
      ...prev,
      images: prev.images.filter((_, i) => i !== index)
    }));
  };

  const handleCalculateSettlements = async () => {
    try {
      // 如果有pendingExpenses，先保存到后端
      if (pendingExpenses.length > 0) {
        console.log('保存pendingExpenses到后端:', pendingExpenses);
        
        for (const expense of pendingExpenses) {
          try {
            // 创建支出记录
            const expenseData = {
              trip_id: parseInt(id!),
              user_id: expense.user_id,
              category: expense.type,  // 前端用type，后端用category
              amount: expense.amount,
              currency: expense.currency,
              description: expense.description,
              status: expense.status,
              shares: expense.shares?.map((share: any) => ({
                user_id: share.user_id
              })) || []
            };
            
            const expenseResponse = await apiService.createTripExpense(parseInt(id!), expenseData);
            const createdExpense = expenseResponse.data;
            
            // 不再需要单独调用splitExpense，因为shares已经包含在expenseData中
          } catch (error: any) {
            console.error('保存支出失败:', error);
            alert('保存支出失败: ' + (error.response?.data?.detail || error.message));
            return;
          }
        }
        
        // 清空pendingExpenses
        clearPendingExpenses();
        
        // 重新加载支出数据
        await fetchExpenses(parseInt(id!));
      }
      
      // 获取分摊计算
      const response = await apiService.getExpenseSummary(parseInt(id!));
      const summaryData = response.data;
      console.log('后端返回的分摊数据:', summaryData);
      
      setSettlements(summaryData.settlements || []);
      setShowSettlements(true);
    } catch (error: any) {
      console.error('获取分摊数据失败:', error);
      alert('获取分摊数据失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const getTypeText = (type: string) => {
    const typeMap: Record<string, string> = {
      'food': '餐饮',
      'transport': '交通',
      'accommodation': '住宿',
      'entertainment': '娱乐',
      'shopping': '购物',
      'other': '其他'
    };
    return typeMap[type] || type;
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

  const totalExpenses = expenses?.reduce((sum, expense) => sum + expense.amount, 0) || 0;
  const userExpenses = expenses?.filter(expense => 
    expense.shares?.some(share => share.user_id === user?.id)
  ) || [];

  const tabs = [
    { id: 'overview', label: '概览', icon: MapPin },
    { id: 'expenses', label: '支出', icon: DollarSign },
    { id: 'memories', label: '时光记录', icon: Camera },
    { id: 'plan', label: '旅行计划', icon: MessageSquare },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            onClick={() => navigate('/trips')}
            className="p-2"
          >
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{currentTrip.title}</h1>
            <p className="text-gray-600">{currentTrip.destination}</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <span className={`px-3 py-1 text-sm font-medium rounded-full ${getStatusColor(currentTrip.status)}`}>
            {getStatusText(currentTrip.status)}
          </span>
          <Button variant="outline" size="sm">
            <Settings className="w-4 h-4 mr-2" />
            设置
          </Button>
        </div>
      </div>

      {/* Trip Info */}
      <Card>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <Calendar className="w-6 h-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600">旅行日期</p>
              <p className="font-semibold text-gray-900">
                {new Date(currentTrip.start_date).toLocaleDateString()} - 
                {new Date(currentTrip.end_date).toLocaleDateString()}
              </p>
            </div>
          </div>

          <div className="flex items-center">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <Users className="w-6 h-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600">成员数量</p>
              <p className="font-semibold text-gray-900">{currentTrip.members?.length || 0} 人</p>
            </div>
          </div>

          <div className="flex items-center">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
              <DollarSign className="w-6 h-6 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600">总支出</p>
              <p className="font-semibold text-gray-900">¥{totalExpenses.toLocaleString()}</p>
            </div>
          </div>

          <div className="flex items-center">
            <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
              <Camera className="w-6 h-6 text-orange-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600">时光记录</p>
              <p className="font-semibold text-gray-900">{memories?.length || 0} 条</p>
            </div>
          </div>
        </div>
      </Card>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="space-y-6">
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Members */}
            <Card>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">旅行成员</h3>
                <Button size="sm" variant="outline" onClick={() => setShowInviteForm(!showInviteForm)}>
                  <Plus className="w-4 h-4 mr-2" />
                  邀请成员
                </Button>
              </div>

              {/* 邀请成员表单 */}
              {showInviteForm && (
                <div className="mb-4 p-4 border border-gray-200 rounded-lg bg-gray-50">
                  <h4 className="text-lg font-medium mb-4">邀请成员</h4>
                  <div className="flex items-center space-x-4">
                    <div className="flex-1">
                      <label className="block text-sm font-medium text-gray-700 mb-1">选择用户</label>
                      <select
                        value={selectedUserId}
                        onChange={(e) => setSelectedUserId(parseInt(e.target.value))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value={0}>请选择用户</option>
                        {allUsers
                          .filter(u => !currentTrip.members?.some(m => m.user_id === u.id))
                          .map(user => (
                            <option key={user.id} value={user.id}>
                              {user.username} ({user.email})
                            </option>
                          ))}
                      </select>
                    </div>
                    <div className="flex space-x-2">
                      <Button variant="outline" onClick={() => setShowInviteForm(false)}>
                        <X className="w-4 h-4 mr-2" />
                        取消
                      </Button>
                      <Button onClick={handleInviteMember}>
                        <Check className="w-4 h-4 mr-2" />
                        邀请
                      </Button>
                    </div>
                  </div>
                </div>
              )}

              <div className="space-y-3">
                {currentTrip.members?.map((member) => (
                  <div key={member.id} className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                      <span className="text-sm font-medium text-primary-600">
                        {member.user?.username?.charAt(0).toUpperCase() || 'U'}
                      </span>
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{member.user?.username || '未知用户'}</p>
                      <p className="text-sm text-gray-500">{member.role === 'owner' ? '创建者' : '成员'}</p>
                    </div>
                  </div>
                )) || []}
              </div>
            </Card>

            {/* Recent Activities */}
            <Card>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">最近活动</h3>
              <div className="space-y-3">
                {memories?.slice(0, 3).map((memory) => (
                  <div key={memory.id} className="flex items-start space-x-3">
                    <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center">
                      <Camera className="w-4 h-4 text-orange-600" />
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">{memory.title}</p>
                      <p className="text-xs text-gray-500">
                        {memory.user?.username || '未知用户'} · {new Date(memory.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                )) || []}
                {(!memories || memories.length === 0) && (
                  <p className="text-gray-500 text-sm">暂无活动记录</p>
                )}
              </div>
            </Card>
          </div>
        )}

        {activeTab === 'expenses' && (
          <Card>
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-900">支出记录</h3>
              <div className="flex space-x-2">
                <Button onClick={() => navigate(`/trips/${id}/expenses`)}>
                  <DollarSign className="w-4 h-4 mr-2" />
                  记账分摊
                </Button>
                <Button onClick={() => setShowAddExpenseForm(!showAddExpenseForm)}>
                <Plus className="w-4 h-4 mr-2" />
                添加支出
              </Button>
            </div>
            </div>

            {/* 添加支出表单 */}
            {showAddExpenseForm && (
              <div className="mb-6 p-4 border border-gray-200 rounded-lg bg-gray-50">
                <h4 className="text-lg font-medium mb-4">添加支出</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">用户</label>
                    <select
                      value={newExpense.user_id}
                      onChange={(e) => setNewExpense({...newExpense, user_id: parseInt(e.target.value)})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {currentTrip.members?.map(member => (
                        <option key={member.user_id} value={member.user_id}>
                          {member.user?.username || '未知用户'}
                        </option>
                      ))}
                    </select>
                    </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">类型</label>
                    <select
                      value={newExpense.type}
                      onChange={(e) => setNewExpense({...newExpense, type: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="food">餐饮</option>
                      <option value="transport">交通</option>
                      <option value="accommodation">住宿</option>
                      <option value="entertainment">娱乐</option>
                      <option value="shopping">购物</option>
                      <option value="other">其他</option>
                    </select>
                    </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">金额</label>
                    <Input
                      type="number"
                      value={newExpense.amount}
                      onChange={(e) => setNewExpense({...newExpense, amount: e.target.value})}
                      placeholder="0.00"
                      step="0.01"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">币种</label>
                    <select
                      value={newExpense.currency}
                      onChange={(e) => setNewExpense({...newExpense, currency: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="CNY">人民币</option>
                      <option value="IDR">印尼盾</option>
                    </select>
                  </div>

                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">描述</label>
                    <Input
                      value={newExpense.description}
                      onChange={(e) => setNewExpense({...newExpense, description: e.target.value})}
                      placeholder="支出描述"
                    />
                  </div>

                  <div className="md:col-span-3">
                    <label className="block text-sm font-medium text-gray-700 mb-1">分摊人</label>
                    <select
                      multiple
                      value={selectedShareUsers.map(String)}
                      onChange={(e) => {
                        const selectedOptions = Array.from(e.target.selectedOptions, option => parseInt(option.value));
                        setSelectedShareUsers(selectedOptions);
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[120px] resize-none bg-white"
                      size={Math.min(currentTrip.members?.length || 3, 5)}
                      style={{
                        display: 'block',
                        overflowY: 'auto'
                      }}
                    >
                      {currentTrip.members?.map(member => (
                        <option key={member.user_id} value={member.user_id}>
                          {member.user?.username || '未知用户'}
                        </option>
                      ))}
                    </select>
                    <p className="text-xs text-gray-500 mt-1">
                      {selectedShareUsers.length > 0 
                        ? `已选择 ${selectedShareUsers.length} 人分摊` 
                        : '默认所有成员分摊 (按住Ctrl键可多选)'}
                    </p>
                  </div>
                </div>
                
                <div className="flex justify-end space-x-2 mt-4">
                  <Button variant="outline" onClick={() => {
                    setShowAddExpenseForm(false);
                    setSelectedShareUsers([]);
                  }}>
                    <X className="w-4 h-4 mr-2" />
                    取消
                  </Button>
                  <Button onClick={handleAddExpense}>
                    <Check className="w-4 h-4 mr-2" />
                    添加
                  </Button>
                </div>
              </div>
            )}

            {/* 编辑支出表单 */}
            {showEditExpenseForm && editingExpense && (
              <div className="bg-gray-50 p-4 rounded-lg mb-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">编辑支出</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">用户</label>
                    <select
                      value={editingExpense.user_id}
                      onChange={(e) => setEditingExpense({...editingExpense, user_id: parseInt(e.target.value)})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {currentTrip.members?.map(member => (
                        <option key={member.user_id} value={member.user_id}>
                          {member.user?.username || '未知用户'}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">类型</label>
                    <select
                      value={editingExpense.type}
                      onChange={(e) => setEditingExpense({...editingExpense, type: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="food">餐饮</option>
                      <option value="transport">交通</option>
                      <option value="accommodation">住宿</option>
                      <option value="entertainment">娱乐</option>
                      <option value="shopping">购物</option>
                      <option value="other">其他</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">金额</label>
                    <Input
                      type="number"
                      value={editingExpense.amount}
                      onChange={(e) => setEditingExpense({...editingExpense, amount: parseFloat(e.target.value) || 0})}
                      placeholder="0.00"
                      step="0.01"
                    />
                  </div>

                    <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">币种</label>
                    <select
                      value={editingExpense.currency}
                      onChange={(e) => setEditingExpense({...editingExpense, currency: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="CNY">人民币</option>
                      <option value="IDR">印尼盾</option>
                    </select>
                    </div>

                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">描述</label>
                    <Input
                      value={editingExpense.description}
                      onChange={(e) => setEditingExpense({...editingExpense, description: e.target.value})}
                      placeholder="支出描述"
                    />
                    </div>

                  <div className="md:col-span-3">
                    <label className="block text-sm font-medium text-gray-700 mb-1">分摊人</label>
                    <select
                      multiple
                      value={selectedShareUsers.map(String)}
                      onChange={(e) => {
                        const selectedOptions = Array.from(e.target.selectedOptions, option => parseInt(option.value));
                        setSelectedShareUsers(selectedOptions);
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[120px] resize-none bg-white"
                      size={Math.min(currentTrip.members?.length || 3, 5)}
                      style={{
                        display: 'block',
                        overflowY: 'auto'
                      }}
                    >
                      {currentTrip.members?.map(member => (
                        <option key={member.user_id} value={member.user_id}>
                          {member.user?.username || '未知用户'}
                        </option>
                      ))}
                    </select>
                    <p className="text-xs text-gray-500 mt-1">
                      {selectedShareUsers.length > 0 
                        ? `已选择 ${selectedShareUsers.length} 人分摊` 
                        : '默认所有成员分摊 (按住Ctrl键可多选)'}
                    </p>
                  </div>
                </div>
                
                <div className="flex justify-end space-x-2 mt-4">
                  <Button variant="outline" onClick={() => {
                    setShowEditExpenseForm(false);
                    setEditingExpense(null);
                    setSelectedShareUsers([]);
                  }}>
                    <X className="w-4 h-4 mr-2" />
                    取消
                  </Button>
                  <Button onClick={handleUpdateExpense}>
                    <Check className="w-4 h-4 mr-2" />
                    更新
                  </Button>
                </div>
              </div>
            )}

            {/* 支出表格 */}
            {(() => {
              console.log('支出表格渲染条件检查:');
              console.log('expenses:', expenses);
              console.log('expenses?.length:', expenses?.length);
              console.log('pendingExpenses:', pendingExpenses);
              console.log('pendingExpenses.length:', pendingExpenses.length);
              console.log('条件结果:', (expenses && expenses.length > 0) || pendingExpenses.length > 0);
              return (expenses && expenses.length > 0) || pendingExpenses.length > 0;
            })() ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">用户</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">类型</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">金额</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">币种</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">分摊人</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">状态</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">操作</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {[...expenses, ...pendingExpenses].map((expense) => (
                      <tr key={expense.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {currentTrip.members?.find(m => m.user_id === expense.user_id)?.user?.username || '未知用户'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {getTypeText(expense.category || expense.type)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {expense.amount.toFixed(2)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {expense.currency === 'CNY' ? '人民币' : '印尼盾'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {(() => {
                            // 尝试从不同来源获取分摊人信息
                            let sharers = [];
                            
                            // 1. 从expense.shares获取
                            if (expense.shares && expense.shares.length > 0) {
                              sharers = expense.shares.map((share: any) => 
                                currentTrip.members?.find(m => m.user_id === share.user_id)?.user?.username || '未知用户'
                              );
                            }
                            // 2. 从expense.expense_shares获取（后端可能使用这个字段名）
                            else if (expense.expense_shares && expense.expense_shares.length > 0) {
                              sharers = expense.expense_shares.map((share: any) => 
                                currentTrip.members?.find(m => m.user_id === share.user_id)?.user?.username || '未知用户'
                              );
                            }
                            // 3. 如果是pendingExpenses，使用shares字段
                            else if (expense.shares && Array.isArray(expense.shares)) {
                              sharers = expense.shares.map((share: any) => 
                                currentTrip.members?.find(m => m.user_id === share.user_id)?.user?.username || '未知用户'
                              );
                            }
                            
                            return sharers.length > 0 ? sharers.join('、') : '0 人';
                          })()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                            expense.status === 'pending' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'
                          }`}>
                            {expense.status === 'pending' ? '待分摊' : '完成'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <div className="flex space-x-2">
                            <button
                              onClick={() => handleEditExpense(expense)}
                              className="text-blue-600 hover:text-blue-900 text-xs"
                            >
                              编辑
                            </button>
                            <button
                              onClick={() => handleDeleteExpense(expense.id)}
                              className="text-red-600 hover:text-red-900 text-xs"
                            >
                              删除
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-8">
                <DollarSign className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">还没有支出记录</p>
              </div>
            )}

            {/* 分摊计算按钮和分摊信息显示 */}
            {((expenses && expenses.length > 0) || pendingExpenses.length > 0) && (
              <div className="mt-6">
                <Button onClick={handleCalculateSettlements}>
                  计算分摊
                </Button>
                
                {/* 分摊信息显示区域 */}
                {showSettlements && (
                  <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <h4 className="text-sm font-medium text-blue-900 mb-3">分摊方案</h4>
                    {settlements.length > 0 ? (
                      <div className="space-y-2">
                        {settlements.map((settlement, index) => (
                          <div key={index} className="text-sm text-gray-700">
                            <span className="font-medium">
                              {settlement.from_username || currentTrip.members?.find(m => m.user_id === settlement.from_user_id)?.user?.username || '未知用户'}
                            </span>
                            {' 向 '}
                            <span className="font-medium">
                              {settlement.to_username || currentTrip.members?.find(m => m.user_id === settlement.to_user_id)?.user?.username || '未知用户'}
                            </span>
                            {' 支付 ¥'}
                            <span className="font-medium text-blue-600">
                              {settlement.amount.toFixed(2)}
                            </span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-gray-600">无需分摊</p>
                    )}
                    <div className="mt-3 pt-3 border-t border-blue-200">
                      <button
                        onClick={() => setShowSettlements(false)}
                        className="text-xs text-blue-600 hover:text-blue-800"
                      >
                        关闭
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </Card>
        )}

        {activeTab === 'memories' && (
          <Card>
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-900">时光记录</h3>
              <Button onClick={() => setShowAddMemoryForm(!showAddMemoryForm)}>
                <Plus className="w-4 h-4 mr-2" />
                添加记录
              </Button>
            </div>

            {/* 添加时光记录表单 */}
            {showAddMemoryForm && (
              <div className="mb-6 p-4 bg-gray-50 border border-gray-200 rounded-lg">
                <h4 className="text-sm font-medium text-gray-900 mb-4">添加时光记录</h4>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">标题</label>
                    <Input
                      value={newMemory.title}
                      onChange={(e) => setNewMemory({ ...newMemory, title: e.target.value })}
                      placeholder="输入记录标题"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">内容</label>
                    <textarea
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      rows={3}
                      value={newMemory.content}
                      onChange={(e) => setNewMemory({ ...newMemory, content: e.target.value })}
                      placeholder="记录下这一刻的美好..."
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">地点</label>
                    <Input
                      value={newMemory.location}
                      onChange={(e) => setNewMemory({ ...newMemory, location: e.target.value })}
                      placeholder="输入地点"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">日期（可选）</label>
                    <Input
                      type="date"
                      value={newMemory.date}
                      onChange={(e) => setNewMemory({ ...newMemory, date: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">图片</label>
                    <div className="space-y-2">
                      <input
                        type="file"
                        accept="image/*"
                        multiple
                        onChange={handleImageUpload}
                        className="block w-full text-sm text-gray-500
                          file:mr-4 file:py-2 file:px-4
                          file:rounded-full file:border-0
                          file:text-sm file:font-semibold
                          file:bg-blue-50 file:text-blue-700
                          hover:file:bg-blue-100"
                      />
                      {newMemory.images.length > 0 && (
                        <div className="max-h-48 overflow-y-auto border border-gray-200 rounded-lg p-2 bg-gray-50">
                          <div className="grid grid-cols-2 gap-2">
                            {newMemory.images.map((image, index) => (
                              <div key={index} className="relative group">
                                <img
                                  src={image}
                                  alt={`预览 ${index + 1}`}
                                  className="w-full h-24 object-cover rounded border cursor-pointer hover:opacity-80 transition-opacity"
                                  onClick={() => window.open(image, '_blank')}
                                />
                                <button
                                  type="button"
                                  onClick={() => handleImageDelete(index)}
                                  className="absolute top-1 right-1 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm hover:bg-red-600 opacity-0 group-hover:opacity-100 transition-opacity shadow-lg"
                                  title="删除图片"
                                >
                                  ×
                                </button>
                                <div className="absolute bottom-1 left-1 bg-black bg-opacity-70 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity">
                                  图片 {index + 1}
                                </div>
                              </div>
                            ))}
                          </div>
                          <div className="mt-2 text-xs text-gray-500 text-center border-t border-gray-300 pt-2">
                            📷 已上传 {newMemory.images.length} 张图片，点击图片可预览大图
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="flex space-x-2">
                    <Button onClick={handleAddMemory}>
                      <Check className="w-4 h-4 mr-2" />
                      保存
                    </Button>
                    <Button variant="ghost" onClick={() => {
                      setShowAddMemoryForm(false);
                      setNewMemory({ title: '', content: '', location: '', date: '', tags: [], images: [] });
                    }}>
                      <X className="w-4 h-4 mr-2" />
                      取消
                    </Button>
                  </div>
                </div>
              </div>
            )}

            {/* 编辑时光记录表单 */}
            {showEditMemoryForm && editingMemory && (
              <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <h4 className="text-sm font-medium text-gray-900 mb-4">编辑时光记录</h4>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">标题</label>
                    <Input
                      value={newMemory.title}
                      onChange={(e) => setNewMemory({ ...newMemory, title: e.target.value })}
                      placeholder="输入记录标题"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">内容</label>
                    <textarea
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      rows={3}
                      value={newMemory.content}
                      onChange={(e) => setNewMemory({ ...newMemory, content: e.target.value })}
                      placeholder="记录下这一刻的美好..."
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">地点</label>
                    <Input
                      value={newMemory.location}
                      onChange={(e) => setNewMemory({ ...newMemory, location: e.target.value })}
                      placeholder="输入地点"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">日期（可选）</label>
                    <Input
                      type="date"
                      value={newMemory.date}
                      onChange={(e) => setNewMemory({ ...newMemory, date: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">图片</label>
                    <div className="space-y-2">
                      <input
                        type="file"
                        accept="image/*"
                        multiple
                        onChange={handleImageUpload}
                        className="block w-full text-sm text-gray-500
                          file:mr-4 file:py-2 file:px-4
                          file:rounded-full file:border-0
                          file:text-sm file:font-semibold
                          file:bg-blue-50 file:text-blue-700
                          hover:file:bg-blue-100"
                      />
                      {newMemory.images.length > 0 && (
                        <div className="max-h-48 overflow-y-auto border border-gray-200 rounded-lg p-2 bg-gray-50">
                          <div className="grid grid-cols-2 gap-2">
                            {newMemory.images.map((image, index) => (
                              <div key={index} className="relative group">
                                <img
                                  src={image}
                                  alt={`预览 ${index + 1}`}
                                  className="w-full h-24 object-cover rounded border cursor-pointer hover:opacity-80 transition-opacity"
                                  onClick={() => window.open(image, '_blank')}
                                />
                                <button
                                  type="button"
                                  onClick={() => handleImageDelete(index)}
                                  className="absolute top-1 right-1 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm hover:bg-red-600 opacity-0 group-hover:opacity-100 transition-opacity shadow-lg"
                                  title="删除图片"
                                >
                                  ×
                                </button>
                                <div className="absolute bottom-1 left-1 bg-black bg-opacity-70 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity">
                                  图片 {index + 1}
                                </div>
                              </div>
                            ))}
                          </div>
                          <div className="mt-2 text-xs text-gray-500 text-center border-t border-gray-300 pt-2">
                            📷 已上传 {newMemory.images.length} 张图片，点击图片可预览大图
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="flex space-x-2">
                    <Button onClick={handleUpdateMemory}>
                      <Check className="w-4 h-4 mr-2" />
                      更新
                    </Button>
                    <Button variant="ghost" onClick={() => {
                      setShowEditMemoryForm(false);
                      setEditingMemory(null);
                      setNewMemory({ title: '', content: '', location: '', date: '', tags: [], images: [] });
                    }}>
                      <X className="w-4 h-4 mr-2" />
                      取消
                    </Button>
                  </div>
                </div>
              </div>
            )}

            {memories && memories.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {memories.map((memory) => (
                  <div key={memory.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="font-medium text-gray-900">{memory.title}</h4>
                      <div className="flex space-x-1">
                        <button
                          onClick={() => handleEditMemory(memory)}
                          className="text-blue-600 hover:text-blue-800 text-sm"
                        >
                          编辑
                        </button>
                        <button
                          onClick={() => handleDeleteMemory(memory.id)}
                          className="text-red-600 hover:text-red-800 text-sm"
                        >
                          删除
                        </button>
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 mb-3 line-clamp-3">{memory.content}</p>
                    {memory.images && memory.images.length > 0 && (
                      <div className="mb-3">
                        <div className="max-h-32 overflow-y-auto border border-gray-200 rounded-lg p-2 bg-gray-50">
                          <div className="grid grid-cols-3 gap-1">
                            {memory.images.map((image, index) => (
                              <div key={index} className="relative group">
                                <img
                                  src={image}
                                  alt={`${memory.title} 图片 ${index + 1}`}
                                  className="w-full h-16 object-cover rounded border cursor-pointer hover:opacity-80 transition-opacity"
                                  onClick={() => window.open(image, '_blank')}
                                />
                                <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-60 text-white text-xs text-center py-1 rounded-b opacity-0 group-hover:opacity-100 transition-opacity">
                                  {index + 1}/{memory.images.length}
                                </div>
                              </div>
                            ))}
                          </div>
                          <div className="mt-1 text-xs text-gray-500 text-center">
                            📷 {memory.images.length} 张图片 - 点击查看大图
                          </div>
                        </div>
                      </div>
                    )}
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <div className="flex items-center">
                        <MapPin className="w-3 h-3 mr-1" />
                        {memory.location || '未知位置'}
                    </div>
                      <div className="flex items-center">
                        <span>{memory.user?.username || '未知用户'}</span>
                        <span className="mx-1">·</span>
                        <span>{new Date(memory.date || memory.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                    {memory.tags && memory.tags.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {memory.tags.map((tag, index) => (
                          <span
                            key={index}
                            className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded"
                          >
                            #{tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <Camera className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">还没有时光记录</p>
              </div>
            )}
          </Card>
        )}

        {activeTab === 'plan' && (
          <Card>
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-900">旅行计划</h3>
              <Button onClick={handleGenerateAIItinerary} disabled={isLoading}>
                <Plus className="w-4 h-4 mr-2" />
                {isLoading ? '生成中...' : '生成AI计划'}
              </Button>
            </div>
            {plan && plan.daily_plans ? (
              <div className="space-y-6">
                {plan.daily_plans.map((dayPlan) => (
                  <div key={dayPlan.day} className="border border-gray-200 rounded-lg p-4">
                    <h4 className="font-semibold text-gray-900 mb-3">第 {dayPlan.day} 天</h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <p className="text-sm font-medium text-gray-700 mb-1">上午</p>
                        <p className="text-sm text-gray-600">{dayPlan.morning}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-700 mb-1">下午</p>
                        <p className="text-sm text-gray-600">{dayPlan.afternoon}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-700 mb-1">晚上</p>
                        <p className="text-sm text-gray-600">{dayPlan.evening}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <MessageSquare className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500 mb-4">还没有旅行计划</p>
                <Button onClick={handleGenerateAIItinerary} disabled={isLoading}>
                  {isLoading ? '生成中...' : '使用AI生成计划'}
                </Button>
              </div>
            )}
          </Card>
        )}
      </div>
    </div>
  );
};

export default TripDetailPage;

