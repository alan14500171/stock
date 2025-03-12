import axios from 'axios'
import { useUserStore } from '@/stores/user'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'
import { ElMessage } from 'element-plus'

// 创建axios实例
const service = axios.create({
    timeout: 15000,
    withCredentials: true,
    headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/json',
    },
    // 添加重试配置
    retry: 3,
    retryDelay: 1000
})

// 请求拦截器
service.interceptors.request.use(
    config => {
        // 从localStorage获取token
        const token = localStorage.getItem('token')
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`
        }
        
        // 添加时间戳，避免GET请求缓存
        if (config.method === 'get' && !config.params) {
            config.params = {}
        }
        if (config.method === 'get' && !config.params._t) {
            config.params._t = Date.now()
        }
        
        return config
    },
    error => {
        return Promise.reject(error)
    }
)

// 响应拦截器
service.interceptors.response.use(
    response => {
        // 身份验证过期，跳转到登录页
        if (response.data && response.data.code === 401) {
            sessionStorage.clear()
            localStorage.removeItem('token')
            
            // 重新登录
            location.href = '/#/login'
            
            return Promise.reject(new Error('身份验证失败，请重新登录'))
        }
        
        return response.data
    },
    async error => {
        if (error.message.includes('timeout')) {
            // 请求超时
            ElMessage.error('请求超时，请重试')
            return Promise.reject(error)
        }
        
        // 获取错误状态码
        const status = error.response ? error.response.status : null
        
        if (status === 404) {
            ElMessage.error('请求的资源不存在')
        } else if (status === 401) {
            // 身份验证失败
            sessionStorage.clear()
            localStorage.removeItem('token')
            location.href = '/#/login'
        } else if (status === 403) {
            ElMessage.error('没有权限进行此操作')
        } else if (status >= 500) {
            ElMessage.error('服务器内部错误，请稍后再试')
        } else if (!error.response && error.message.includes('Network Error')) {
            // 网络错误且配置了自动重试
            if (error.config && error.config.retry) {
                error.config.retryCount = error.config.retryCount || 0
                
                // 是否达到最大重试次数
                if (error.config.retryCount < error.config.retry) {
                    // 增加重试次数
                    error.config.retryCount++
                    
                    // 创建新的Promise来处理重试
                    return new Promise(resolve => {
                        setTimeout(() => {
                            resolve(service(error.config))
                        }, error.config.retryDelay || 1000)
                    })
                }
            }
            
            ElMessage.error('网络错误，请检查您的网络连接')
        } else {
            ElMessage.error(error.message || '请求失败')
        }
        
        return Promise.reject(error)
    }
)

export default service 