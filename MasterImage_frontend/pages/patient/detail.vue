<template>
  <view class="page">
    <view class="safe-area">
      <view class="card summary-card">
        <view class="row">
          <view>
            <text class="name">{{ patient.name || '未命名' }}</text>
            <text class="subtle">
              {{ patient.sex || '-' }} · {{ patient.age || '-' }} 岁 · {{ patient.stage || '未分期' }}
            </text>
          </view>
          <wd-button size="small" shape="round" type="default" plain @click="editProfile">编辑</wd-button>
        </view>
        <view class="meta">
          <text>ID {{ patient.id || '-' }}</text>
          <text>影像号 {{ patient.studyId || '-' }}</text>
        </view>
        <view class="meta">
          <text>{{ patient.diagnosis || '-' }}</text>
          <text>{{ patient.lastUpdate || '-' }}</text>
        </view>
        <view class="action-bar">
          <wd-button
            size="small"
            shape="round"
            :type="confirmButtonType"
            :plain="!isConfirmed"
            @click="confirmContour"
          >
            {{ confirmButtonText }}
          </wd-button>
          <wd-button size="small" shape="round" type="default" plain @click="open3D(patient.studyId)">
            查看 3D
          </wd-button>
          <wd-button size="small" shape="round" type="default" plain @click="exportRT">
            导出结构
          </wd-button>
        </view>
      </view>

      <view class="card ai-card">
        <view class="section-title">靶区 AI 结果</view>
        <wd-cell-group>
          <wd-cell title="GTV 初稿" is-link @click="open3D(patient.studyId)">
            <wd-tag slot="value" :type="gtvStatusType" plain>{{ gtvStatusText }}</wd-tag>
          </wd-cell>
          <wd-cell title="CTV 精修" :label="ctvLabel" is-link @click="open3D(patient.studyId)">
            <wd-tag slot="value" :type="ctvStatusType" plain>{{ ctvStatusText }}</wd-tag>
          </wd-cell>
          <wd-cell title="置信度热力图" is-link @click="open3D(patient.studyId)">
            <wd-tag slot="value" type="warning" plain>可查看</wd-tag>
          </wd-cell>
        </wd-cell-group>
      </view>

      <view class="card">
        <view class="section-title">影像序列</view>
        <view v-for="item in studies" :key="item.id" class="study">
          <view class="row">
            <view>
              <text class="label">{{ item.modality || '-' }}</text>
              <text class="subtle">{{ item.desc || '暂无描述' }}</text>
            </view>
            <wd-tag plain>{{ item.status || '处理中' }}</wd-tag>
          </view>
          <view class="meta">
            <text>序列号 {{ item.id }}</text>
            <text>{{ item.time || '-' }}</text>
          </view>
          <view class="action-bar">
            <wd-button size="small" shape="round" type="primary" plain @click="open3D(item.id)">
              浏览/切片
            </wd-button>
            <wd-button
              size="small"
              shape="round"
              type="default"
              plain
              :loading="uploading"
              :disabled="uploading"
              @click="handleUpload(item)"
            >
              替换影像
            </wd-button>
          </view>
        </view>
        <wd-button
          block
          shape="round"
          type="primary"
          plain
          :loading="uploading"
          :disabled="uploading"
          @click="handleUpload()"
        >
          上传新影像
        </wd-button>
      </view>
    </view>
  </view>
</template>

<script>
import {
  getPatientDetail,
  getStudiesByPatient,
  getContours,
  reviewPatient,
  downloadContour,
  createStudy
} from '../../common/api'
import { BASE_URL } from '../../common/request'

