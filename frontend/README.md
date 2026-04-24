# Travel Agent Frontend

基于React的智能旅游规划应用前端，支持多人协作、智能记账分摊、时光记录和AI问答助手。

## 技术栈

- **React 18** - 用户界面框架
- **TypeScript** - 类型安全
- **Tailwind CSS** - 样式框架
- **React Router** - 路由管理
- **Zustand** - 状态管理
- **React Query** - 数据获取和缓存
- **React Hook Form** - 表单处理
- **Socket.io** - WebSocket实时通信
- **Lucide React** - 图标库
- **React Hot Toast** - 通知组件

## 功能特性

### 🏠 首页
- 用户欢迎界面
- 旅行统计概览
- 最近旅行展示
- 快速操作入口

### 🔐 用户认证
- 用户注册/登录
- 表单验证
- 自动登录状态检查
- 受保护路由

### 🗺️ 旅行管理
- 创建新旅行
- 旅行列表展示
- 旅行详情页面
- 状态筛选和搜索

### 💰 支出管理
- 添加支出记录
- 智能分摊计算
- 支出分类管理
- 实时同步更新

### 📸 时光记录
- 记录旅行时光
- 照片上传
- 位置标记
- 天气信息

### 🤖 AI助手
- 智能旅行规划
- 问答助手
- RAG知识检索
- 个性化推荐

### 👥 多人协作
- 邀请旅行成员
- 实时数据同步
- WebSocket通信
- 权限管理

## 项目结构

```
src/
├── components/          # 可复用组件
│   ├── Layout/         # 布局组件
│   └── UI/             # 基础UI组件
├── pages/              # 页面组件
│   ├── Auth/           # 认证页面
│   ├── Home/           # 首页
│   └── Trips/          # 旅行相关页面
├── services/           # API服务
├── store/              # 状态管理
├── types/              # TypeScript类型定义
├── utils/              # 工具函数
└── hooks/              # 自定义Hooks
```

## 快速开始

### 安装依赖

```bash
npm install
```

### 环境配置

复制环境变量文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置API地址：

```env
REACT_APP_API_URL=http://localhost:8000
```

### 启动开发服务器

```bash
npm start
```

应用将在 http://localhost:3000 启动

### 构建生产版本

```bash
npm run build
```

## 开发指南

### 添加新页面

1. 在 `src/pages/` 下创建页面组件
2. 在 `src/App.tsx` 中添加路由
3. 更新导航菜单（如需要）

### 添加新组件

1. 在 `src/components/` 下创建组件
2. 导出组件和类型定义
3. 在需要的地方导入使用

### 状态管理

使用 Zustand 进行状态管理：

```typescript
import { useAuthStore } from '@/store/useAuthStore';

const { user, login, logout } = useAuthStore();
```

### API调用

使用封装的API服务：

```typescript
import apiService from '@/services/api';

const trips = await apiService.getTrips();
```

### WebSocket通信

使用WebSocket服务进行实时通信：

```typescript
import websocketService from '@/services/websocket';

websocketService.connect(tripId);
websocketService.on('expense_update', handleExpenseUpdate);
```

## 样式指南

### 使用Tailwind CSS

```jsx
<div className="bg-white rounded-lg shadow-sm p-6">
  <h2 className="text-xl font-semibold text-gray-900">标题</h2>
</div>
```

### 自定义组件样式

使用 `clsx` 进行条件样式：

```jsx
import { clsx } from 'clsx';

<button className={clsx(
  'btn',
  variant === 'primary' && 'btn-primary',
  disabled && 'opacity-50'
)}>
```

## 部署

### 构建优化

```bash
npm run build
```

### 环境变量

确保生产环境配置正确的API地址：

```env
REACT_APP_API_URL=https://your-api-domain.com
```

### 静态文件部署

构建后的文件在 `build/` 目录，可以部署到任何静态文件服务器。

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

MIT License

