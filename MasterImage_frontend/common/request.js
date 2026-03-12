const AUTH_WHITE_LIST = ['/api/auth/login', '/api/auth/register']
const RUNTIME_SERVICE_URLS_KEY = 'runtime_service_urls'

const FALLBACK_GATEWAY_URL = 'http://192.168.1.100:8080'
const FALLBACK_MODEL_URL = 'http://192.168.1.100:5001'

function normalizeBaseUrl(value) {
  if (!value) return ''
  return String(value).trim().replace(/\/+$/, '')
}

function readEnv(key) {
  try {
    return typeof process !== 'undefined' && process.env ? process.env[key] : ''
  } catch (err) {
    return ''
  }
}

const ENV_SERVICE_BASE_URLS = {
  gateway: normalizeBaseUrl(readEnv('VUE_APP_GATEWAY_URL')),
  auth: normalizeBaseUrl(readEnv('VUE_APP_AUTH_URL')),
  patient: normalizeBaseUrl(readEnv('VUE_APP_PATIENT_URL')),
  study: normalizeBaseUrl(readEnv('VUE_APP_STUDY_URL')),
  model: normalizeBaseUrl(readEnv('VUE_APP_MODEL_URL'))
}

function readRuntimeServiceCache() {
  try {
    const cache = uni.getStorageSync(RUNTIME_SERVICE_URLS_KEY)
    if (!cache || typeof cache !== 'object') return {}
    return cache
  } catch (err) {
    return {}
  }
}

export function getRuntimeServiceUrls() {
  const cache = readRuntimeServiceCache()
  return {
    gatewayUrl: normalizeBaseUrl(cache.gatewayUrl),
    modelUrl: normalizeBaseUrl(cache.modelUrl),
    updatedAt: Number(cache.updatedAt || 0)
  }
}

export function setRuntimeServiceUrls(payload = {}) {
  const next = {
    gatewayUrl: normalizeBaseUrl(payload.gatewayUrl),
    modelUrl: normalizeBaseUrl(payload.modelUrl),
    updatedAt: Date.now()
  }
  uni.setStorageSync(RUNTIME_SERVICE_URLS_KEY, next)
  return next
}

export function clearRuntimeServiceUrls() {
  uni.removeStorageSync(RUNTIME_SERVICE_URLS_KEY)
}

function buildServiceBaseUrls() {
  const runtime = getRuntimeServiceUrls()

  const gateway = runtime.gatewayUrl || ENV_SERVICE_BASE_URLS.gateway || FALLBACK_GATEWAY_URL
  const model = runtime.modelUrl || ENV_SERVICE_BASE_URLS.model || FALLBACK_MODEL_URL

  return {
    gateway,
    auth: ENV_SERVICE_BASE_URLS.auth || gateway,
    patient: ENV_SERVICE_BASE_URLS.patient || gateway,
    study: ENV_SERVICE_BASE_URLS.study || gateway,
    model
  }
}

export function getEffectiveServiceUrls() {
  const urls = buildServiceBaseUrls()
  return {
    gatewayUrl: urls.gateway,
    modelUrl: urls.model
  }
}

export function resolveServiceBase(name) {
  const urls = buildServiceBaseUrls()
  return urls[name] || urls.gateway
}

export function resolveApiBase(path) {
  const gateway = resolveServiceBase('gateway')
  if (!path || /^https?:\/\//i.test(path)) return gateway
  if (path.startsWith('/api/auth/')) return resolveServiceBase('auth')
  if (path.startsWith('/api/patients/') && /\/studies(\/|$)/.test(path)) {
    return resolveServiceBase('study')
  }
  if (path.startsWith('/api/studies/') || path.startsWith('/api/files/')) {
    return resolveServiceBase('study')
  }
  if (path.startsWith('/api/patients')) return resolveServiceBase('patient')
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

export const BASE_URL = resolveServiceBase('gateway')
export const MODEL_BASE_URL = resolveServiceBase('model')

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

function isAuthWhiteUrl(url = '') {
  const target = String(url || '')
  return AUTH_WHITE_LIST.some((path) => target.startsWith(path))
}

function needAuth(url) {
  return !isAuthWhiteUrl(url)
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
          if (!isAuthWhiteUrl(url)) {
            handleAuthFailure()
            reject(new Error('Unauthorized'))
            return
          }
          const authErr = payload && typeof payload === 'object' ? payload : { code: 401, message: '账号或密码错误' }
          showError && uni.showToast({ title: authErr.message || '账号或密码错误', icon: 'none' })
          reject(authErr)
          return
        }
        if (!payload || payload.code === undefined) {
          console.error('Invalid response', { url, statusCode, payload, raw: res.data, header: res.header })
          if (statusCode >= 200 && statusCode < 300 && payload !== undefined) {
            resolve(payload)
            return
          }
          showError && uni.showToast({ title: `响应异常 (${statusCode})`, icon: 'none' })
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
          showError && uni.showToast({ title: '模型服务异常', icon: 'none' })
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
        showError && uni.showToast({ title: '网络异常', icon: 'none' })
        reject(err)
      }
    })
  })
}

export default {
  request,
  setAuth,
  clearAuth,
  requestModel,
  getRuntimeServiceUrls,
  setRuntimeServiceUrls,
  clearRuntimeServiceUrls,
  getEffectiveServiceUrls
}
