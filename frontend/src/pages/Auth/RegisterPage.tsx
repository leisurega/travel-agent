import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { Eye, EyeOff, Mail, Lock, User } from 'lucide-react';
import { useAuthStore } from 'store/useAuthStore';
import Button from 'components/UI/Button';
import Input from 'components/UI/Input';
import Card from 'components/UI/Card';
import toast from 'react-hot-toast';

interface RegisterForm {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
}

const RegisterPage: React.FC = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const { register: registerUser, isLoading, error, clearError } = useAuthStore();
  const navigate = useNavigate();

  const {
    register: registerField,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<RegisterForm>();

  const password = watch('password');

  const onSubmit = async (data: RegisterForm) => {
    try {
      clearError();
      await registerUser({
        username: data.username,
        email: data.email,
        password: data.password,
      });
      toast.success('注册成功！');
      navigate('/');
    } catch (error) {
      toast.error('注册失败，请重试');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-primary-100 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="w-16 h-16 bg-primary-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <span className="text-white font-bold text-xl">T</span>
          </div>
          <h2 className="text-3xl font-bold text-gray-900">创建账户</h2>
          <p className="mt-2 text-gray-600">
            已有账户？{' '}
            <Link to="/login" className="text-primary-600 hover:text-primary-500 font-medium">
              立即登录
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
              leftIcon={<User className="w-4 h-4" />}
              error={errors.username?.message}
              {...registerField('username', {
                required: '请输入用户名',
                minLength: {
                  value: 3,
                  message: '用户名至少3个字符',
                },
                maxLength: {
                  value: 20,
                  message: '用户名最多20个字符',
                },
                pattern: {
                  value: /^[a-zA-Z0-9_]+$/,
                  message: '用户名只能包含字母、数字和下划线',
                },
              })}
            />

            <Input
              label="邮箱"
              type="email"
              leftIcon={<Mail className="w-4 h-4" />}
              error={errors.email?.message}
              {...registerField('email', {
                required: '请输入邮箱',
                pattern: {
                  value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                  message: '请输入有效的邮箱地址',
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
              {...registerField('password', {
                required: '请输入密码',
                minLength: {
                  value: 6,
                  message: '密码至少6个字符',
                },
                pattern: {
                  value: /^(?=.*[a-zA-Z])(?=.*\d)/,
                  message: '密码必须包含字母和数字',
                },
              })}
            />

            <Input
              label="确认密码"
              type={showConfirmPassword ? 'text' : 'password'}
              leftIcon={<Lock className="w-4 h-4" />}
              rightIcon={
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              }
              error={errors.confirmPassword?.message}
              {...registerField('confirmPassword', {
                required: '请确认密码',
                validate: (value) =>
                  value === password || '两次输入的密码不一致',
              })}
            />

            <div className="flex items-center">
              <input
                id="agree-terms"
                name="agree-terms"
                type="checkbox"
                required
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <label htmlFor="agree-terms" className="ml-2 block text-sm text-gray-700">
                我同意{' '}
                <a href="#" className="text-primary-600 hover:text-primary-500">
                  服务条款
                </a>{' '}
                和{' '}
                <a href="#" className="text-primary-600 hover:text-primary-500">
                  隐私政策
                </a>
              </label>
            </div>

            <Button
              type="submit"
              className="w-full"
              loading={isLoading}
              disabled={isLoading}
            >
              {isLoading ? '注册中...' : '创建账户'}
            </Button>
          </form>
        </Card>
      </div>
    </div>
  );
};

export default RegisterPage;

