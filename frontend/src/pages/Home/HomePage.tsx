import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Plus, MapPin, Users, DollarSign, Calendar, Sparkles } from 'lucide-react';
import { useAuthStore } from 'store/useAuthStore';
import { useTripStore } from 'store/useTripStore';
import Card from 'components/UI/Card';
import Button from 'components/UI/Button';
import LoadingSpinner from 'components/UI/LoadingSpinner';

const HomePage: React.FC = () => {
  const { user, isAuthenticated } = useAuthStore();
  const { trips, isLoading, fetchTrips } = useTripStore();

  useEffect(() => {
    if (isAuthenticated) {
      fetchTrips();
    }
  }, [isAuthenticated, fetchTrips]);

  const recentTrips = trips.slice(0, 3);
  const activeTrips = trips.filter(trip => trip.status === 'active');

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-primary-50 to-primary-100 flex items-center justify-center">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <div className="mb-8">
            <div className="w-20 h-20 bg-primary-600 rounded-2xl flex items-center justify-center mx-auto mb-6">
              <Sparkles className="w-10 h-10 text-white" />
            </div>
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              智能旅游规划助手
            </h1>
            <p className="text-xl text-gray-600 mb-8">
              基于AI的智能旅游规划和管理应用，支持多人协作、智能记账分摊、时光记录
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 mb-8">
            <Card className="text-center">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <MapPin className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="text-lg font-semibold mb-2">AI智能规划</h3>
              <p className="text-gray-600">使用通义千问大模型生成个性化旅行计划</p>
            </Card>

            <Card className="text-center">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <Users className="w-6 h-6 text-green-600" />
              </div>
              <h3 className="text-lg font-semibold mb-2">多人协作</h3>
              <p className="text-gray-600">实时同步旅行计划更新，多人同时编辑</p>
            </Card>

            <Card className="text-center">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <DollarSign className="w-6 h-6 text-purple-600" />
              </div>
              <h3 className="text-lg font-semibold mb-2">智能记账</h3>
              <p className="text-gray-600">支持多种分摊方式，自动计算每人应付金额</p>
            </Card>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/register">
              <Button size="lg" className="w-full sm:w-auto">
                立即注册
              </Button>
            </Link>
            <Link to="/login">
              <Button variant="outline" size="lg" className="w-full sm:w-auto">
                已有账号登录
              </Button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-800 rounded-2xl p-8 text-white">
        <h1 className="text-3xl font-bold mb-2">
          欢迎回来，{user?.username}！
        </h1>
        <p className="text-primary-100 text-lg">
          准备好开始新的冒险了吗？
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <div className="flex items-center">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <Calendar className="w-6 h-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-2xl font-bold text-gray-900">{trips.length}</p>
              <p className="text-gray-600">总旅行数</p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <MapPin className="w-6 h-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-2xl font-bold text-gray-900">{activeTrips.length}</p>
              <p className="text-gray-600">进行中</p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
              <Users className="w-6 h-6 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-2xl font-bold text-gray-900">
                {trips.reduce((acc, trip) => acc + trip.members.length, 0)}
              </p>
              <p className="text-gray-600">旅行伙伴</p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center">
            <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
              <DollarSign className="w-6 h-6 text-orange-600" />
            </div>
            <div className="ml-4">
              <p className="text-2xl font-bold text-gray-900">
                {trips.reduce((acc, trip) => acc + (trip.expense_count || 0), 0)}
              </p>
              <p className="text-gray-600">支出记录</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Recent Trips */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">最近的旅行</h2>
        <Link to="/trips">
          <Button variant="outline">查看全部</Button>
        </Link>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" text="加载中..." />
        </div>
      ) : recentTrips.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {recentTrips.map((trip) => (
            <Link key={trip.id} to={`/trips/${trip.id}`}>
              <Card hover className="h-full">
                <div className="flex items-start justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900 line-clamp-1">
                    {trip.title}
                  </h3>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                    trip.status === 'active' 
                      ? 'bg-green-100 text-green-800'
                      : trip.status === 'planning'
                      ? 'bg-blue-100 text-blue-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {trip.status === 'active' ? '进行中' : 
                     trip.status === 'planning' ? '规划中' : '已完成'}
                  </span>
                </div>
                
                <div className="space-y-2 mb-4">
                  <div className="flex items-center text-gray-600">
                    <MapPin className="w-4 h-4 mr-2" />
                    <span className="text-sm">{trip.destination}</span>
                  </div>
                  <div className="flex items-center text-gray-600">
                    <Calendar className="w-4 h-4 mr-2" />
                    <span className="text-sm">
                      {new Date(trip.start_date).toLocaleDateString()} - 
                      {new Date(trip.end_date).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="flex items-center text-gray-600">
                    <Users className="w-4 h-4 mr-2" />
                    <span className="text-sm">{trip.members.length} 位成员</span>
                  </div>
                </div>

                {trip.description && (
                  <p className="text-gray-600 text-sm line-clamp-2">
                    {trip.description}
                  </p>
                )}
              </Card>
            </Link>
          ))}
        </div>
      ) : (
        <Card className="text-center py-12">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <MapPin className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">还没有旅行计划</h3>
          <p className="text-gray-600 mb-6">创建你的第一个旅行计划，开始精彩的旅程！</p>
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

export default HomePage;

