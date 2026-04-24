// pages/ai/assistant.js
Page({
  data: {
    tripId: null,
    messages: [],
    inputValue: '',
    loading: false
  },

  onLoad(options) {
    this.setData({ tripId: options.tripId })
    this.initMessages()
  },

  initMessages() {
    this.setData({
      messages: [{
        type: 'ai',
        content: '你好！我是你的AI旅行助手，有什么可以帮助你的吗？',
        timestamp: new Date().toLocaleString()
      }]
    })
  },

  onInput(e) {
    this.setData({ inputValue: e.detail.value })
  },

  async sendMessage() {
    if (!this.data.inputValue.trim()) return
    
    const userMessage = {
      type: 'user',
      content: this.data.inputValue,
      timestamp: new Date().toLocaleString()
    }
    
    this.setData({
      messages: [...this.data.messages, userMessage],
      inputValue: '',
      loading: true
    })
    
    try {
      const response = await this.askAI(userMessage.content)
      const aiMessage = {
        type: 'ai',
        content: response.answer,
        timestamp: new Date().toLocaleString()
      }
      
      this.setData({
        messages: [...this.data.messages, aiMessage],
        loading: false
      })
    } catch (error) {
      wx.showToast({ title: 'AI回答失败', icon: 'none' })
      this.setData({ loading: false })
    }
  },

  askAI(question) {
    return new Promise((resolve, reject) => {
      const token = wx.getStorageSync('token')
      
      wx.request({
        url: `${getApp().globalData.baseUrl}/ai/ask/`,
        method: 'POST',
        header: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        data: { question },
        success: (res) => resolve(res.data),
        fail: reject
      })
    })
  }
})
