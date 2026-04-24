// app.js
App({
  globalData: {
    userInfo: null,
    currentTrip: null,
    baseUrl: 'http://localhost:8000'
  },

  onLaunch() {
    // 检查登录状态
    this.checkLoginStatus()
  },

  checkLoginStatus() {
    const token = wx.getStorageSync('token')
    if (token) {
      // 验证token有效性
      this.validateToken(token)
    }
  },

  validateToken(token) {
    wx.request({
      url: `${this.globalData.baseUrl}/users/me`,
      header: {
        'Authorization': `Bearer ${token}`
      },
      success: (res) => {
        if (res.statusCode === 200) {
          this.globalData.userInfo = res.data
        } else {
          wx.removeStorageSync('token')
        }
      },
      fail: () => {
        wx.removeStorageSync('token')
      }
    })
  }
})
