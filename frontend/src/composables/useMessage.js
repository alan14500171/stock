import { ref, h, render } from 'vue'
import MessageToast from '../components/MessageToast.vue'

const messageInstance = ref(null)

const createMessageInstance = () => {
  const container = document.createElement('div')
  const vnode = h(MessageToast)
  render(vnode, container)
  document.body.appendChild(container)
  messageInstance.value = vnode.component.exposed
}

const useMessage = () => {
  if (!messageInstance.value) {
    createMessageInstance()
  }

  return {
    show: (text, type = 'info', duration) => messageInstance.value.show(text, type, duration),
    success: (text, duration) => messageInstance.value.success(text, duration),
    error: (text, duration) => messageInstance.value.error(text, duration),
    info: (text, duration) => messageInstance.value.info(text, duration),
    warning: (text, duration) => messageInstance.value.warning(text, duration)
  }
}

export default useMessage 