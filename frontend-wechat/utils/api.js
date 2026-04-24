// utils/api.js
const baseUrl = getApp().globalData.baseUrl

const request = (options) => {
  return new Promise((resolve, reject) => {
    const token = wx.getStorageSync('token')
    
    wx.request({
      url: `${baseUrl}${options.url}`,
      method: options.method || 'GET',
      data: options.data,
      header: {
        'Authorization': token ? `Bearer ${token}` : '',
        'Content-Type': 'application/json',
        ...options.header
      },
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
        } else {
          reject(res)
        }
      },
      fail: reject
    })
  })
}

const api = {
  // 用户相关
  login: (data) => request({ url: '/auth/login', method: 'POST', data }),
  register: (data) => request({ url: '/auth/register', method: 'POST', data }),
  getUserInfo: () => request({ url: '/users/me' }),
  
  // 旅行相关
  getTrips: () => request({ url: '/trips/' }),
  getTrip: (id) => request({ url: `/trips/${id}` }),
  createTrip: (data) => request({ url: '/trips/', method: 'POST', data }),
  updateTrip: (id, data) => request({ url: `/trips/${id}`, method: 'PUT', data }),
  
  // 支出相关
  getExpenses: (tripId) => request({ url: `/trips/${tripId}/expenses` }),
  createExpense: (data) => request({ url: '/expenses/', method: 'POST', data }),
  splitExpense: (id, data) => request({ url: `/expenses/${id}/split`, method: 'POST', data }),
  
  // 时光记录相关
  getMemories: (tripId) => request({ url: `/trips/${tripId}/memories` }),
  createMemory: (data) => request({ url: '/memories/', method: 'POST', data }),
  
  // AI相关
  askAI: (question) => request({ url: '/ai/ask', method: 'POST', data: { question } }),
  generatePlan: (tripId, data) => request({ url: `/trips/${tripId}/plan`, method: 'POST', data }),
  
  // 仪表盘
  getDashboard: (tripId) => request({ url: `/trips/${tripId}/dashboard` })
}

module.exports = api
