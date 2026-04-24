import { create } from 'zustand';
import { Trip, Expense, Memory, TripPlan } from 'types';
import apiService from 'services/api';

interface TripState {
  trips: Trip[];
  currentTrip: Trip | null;
  expenses: Expense[];
  memories: Memory[];
  plan: TripPlan | null;
  isLoading: boolean;
  error: string | null;
  pendingExpenses: any[];
}

interface TripActions {
  // Trip actions
  fetchTrips: () => Promise<void>;
  fetchTrip: (tripId: number, generateAI?: boolean) => Promise<void>;
  createTrip: (tripData: any) => Promise<void>;
  updateTrip: (tripId: number, tripData: any) => Promise<void>;
  deleteTrip: (tripId: number) => Promise<void>;
  setCurrentTrip: (trip: Trip | null) => void;
  
  // Expense actions
  fetchExpenses: (tripId: number) => Promise<void>;
  createExpense: (expenseData: any) => Promise<void>;
  updateExpense: (expenseId: number, expenseData: any) => Promise<void>;
  deleteExpense: (expenseId: number) => Promise<void>;
  splitExpense: (expenseId: number, splitData: any) => Promise<void>;
  addPendingExpense: (expense: any) => void;
  clearPendingExpenses: () => void;
  
  // Memory actions
  fetchMemories: (tripId: number) => Promise<void>;
  createMemory: (tripId: number, memoryData: any) => Promise<void>;
  updateMemory: (memoryId: number, memoryData: any) => Promise<void>;
  deleteMemory: (memoryId: number) => Promise<void>;
  
  // Plan actions
  generatePlan: (tripId: number, planRequest: any) => Promise<void>;
  generateAIItinerary: (tripId: number) => Promise<void>;
  
  // Utility actions
  clearError: () => void;
  clearCurrentTrip: () => void;
}

type TripStore = TripState & TripActions;

