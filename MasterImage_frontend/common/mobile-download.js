import { resolveModelUrl } from './request'

const OPEN_DOCUMENT_EXT_SET = new Set(['doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'pdf'])

function isWebRuntime() {
  return typeof window !== 'undefined' && typeof document !== 'undefined'
}

function isAppPlusRuntime() {
  return typeof plus !== 'undefined' && !!plus.runtime
}

function normalizeUrl(url = '') {
  const raw = String(url || '').trim()
  if (!raw) return ''
  if (/^https?:\/\//i.test(raw)) return raw
  return resolveModelUrl(raw)
}

function safeDecode(value = '') {
  try {
    return decodeURIComponent(value)
  } catch (err) {
    return value
  }
}

function guessFilename(url = '', fallback = '') {
  const fromFallback = String(fallback || '').trim()
  if (fromFallback) return fromFallback
  const clean = String(url || '').split('?')[0].split('#')[0]
  const normalized = clean.replace(/\\/g, '/')
  const part = normalized.split('/').pop() || ''
  const decoded = safeDecode(part)
  return decoded || `download_${Date.now()}.bin`
}

function sanitizeFilename(name = '') {
  const raw = String(name || '').trim()
  const cleaned = raw.replace(/[\\/:*?"<>|]/g, '_')
  return cleaned || `download_${Date.now()}.bin`
}

function extractExt(name = '') {
  const value = String(name || '')
  const dot = value.lastIndexOf('.')
  if (dot < 0 || dot >= value.length - 1) return ''
  return value.slice(dot + 1).toLowerCase()
}

function downloadByUni(url, headers = {}) {
  return new Promise((resolve, reject) => {
    uni.downloadFile({
      url,
      header: headers || {},
      success: (res) => {
        if (typeof res.statusCode === 'number' && res.statusCode !== 200) {
          reject(new Error(`download status ${res.statusCode}`))
          return
        }
        const tempPath = res.tempFilePath || res.filePath || res.apFilePath || ''
        if (!tempPath) {
          reject(new Error('missing temp file path'))
          return
        }
        if (typeof uni.saveFile !== 'function') {
          resolve({ path: tempPath, fromPublicDir: false })
          return
        }
        uni.saveFile({
          tempFilePath: tempPath,
          success: (saveRes) => {
            resolve({ path: saveRes.savedFilePath || tempPath, fromPublicDir: false })
          },
          fail: () => {
            resolve({ path: tempPath, fromPublicDir: false })
          }
        })
      },
      fail: (err) => reject(err)
    })
  })
}

function downloadByPlus(url, filename, headers = {}) {
  if (!isAppPlusRuntime() || !plus.downloader || typeof plus.downloader.createDownload !== 'function') {
    return Promise.resolve(null)
  }
  const safeName = sanitizeFilename(guessFilename(url, filename))
  const saveTarget = `_downloads/${safeName}`
  return new Promise((resolve, reject) => {
    try {
      const task = plus.downloader.createDownload(
        url,
        { filename: saveTarget },
        (download, status) => {
          if (status === 200) {
            resolve({
              path: download?.filename || saveTarget,
              fromPublicDir: true
            })
            return
          }
          reject(new Error(`download status ${status}`))
        }
      )
      Object.keys(headers || {}).forEach((key) => {
        if (key && headers[key] !== undefined && headers[key] !== null) {
          task.setRequestHeader(String(key), String(headers[key]))
        }
      })
      task.start()
    } catch (err) {
      reject(err)
    }
  })
}

function tryOpenByUniDocument(path, filename = '') {
  if (typeof uni.openDocument !== 'function') return Promise.resolve(false)
  const ext = extractExt(filename || path)
  if (!OPEN_DOCUMENT_EXT_SET.has(ext)) return Promise.resolve(false)
  return new Promise((resolve) => {
    uni.openDocument({
      filePath: path,
      showMenu: true,
      success: () => resolve(true),
      fail: () => resolve(false)
    })
  })
}

function tryOpenByPlusRuntime(path) {
  if (!isAppPlusRuntime() || !plus.runtime || typeof plus.runtime.openFile !== 'function') {
    return Promise.resolve(false)
  }
  return new Promise((resolve) => {
    try {
      plus.runtime.openFile(
        path,
        {},
        () => resolve(true),
        () => resolve(false)
      )
    } catch (err) {
      resolve(false)
    }
  })
}

async function tryOpenDownloadedFile(path, filename = '') {
  if (!path) return false
  if (await tryOpenByUniDocument(path, filename)) return true
  return tryOpenByPlusRuntime(path)
}

export async function downloadWithMobileSupport(options = {}) {
  const {
    url,
    filename = '',
    loadingTitle = '下载中...',
    successTitle = '已下载',
    failTitle = '下载失败',
    headers = null,
    autoOpen = false
  } = options

  const targetUrl = normalizeUrl(url)
  if (!targetUrl) {
    uni.showToast({ title: failTitle, icon: 'none' })
    return null
  }

  if (isWebRuntime()) {
    window.open(targetUrl, '_blank')
    return { path: targetUrl, fromPublicDir: false, opened: false }
  }

  uni.showLoading({ title: loadingTitle, mask: true })
  try {
    let result = null
    if (isAppPlusRuntime()) {
      result = await downloadByPlus(targetUrl, filename, headers || {}).catch((err) => {
        console.error('plus downloader failed, fallback to uni.downloadFile', err)
        return null
      })
    }
    if (!result) {
      result = await downloadByUni(targetUrl, headers || {})
    }
    const opened = autoOpen ? await tryOpenDownloadedFile(result.path, filename) : false
    uni.hideLoading()
    const title = opened ? '已下载并打开' : (result.fromPublicDir ? '已下载到系统下载目录' : successTitle)
    uni.showToast({ title, icon: 'success' })
    return { ...result, opened }
  } catch (err) {
    console.error('downloadWithMobileSupport failed', err)
    uni.hideLoading()
    uni.showToast({ title: failTitle, icon: 'none' })
    return null
  }
}
