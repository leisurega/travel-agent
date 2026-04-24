import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { 
  User, 
  Trip, 
  Expense, 
  Memory, 
  TripPlan, 
  CreateTripForm, 
  CreateExpenseForm, 
  CreateMemoryForm,
  AIQuestion,
  AIAnswer,
  DashboardData,
  ApiResponse 
} from 'types';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      // 默认指向 8000；如需自定义，可设置 REACT_APP_API_URL
      baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 请求拦截器 - 添加认证token
    this.api.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // 响应拦截器 - 处理错误
    this.api.interceptors.response.use(
      (response: AxiosResponse) => {
        return response;
      },
      (error) => {
        if (error.response?.status === 401) {
          // Token过期，清除本地存储并跳转到登录页
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // 用户相关API
  async createUser(userData: Partial<User>): Promise<ApiResponse<User>> {
    const response = await this.api.post('/users/', userData);
    return response.data;
  }

  async getUser(userId: number): Promise<ApiResponse<User>> {
    const response = await this.api.get(`/users/${userId}`);
    return response.data;
  }

  async getCurrentUser(): Promise<ApiResponse<User>> {
    const response = await this.api.get('/users/me');
    return response.data;
  }

  async getUsers(): Promise<ApiResponse<User[]>> {
    const response = await this.api.get('/users/');
    return response.data;
  }

  async updateUser(userId: number, userData: Partial<User>): Promise<ApiResponse<User>> {
    const response = await this.api.put(`/users/${userId}`, userData);
    return response.data;
  }

  // 旅行相关API
  async createTrip(tripData: CreateTripForm): Promise<ApiResponse<Trip>> {
    // 后端需要 name 字段，这里将前端的 title 映射为 name
    const payload: any = {
      name: (tripData as any).title,
      description: tripData.description,
      destination: tripData.destination,
      // 将偏好直接传给后端持久化
      days: (tripData as any).days,
      interests: (tripData as any).interests ? (tripData as any).interests.split(',').map((s:string)=>s.trim()).filter(Boolean) : [],
      avoids: (tripData as any).avoids ? (tripData as any).avoids.split(',').map((s:string)=>s.trim()).filter(Boolean) : [],
    };
    const response = await this.api.post('/trips/', payload);
    return response.data;
  }

  async getTrips(): Promise<ApiResponse<Trip[]>> {
    const response = await this.api.get('/trips/');
    return response.data;
  }

  async getTrip(tripId: number, options?: { with_itinerary?: boolean; interests?: string[]; avoid?: string[]; route_mode?: 'walking' | 'driving' }): Promise<ApiResponse<Trip>> {
    const params: any = {};
    if (options?.with_itinerary) params.with_itinerary = true;
    if (options?.interests?.length) params.interests = options.interests.join(',');
    if (options?.avoid?.length) params.avoid = options.avoid.join(',');
    if (options?.route_mode) params.route_mode = options.route_mode;
    const response = await this.api.get(`/trips/${tripId}`, { params });
    return response.data;
  }

  async updateTrip(tripId: number, tripData: Partial<Trip>): Promise<ApiResponse<Trip>> {
    const response = await this.api.put(`/trips/${tripId}`, tripData);
    return response.data;
  }

  async deleteTrip(tripId: number): Promise<ApiResponse<void>> {
    const response = await this.api.delete(`/trips/${tripId}`);
    return response.data;
  }

  async addTripMember(tripId: number, userId: number): Promise<ApiResponse<void>> {
    const response = await this.api.post(`/trips/${tripId}/members/`, { user_id: userId });
    return response.data;
  }

  async removeTripMember(tripId: number, userId: number): Promise<ApiResponse<void>> {
    const response = await this.api.delete(`/trips/${tripId}/members/${userId}`);
    return response.data;
  }

  // 支出相关API
  async createExpense(expenseData: CreateExpenseForm): Promise<ApiResponse<Expense>> {
    const response = await this.api.post('/expenses/', expenseData);
    return response.data;
  }

  async getTripExpenses(tripId: number): Promise<ApiResponse<Expense[]>> {
    const response = await this.api.get(`/trips/${tripId}/expenses/`);
    return response.data;
  }

  async getExpenseSummary(tripId: number): Promise<ApiResponse<any>> {
    const response = await this.api.get(`/trips/${tripId}/expenses/summary/`);
    return response.data;
  }

  // Memory APIs
  async getTripMemories(tripId: number): Promise<ApiResponse<Memory[]>> {
    const response = await this.api.get(`/trips/${tripId}/memories/`);
    return response.data;
  }

  async createTripMemory(tripId: number, memoryData: any): Promise<ApiResponse<Memory>> {
    const response = await this.api.post(`/trips/${tripId}/memories/`, memoryData);
    return response.data;
  }

  async getMemory(memoryId: number): Promise<ApiResponse<Memory>> {
    const response = await this.api.get(`/memories/${memoryId}`);
    return response.data;
  }

  async updateMemory(memoryId: number, memoryData: any): Promise<ApiResponse<Memory>> {
    const response = await this.api.put(`/memories/${memoryId}`, memoryData);
    return response.data;
  }

  async deleteMemory(memoryId: number): Promise<ApiResponse<void>> {
    const response = await this.api.delete(`/memories/${memoryId}`);
    return response.data;
  }

  async createTripExpense(tripId: number, expenseData: any): Promise<ApiResponse<Expense>> {
    const response = await this.api.post(`/trips/${tripId}/expenses/`, expenseData);
    return response.data;
  }

  async updateExpense(expenseId: number, expenseData: any): Promise<ApiResponse<Expense>> {
    const response = await this.api.put(`/expenses/${expenseId}`, expenseData);
    return response.data;
  }

  async deleteExpense(expenseId: number): Promise<ApiResponse<void>> {
    const response = await this.api.delete(`/expenses/${expenseId}`);
    return response.data;
  }

  async splitExpense(expenseId: number, splitData: { shares: { user_id: number; amount: number }[] }): Promise<ApiResponse<Expense>> {
    const response = await this.api.post(`/expenses/${expenseId}/split/`, splitData);
    return response.data;
  }

  // 时光记录API
  async createMemory(memoryData: CreateMemoryForm): Promise<ApiResponse<Memory>> {
    const formData = new FormData();
    formData.append('title', memoryData.title);
    formData.append('content', memoryData.content);
    if (memoryData.location) formData.append('location', memoryData.location);
    if (memoryData.weather) formData.append('weather', memoryData.weather);
    memoryData.photos.forEach((photo, index) => {
      formData.append(`photos`, photo);
    });

    const response = await this.api.post('/memories/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }


  // AI相关API
  async generateTripPlan(tripId: number, planRequest: { destination: string; days?: number; interests?: string[]; avoid?: string[]; route_mode?: 'walking'|'driving' }): Promise<ApiResponse<TripPlan>> {
    const response = await this.api.post(`/trips/${tripId}/plan/`, planRequest);
    return response.data;
  }

  async askAI(question: AIQuestion): Promise<ApiResponse<AIAnswer>> {
    const response = await this.api.post('/ai/ask/', question);
    return response.data;
  }

  // 仪表盘API
  async getTripDashboard(tripId: number): Promise<ApiResponse<DashboardData>> {
    const response = await this.api.get(`/trips/${tripId}/dashboard/`);
    return response.data;
  }

  // 认证相关
  async login(credentials: { username: string; password: string }): Promise<ApiResponse<{ token: string; user: User }>> {
    const response = await this.api.post('/auth/login/', credentials);
    return response.data;
  }

  async register(userData: { username: string; email: string; password: string }): Promise<ApiResponse<{ token: string; user: User }>> {
    const response = await this.api.post('/auth/register/', userData);
    return response.data;
  }

  async logout(): Promise<void> {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  }

  // 聊天机器人API
  async chatWithAI(message: string): Promise<ApiResponse<any>> {
    console.log('API Service - 发送请求到 /chat/test/');
    console.log('API Service - 请求数据:', { message });
    console.log('API Service - Base URL:', this.api.defaults.baseURL);
    
    try {
      // 增加超时时间到60秒，因为AI请求需要更长时间
      const response = await this.api.post('/chat/test/', { message }, { timeout: 60000 });
      console.log('API Service - 收到响应:', response);
      console.log('API Service - 响应状态:', response.status);
      console.log('API Service - 响应数据:', response.data);
      console.log('API Service - 响应数据类型:', typeof response.data);
      console.log('API Service - response.data.success:', response.data?.success);
      console.log('API Service - response.data.data:', response.data?.data);
      return response.data;
    } catch (error: any) {
      console.error('API Service - 请求失败:', error);
      console.error('API Service - 错误状态:', error.response?.status);
      console.error('API Service - 错误数据:', error.response?.data);
      console.error('API Service - 错误消息:', error.message);
      console.error('API Service - 错误类型:', typeof error);
      console.error('API Service - 错误堆栈:', error.stack);
      throw error;
    }
  }

  async mcpIntentExecute(body: { query: string; params?: Record<string, any>; mode?: string }): Promise<ApiResponse<any>> {
    try {
      // 首次拉起外部 MCP 服务器（npx 下载）可能较慢，增加超时
      const response = await this.api.post('/mcp/intent/execute', body, { timeout: 60000 });
      return response.data;
    } catch (error: any) {
      console.error('MCP Intent Execute - 请求失败:', error);
      throw error;
    }
  }

  async getChatMemories(): Promise<ApiResponse<any[]>> {
    const response = await this.api.get('/chat/memories/');
    return response.data;
  }

  // Weather API methods
  async getCurrentWeather(city: string, latitude?: number, longitude?: number): Promise<ApiResponse<any>> {
    try {
      const params = new URLSearchParams();
      if (city) params.append('city', city);
      if (latitude !== undefined) params.append('latitude', latitude.toString());
      if (longitude !== undefined) params.append('longitude', longitude.toString());
      
      const response = await this.api.get(`/weather/current?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Get Current Weather - 请求失败:', error);
      throw error;
    }
  }

  async getWeatherForecast(city: string, days: number = 7, latitude?: number, longitude?: number): Promise<ApiResponse<any>> {
    try {
      const params = new URLSearchParams();
      if (city) params.append('city', city);
      if (days) params.append('days', days.toString());
      if (latitude !== undefined) params.append('latitude', latitude.toString());
      if (longitude !== undefined) params.append('longitude', longitude.toString());
      
      const response = await this.api.get(`/weather/forecast?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Get Weather Forecast - 请求失败:', error);
      throw error;
    }
  }
}

export const apiService = new ApiService();
export default apiService;

