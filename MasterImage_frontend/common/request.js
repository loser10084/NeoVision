const DEFAULT_GATEWAY_URL = 'http://localhost:8080'
const DEFAULT_MODEL_URL = 'http://localhost:5001'
const AUTH_WHITE_LIST = ['/api/auth/login', '/api/auth/register']

function normalizeBaseUrl(value) {
  if (!value) return ''
  return String(value).replace(/\/+$/, '')
}

function readEnv(key) {
  try {
    return typeof process !== 'undefined' && process.env ? process.env[key] : ''
  } catch (err) {
    return ''
  }
}

const SERVICE_BASE_URLS = {
  gateway: normalizeBaseUrl(readEnv('VUE_APP_GATEWAY_URL') || DEFAULT_GATEWAY_URL),
  auth: normalizeBaseUrl(readEnv('VUE_APP_AUTH_URL')),
  patient: normalizeBaseUrl(readEnv('VUE_APP_PATIENT_URL')),
  study: normalizeBaseUrl(readEnv('VUE_APP_STUDY_URL')),
  model: normalizeBaseUrl(readEnv('VUE_APP_MODEL_URL') || DEFAULT_MODEL_URL)
}

export const BASE_URL = SERVICE_BASE_URLS.gateway
export const MODEL_BASE_URL = SERVICE_BASE_URLS.model

export function resolveServiceBase(name) {
  const base = SERVICE_BASE_URLS[name]
  return base || SERVICE_BASE_URLS.gateway
}

export function resolveApiBase(path) {
  const gateway = resolveServiceBase('gateway')
  if (!path || /^https?:\/\//i.test(path)) return gateway
  if (path.startsWith('/api/auth/')) return resolveServiceBase('auth') || gateway
  if (path.startsWith('/api/patients/') && /\/studies(\/|$)/.test(path)) {
    return resolveServiceBase('study') || gateway
  }
  if (path.startsWith('/api/studies/') || path.startsWith('/api/files/')) {
    return resolveServiceBase('study') || gateway
  }
  if (path.startsWith('/api/patients')) return resolveServiceBase('patient') || gateway
  return gateway
}

export function resolveApiUrl(path = '') {
  if (!path) return resolveServiceBase('gateway')
  if (/^https?:\/\//i.test(path)) return path
  const base = resolveApiBase(path)
  if (!base) return path
  return `${base}${path}`
}

export function resolveModelUrl(path = '') {
  if (!path) return resolveServiceBase('model')
  if (/^https?:\/\//i.test(path)) return path
  const base = resolveServiceBase('model')
  if (!base) return path
  return `${base}${path}`
}

export function resolveStudyResourceUrl(path = '') {
  if (!path) return ''
  if (/^https?:\/\//i.test(path)) return path
  const base = resolveServiceBase('study') || resolveServiceBase('gateway')
  if (!base) return path
  const normalized = path.startsWith('/') ? path : `/${path}`
  return `${base}${normalized}`
}

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

function parsePayload(res) {
  let payload = res && res.data
  if (typeof payload === 'string') {
    try {
      payload = JSON.parse(payload)
    } catch (err) {
      return payload
    }
  }
  return payload
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
      url: resolveApiUrl(url),
      method,
      data,
      header: buildHeaders(url, header),
      success: (res) => {
        const { statusCode } = res
        const payload = parsePayload(res)
        if (statusCode === 401 || payload?.code === 401) {
          handleAuthFailure()
          reject(new Error('Unauthorized'))
          return
        }
        if (!payload || payload.code === undefined) {
          console.error('Invalid response', { url, statusCode, payload, raw: res.data, header: res.header })
          if (statusCode >= 200 && statusCode < 300 && payload !== undefined) {
            resolve(payload)
            return
          }
          showError && uni.showToast({ title: `Invalid response (${statusCode})`, icon: 'none' })
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
      url: resolveModelUrl(url),
      method,
      data,
      header: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...header
      },
      success: (res) => {
        const { statusCode } = res
        const payload = parsePayload(res)
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
