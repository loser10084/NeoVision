export const BASE_URL = 'http://localhost:8080'
export const MODEL_BASE_URL = 'http://localhost:5001'
const AUTH_WHITE_LIST = ['/api/auth/login', '/api/auth/register']

export function getToken() {
  return uni.getStorageSync('token') || ''
}

export function setAuth(token, user) {
  if (token) {
    uni.setStorageSync('token', token)
  }
  if (user) {
    uni.setStorageSync('userProfile', user)
  }
}

export function clearAuth() {
  uni.removeStorageSync('token')
  uni.removeStorageSync('userProfile')
}

function needAuth(url) {
  return !AUTH_WHITE_LIST.some((path) => url.startsWith(path))
}

function buildHeaders(url, extraHeaders = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...extraHeaders
  }
  if (needAuth(url)) {
    const token = getToken()
    if (token) {
      headers.Authorization = `Bearer ${token}`
    }
  }
  return headers
}

function handleAuthFailure() {
  clearAuth()
  uni.showModal({
    title: '登录失效',
    content: '凭证无效，请重新登录',
    confirmText: '去登录',
    showCancel: false,
    success: () => {
      uni.reLaunch({ url: '/pages/auth/login' })
    }
  })
}

export function request({ url, method = 'GET', data = {}, header = {}, showError = true }) {
  return new Promise((resolve, reject) => {
    uni.request({
      url: `${BASE_URL}${url}`,
      method,
      data,
      header: buildHeaders(url, header),
      success: (res) => {
        const { statusCode, data: payload } = res
        if (statusCode === 401 || payload?.code === 401) {
          handleAuthFailure()
          reject(new Error('Unauthorized'))
          return
        }
        if (!payload || payload.code === undefined) {
          showError && uni.showToast({ title: '接口返回异常', icon: 'none' })
          reject(new Error('Invalid response'))
          return
        }
        if (payload.code !== 0) {
          showError && uni.showToast({ title: payload.message || '请求失败', icon: 'none' })
          reject(payload)
          return
        }
        resolve(payload.data)
      },
      fail: (err) => {
        showError && uni.showToast({ title: '网络异常', icon: 'none' })
        reject(err)
      }
    })
  })
}

export function requestModel({ url, method = 'GET', data = {}, header = {}, showError = true }) {
  return new Promise((resolve, reject) => {
    const token = getToken()
    uni.request({
      url: `${MODEL_BASE_URL}${url}`,
      method,
      data,
      header: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...header
      },
      success: (res) => {
        const { statusCode, data: payload } = res
        if (statusCode < 200 || statusCode >= 300) {
          showError && uni.showToast({ title: 'model error', icon: 'none' })
          reject(new Error(`HTTP ${statusCode}`))
          return
        }
        if (payload?.error) {
          showError && uni.showToast({ title: payload.error, icon: 'none' })
          reject(payload)
          return
        }
        resolve(payload)
      },
      fail: (err) => {
        showError && uni.showToast({ title: 'network error', icon: 'none' })
        reject(err)
      }
    })
  })
}

export default {
  request,
  setAuth,
  clearAuth,
  requestModel
}
