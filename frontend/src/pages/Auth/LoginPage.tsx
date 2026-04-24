import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { Eye, EyeOff, Mail, Lock } from 'lucide-react';
import { useAuthStore } from 'store/useAuthStore';
import Button from 'components/UI/Button';
import Input from 'components/UI/Input';
import Card from 'components/UI/Card';
import toast from 'react-hot-toast';

interface LoginForm {
  username: string;
  password: string;
}

const LoginPage: React.FC = () => {
  const [showPassword, setShowPassword] = useState(false);
  const { login, isLoading, error, clearError } = useAuthStore();
  const navigate = useNavigate();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>();

  const onSubmit = async (data: LoginForm) => {
    try {
      clearError();
      await login(data);
      toast.success('登录成功！');
      navigate('/');
    } catch (error) {
      toast.error('登录失败，请检查用户名和密码');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-primary-100 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="w-16 h-16 bg-primary-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <span className="text-white font-bold text-xl">T</span>
          </div>
          <h2 className="text-3xl font-bold text-gray-900">登录账户</h2>
          <p className="mt-2 text-gray-600">
            还没有账户？{' '}
            <Link to="/register" className="text-primary-600 hover:text-primary-500 font-medium">
              立即注册
            </Link>
          </p>
        </div>

        <Card>
          <form className="space-y-6" onSubmit={handleSubmit(onSubmit)}>
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-600 text-sm">{error}</p>
              </div>
            )}

            <Input
              label="用户名"
              type="text"
              leftIcon={<Mail className="w-4 h-4" />}
              error={errors.username?.message}
              {...register('username', {
                required: '请输入用户名',
                minLength: {
                  value: 3,
                  message: '用户名至少3个字符',
                },
              })}
            />

            <Input
              label="密码"
              type={showPassword ? 'text' : 'password'}
              leftIcon={<Lock className="w-4 h-4" />}
              rightIcon={
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              }
              error={errors.password?.message}
              {...register('password', {
                required: '请输入密码',
                minLength: {
                  value: 6,
                  message: '密码至少6个字符',
                },
              })}
            />

            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <input
                  id="remember-me"
                  name="remember-me"
                  type="checkbox"
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-700">
                  记住我
                </label>
              </div>

              <div className="text-sm">
                <a href="#" className="text-primary-600 hover:text-primary-500">
                  忘记密码？
                </a>
              </div>
            </div>

            <Button
              type="submit"
              className="w-full"
              loading={isLoading}
              disabled={isLoading}
            >
              {isLoading ? '登录中...' : '登录'}
            </Button>
          </form>
        </Card>

        <div className="text-center">
          <p className="text-sm text-gray-600">
            登录即表示您同意我们的{' '}
            <a href="#" className="text-primary-600 hover:text-primary-500">
              服务条款
            </a>{' '}
            和{' '}
            <a href="#" className="text-primary-600 hover:text-primary-500">
              隐私政策
            </a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;

