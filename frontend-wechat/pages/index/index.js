// pages/index/index.js
Page({
  data: {
    userInfo: null,
    trips: [],
    loading: false
  },

  onLoad() {
    this.getUserInfo()
    this.getTrips()
  },

  getUserInfo() {
    const userInfo = getApp().globalData.userInfo
    if (userInfo) {
      this.setData({ userInfo })
    }
  },

  getTrips() {
    this.setData({ loading: true })
    const token = wx.getStorageSync('token')
    
    wx.request({
      url: `${getApp().globalData.baseUrl}/trips/`,
      header: { 'Authorization': `Bearer ${token}` },
      success: (res) => {
        this.setData({ 
          trips: res.data,
          loading: false 
        })
      },
      fail: () => {
        this.setData({ loading: false })
        wx.showToast({ title: '获取旅行列表失败', icon: 'none' })
      }
    })
  },

  createTrip() {
    wx.navigateTo({ url: '/pages/trip/create' })
  },

  viewTrip(e) {
    const tripId = e.currentTarget.dataset.id
    wx.navigateTo({ url: `/pages/trip/detail?id=${tripId}` })
  }
})