export default {
  data() {
    return {
      patientId: '',
      patient: {},
      studies: [],
      contours: [],
      uploading: false
    }
  },
  computed: {
    gtv() {
      return this.contours.find((c) => c.type === 'GTV') || {}
    },
    ctv() {
      return this.contours.find((c) => c.type === 'CTV') || {}
    },
    gtvStatusText() {
      return this.gtv.status || '待生成'
    },
    gtvStatusType() {
      return this.gtv.status === '已确认' ? 'success' : 'primary'
    },
    ctvStatusText() {
      return this.ctv.status || '待确认'
    },
    ctvStatusType() {
      return this.ctv.status === '已确认' ? 'success' : 'warning'
    },
    gtvLabel() {
      return this.gtv.storagePath || '生成后可查看/下载'
    },
    ctvLabel() {
      return this.ctv.storagePath || '等待医生精修'
    },
    heatmapLabel() {
      return this.ctv.confidenceMap || this.gtv.confidenceMap || '叠加置信度范围'
    },
    isConfirmed() {
      return this.patient.status === '已确认' || this.patient.confirmed === true
    },
    confirmButtonText() {
      return this.isConfirmed ? '已医生确认' : '医生确认方案'
    },
    confirmButtonType() {
      return this.isConfirmed ? 'success' : 'primary'
    }
  },
  async onLoad(query) {
    this.patientId = query.id || ''
    const cache = uni.getStorageSync('currentPatient')
    if (!this.patientId && cache) {
      this.patientId = cache.id
    }
    if (!this.patientId) {
      uni.showToast({ title: '缺少患者ID', icon: 'none' })
      return
    }
    await Promise.all([this.fetchPatient(), this.fetchStudies(), this.fetchContours()])
  },
  methods: {
    async fetchPatient() {
      try {
        this.patient = await getPatientDetail(this.patientId)
        uni.setStorageSync('currentPatient', this.patient)
      } catch (err) {
        console.error('getPatientDetail error', err)
      }
    },
    async fetchStudies() {
      try {
        const data = await getStudiesByPatient(this.patientId)
        this.studies = Array.isArray(data) ? data : []
      } catch (err) {
        console.error('getStudies error', err)
      }
    },
    async fetchContours() {
      try {
        const data = await getContours(this.patientId)
        this.contours = Array.isArray(data) ? data : []
      } catch (err) {
        console.error('getContours error', err)
      }
    },
    open3D(studyId) {
      if (!studyId) {
        uni.showToast({ title: '暂无序列', icon: 'none' })
        return
      }
      uni.navigateTo({
        url: `/pages/model/viewer?studyId=${studyId}`
      })
    },
    async confirmContour() {
      if (!this.patientId) return
      try {
        await reviewPatient(this.patientId, true)
        uni.showToast({ title: '已标记为医生确认', icon: 'success' })
        await this.fetchPatient()
      } catch (err) {
        console.error('reviewPatient error', err)
      }
    },
    async exportRT() {
      if (!this.gtv.id && !this.ctv.id) {
        uni.showToast({ title: '暂无可导出的结构', icon: 'none' })
        return
      }
      const target = this.ctv.id ? this.ctv : this.gtv
      try {
        const data = await downloadContour(this.patientId, target.id)
        const path = data.storagePath || data.modelPath || ''
        uni.showToast({ title: path ? '已返回下载路径' : '已完成请求', icon: 'none' })
        if (path) {
          uni.setClipboardData({ data: path, success: () => {} })
        }
      } catch (err) {
        console.error('downloadContour error', err)
      }
    },
    editProfile() {
      if (!this.patientId) return
      uni.navigateTo({ url: `/pages/patient/edit?id=${this.patientId}` })
    },
    async handleUpload(item) {
      if (this.uploading) return
      const existedStudyId = item?.id
      const file = await this.pickFile()
      if (!file || !file.path) return
      uni.showLoading({ title: '上传中...', mask: true })
      this.uploading = true
      try {
        let targetStudyId = existedStudyId
        if (!targetStudyId) {
          targetStudyId = await this.createStudyForUpload(file)
        }
        if (!targetStudyId) {
          uni.showToast({ title: '序列创建失败', icon: 'none' })
          return
        }
        await this.uploadToBackend(targetStudyId, file)
        await Promise.all([this.fetchStudies(), this.fetchPatient()])
      } catch (err) {
        console.error('handleUpload error', err)
      } finally {
        this.uploading = false
        uni.hideLoading()
      }
    },
    pickFile() {
      return new Promise((resolve) => {
        const choose = uni.chooseFile || uni.chooseMessageFile
        if (!choose) {
          uni.showToast({ title: '当前端暂不支持文件选择', icon: 'none' })
          resolve(null)
          return
        }
        choose({
          count: 1,
          type: 'all',
          success: (res) => {
            const file = res.tempFiles && res.tempFiles[0]
            if (!file) {
              resolve(null)
              return
            }
            const path = file.path || file.tempFilePath
            const name = file.name || (path ? path.split('/').pop() : '')
            resolve({ ...file, path, name })
          },
          fail: () => resolve(null)
        })
      })
    },
    async createStudyForUpload(file) {
      try {
        const data = await createStudy(this.patientId, {
          modality: this.guessModality(file?.name),
          desc: file?.name || '新影像'
        })
        return data?.id
      } catch (err) {
        console.error('createStudy error', err)
        return null
      }
    },
    guessModality(name = '') {
      const lower = (name || '').toLowerCase()
      if (lower.includes('mr') || lower.endsWith('.nii') || lower.endsWith('.nii.gz')) return 'MR'
      if (lower.includes('ct')) return 'CT'
      return 'DICOM'
    },
    extractExt(name = '') {
      const lower = (name || '').toLowerCase()
      if (lower.endsWith('.nii.gz')) {
        return 'nii.gz'
      }
      const parts = (name || '').split('.')
      return parts.length > 1 ? parts.pop() : ''
    },
    uploadToBackend(studyId, file) {
      const token = uni.getStorageSync('token') || ''
      const fileType = this.extractExt(file?.name)
      return new Promise((resolve, reject) => {
        uni.uploadFile({
          url: `${BASE_URL}/api/patients/${this.patientId}/studies/${studyId}/upload`,
          filePath: file.path,
          name: 'file',
          formData: { fileType },
          header: token ? { Authorization: `Bearer ${token}` } : {},
          success: (res) => {
            try {
              const payload = typeof res.data === 'string' ? JSON.parse(res.data) : res.data
              if (!payload || payload.code !== 0) {
                uni.showToast({ title: payload?.message || '上传失败', icon: 'none' })
                reject(payload)
                return
              }
              uni.showToast({ title: '上传成功', icon: 'success' })
              resolve(payload.data)
            } catch (e) {
              uni.showToast({ title: '上传响应异常', icon: 'none' })
              reject(e)
            }
          },
          fail: (err) => {
            uni.showToast({ title: '上传失败', icon: 'none' })
            reject(err)
          }
        })
      })
    }
  }
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: #f7f7f8;
}

