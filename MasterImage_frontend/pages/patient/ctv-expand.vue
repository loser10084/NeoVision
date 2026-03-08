<template>
  <view class="page">
    <view class="safe-area ctv-area">
      <view class="ctv-hero">
        <view class="hero-main">
          <view>
            <text class="hero-title">CTV 精修工作台</text>
            <text class="hero-subtitle">在外扩结果基础上完成精修分割与结果校核</text>
          </view>
          <view class="hero-badge">AI</view>
        </view>
        <view class="hero-metrics">
          <view class="metric-item">
            <text class="metric-value">{{ activeStudyId || '-' }}</text>
            <text class="metric-label">当前序列</text>
          </view>
          <view class="metric-item">
            <text class="metric-value">{{ readyModalityCount }}/{{ modalityOrder.length }}</text>
            <text class="metric-label">模态就绪</text>
          </view>
          <view class="metric-item">
            <text class="metric-value">{{ refinedLabelStatusText }}</text>
            <text class="metric-label">精修 Label</text>
          </view>
        </view>
      </view>

      <view class="card block-card">
        <view class="section-header section-header--edge">
          <text class="section-title">序列与模态检查</text>
          <button class="mi-btn mi-btn--ghost" @click="openStudyPicker">切换序列</button>
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
          <text class="subtle">先确认 CTV 外扩 Label 已生成，再执行精修分割并下载结果。</text>
        </view>
      </view>

      <view class="card block-card">
        <view class="section-header">
          <text class="section-title">精修执行</text>
          <text class="status-pill" :class="`status-pill--${refinedLabelStatusType}`">{{ refinedLabelStatusText }}</text>
        </view>

        <view class="workflow-strip">
          <view class="flow-step">
            <text class="flow-index">1</text>
            <text class="flow-text">确认外扩 Label</text>
          </view>
          <view class="flow-link"></view>
          <view class="flow-step">
            <text class="flow-index">2</text>
            <text class="flow-text">执行精修分割</text>
          </view>
          <view class="flow-link"></view>
          <view class="flow-step">
            <text class="flow-index">3</text>
            <text class="flow-text">下载精修结果</text>
          </view>
        </view>

        <view class="segment-status">
          <text class="label">外扩 Label</text>
          <text class="status-pill" :class="expandLabelFile ? 'status-pill--success' : 'status-pill--warning'">
            {{ expandLabelFile ? '已生成' : '未生成' }}
          </text>
        </view>
        <view class="segment-status">
          <text class="label">精修 Label</text>
          <text class="status-pill" :class="`status-pill--${refinedLabelStatusType}`">{{ refinedLabelStatusText }}</text>
        </view>

        <view class="segment-actions">
          <button class="mi-btn mi-btn--primary" :disabled="processing" @click="downloadRefinedLabel">
            {{ processing ? '处理中...' : '下载精修 Label' }}
          </button>
          <button class="mi-btn mi-btn--ghost" :disabled="processing || !canSubmit" @click="submitExpand">
            开始精修分割
          </button>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { getStudiesByPatient, getContours, upsertContour } from '../../common/api'
import { resolveModelUrl, resolveStudyResourceUrl, getToken } from '../../common/request'

