import { ref } from 'vue'

// 创建一个全局消息队列
const messages = ref([])
let messageId = 0

// 消息提示组合式函数
export default function useMessage() {
  // 添加消息
  const addMessage = (text, type, duration = 3000) => {
    const id = messageId++
    
    // 添加消息到队列
    messages.value.push({
      id,
      text,
      type,
      show: true
    })
    
    // 设置定时器，自动移除消息
    setTimeout(() => {
      removeMessage(id)
    }, duration)
    
    return id
  }
  
  // 移除消息
  const removeMessage = (id) => {
    const index = messages.value.findIndex(msg => msg.id === id)
    
    if (index !== -1) {
      // 先设置 show 为 false，触发动画
      messages.value[index].show = false
      
      // 等待动画结束后移除消息
      setTimeout(() => {
        messages.value = messages.value.filter(msg => msg.id !== id)
      }, 300)
    }
  }
  
  // 成功消息
  const success = (text, duration) => {
    return addMessage(text, 'success', duration)
  }
  
  // 错误消息
  const error = (text, duration) => {
    return addMessage(text, 'danger', duration)
  }
  
  // 警告消息
  const warning = (text, duration) => {
    return addMessage(text, 'warning', duration)
  }
  
  // 信息消息
  const info = (text, duration) => {
    return addMessage(text, 'info', duration)
  }
  
  return {
    messages,
    success,
    error,
    warning,
    info,
    removeMessage
  }
} 