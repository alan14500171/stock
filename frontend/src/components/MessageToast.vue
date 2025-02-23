<template>
  <div class="message-toast-container">
    <div v-for="message in messages" :key="message.id" class="message-toast" :class="message.type">
      <div class="message-toast-content">
        {{ message.text }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const messages = ref([])
let messageId = 0

const show = (text, type = 'info', duration = 3000) => {
  const id = messageId++
  const message = { id, text, type }
  messages.value.push(message)
  setTimeout(() => {
    const index = messages.value.findIndex(m => m.id === id)
    if (index !== -1) {
      messages.value.splice(index, 1)
    }
  }, duration)
}

// 导出方法供其他组件使用
defineExpose({
  show,
  success: (text) => show(text, 'success'),
  error: (text) => show(text, 'error'),
  info: (text) => show(text, 'info'),
  warning: (text) => show(text, 'warning')
})
</script>

<style scoped>
.message-toast-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 10px;
  pointer-events: none;
}

.message-toast {
  padding: 12px 24px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.7);
  color: #fff;
  font-size: 14px;
  line-height: 1.5;
  transition: all 0.3s;
  animation: slideIn 0.3s;
  max-width: 350px;
  box-shadow: 0 3px 6px -4px rgba(0, 0, 0, 0.12),
              0 6px 16px 0 rgba(0, 0, 0, 0.08),
              0 9px 28px 8px rgba(0, 0, 0, 0.05);
}

.message-toast.success {
  background: rgba(40, 167, 69, 0.9);
}

.message-toast.error {
  background: rgba(220, 53, 69, 0.9);
}

.message-toast.warning {
  background: rgba(255, 193, 7, 0.9);
}

.message-toast.info {
  background: rgba(23, 162, 184, 0.9);
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(100%);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}
</style> 