export default {
  data() {
    return {
      patientId: '',
      activeStudyId: '',
      studies: [],
      studyFileMap: {},
      refinedLabelMap: {},
      expandLabelMap: {},
      modalityOrder: ['flair', 't1', 't1c', 't2'],
      processing: false,
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
    refinedLabelFile() {
      return this.expandLabelMap?.[this.activeStudyId] || null
    },
    refinedLabelStatusText() {
      if (!this.refinedLabelFile) return '未生成'
      return '已生成'
    },
    refinedLabelStatusType() {
      return this.refinedLabelFile ? 'success' : 'warning'
    },
    expandLabelFile() {
      return this.getRefinedLabelForStudy(this.activeStudyId)
    },
    canSubmit() {
      return this.hasAllModalities
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
    this.loadRefinedLabelsFromStorage()
    this.loadExpandLabelsFromStorage()
    await this.fetchStudies()
    await this.fetchContours()
  },
  methods: {
    storageKey() {
      return `study_files_${this.patientId || ''}`
    },
    refineStorageKey() {
      return `ctv_refine_${this.patientId || ''}`
    },
    expandStorageKey() {
      return `ctv_expand_${this.patientId || ''}`
    },
    loadStudyFilesFromStorage() {
      const key = this.storageKey()
      if (!key) return
      const cache = uni.getStorageSync(key)
      this.studyFileMap = cache && typeof cache === 'object' ? cache : {}
    },
    loadRefinedLabelsFromStorage() {
      const key = this.refineStorageKey()
      if (!key) return
      const cache = uni.getStorageSync(key)
      this.refinedLabelMap = cache && typeof cache === 'object' ? cache : {}
    },
    loadExpandLabelsFromStorage() {
      const key = this.expandStorageKey()
      if (!key) return
      const cache = uni.getStorageSync(key)
      this.expandLabelMap = cache && typeof cache === 'object' ? cache : {}
    },
    saveExpandLabelsToStorage() {
      const key = this.expandStorageKey()
      if (!key) return
      uni.setStorageSync(key, this.expandLabelMap || {})
    },
    saveRefinedLabelsToStorage() {
      const key = this.refineStorageKey()
      if (!key) return
      uni.setStorageSync(key, this.refinedLabelMap || {})
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
      const itemList = this.studies.map((study) => `序列 ${study.id}`)
      uni.showActionSheet({
        itemList,
        success: ({ tapIndex }) => {
          const study = this.studies[tapIndex]
          if (!study?.id) return
          this.activeStudyId = study.id
        }
      })
    },
    normalizeRefinedLabel(label, fallbackSource = 'upload') {
      if (!label) return null
      return {
        ...label,
        source: label.source || fallbackSource
      }
    },
    getRefinedLabelForStudy(studyId) {
      if (!studyId) return null
      const label = this.refinedLabelMap?.[studyId] || null
      return this.normalizeRefinedLabel(label)
    },
    async fetchContours() {
      try {
        const data = await getContours(this.patientId)
        const list = Array.isArray(data) ? data : []
        const nextMap = { ...(this.refinedLabelMap || {}) }
        list.forEach((contour) => {
          if (contour?.type !== 'CTV' || !contour.storagePath) return
          const studyId = contour.studyId || this.activeStudyId || ''
          if (!studyId || nextMap[studyId]) return
          nextMap[studyId] = {
            name: contour.storagePath.split('/').pop() || '',
            filePath: contour.storagePath,
            localPath: '',
            source: 'model'
          }
        })
        this.refinedLabelMap = nextMap
        this.saveRefinedLabelsToStorage()
      } catch (err) {
        console.error('getContours error', err)
      }
    },
    async downloadRefinedLabel() {
      const label = this.refinedLabelFile
      const url = label?.filePath || label?.localPath || ''
      if (!url) {
        uni.showToast({ title: '暂无精修 Label', icon: 'none' })
        return
      }
      await this.triggerDownload(url)
    },
    async triggerDownload(url) {
      if (!url) return
      const resolvedUrl = this.resolveDownloadUrl(url)
      uni.showLoading({ title: '下载中...', mask: true })
      return new Promise((resolve) => {
        uni.downloadFile({
          url: resolvedUrl,
          success: (res) => {
            if (res.statusCode !== 200) {
              uni.showToast({ title: '下载失败', icon: 'none' })
              uni.hideLoading()
              resolve(null)
              return
            }
            if (typeof uni.saveFile === 'function') {
              uni.saveFile({
                tempFilePath: res.tempFilePath,
                success: (saveRes) => {
                  uni.hideLoading()
                  uni.showToast({ title: '已保存', icon: 'success' })
                  resolve(saveRes.savedFilePath)
                },
                fail: () => {
                  uni.hideLoading()
                  uni.showToast({ title: '已下载', icon: 'success' })
                  resolve(res.tempFilePath)
                }
              })
              return
            }
            uni.hideLoading()
            uni.showToast({ title: '已下载', icon: 'success' })
            resolve(res.tempFilePath)
          },
          fail: () => {
            uni.hideLoading()
            uni.showToast({ title: '下载失败', icon: 'none' })
            resolve(null)
          }
        })
      })
    },
    resolveDownloadUrl(url) {
      if (!url) return ''
      if (/^https?:\/\//i.test(url)) return url
      return resolveStudyResourceUrl(url)
    },
    async submitExpand() {
      if (!this.canSubmit || !this.activeStudyId) {
        uni.showToast({ title: '缺少多模态数据', icon: 'none' })
        return
      }
      this.processing = true
      uni.showLoading({ title: '分割中...', mask: true })
      try {
        const files = {
          flair: this.getModalityFile(this.activeStudyId, 'flair'),
          t1: this.getModalityFile(this.activeStudyId, 't1'),
          t1c: this.getModalityFile(this.activeStudyId, 't1c'),
          t2: this.getModalityFile(this.activeStudyId, 't2')
        }
        const result = await this.uploadMultimodalForExpand(files)
        if (result?.downloadUrl) {
          const url = resolveModelUrl(result.downloadUrl)
          this.expandLabelMap = {
            ...(this.expandLabelMap || {}),
            [this.activeStudyId]: {
              name: result.fileName || 'ctv_expanded.nrrd',
              filePath: url,
              localPath: ''
            }
          }
          this.saveExpandLabelsToStorage()
          await this.syncContourResult(url)
        }
        uni.showToast({ title: '分割完成', icon: 'success' })
      } catch (err) {
        console.error('submit expand error', err)
        uni.showToast({ title: '模型端未就绪', icon: 'none' })
      } finally {
        this.processing = false
        uni.hideLoading()
      }
    },
    async uploadMultimodalForExpand(files) {
      if (this.isH5) {
        return this.uploadMultimodalFetch('/api/ctv/expand', files)
      }
      return this.uploadMultimodalFile('/api/ctv/expand', files)
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
    },
    async syncContourResult(labelUrl) {
      if (!this.patientId || !this.activeStudyId || !labelUrl) return
      try {
        await upsertContour(this.patientId, {
          studyId: this.activeStudyId,
          type: 'CTV',
          storagePath: labelUrl,
          status: 'pending'
        })
      } catch (err) {
        console.error('upsert contour error', err)
      }
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
}

.hint-bar {
  margin-top: 12rpx;
  padding: 12rpx 14rpx;
  border-radius: 14rpx;
  background: #f7fbff;
  border: 1rpx solid #d9e8f9;
}

.segment-status {
  margin-top: 14rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
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

