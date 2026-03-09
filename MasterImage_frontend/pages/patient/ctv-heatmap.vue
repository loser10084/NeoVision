<template>
  <view class="page">
    <view class="safe-area ctv-area">
      <view class="ctv-hero">
        <view class="hero-main">
          <view>
            <text class="hero-title">{{ '置信度热力图工作台' }}</text>
            <text class="hero-subtitle">{{ '基于多模态分割结果生成置信度分布热图' }}</text>
          </view>
          <view class="hero-badge">AI</view>
        </view>
        <view class="hero-metrics">
          <view class="metric-item">
            <text class="metric-value">{{ activeStudyId || '-' }}</text>
            <text class="metric-label">{{ '当前序列' }}</text>
          </view>
          <view class="metric-item">
            <text class="metric-value">{{ readyModalityCount }}/{{ modalityOrder.length }}</text>
            <text class="metric-label">{{ '模态就绪' }}</text>
          </view>
          <view class="metric-item">
            <text class="metric-value">{{ heatmapUrl ? '已生成' : '未生成' }}</text>
            <text class="metric-label">{{ '热力图状态' }}</text>
          </view>
        </view>
      </view>

      <view class="card block-card">
        <view class="section-header section-header--edge">
          <text class="section-title">{{ '序列与模态检查' }}</text>
          <button class="mi-btn mi-btn--ghost" @click="openStudyPicker">{{ '切换序列' }}</button>
        </view>
        <view class="study-modalities">
          <view v-for="modality in modalityOrder" :key="modality" class="modality-item">
            <view class="modality-left">
              <view class="modality-dot"></view>
              <text class="label">{{ modalityLabel(modality) }}</text>
            </view>
            <text class="status-pill" :class="`status-pill--${modalityTagType(activeStudyId, modality)}`">
              {{ modalityTagText(activeStudyId, modality) }}
            </text>
          </view>
        </view>
        <view class="hint-bar">
          <text class="subtle">{{ '全部模态就绪后可生成热力图，用于医生快速评估分割置信区域。' }}</text>
        </view>
      </view>

      <view class="card block-card">
        <view class="section-header">
          <text class="section-title">{{ '热力图生成' }}</text>
          <text class="status-pill" :class="heatmapUrl ? 'status-pill--success' : 'status-pill--warning'">
            {{ heatmapUrl ? '可下载' : '待生成' }}
          </text>
        </view>

        <view class="workflow-strip">
          <view class="flow-step">
            <text class="flow-index">1</text>
            <text class="flow-text">{{ '检查模态' }}</text>
          </view>
          <view class="flow-link"></view>
          <view class="flow-step">
            <text class="flow-index">2</text>
            <text class="flow-text">{{ '生成热图' }}</text>
          </view>
          <view class="flow-link"></view>
          <view class="flow-step">
            <text class="flow-index">3</text>
            <text class="flow-text">{{ '下载归档' }}</text>
          </view>
        </view>

        <view class="segment-actions">
          <button class="mi-btn mi-btn--primary" :disabled="processing || !hasAllModalities" @click="generateHeatmap">
            {{ processing ? '生成中...' : '生成热力图' }}
          </button>
          <button class="mi-btn mi-btn--ghost" :disabled="!heatmapUrl" @click="downloadHeatmap">{{ '下载热力图' }}</button>
        </view>

        <view v-if="heatmapUrl" class="preview">
          <image :src="heatmapUrl" mode="widthFix" class="heatmap-image" />
        </view>
        <view v-else class="hint">
          <text class="subtle">{{ '暂无热力图，请先生成。' }}</text>
        </view>
      </view>

      <view class="card block-card">
        <view class="section-header">
          <text class="section-title">{{ 'CPDM ' + '预测' }}</text>
          <text class="status-pill" :class="`status-pill--${cpdmStatusType}`">{{ cpdmStatusText }}</text>
        </view>
        <view class="hint-bar">
          <text class="subtle">{{ '上传 CT 文件（.npy/.nrrd/.png）并执行预测' }}</text>
        </view>

        <view class="segment-actions">
          <button class="mi-btn mi-btn--primary" :disabled="cpdmProcessing" @click="submitCpdm">
            {{ cpdmProcessing ? '处理中...' : '上传' }}
          </button>
          <button class="mi-btn mi-btn--ghost" :disabled="!cpdmPngUrl" @click="openCpdmPng">{{ '下载图片' }}</button>
        </view>

        <view v-if="cpdmPngUrl" class="preview">
          <image :src="cpdmPngUrl" mode="widthFix" class="heatmap-image" />
        </view>
        <view v-else class="hint">
          <text class="subtle">{{ cpdmEntry?.inputName ? ('输入文件：' + cpdmEntry.inputName) : '暂无 CPDM 结果' }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { getStudiesByPatient } from '../../common/api'
import { resolveModelUrl, getToken } from '../../common/request'

export default {
  data() {
    return {
      patientId: '',
      activeStudyId: '',
      studies: [],
      studyFileMap: {},
      heatmapMap: {},
      cpdmMap: {},
      modalityOrder: ['flair', 't1', 't1c', 't2'],
      processing: false,
      cpdmSubmitting: false,
      cpdmPollingTimer: null,
      isH5: false
    }
  },
  computed: {
    readyModalityCount() {
      if (!this.activeStudyId) return 0
      return this.modalityOrder.reduce((count, modality) => count + (this.getModalityFile(this.activeStudyId, modality) ? 1 : 0), 0)
    },
    hasAllModalities() {
      return this.modalityOrder.every((m) => !!this.getModalityFile(this.activeStudyId, m))
    },
    heatmapUrl() {
      const entry = this.heatmapMap?.[this.activeStudyId]
      return entry?.filePath || ''
    },
    cpdmEntry() {
      if (!this.activeStudyId) return null
      return this.cpdmMap?.[this.activeStudyId] || null
    },
    cpdmPngUrl() {
      return this.cpdmEntry?.petPngUrl || ''
    },
    cpdmStatus() {
      return this.cpdmEntry?.status || 'idle'
    },
    cpdmStatusType() {
      if (this.cpdmStatus === 'completed') return 'success'
      if (this.cpdmStatus === 'failed') return 'warning'
      return 'default'
    },
    cpdmStatusText() {
      const status = this.cpdmStatus
      if (status === 'completed') return '已完成'
      if (status === 'failed') return '失败'
      if (status === 'running' || status === 'queued') {
        const pct = Number(this.cpdmEntry?.progress || 0)
        return `处理中 ${pct}%`
      }
      return '待上传'
    },
    cpdmProcessing() {
      return this.cpdmSubmitting || this.cpdmStatus === 'queued' || this.cpdmStatus === 'running'
    }
  },
  async onLoad(query) {
    this.patientId = query.patientId || ''
    this.activeStudyId = query.studyId || ''
    const cache = uni.getStorageSync('currentPatient')
    if (!this.patientId && cache) {
      this.patientId = cache.id
    }
    this.isH5 = typeof window !== 'undefined' && typeof document !== 'undefined'
    if (!this.patientId) {
      uni.showToast({ title: '缺少患者ID', icon: 'none' })
      return
    }
    this.loadStudyFilesFromStorage()
    this.loadHeatmapFromStorage()
    this.loadCpdmFromStorage()
    await this.fetchStudies()
    this.resumeCpdmPollingIfNeeded()
  },
  onUnload() {
    this.stopCpdmPolling()
  },
  onHide() {
    this.stopCpdmPolling()
  },
  methods: {
    storageKey() {
      return `study_files_${this.patientId || ''}`
    },
    heatmapStorageKey() {
      return `ctv_heatmap_${this.patientId || ''}`
    },
    cpdmStorageKey() {
      return `cpdm_ct2pet_${this.patientId || ''}`
    },
    loadStudyFilesFromStorage() {
      const key = this.storageKey()
      if (!key) return
      const cache = uni.getStorageSync(key)
      this.studyFileMap = cache && typeof cache === 'object' ? cache : {}
    },
    loadHeatmapFromStorage() {
      const key = this.heatmapStorageKey()
      if (!key) return
      const cache = uni.getStorageSync(key)
      this.heatmapMap = cache && typeof cache === 'object' ? cache : {}
    },
    saveHeatmapToStorage() {
      const key = this.heatmapStorageKey()
      if (!key) return
      uni.setStorageSync(key, this.heatmapMap || {})
    },
    loadCpdmFromStorage() {
      const key = this.cpdmStorageKey()
      if (!key) return
      const cache = uni.getStorageSync(key)
      this.cpdmMap = cache && typeof cache === 'object' ? cache : {}
    },
    saveCpdmToStorage() {
      const key = this.cpdmStorageKey()
      if (!key) return
      uni.setStorageSync(key, this.cpdmMap || {})
    },
    resumeCpdmPollingIfNeeded() {
      const entry = this.cpdmEntry
      if (!entry?.jobId) return
      if (entry.status === 'queued' || entry.status === 'running') {
        this.startCpdmPolling(entry.jobId)
      }
    },
    modalityLabel(modality) {
      const key = String(modality || '').toLowerCase()
      const map = { flair: 'Flair', t1: 'T1', t1c: 'T1c', t2: 'T2' }
      return map[key] || key
    },
    modalityTagType(studyId, modality) {
      const file = this.getModalityFile(studyId, modality)
      return file ? 'success' : 'default'
    },
    modalityTagText(studyId, modality) {
      const file = this.getModalityFile(studyId, modality)
      return file ? '已上传' : '未上传'
    },
    getModalityFile(studyId, modality) {
      return this.studyFileMap?.[studyId]?.[modality]
    },
    async fetchStudies() {
      try {
        const data = await getStudiesByPatient(this.patientId)
        this.studies = Array.isArray(data) ? data : []
        if (!this.activeStudyId && this.studies[0]?.id) {
          this.activeStudyId = this.studies[0].id
        }
      } catch (err) {
        console.error('getStudies error', err)
      }
    },
    openStudyPicker() {
      if (!this.studies.length) return
      const itemList = this.studies.map((study) => '序列 ' + study.id)
      uni.showActionSheet({
        itemList,
        success: ({ tapIndex }) => {
          const study = this.studies[tapIndex]
          if (!study?.id) return
          this.activeStudyId = study.id
          this.resumeCpdmPollingIfNeeded()
        }
      })
    },
    async generateHeatmap() {
      if (!this.hasAllModalities || !this.activeStudyId) {
        uni.showToast({ title: '缺少多模态数据', icon: 'none' })
        return
      }
      if (this.processing) return
      this.processing = true
      uni.showLoading({ title: '处理中...', mask: true })
      try {
        const files = {
          flair: this.getModalityFile(this.activeStudyId, 'flair'),
          t1: this.getModalityFile(this.activeStudyId, 't1'),
          t1c: this.getModalityFile(this.activeStudyId, 't1c'),
          t2: this.getModalityFile(this.activeStudyId, 't2')
        }
        const result = await this.uploadMultimodalForHeatmap(files)
        if (result?.downloadUrl) {
          const url = resolveModelUrl(result.downloadUrl)
          this.heatmapMap = {
            ...(this.heatmapMap || {}),
            [this.activeStudyId]: {
              name: result.fileName || 'confidence.png',
              filePath: url,
              localPath: ''
            }
          }
          this.saveHeatmapToStorage()
        }
        uni.showToast({ title: '完成', icon: 'success' })
      } catch (err) {
        console.error('generate heatmap error', err)
        uni.showToast({ title: '模型服务未就绪', icon: 'none' })
      } finally {
        this.processing = false
        uni.hideLoading()
      }
    },
    downloadHeatmap() {
      const url = this.heatmapUrl
      if (!url) return
      if (this.isH5 && typeof window !== 'undefined') {
        window.open(url)
        return
      }
      uni.showLoading({ title: '处理中...', mask: true })
      uni.downloadFile({
        url,
        success: () => {
          uni.hideLoading()
          uni.showToast({ title: '完成', icon: 'success' })
        },
        fail: () => {
          uni.hideLoading()
          uni.showToast({ title: '操作失败', icon: 'none' })
        }
      })
    },
    async uploadMultimodalForHeatmap(files) {
      if (this.isH5) {
        return this.uploadMultimodalFetch('/api/ctv/heatmap', files)
      }
      return this.uploadMultimodalFile('/api/ctv/heatmap', files)
    },
    async submitCpdm() {
      if (!this.activeStudyId) {
        uni.showToast({ title: '缺少检查序列', icon: 'none' })
        return
      }
      if (this.cpdmSubmitting) return

      const file = await this.pickCpdmFile()
      if (!file) return

      this.cpdmSubmitting = true
      uni.showLoading({ title: '提交中...', mask: true })
      try {
        const payload = await this.uploadCpdmFile(file)
        const jobId = payload?.jobId || ''
        if (!jobId) {
          throw new Error('missing job id')
        }
        this.cpdmMap = {
          ...(this.cpdmMap || {}),
          [this.activeStudyId]: {
            inputName: file.name || 'ct.npy',
            jobId,
            status: payload.status || 'queued',
            progress: Number(payload.progress || 0),
            message: payload.message || 'queued',
            petPngUrl: '',
            error: ''
          }
        }
        this.saveCpdmToStorage()
        this.startCpdmPolling(jobId)
        uni.showToast({ title: '已提交', icon: 'success' })
      } catch (err) {
        console.error('submit cpdm error', err)
        uni.showToast({ title: '提交失败', icon: 'none' })
      } finally {
        this.cpdmSubmitting = false
        uni.hideLoading()
      }
    },
    async pickCpdmFile() {
      return new Promise((resolve) => {
        const choose = uni.chooseFile || uni.chooseMessageFile
        if (!choose) {
          uni.showToast({ title: '当前环境不支持选择文件', icon: 'none' })
          resolve(null)
          return
        }
        choose({
          count: 1,
          type: 'all',
          success: (res) => {
            const item = res.tempFiles && res.tempFiles[0]
            if (!item) {
              resolve(null)
              return
            }
            const path = item.path || item.tempFilePath || ''
            const name = item.name || (path ? path.split('/').pop() : 'ct.npy')
            const fileObj = item.file || null
            resolve({ path, name, fileObj })
          },
          fail: () => resolve(null)
        })
      })
    },
    async uploadCpdmFile(file) {
      const token = getToken()
      if (this.isH5 && file.fileObj) {
        const form = new FormData()
        form.append('ct', file.fileObj, file.name || 'ct.npy')
        const res = await fetch(resolveModelUrl('/api/cpdm/ct2pet'), {
          method: 'POST',
          body: form,
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        })
        const payload = await res.json().catch(() => null)
        if (!res.ok || !payload || payload.error) {
          throw payload || new Error(`HTTP ${res.status}`)
        }
        return payload
      }

      const localPath = file.path || ''
      if (!localPath) {
        throw new Error('missing file path')
      }
      return new Promise((resolve, reject) => {
        uni.uploadFile({
          url: resolveModelUrl('/api/cpdm/ct2pet'),
          filePath: localPath,
          name: 'ct',
          header: token ? { Authorization: `Bearer ${token}` } : {},
          success: (res) => {
            try {
              const payload = typeof res.data === 'string' ? JSON.parse(res.data) : res.data
              if (payload?.error) {
                reject(payload)
                return
              }
              resolve(payload)
            } catch (e) {
              reject(e)
            }
          },
          fail: (err) => reject(err)
        })
      })
    },
    startCpdmPolling(jobId) {
      this.stopCpdmPolling()
      if (!jobId) return
      this.queryCpdmJob(jobId)
      this.cpdmPollingTimer = setInterval(() => {
        this.queryCpdmJob(jobId)
      }, 3000)
    },
    stopCpdmPolling() {
      if (this.cpdmPollingTimer) {
        clearInterval(this.cpdmPollingTimer)
        this.cpdmPollingTimer = null
      }
    },
    async queryCpdmJob(jobId) {
      if (!jobId || !this.activeStudyId) return
      try {
        const payload = await this.fetchCpdmJob(jobId)
        const result = payload?.result || {}
        const status = payload?.status || 'queued'
        const next = {
          ...(this.cpdmEntry || {}),
          jobId,
          status,
          progress: Number(payload?.progress || 0),
          message: payload?.message || '',
          error: payload?.error || '',
          petPngUrl: result?.petPngUrl ? resolveModelUrl(result.petPngUrl) : (this.cpdmEntry?.petPngUrl || '')
        }
        this.cpdmMap = {
          ...(this.cpdmMap || {}),
          [this.activeStudyId]: next
        }
        this.saveCpdmToStorage()
        if (status === 'completed' || status === 'failed') {
          this.stopCpdmPolling()
        }
      } catch (err) {
        console.error('cpdm status error', err)
        if (err?.statusCode === 404 || err?.error === 'job not found') {
          const next = {
            ...(this.cpdmEntry || {}),
            jobId,
            status: 'failed',
            progress: 100,
            message: '任务不存在或已过期',
            error: 'job not found'
          }
          this.cpdmMap = {
            ...(this.cpdmMap || {}),
            [this.activeStudyId]: next
          }
          this.saveCpdmToStorage()
          this.stopCpdmPolling()
        }
      }
    },
    async fetchCpdmJob(jobId) {
      const token = getToken()
      return new Promise((resolve, reject) => {
        uni.request({
          url: resolveModelUrl(`/api/cpdm/jobs/${jobId}`),
          method: 'GET',
          header: token ? { Authorization: `Bearer ${token}` } : {},
          success: (res) => {
            const payload = typeof res.data === 'string' ? JSON.parse(res.data) : res.data
            if (res.statusCode < 200 || res.statusCode >= 300 || payload?.error) {
              reject({
                ...(payload || {}),
                statusCode: res.statusCode
              })
              return
            }
            resolve(payload)
          },
          fail: (err) => reject(err)
        })
      })
    },
    async openCpdmPng() {
      const url = this.cpdmPngUrl
      if (!url) return
      if (this.isH5 && typeof window !== 'undefined') {
        window.open(url)
        return
      }
      uni.showLoading({ title: '下载中...', mask: true })
      uni.downloadFile({
        url,
        success: () => {
          uni.hideLoading()
          uni.showToast({ title: '下载成功', icon: 'success' })
        },
        fail: () => {
          uni.hideLoading()
          uni.showToast({ title: '下载失败', icon: 'none' })
        }
      })
    },
    async uploadMultimodalFile(endpoint, files) {
      const flairPath = await this.resolveLocalPath(files.flair)
      const t1Path = await this.resolveLocalPath(files.t1)
      const t1cPath = await this.resolveLocalPath(files.t1c)
      const t2Path = await this.resolveLocalPath(files.t2)
      if (!flairPath || !t1Path || !t1cPath || !t2Path) {
        throw new Error('Missing local file')
      }
      const fileList = [
        { name: 'flair', filePath: flairPath },
        { name: 't1', filePath: t1Path },
        { name: 't1c', filePath: t1cPath },
        { name: 't2', filePath: t2Path }
      ]
      const token = getToken()
      return new Promise((resolve, reject) => {
        uni.uploadFile({
          url: resolveModelUrl(endpoint),
          files: fileList,
          header: token ? { Authorization: `Bearer ${token}` } : {},
          success: (res) => {
            try {
              const payload = typeof res.data === 'string' ? JSON.parse(res.data) : res.data
              if (payload?.error) {
                reject(payload)
                return
              }
              resolve(payload)
            } catch (e) {
              reject(e)
            }
          },
          fail: (err) => reject(err)
        })
      })
    },
    async uploadMultimodalFetch(endpoint, files) {
      const flairBlob = await this.fetchBlob(files.flair)
      const t1Blob = await this.fetchBlob(files.t1)
      const t1cBlob = await this.fetchBlob(files.t1c)
      const t2Blob = await this.fetchBlob(files.t2)
      if (!flairBlob || !t1Blob || !t1cBlob || !t2Blob) {
        throw new Error('Missing file data')
      }
      const form = new FormData()
      form.append('flair', flairBlob, files.flair?.name || 'flair.nrrd')
      form.append('t1', t1Blob, files.t1?.name || 't1.nrrd')
      form.append('t1c', t1cBlob, files.t1c?.name || 't1c.nrrd')
      form.append('t2', t2Blob, files.t2?.name || 't2.nrrd')
      const token = getToken()
      const res = await fetch(resolveModelUrl(endpoint), {
        method: 'POST',
        body: form,
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      })
      const payload = await res.json().catch(() => null)
      if (!res.ok || !payload || payload.error) {
        throw payload || new Error(`HTTP ${res.status}`)
      }
      return payload
    },
    async fetchBlob(file) {
      if (!file) return null
      if (file.fileObj) return file.fileObj
      const target = file.filePath || file.localPath || ''
      if (!target) return null
      const res = await fetch(target)
      if (!res.ok) return null
      return res.blob()
    },
    async resolveLocalPath(file) {
      if (!file) return ''
      const local = file.localPath || ''
      if (local && !/^https?:\/\//i.test(local)) return local
      const remote = file.filePath || ''
      if (!remote || !/^https?:\/\//i.test(remote)) return remote
      return new Promise((resolve) => {
        uni.downloadFile({
          url: remote,
          success: (res) => resolve(res.tempFilePath),
          fail: () => resolve('')
        })
      })
    }
  }
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: #edf4ff;
}

.ctv-area {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.ctv-hero {
  border-radius: 28rpx;
  padding: 24rpx 24rpx 20rpx;
  background: linear-gradient(150deg, #2f78d8 0%, #3f88e6 46%, #6baef4 100%);
  box-shadow: 0 18rpx 40rpx rgba(44, 110, 192, 0.28);
}

.hero-main {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14rpx;
}

.hero-title {
  display: block;
  font-size: 38rpx;
  font-weight: 700;
  color: #ffffff;
}

.hero-subtitle {
  display: block;
  margin-top: 6rpx;
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.84);
}

.hero-badge {
  min-width: 62rpx;
  height: 46rpx;
  padding: 0 12rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.24);
  border: 1rpx solid rgba(255, 255, 255, 0.42);
  color: #ffffff;
  font-size: 24rpx;
  font-weight: 700;
  line-height: 46rpx;
  text-align: center;
}

.hero-metrics {
  margin-top: 18rpx;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10rpx;
}

.metric-item {
  border-radius: 16rpx;
  background: rgba(255, 255, 255, 0.16);
  border: 1rpx solid rgba(255, 255, 255, 0.28);
  padding: 10rpx 12rpx;
}

.metric-value {
  display: block;
  font-size: 24rpx;
  font-weight: 650;
  color: #ffffff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.metric-label {
  display: block;
  margin-top: 4rpx;
  font-size: 21rpx;
  color: rgba(255, 255, 255, 0.8);
}

.block-card {
  margin-bottom: 0;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
  margin-bottom: 14rpx;
}

.section-header--edge {
  margin-left: -24rpx;
  margin-right: -24rpx;
  padding-left: 24rpx;
  padding-right: 10rpx;
}

.section-header--edge > .mi-btn {
  margin-left: auto;
  margin-right: 0;
}

.section-title {
  font-size: 30rpx;
  font-weight: 700;
  color: #173a64;
  margin-bottom: 0;
}

.study-modalities {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12rpx;
}

.modality-item {
  padding: 12rpx;
  background: #f6faff;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
  border: 1rpx solid #d6e5f7;
}

.modality-left {
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.modality-dot {
  width: 14rpx;
  height: 14rpx;
  border-radius: 50%;
  background: #8cb4e4;
  box-shadow: 0 0 0 6rpx rgba(144, 180, 224, 0.2);
}

.segment-actions,
.action-row {
  display: flex;
  justify-content: space-between;
  align-items: stretch;
  gap: 12rpx;
  flex-wrap: nowrap;
  margin-top: 14rpx;
}

.segment-actions .mi-btn {
  flex: 1 1 0;
  min-width: 0;
  text-align: center;
  padding: 0 12rpx;
  font-weight: 600;
}

.action-row .mi-btn {
  flex: 1 1 0;
  min-width: 0;
  text-align: center;
  padding: 0 12rpx;
  font-weight: 600;
}

.segment-actions .mi-btn--primary[disabled] {
  opacity: 1;
  background: #dce9f9;
  border-color: #c3d8f3;
  color: #3b5f88;
  box-shadow: none;
  -webkit-text-fill-color: currentColor;
}

.segment-actions .mi-btn--ghost[disabled] {
  opacity: 1;
  background: #f4f8fd;
  border-color: #d9e6f7;
  color: #6b86a8;
  box-shadow: none;
  -webkit-text-fill-color: currentColor;
}

.hint-bar {
  margin-top: 12rpx;
  padding: 12rpx 14rpx;
  border-radius: 14rpx;
  background: #f7fbff;
  border: 1rpx solid #d9e8f9;
}

.preview {
  margin-top: 14rpx;
  border-radius: 16rpx;
  overflow: hidden;
  border: 1rpx solid #d6e5f7;
  box-shadow: 0 10rpx 24rpx rgba(47, 120, 216, 0.14);
}

.heatmap-image {
  width: 100%;
  display: block;
  background: #eff6ff;
}

.hint {
  margin-top: 14rpx;
  padding: 12rpx 14rpx;
  border-radius: 14rpx;
  border: 1rpx dashed #c7daf2;
  background: #f7fbff;
}

.label {
  color: #234567;
  font-weight: 600;
  font-size: 26rpx;
}

.subtle {
  color: #5f7899;
  font-size: 24rpx;
}

.workflow-strip {
  margin-bottom: 4rpx;
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.flow-step {
  display: inline-flex;
  align-items: center;
  gap: 8rpx;
}

.flow-index {
  width: 32rpx;
  height: 32rpx;
  border-radius: 50%;
  text-align: center;
  line-height: 32rpx;
  font-size: 20rpx;
  font-weight: 700;
  color: #245eac;
  background: #eaf3ff;
  border: 1rpx solid #bfd5ef;
}

.flow-text {
  font-size: 23rpx;
  color: #53729a;
}

.flow-link {
  flex: 1;
  min-width: 18rpx;
  height: 1rpx;
  background: linear-gradient(90deg, #d2e3f8 0%, #bfd5ef 100%);
}

.status-pill {
  display: inline-flex;
  align-items: center;
  padding: 8rpx 16rpx;
  border-radius: 999rpx;
  border: 1rpx solid #d6e5f7;
  font-size: 22rpx;
  color: #4f6788;
  background: #f8fbff;
}

.status-pill--success {
  color: #1f8b4c;
  border-color: #bce2cb;
  background: #f3fbf6;
}

.status-pill--warning {
  color: #b27613;
  border-color: #f2dfbe;
  background: #fdf8ef;
}

.status-pill--default {
  color: #6a84a6;
  border-color: #d6e5f7;
  background: #f8fbff;
}

.mi-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin: 0;
  height: 68rpx;
  line-height: 68rpx;
  padding: 0 24rpx;
  border-radius: 999rpx;
  font-size: 25rpx;
  border: 1rpx solid #c8daf4;
  background: #ffffff;
  color: #2f4f73;
  box-shadow: 0 8rpx 20rpx rgba(47, 120, 216, 0.12);
}

.mi-btn--primary {
  background: linear-gradient(135deg, #2f78d8 0%, #245eac 100%);
  border-color: transparent;
  color: #ffffff;
  box-shadow: 0 12rpx 28rpx rgba(47, 120, 216, 0.26);
}

.mi-btn--ghost {
  background: #ffffff;
  color: #305377;
}

.mi-btn[disabled] {
  opacity: 0.55;
  box-shadow: none;
}

button::after {
  border: none;
}
</style>






