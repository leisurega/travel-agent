import { io, Socket } from 'socket.io-client';
import { WebSocketMessage } from 'types';

class WebSocketService {
  private socket: Socket | null = null;
  private tripId: number | null = null;
  private listeners: Map<string, Function[]> = new Map();

  connect(tripId: number): void {
    if (this.socket && this.tripId === tripId) {
      return; // 已经连接到同一个trip
    }

    this.disconnect(); // 断开之前的连接

    const baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
    this.socket = io(baseURL, {
      path: '/ws',
      transports: ['websocket'],
    });

    this.tripId = tripId;

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      // 加入特定的trip房间
      this.socket?.emit('join_trip', { trip_id: tripId });
    });

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
    });

    this.socket.on('expense_update', (data: WebSocketMessage) => {
      this.emit('expense_update', data);
    });

    this.socket.on('memory_update', (data: WebSocketMessage) => {
      this.emit('memory_update', data);
    });

    this.socket.on('plan_update', (data: WebSocketMessage) => {
      this.emit('plan_update', data);
    });

    this.socket.on('member_update', (data: WebSocketMessage) => {
      this.emit('member_update', data);
    });

    this.socket.on('error', (error: any) => {
      console.error('WebSocket error:', error);
      this.emit('error', error);
    });
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.tripId = null;
    }
  }

  // 发送消息
  sendMessage(type: string, data: any): void {
    if (this.socket && this.tripId) {
      const message: WebSocketMessage = {
        type: type as any,
        data,
        trip_id: this.tripId,
        user_id: this.getCurrentUserId(),
        timestamp: new Date().toISOString(),
      };
      this.socket.emit(type, message);
    }
  }

  // 发送支出更新
  sendExpenseUpdate(expenseData: any): void {
    this.sendMessage('expense_update', expenseData);
  }

  // 发送时光记录更新
  sendMemoryUpdate(memoryData: any): void {
    this.sendMessage('memory_update', memoryData);
  }

  // 发送计划更新
  sendPlanUpdate(planData: any): void {
    this.sendMessage('plan_update', planData);
  }

  // 发送成员更新
  sendMemberUpdate(memberData: any): void {
    this.sendMessage('member_update', memberData);
  }

  // 事件监听
  on(event: string, callback: Function): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event)?.push(callback);
  }

  // 移除事件监听
  off(event: string, callback?: Function): void {
    if (!this.listeners.has(event)) return;

    if (callback) {
      const callbacks = this.listeners.get(event) || [];
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    } else {
      this.listeners.delete(event);
    }
  }

  // 触发事件
  private emit(event: string, data: any): void {
    const callbacks = this.listeners.get(event) || [];
    callbacks.forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        console.error(`Error in WebSocket event handler for ${event}:`, error);
      }
    });
  }

  // 获取当前用户ID
  private getCurrentUserId(): number {
    const user = localStorage.getItem('user');
    if (user) {
      try {
        return JSON.parse(user).id;
      } catch {
        return 0;
      }
    }
    return 0;
  }

  // 检查连接状态
  isConnected(): boolean {
    return this.socket?.connected || false;
  }

  // 获取当前trip ID
  getCurrentTripId(): number | null {
    return this.tripId;
  }
}

export const websocketService = new WebSocketService();
export default websocketService;

