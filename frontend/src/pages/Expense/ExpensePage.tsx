import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Button, Input, LoadingSpinner } from '../../components/UI';
import { apiService } from '../../services/api';
import { useAuthStore } from '../../store/useAuthStore';
import { Expense, ExpenseShare, TripMember } from '../../types';

interface ExpenseSummary {
  total_expenses: number;
  user_payments: Record<number, number>;
  user_shares: Record<number, number>;
  user_net: Record<number, number>;
  settlements: Settlement[];
}

interface Settlement {
  from_user_id: number;
  to_user_id: number;
  amount: number;
}

const ExpensePage: React.FC = () => {
  const { tripId } = useParams<{ tripId: string }>();
  const navigate = useNavigate();
  const { user } = useAuthStore();
  
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [summary, setSummary] = useState<ExpenseSummary | null>(null);
  const [members, setMembers] = useState<TripMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  
  // 新增支出表单
  const [newExpense, setNewExpense] = useState({
    amount: '',
    category: 'food',
    description: '',
    location: '',
    shares: [] as { user_id: number; amount: number }[]
  });

  useEffect(() => {
    if (tripId) {
      loadExpenses();
      loadTripMembers();
    }
  }, [tripId]);

  const loadExpenses = async () => {
    try {
      const response = await apiService.getTripExpenses(parseInt(tripId!));
      setExpenses(response.data);
      
      const summaryResponse = await apiService.getExpenseSummary(parseInt(tripId!));
      setSummary(summaryResponse.data);
    } catch (error) {
      console.error('加载支出记录失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadTripMembers = async () => {
    try {
      const response = await apiService.getTrip(parseInt(tripId!));
      setMembers(response.data.members);
    } catch (error) {
      console.error('加载成员信息失败:', error);
    }
  };

  const handleAddExpense = async () => {
    try {
      const expenseData = {
        ...newExpense,
        amount: parseFloat(newExpense.amount),
        shares: newExpense.shares.length > 0 ? newExpense.shares : 
          members.map(member => ({
            user_id: member.user_id,
            amount: parseFloat(newExpense.amount) / members.length
          }))
      };

      await apiService.createTripExpense(parseInt(tripId!), expenseData);
      
      // 重置表单
      setNewExpense({
        amount: '',
        category: 'food',
        description: '',
        location: '',
        shares: []
      });
      setShowAddForm(false);
      
      // 重新加载数据
      loadExpenses();
    } catch (error) {
      console.error('添加支出失败:', error);
    }
  };

  const getCategoryName = (category: string) => {
    const categories = {
      food: '餐饮',
      transport: '交通',
      accommodation: '住宿',
      entertainment: '娱乐',
      shopping: '购物',
      other: '其他'
    };
    return categories[category as keyof typeof categories] || category;
  };

  const getUserName = (userId: number) => {
    const member = members.find(m => m.user_id === userId);
    return member?.user?.username || `用户${userId}`;
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-800">记账分摊</h1>
        <Button onClick={() => navigate(`/trips/${tripId}`)}>
          返回旅行详情
        </Button>
      </div>

      {/* 支出汇总 */}
      {summary && (
        <Card className="mb-6">
          <h2 className="text-xl font-semibold mb-4">支出汇总</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-lg font-medium">总支出: ¥{summary.total_expenses}</p>
              <div className="mt-2">
                <h3 className="font-medium mb-2">各人支付:</h3>
                {Object.entries(summary.user_payments).map(([userId, amount]) => (
                  <p key={userId} className="text-sm">
                    {getUserName(parseInt(userId))}: ¥{amount}
                  </p>
                ))}
              </div>
            </div>
            <div>
              <h3 className="font-medium mb-2">分摊结算:</h3>
              {summary.settlements.length > 0 ? (
                summary.settlements.map((settlement, index) => (
                  <p key={index} className="text-sm text-red-600">
                    {getUserName(settlement.from_user_id)} → {getUserName(settlement.to_user_id)}: ¥{settlement.amount}
                  </p>
                ))
              ) : (
                <p className="text-sm text-green-600">无需分摊</p>
              )}
            </div>
          </div>
        </Card>
      )}

      {/* 添加支出按钮 */}
      <div className="mb-6">
        <Button onClick={() => setShowAddForm(!showAddForm)}>
          {showAddForm ? '取消' : '添加支出'}
        </Button>
      </div>

      {/* 添加支出表单 */}
      {showAddForm && (
        <Card className="mb-6">
          <h2 className="text-xl font-semibold mb-4">添加支出</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">金额</label>
              <Input
                type="number"
                value={newExpense.amount}
                onChange={(e) => setNewExpense({...newExpense, amount: e.target.value})}
                placeholder="输入金额"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">类别</label>
              <select
                value={newExpense.category}
                onChange={(e) => setNewExpense({...newExpense, category: e.target.value})}
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
              <label className="block text-sm font-medium mb-2">描述</label>
              <Input
                value={newExpense.description}
                onChange={(e) => setNewExpense({...newExpense, description: e.target.value})}
                placeholder="支出描述"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">地点</label>
              <Input
                value={newExpense.location}
                onChange={(e) => setNewExpense({...newExpense, location: e.target.value})}
                placeholder="支出地点"
              />
            </div>
          </div>
          <div className="mt-4">
            <Button onClick={handleAddExpense} disabled={!newExpense.amount}>
              添加支出
            </Button>
          </div>
        </Card>
      )}

      {/* 支出记录列表 */}
      <div className="space-y-4">
        <h2 className="text-xl font-semibold">支出记录</h2>
        {expenses.length === 0 ? (
          <Card>
            <p className="text-gray-500 text-center py-8">暂无支出记录</p>
          </Card>
        ) : (
          expenses.map((expense) => (
            <Card key={expense.id}>
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-lg font-semibold">¥{expense.amount}</span>
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                      {getCategoryName(expense.category)}
                    </span>
                  </div>
                  <p className="text-gray-700 mb-1">{expense.description}</p>
                  {expense.location && (
                    <p className="text-sm text-gray-500 mb-2">📍 {expense.location}</p>
                  )}
                  <p className="text-sm text-gray-500">
                    支付者: {getUserName(expense.paid_by)} | 
                    时间: {new Date(expense.created_at).toLocaleString()}
                  </p>
                </div>
              </div>
              
              {/* 分摊信息 */}
              <div className="mt-4 pt-4 border-t border-gray-200">
                <h4 className="font-medium mb-2">分摊情况:</h4>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {expense.shares.map((share, index) => (
                    <div key={index} className="text-sm">
                      <span className={share.is_paid ? 'line-through text-gray-500' : ''}>
                        {getUserName(share.user_id)}: ¥{share.amount}
                      </span>
                      {share.is_paid && <span className="text-green-600 ml-1">✓</span>}
                    </div>
                  ))}
                </div>
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};

export default ExpensePage;
