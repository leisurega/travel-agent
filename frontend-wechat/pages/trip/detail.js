// pages/trip/detail.js
Page({
  data: {
    tripId: null,
    trip: null,
    activeTab: 'plan',
    expenses: [],
    memories: [],
    loading: false
  },

  onLoad(options) {
    this.setData({ tripId: options.id })
    this.getTripDetail()
    this.getExpenses()
    this.getMemories()
  },

  getTripDetail() {
    const token = wx.getStorageSync('token')
    
    wx.request({
      url: `${getApp().globalData.baseUrl}/trips/${this.data.tripId}`,
      header: { 'Authorization': `Bearer ${token}` },
      success: (res) => {
        this.setData({ trip: res.data })
        getApp().globalData.currentTrip = res.data
      }
    })
  },

  getExpenses() {
    const token = wx.getStorageSync('token')
    
    wx.request({
      url: `${getApp().globalData.baseUrl}/trips/${this.data.tripId}/expenses`,
      header: { 'Authorization': `Bearer ${token}` },
      success: (res) => {
        this.setData({ expenses: res.data })
      }
    })
  },

  getMemories() {
    const token = wx.getStorageSync('token')
    
    wx.request({
      url: `${getApp().globalData.baseUrl}/trips/${this.data.tripId}/memories`,
      header: { 'Authorization': `Bearer ${token}` },
      success: (res) => {
        this.setData({ memories: res.data })
      }
    })
  },

  switchTab(e) {
    const tab = e.currentTarget.dataset.tab
    this.setData({ activeTab: tab })
  },

  addExpense() {
    wx.navigateTo({ url: `/pages/expense/add?tripId=${this.data.tripId}` })
  },

  addMemory() {
    wx.navigateTo({ url: `/pages/memory/add?tripId=${this.data.tripId}` })
  },

  askAI() {
    wx.navigateTo({ url: `/pages/ai/assistant?tripId=${this.data.tripId}` })
  }
})
