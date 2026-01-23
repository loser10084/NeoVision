import { request, requestModel, setAuth, clearAuth, MODEL_BASE_URL, getToken } from './request'

// 认证
export function login(payload) {
  return request({ url: '/api/auth/login', method: 'POST', data: payload }).then((data) => {
    setAuth(data.token, data.user)
    return data
  })
}

export function registerUser(payload) {
  return request({ url: '/api/auth/register', method: 'POST', data: payload })
}

export function logout() {
  clearAuth()
}

// 患者
export function getPatients(keyword = '') {
  return request({ url: '/api/patients', method: 'GET', data: keyword ? { keyword } : {} })
}

export function createPatient(payload) {
  return request({ url: '/api/patients', method: 'POST', data: payload })
}

export function getPatientDetail(id) {
  return request({ url: `/api/patients/${id}`, method: 'GET' })
}

export function updatePatient(id, payload) {
  return request({ url: `/api/patients/${id}`, method: 'PUT', data: payload })
}

export function deletePatient(id) {
  return request({ url: `/api/patients/${id}`, method: 'DELETE' })
}

export function reviewPatient(id, confirmed = true) {
  return request({ url: `/api/patients/${id}/review`, method: 'POST', data: { confirmed } })
}

// 序列/影像
export function getStudiesByPatient(id) {
  return request({ url: `/api/patients/${id}/studies`, method: 'GET' })
}

export function createStudy(id, payload) {
  return request({ url: `/api/patients/${id}/studies`, method: 'POST', data: payload })
}

export function updateStudy(id, studyId, payload) {
  return request({ url: `/api/patients/${id}/studies/${studyId}`, method: 'PUT', data: payload })
}

// 直传返回 fileId/filePath（如需）
export function uploadStudyFile(id, studyId, payload) {
  return request({ url: `/api/patients/${id}/studies/${studyId}/upload`, method: 'POST', data: payload })
}

// AI 结果/靶区
export function getContours(id) {
  return request({ url: `/api/patients/${id}/contours`, method: 'GET' })
}

export function updateContourStatus(id, contourId, status) {
  return request({
    url: `/api/patients/${id}/contours/${contourId}`,
    method: 'PUT',
    data: { status }
  })
}

export function downloadContour(id, contourId) {
  return request({ url: `/api/patients/${id}/contours/${contourId}/download`, method: 'GET' })
}

// 文件与 3D 模型
export function getFile(fileId) {
  return request({ url: `/api/files/${fileId}`, method: 'GET' })
}

export function getModel(studyId) {
  return request({ url: `/api/studies/${studyId}/model`, method: 'GET' })
}

// 智能体交互
export function sendAgentMessage(payload) {
  const data = typeof payload === 'string' ? { prompt: payload } : payload
  return requestModel({ url: '/api/agent/chat', method: 'POST', data })
}

export function sendAgentMessageWithImage(prompt, imagePath) {
  return new Promise((resolve, reject) => {
    const token = getToken()
    uni.uploadFile({
      url: `${MODEL_BASE_URL}/api/agent/chat`,
      filePath: imagePath,
      name: 'image',
      formData: { prompt: prompt || '' },
      header: token ? { Authorization: `Bearer ${token}` } : {},
      success: (res) => {
        if (res.statusCode < 200 || res.statusCode >= 300) {
          reject(new Error(`HTTP ${res.statusCode}`))
          return
        }
        try {
          const payload = JSON.parse(res.data)
          if (payload?.error) {
            reject(payload)
            return
          }
          resolve(payload)
        } catch (err) {
          reject(err)
        }
      },
      fail: (err) => {
        reject(err)
      }
    })
  })
}

export function getAgentHistory() {
  return requestModel({ url: '/api/agent/history', method: 'GET' })
}

export default {
  login,
  registerUser,
  logout,
  getPatients,
  createPatient,
  getPatientDetail,
  updatePatient,
  deletePatient,
  reviewPatient,
  getStudiesByPatient,
  createStudy,
  updateStudy,
  uploadStudyFile,
  getContours,
  updateContourStatus,
  downloadContour,
  getFile,
  getModel,
  sendAgentMessage,
  sendAgentMessageWithImage,
  getAgentHistory
}