.summary-card {
  margin-bottom: 18rpx;
}

.ai-card {
  padding-right: 0;
}

.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
}

.row > view:first-child {
  flex: 1;
  min-width: 0;
}

.row :deep(.wd-tag) {
  flex: 0 0 auto;
  white-space: nowrap;
  display: inline-flex;
  align-items: center;
}

.card :deep(.wd-cell) {
  align-items: center;
}

.card :deep(.wd-cell__title) {
  flex: 1;
  min-width: 0;
}

.card :deep(.wd-cell__label) {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card :deep(.wd-cell__value) {
  flex: 0 0 auto;
  white-space: nowrap;
}

.card :deep(.wd-cell__value .wd-tag) {
  white-space: nowrap;
  display: inline-flex;
  align-items: center;
}

.card :deep(.wd-cell__right) {
  margin-left: auto;
}

.ai-card :deep(.wd-cell) {
  padding-right: 0 !important;
}

.ai-card :deep(.wd-cell__right) {
  margin-right: 0 !important;
}

.ai-card :deep(.wd-cell__value) {
  margin-left: auto;
}

.name {
  display: block;
  font-size: 34rpx;
  font-weight: 700;
  color: #0c0d0f;
}

.meta {
  display: flex;
  justify-content: space-between;
  color: #6b7075;
  font-size: 26rpx;
  margin-top: 12rpx;
}

.study {
  padding: 10rpx 0 16rpx;
}

.label {
  color: #0c0d0f;
  font-weight: 650;
}
</style>
