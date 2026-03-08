import { request, requestModel, setAuth, clearAuth, resolveModelUrl, resolveApiUrl, getToken } from './request'

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

export function deleteStudy(id, studyId) {
  return request({ url: `/api/patients/${id}/studies/${studyId}`, method: 'DELETE' })
}

// 直传返回 fileId/filePath（如需）
export function uploadStudyFile(id, studyId, payload) {
  return request({ url: `/api/patients/${id}/studies/${studyId}/upload`, method: 'POST', data: payload })
}

export function downloadStudyVolume(studyId) {
  return request({ url: `/api/studies/${studyId}/download/volume`, method: 'GET' })
}

export function downloadStudyLabel(studyId) {
  return request({ url: `/api/studies/${studyId}/download/label`, method: 'GET' })
}

export function segmentStudyMultimodal(studyId, payload) {
  return request({ url: `/api/studies/${studyId}/segment/multimodal`, method: 'POST', data: payload })
}

// AI 结果/分区
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

export function upsertContour(id, payload) {
  return request({ url: `/api/patients/${id}/contours/upsert`, method: 'POST', data: payload })
}

// 文件与 3D 模型
export function getFile(fileId) {
  return request({ url: `/api/files/${fileId}`, method: 'GET' })
}

export function deleteFile(fileId) {
  return request({ url: `/api/files/${fileId}`, method: 'DELETE' })
}

export function getModel(studyId) {
  return request({ url: `/api/studies/${studyId}/model`, method: 'GET' })
}

export function submitCtvExpand(payload) {
  return requestModel({
    url: '/api/ctv/expand',
    method: 'POST',
    data: payload,
    showError: false
  })
}

// 智能体对话
export function sendAgentMessage(payload) {
  const data = typeof payload === 'string' ? { prompt: payload } : payload
  return requestModel({ url: '/api/agent/chat', method: 'POST', data })
}

export function sendAgentMessageWithImage(prompt, imagePath) {
  return new Promise((resolve, reject) => {
    const token = getToken()
    uni.uploadFile({
      url: resolveModelUrl('/api/agent/chat'),
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
// 社交/联合会诊
export function searchDoctors(keyword = '') {
  return request({ url: '/api/patients/social/doctors', method: 'GET', data: keyword ? { keyword } : {} })
}

export function listFriends() {
  return request({ url: '/api/patients/social/friends', method: 'GET' })
}

export function addFriend(friendId) {
  return request({ url: `/api/patients/social/friends/${friendId}`, method: 'POST' })
}

export function removeFriend(friendId) {
  return request({ url: `/api/patients/social/friends/${friendId}`, method: 'DELETE' })
}

export function listConsultations() {
  return request({ url: '/api/patients/social/consultations', method: 'GET' })
}

export function createConsultation(payload) {
  return request({ url: '/api/patients/social/consultations', method: 'POST', data: payload, showError: false })
}

export function listConsultationMembers(consultationId) {
  return request({ url: `/api/patients/social/consultations/${consultationId}/members`, method: 'GET' })
}

export function addConsultationMember(consultationId, doctorId) {
  return request({ url: `/api/patients/social/consultations/${consultationId}/members/${doctorId}`, method: 'POST' })
}

export function removeConsultationMember(consultationId, doctorId) {
  return request({ url: `/api/patients/social/consultations/${consultationId}/members/${doctorId}`, method: 'DELETE' })
}

export function listConsultationMessages(consultationId, params = {}) {
  const query = {}
  if (params.beforeId) query.beforeId = params.beforeId
  if (params.limit) query.limit = params.limit
  return request({ url: `/api/patients/social/consultations/${consultationId}/messages`, method: 'GET', data: query })
}

export function sendConsultationMessage(consultationId, payload) {
  return request({ url: `/api/patients/social/consultations/${consultationId}/messages`, method: 'POST', data: payload })
}

export function uploadConsultationAttachment(consultationId, filePath, options = {}) {
  return new Promise((resolve, reject) => {
    const token = getToken()
    const formData = {}
    if (options.messageType) {
      formData.messageType = options.messageType
    }
    uni.uploadFile({
      url: resolveApiUrl(`/api/patients/social/consultations/${consultationId}/attachments`),
      filePath,
      name: 'file',
      formData,
      header: token ? { Authorization: `Bearer ${token}` } : {},
      success: (res) => {
        if (res.statusCode < 200 || res.statusCode >= 300) {
          reject(new Error(`HTTP ${res.statusCode}`))
          return
        }
        try {
          const payload = JSON.parse(res.data)
          if (payload?.code !== 0) {
            reject(payload)
            return
          }
          resolve(payload.data)
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
  deleteStudy,
  uploadStudyFile,
  downloadStudyVolume,
  downloadStudyLabel,
  segmentStudyMultimodal,
  getContours,
  updateContourStatus,
  downloadContour,
  upsertContour,
  getFile,
  deleteFile,
  getModel,
  submitCtvExpand,
  sendAgentMessage,
  sendAgentMessageWithImage,
  getAgentHistory,
  searchDoctors,
  listFriends,
  addFriend,
  removeFriend,
  listConsultations,
  createConsultation,
  listConsultationMembers,
  addConsultationMember,
  removeConsultationMember,
  listConsultationMessages,
  sendConsultationMessage,
  uploadConsultationAttachment
}



