import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { MapPin, Calendar, FileText, Sparkles } from 'lucide-react';
import { useTripStore } from 'store/useTripStore';
import Button from 'components/UI/Button';
import Input from 'components/UI/Input';
import Card from 'components/UI/Card';
import toast from 'react-hot-toast';

interface CreateTripForm {
  title: string;
  description: string;
  destination: string;
  // 新增：用于AI规划的偏好设置（不会影响后端创建Trip接口）
  days?: number;
  interests?: string; // 逗号分隔
  avoids?: string;    // 逗号分隔
}

const CreateTripPage: React.FC = () => {
  const navigate = useNavigate();
  const { createTrip, isLoading } = useTripStore();

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm<CreateTripForm>();

  const onSubmit = async (data: CreateTripForm) => {
    try {
      // 将偏好设置暂存，后续在详情页也可使用
      const prefs = {
        days: data.days,
        interests: (data.interests || '')?.split(',').map(s => s.trim()).filter(Boolean),
        avoid: (data.avoids || '')?.split(',').map(s => s.trim()).filter(Boolean),
      };
      localStorage.setItem('trip_plan_prefs', JSON.stringify(prefs));

      await createTrip({
        title: data.title,
        description: data.description,
        destination: data.destination,
        days: data.days,
        interests: data.interests,
        avoids: data.avoids,
      } as any);
      toast.success('旅行创建成功！');
      navigate('/trips');
    } catch (error) {
      toast.error('创建旅行失败，请重试');
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div className="text-center">
        <div className="w-16 h-16 bg-primary-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <Sparkles className="w-8 h-8 text-white" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900">创建新旅行</h1>
        <p className="text-gray-600 mt-2">开始规划你的精彩旅程</p>
      </div>

      <Card>
        <form className="space-y-6" onSubmit={handleSubmit(onSubmit)}>
          <Input
            label="旅行标题"
            type="text"
            placeholder="例如：2024年日本樱花之旅"
            leftIcon={<FileText className="w-4 h-4" />}
            error={errors.title?.message}
            {...register('title', {
              required: '请输入旅行标题',
              minLength: {
                value: 2,
                message: '标题至少2个字符',
              },
              maxLength: {
                value: 50,
                message: '标题最多50个字符',
              },
            })}
          />

          <div>
            <label className="label">旅行描述</label>
            <textarea
              className="input min-h-[100px] resize-none"
              placeholder="描述这次旅行的目的、期望或特殊安排..."
              {...register('description', {
                maxLength: {
                  value: 500,
                  message: '描述最多500个字符',
                },
              })}
            />
            {errors.description && (
              <p className="error">{errors.description.message}</p>
            )}
          </div>

          <Input
            label="目的地"
            type="text"
            placeholder="例如：东京，日本"
            leftIcon={<MapPin className="w-4 h-4" />}
            error={errors.destination?.message}
            {...register('destination', {
              required: '请输入目的地',
              minLength: {
                value: 2,
                message: '目的地至少2个字符',
              },
            })}
          />

          {/* 天数单独一行 */}
          <Input
            label="天数（用于AI规划，必填）"
            type="number"
            placeholder="例如：3"
            error={errors.days?.message}
            {...register('days', {
              valueAsNumber: true,
              required: '请输入天数',
              min: { value: 1, message: '至少1天' },
              max: { value: 15, message: '最多15天' },
            })}
          />

          {/* 偏好设置（仅用于AI行程生成） */}
          {/* interests/avoids 每个字段单独一行 */}
          <Input
            label="旅行偏好 interests（逗号分隔）"
            type="text"
            placeholder="美食,购物,旅游景点"
            error={errors.interests?.message}
            {...register('interests')}
          />

          <Input
            label="旅行规避 avoids（逗号分隔）"
            type="text"
            placeholder="高强度运动,排队景点"
            error={errors.avoids?.message}
            {...register('avoids')}
          />

          <div className="flex flex-col sm:flex-row gap-4 pt-6">
            <Button
              type="button"
              variant="outline"
              className="flex-1"
              onClick={() => navigate('/trips')}
            >
              取消
            </Button>
            <Button
              type="submit"
              className="flex-1"
              loading={isLoading}
              disabled={isLoading}
            >
              {isLoading ? '创建中...' : '创建旅行'}
            </Button>
          </div>
        </form>
      </Card>

      {/* Tips */}
      <Card className="bg-blue-50 border-blue-200">
        <div className="flex items-start">
          <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center mr-3 flex-shrink-0">
            <Sparkles className="w-4 h-4 text-blue-600" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-blue-900 mb-1">创建提示</h3>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• 创建后可以邀请朋友一起规划旅行</li>
              <li>• 使用AI助手生成详细的旅行计划</li>
              <li>• 记录旅行中的每一笔支出和美好时光</li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default CreateTripPage;