export const useTripStore = create<TripStore>((set, get) => ({
  // State
  trips: [],
  currentTrip: null,
  expenses: [],
  memories: [],
  plan: null,
  isLoading: false,
  error: null,
  pendingExpenses: [],

  // Trip actions
  fetchTrips: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiService.getTrips();
      set({ trips: response.data, isLoading: false });
    } catch (error: any) {
      set({ 
        error: error.response?.data?.message || '获取旅行列表失败',
        isLoading: false 
      });
    }
  },

  fetchTrip: async (tripId: number, generateAI: boolean = false) => {
    set({ isLoading: true, error: null });
    try {
      // 默认只从数据库读取，不生成AI行程
      let options: any = {};
      
      // 只有明确要求时才生成AI行程
      if (generateAI) {
        let prefs: any = null;
        try { prefs = JSON.parse(localStorage.getItem('trip_plan_prefs') || 'null'); } catch {}
        options = {
          with_itinerary: true,
          interests: prefs?.interests || [],
          avoid: prefs?.avoid || [],
          route_mode: 'walking',
        };
      }
      
      const response = await apiService.getTrip(tripId, options);
      // 处理计划数据格式转换
      const tripData = response.data;
      let planData = null;
      
      if (tripData.itinerary && tripData.itinerary.days) {
        // 使用AI生成的itinerary数据
        planData = {
          id: 0,
          trip_id: tripId,
          daily_plans: tripData.itinerary.days.map((day: any) => {
            const attractions = day.attractions || [];
            const morningAttractions = attractions.slice(0, 2).map((a: any) => a.name).join('、');
            const afternoonAttractions = attractions.slice(2, 4).map((a: any) => a.name).join('、');
            const eveningAttractions = attractions.slice(4).map((a: any) => a.name).join('、');
            
            return {
              day: parseInt(day.day.replace('DAY ', '')),
              morning: morningAttractions || '待规划',
              afternoon: afternoonAttractions || '待规划',
              evening: eveningAttractions || '待规划',
              accommodation: '待安排',
              transportation: '待安排',
              estimated_cost: '待计算'
            };
          }),
          total_estimated_cost: '待计算',
          tips: 'AI智能推荐行程',
          created_at: tripData.created_at,
          updated_at: tripData.updated_at
        };
      } else if (tripData.plans && tripData.plans.length > 0) {
        // 将 plans 数组转换为 TripPlan 格式
        planData = {
          id: 0,
          trip_id: tripId,
          daily_plans: tripData.plans.map((plan: any) => {
            const activities = plan.plan_data?.activities || [];
            // 由于初始计划只有一个活动，我们将其作为上午活动
            const morningActivity = activities.find((a: any) => a.time.includes('09'))?.activity || '待规划';
            
            return {
              day: plan.day,
              morning: morningActivity,
              afternoon: '待规划',
              evening: '待规划',
              accommodation: '待安排',
              transportation: '待安排',
              estimated_cost: '待计算'
            };
          }),
          total_estimated_cost: '待计算',
          tips: '点击生成计划获取AI推荐',
          created_at: tripData.created_at,
          updated_at: tripData.updated_at
        };
      }
      
      console.log('Trip data:', tripData); // 添加调试日志
      console.log('Itinerary data:', tripData.itinerary); // 添加调试日志
      console.log('Plans data:', tripData.plans); // 添加调试日志
      console.log('Plan data:', planData); // 添加调试日志
      console.log('Plan daily_plans:', planData?.daily_plans); // 添加调试日志
      console.log('Plan exists:', !!planData); // 添加调试日志
      console.log('Daily plans exist:', !!(planData && planData.daily_plans)); // 添加调试日志
      
      set({ 
        currentTrip: tripData,
        plan: planData,
        isLoading: false 
      });
    } catch (error: any) {
      set({ 
        error: error.response?.data?.message || '获取旅行详情失败',
        isLoading: false 
      });
    }
  },

  createTrip: async (tripData: any) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiService.createTrip(tripData);
      const newTrip = response.data;
      set(state => ({
        trips: [...state.trips, newTrip],
        currentTrip: newTrip,
        isLoading: false
      }));
    } catch (error: any) {
      set({ 
        error: error.response?.data?.message || '创建旅行失败',
        isLoading: false 
      });
      throw error;
    }
  },

  updateTrip: async (tripId: number, tripData: any) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiService.updateTrip(tripId, tripData);
      const updatedTrip = response.data;
      set(state => ({
        trips: state.trips.map(trip => 
          trip.id === tripId ? updatedTrip : trip
        ),
        currentTrip: state.currentTrip?.id === tripId ? updatedTrip : state.currentTrip,
        isLoading: false
      }));
    } catch (error: any) {
      set({ 
        error: error.response?.data?.message || '更新旅行失败',
        isLoading: false 
      });
      throw error;
    }
  },

  deleteTrip: async (tripId: number) => {
    set({ isLoading: true, error: null });
    try {
      await apiService.deleteTrip(tripId);
      set(state => ({
        trips: state.trips.filter(trip => trip.id !== tripId),
        currentTrip: state.currentTrip?.id === tripId ? null : state.currentTrip,
        isLoading: false
      }));
    } catch (error: any) {
      set({ 
        error: error.response?.data?.message || '删除旅行失败',
        isLoading: false 
      });
      throw error;
    }
  },

  setCurrentTrip: (trip: Trip | null) => {
    set({ currentTrip: trip, plan: trip?.plan || null });
  },

  // Expense actions
  fetchExpenses: async (tripId: number) => {
    set({ isLoading: true, error: null });
    try {
      console.log('正在获取支出记录，tripId:', tripId);
      const response = await apiService.getTripExpenses(tripId);
      console.log('获取支出记录成功:', response);
      set({ expenses: response.data, isLoading: false });
    } catch (error: any) {
      console.error('获取支出记录失败:', error);
      console.error('错误详情:', error.response?.data);
      set({ 
        expenses: [],
        error: error.response?.data?.detail || error.response?.data?.message || '获取支出列表失败',
        isLoading: false 
      });
    }
  },

  createExpense: async (expenseData: any) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiService.createExpense(expenseData);
      const newExpense = response.data;
      set(state => ({
        expenses: [...state.expenses, newExpense],
        isLoading: false
      }));
    } catch (error: any) {
      set({ 
        error: error.response?.data?.message || '创建支出失败',
        isLoading: false 
      });
      throw error;
    }
  },

  updateExpense: async (expenseId: number, expenseData: any) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiService.updateExpense(expenseId, expenseData);
      const updatedExpense = response.data;
      set(state => ({
        expenses: state.expenses.map(expense => 
          expense.id === expenseId ? updatedExpense : expense
        ),
        isLoading: false
      }));
    } catch (error: any) {
      set({ 
        error: error.response?.data?.message || '更新支出失败',
        isLoading: false 
      });
      throw error;
    }
  },

  deleteExpense: async (expenseId: number) => {
    set({ isLoading: true, error: null });
    try {
      await apiService.deleteExpense(expenseId);
      set(state => ({
        expenses: state.expenses.filter(expense => expense.id !== expenseId),
        isLoading: false
      }));
    } catch (error: any) {
      set({ 
        error: error.response?.data?.message || '删除支出失败',
        isLoading: false 
      });
      throw error;
    }
  },

  splitExpense: async (expenseId: number, splitData: any) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiService.splitExpense(expenseId, splitData);
      const updatedExpense = response.data;
      set(state => ({
        expenses: state.expenses.map(expense => 
          expense.id === expenseId ? updatedExpense : expense
        ),
        isLoading: false
      }));
    } catch (error: any) {
      set({ 
        error: error.response?.data?.message || '分摊支出失败',
        isLoading: false 
      });
      throw error;
    }
  },

  // Memory actions
  fetchMemories: async (tripId: number) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiService.getTripMemories(tripId);
      set({ memories: response.data, isLoading: false });
    } catch (error: any) {
      set({ 
        memories: [],
        error: error.response?.data?.message || '获取时光记录失败',
        isLoading: false 
      });
    }
  },

  createMemory: async (tripId: number, memoryData: any) => {
    set({ isLoading: true, error: null });
    try {
      console.log('正在创建时光记录:', memoryData);
      const response = await apiService.createTripMemory(tripId, memoryData);
      console.log('创建时光记录成功:', response);
      const newMemory = response.data;
      set(state => ({
        memories: [newMemory, ...state.memories],
        isLoading: false
      }));
    } catch (error: any) {
      console.error('创建时光记录失败:', error);
      set({ 
        error: error.response?.data?.detail || error.response?.data?.message || '创建时光记录失败',
        isLoading: false 
      });
      throw error;
    }
  },

  updateMemory: async (memoryId: number, memoryData: any) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiService.updateMemory(memoryId, memoryData);
      const updatedMemory = response.data;
      set(state => ({
        memories: state.memories.map(memory => 
          memory.id === memoryId ? updatedMemory : memory
        ),
        isLoading: false
      }));
    } catch (error: any) {
      set({ 
        error: error.response?.data?.message || '更新时光记录失败',
        isLoading: false 
      });
      throw error;
    }
  },

  deleteMemory: async (memoryId: number) => {
    set({ isLoading: true, error: null });
    try {
      await apiService.deleteMemory(memoryId);
      set(state => ({
        memories: state.memories.filter(memory => memory.id !== memoryId),
        isLoading: false
      }));
    } catch (error: any) {
      set({ 
        error: error.response?.data?.message || '删除时光记录失败',
        isLoading: false 
      });
      throw error;
    }
  },

  // Plan actions
  generatePlan: async (tripId: number, planRequest: any) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiService.generateTripPlan(tripId, planRequest);
      const newPlan = response.data;
      set({ 
        plan: newPlan,
        isLoading: false 
      });
    } catch (error: any) {
      set({ 
        error: error.response?.data?.message || '生成旅行计划失败',
        isLoading: false 
      });
      throw error;
    }
  },

  generateAIItinerary: async (tripId: number) => {
    set({ isLoading: true, error: null });
    try {
      console.log('正在生成AI行程...');
      // 重新获取行程，这次要求生成AI行程
      await get().fetchTrip(tripId, true);
      console.log('AI行程生成成功');
    } catch (error: any) {
      console.error('生成AI行程失败:', error);
      set({ 
        error: error.response?.data?.message || '生成AI行程失败',
        isLoading: false 
      });
    }
  },

  // Utility actions
  clearError: () => {
    set({ error: null });
  },

  addPendingExpense: (expense: any) => {
    set(state => ({
      pendingExpenses: [...state.pendingExpenses, expense]
    }));
  },

  clearPendingExpenses: () => {
    set({ pendingExpenses: [] });
  },

  clearCurrentTrip: () => {
    set({ 
      currentTrip: null, 
      expenses: [], 
      memories: [], 
      plan: null,
      pendingExpenses: []
    });
  },
}));

