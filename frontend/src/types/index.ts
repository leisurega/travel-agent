// 用户相关类型
export interface User {
  id: number;
  username: string;
  email: string;
  avatar?: string;
  created_at: string;
  updated_at: string;
}

// 旅行相关类型
export interface Trip {
  id: number;
  title: string;
  description?: string;
  destination: string;
  start_date: string;
  end_date: string;
  status: 'planning' | 'active' | 'completed' | 'cancelled';
  created_by: number;
  created_at: string;
  updated_at: string;
  members: TripMember[];
  plan?: TripPlan;
  // 数量统计字段（用于列表显示）
  expense_count?: number;
  memory_count?: number;
  // 详细数据字段（用于详情页面）
  expenses?: Expense[];
  memories?: Memory[];
  // 后端返回的额外字段
  itinerary?: any;
  plans?: any[];
}

export interface TripMember {
  id: number;
  trip_id: number;
  user_id: number;
  role: 'owner' | 'member';
  joined_at: string;
  user: User;
}

export interface TripPlan {
  id: number;
  trip_id: number;
  daily_plans: DailyPlan[];
  total_estimated_cost: string;
  tips: string;
  created_at: string;
  updated_at: string;
}

export interface DailyPlan {
  day: number;
  morning: string;
  afternoon: string;
  evening: string;
  accommodation: string;
  transportation: string;
  estimated_cost: string;
}

// 支出相关类型
export interface Expense {
  id: number;
  trip_id: number;
  title: string;
  description?: string;
  amount: number;
  currency: string;
  category: string;
  paid_by: number;
  location?: string;
  created_at: string;
  updated_at: string;
  shares: ExpenseShare[];
  paid_by_user: User;
}

export interface ExpenseShare {
  id: number;
  expense_id: number;
  user_id: number;
  amount: number;
  is_paid: boolean;
  user: User;
}

// 时光记录类型
export interface Memory {
  id: number;
  trip_id: number;
  user_id: number;
  user?: User;
  title: string;
  content: string;
  location?: string;
  images: string[];
  tags: string[];
  date: string;
  created_at: string;
  updated_at?: string;
}

// AI相关类型
export interface AIQuestion {
  question: string;
  context?: string;
}

export interface AIAnswer {
  answer: string;
}

// WebSocket消息类型
export interface WebSocketMessage {
  type: 'expense_update' | 'memory_update' | 'plan_update' | 'member_update';
  data: any;
  trip_id: number;
  user_id: number;
  timestamp: string;
}

// API响应类型
export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  success: boolean;
}

// 表单类型
export interface CreateTripForm {
  title: string;
  description?: string;
  destination: string;
  // start/end 由后端默认值处理
  days?: number;
  interests?: string;
  avoids?: string;
}

export interface CreateExpenseForm {
  title: string;
  description?: string;
  amount: number;
  currency: string;
  category: string;
  paid_by: number;
  shares: { user_id: number; amount: number }[];
}

export interface CreateMemoryForm {
  title: string;
  content: string;
  location?: string;
  weather?: string;
  photos: File[];
}

// 仪表盘数据类型
export interface DashboardData {
  total_trips: number;
  active_trips: number;
  total_expenses: number;
  recent_memories: Memory[];
  expense_breakdown: { category: string; amount: number }[];
  member_activity: { user: User; memory_count: number; expense_count: number }[];
}

