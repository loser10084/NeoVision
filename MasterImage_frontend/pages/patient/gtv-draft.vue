<template>
  <view class="page">
    <view class="safe-area gtv-area">
      <view class="gtv-hero">
        <view class="hero-main">
          <view>
            <text class="hero-title">GTV 初稿工作台</text>
            <text class="hero-subtitle">面向放疗医生的快速靶区分割与校核</text>
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
            <text class="metric-value">{{ labelUrl ? '已生成' : '未生成' }}</text>
            <text class="metric-label">GTV Label</text>
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
          <text class="subtle">建议先确认 Flair 上传，再执行基础分割；全模态齐全后可执行多模态分割。</text>
        </view>
      </view>

      <view class="card block-card">
        <view class="section-header">
          <text class="section-title">分割执行</text>
          <text class="status-pill" :class="labelUrl ? 'status-pill--success' : 'status-pill--warning'">
            {{ labelUrl ? '结果可下载' : '待生成结果' }}
          </text>
        </view>

        <view class="workflow-strip">
          <view class="flow-step">
            <text class="flow-index">1</text>
            <text class="flow-text">检查模态</text>
          </view>
          <view class="flow-link"></view>
          <view class="flow-step">
            <text class="flow-index">2</text>
            <text class="flow-text">执行分割</text>
          </view>
          <view class="flow-link"></view>
          <view class="flow-step">
            <text class="flow-index">3</text>
            <text class="flow-text">下载复核</text>
          </view>
        </view>

        <view class="segment-actions">
          <button
            class="mi-btn mi-btn--primary"
            :disabled="processing || !hasFlair"
            @click="runFlairSegmentation"
          >
            {{ processing ? '处理中...' : 'Flair 基础分割' }}
          </button>
          <button
            class="mi-btn mi-btn--ghost"
            :disabled="processing || !hasAllModalities"
            @click="runMultimodalSegmentation"
          >
            多模态分割
          </button>
        </view>

        <view class="segment-status">
          <text class="label">分割结果</text>
          <text class="status-pill" :class="labelUrl ? 'status-pill--success' : 'status-pill--warning'">
            {{ labelUrl ? '已生成' : '未生成' }}
          </text>
        </view>

        <view class="download-actions">
          <button class="mi-btn mi-btn--ghost" @click="openDownloadSheet">下载结果与源数据</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { getStudiesByPatient, getModel, upsertContour } from '../../common/api'
import { resolveApiUrl, resolveStudyResourceUrl } from '../../common/request'

export default {
  data() {
    return {
      patientId: '',
      activeStudyId: '',
      studies: [],
      volumeUrl: '',
      labelUrl: '',
      processing: false,
      studyFileMap: {},
      modalityOrder: ['flair', 't1', 't1c', 't2'],
      isH5: false
    }
  },
  computed: {
    readyModalityCount() {
      if (!this.activeStudyId) return 0
      return this.modalityOrder.reduce((count, modality) => {
        return count + (this.getModalityFile(this.activeStudyId, modality) ? 1 : 0)
      }, 0)
    },
    hasFlair() {
      return !!this.getModalityFile(this.activeStudyId, 'flair') || !!this.volumeUrl
    },
    hasAllModalities() {
      return this.modalityOrder.every((m) => !!this.getModalityFile(this.activeStudyId, m))
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
    await this.fetchStudies()
    await this.fetchModel()
  },
  methods: {
    storageKey() {
      return `study_files_${this.patientId || ''}`
    },
    loadStudyFilesFromStorage() {
      const key = this.storageKey()
      if (!key) return
      const cache = uni.getStorageSync(key)
      this.studyFileMap = cache && typeof cache === 'object' ? cache : {}
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
        success: async ({ tapIndex }) => {
          const study = this.studies[tapIndex]
          if (!study?.id) return
          this.activeStudyId = study.id
          await this.fetchModel()
        }
      })
    },
    buildDownloadActions() {
      const actions = []
      actions.push({ name: 'Label', id: 'label', disabled: !this.labelUrl })
      actions.push({ name: 'Flair', id: 'flair', disabled: !this.getModalityFile(this.activeStudyId, 'flair') && !this.volumeUrl })
      actions.push({ name: 'T1', id: 't1', disabled: !this.getModalityFile(this.activeStudyId, 't1') })
      actions.push({ name: 'T1c', id: 't1c', disabled: !this.getModalityFile(this.activeStudyId, 't1c') })
      actions.push({ name: 'T2', id: 't2', disabled: !this.getModalityFile(this.activeStudyId, 't2') })
      return actions.filter((item) => !item.disabled)
    },
    openDownloadSheet() {
      const actions = this.buildDownloadActions()
      if (!actions.length) {
        uni.showToast({ title: '暂无可下载内容', icon: 'none' })
        return
      }
      uni.showActionSheet({
        itemList: actions.map((item) => item.name),
        success: ({ tapIndex }) => {
          const item = actions[tapIndex]
          if (!item?.id) return
          if (item.id === 'label') {
            this.downloadLabel()
            return
          }
          this.downloadModality(item.id)
        }
      })
    },
    async fetchModel() {
      if (!this.activeStudyId) return
      try {
        const model = await getModel(this.activeStudyId)
        this.volumeUrl = model?.volumeUrl || model?.modelPath || model?.modelUrl || ''
        this.labelUrl = model?.labelUrl || ''
        if (this.labelUrl) {
          await this.syncContourResult(this.labelUrl)
        }
      } catch (err) {
        console.error('getModel error', err)
      }
    },
    async syncContourResult(labelUrl) {
      if (!this.patientId || !this.activeStudyId || !labelUrl) return
      try {
        await upsertContour(this.patientId, {
          studyId: this.activeStudyId,
          type: 'GTV',
          storagePath: labelUrl,
          status: 'pending'
        })
      } catch (err) {
        console.error('upsert contour error', err)
      }
    },
    async downloadLabel() {
      if (!this.labelUrl) {
        uni.showToast({ title: '暂无Label', icon: 'none' })
        return
      }
      await this.triggerDownload(this.labelUrl)
    },
    async downloadModality(modality) {
      if (!this.activeStudyId) return
      const file = this.getModalityFile(this.activeStudyId, modality)
      const url = file?.filePath || file?.localPath || ''
      if (!url && modality === 'flair' && this.volumeUrl) {
        await this.triggerDownload(this.volumeUrl)
        return
      }
      if (!url) {
        uni.showToast({ title: '暂无该模态文件', icon: 'none' })
        return
      }
      await this.triggerDownload(url)
    },
    async triggerDownload(url) {
      if (!url) return
      const resolvedUrl = resolveStudyResourceUrl(url)
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
    async runFlairSegmentation() {
      if (this.processing || !this.activeStudyId) return
      const flair = this.getModalityFile(this.activeStudyId, 'flair')
      if (!flair && !this.volumeUrl) {
        uni.showToast({ title: '缺少Flair文件', icon: 'none' })
        return
      }
      this.processing = true
      uni.showLoading({ title: '分割中...', mask: true })
      try {
        const file = flair || { filePath: this.volumeUrl, name: 'flair.nrrd' }
        await this.uploadSingleForSegmentation(this.activeStudyId, file)
        await this.fetchModel()
        uni.showToast({ title: '分割完成', icon: 'success' })
      } catch (err) {
        console.error('segment error', err)
        uni.showToast({ title: '分割失败', icon: 'none' })
      } finally {
        this.processing = false
        uni.hideLoading()
      }
    },
    async runMultimodalSegmentation() {
      if (this.processing || !this.activeStudyId) return
      if (!this.hasAllModalities) {
        uni.showToast({ title: '缺少模态', icon: 'none' })
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
        await this.uploadMultimodalForSegmentation(this.activeStudyId, files)
        await this.fetchModel()
        uni.showToast({ title: '分割完成', icon: 'success' })
      } catch (err) {
        console.error('segment multimodal error', err)
        uni.showToast({ title: '分割失败', icon: 'none' })
      } finally {
        this.processing = false
        uni.hideLoading()
      }
    },
    async uploadSingleForSegmentation(studyId, file) {
      if (this.isH5) {
        return this.uploadSingleFetch(studyId, file)
      }
      const filePath = await this.resolveLocalPath(file)
      if (!filePath) {
        throw new Error('Missing file path')
      }
      const token = uni.getStorageSync('token') || ''
      return new Promise((resolve, reject) => {
        uni.uploadFile({
          url: resolveApiUrl(`/api/studies/${studyId}/segment`),
          filePath,
          name: 'file',
          timeout: 600000,
          header: token ? { Authorization: `Bearer ${token}` } : {},
          success: (res) => {
            try {
              const payload = typeof res.data === 'string' ? JSON.parse(res.data) : res.data
              if (!payload || payload.code !== 0) {
                reject(payload)
                return
              }
              resolve(payload.data)
            } catch (e) {
              reject(e)
            }
          },
          fail: (err) => reject(err)
        })
      })
    },
    async uploadMultimodalForSegmentation(studyId, files) {
      if (this.isH5) {
        return this.uploadMultimodalFetch(studyId, files)
      }
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
      const token = uni.getStorageSync('token') || ''
      return new Promise((resolve, reject) => {
        uni.uploadFile({
          url: resolveApiUrl(`/api/studies/${studyId}/segment/multimodal`),
          files: fileList,
          header: token ? { Authorization: `Bearer ${token}` } : {},
          success: (res) => {
            try {
              const payload = typeof res.data === 'string' ? JSON.parse(res.data) : res.data
              if (!payload || payload.code !== 0) {
                reject(payload)
                return
              }
              resolve(payload.data)
            } catch (e) {
              reject(e)
            }
          },
          fail: (err) => reject(err)
        })
      })
    },
    async uploadSingleFetch(studyId, file) {
      const blob = await this.fetchBlob(file)
      if (!blob) throw new Error('Missing file data')
      const form = new FormData()
      form.append('file', blob, file.name || 'volume.nrrd')
      const token = uni.getStorageSync('token') || ''
      const res = await fetch(resolveApiUrl(`/api/studies/${studyId}/segment`), {
        method: 'POST',
        body: form,
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      })
      const payload = await res.json().catch(() => null)
      if (!res.ok || !payload || payload.code !== 0) {
        throw payload || new Error(`HTTP ${res.status}`)
      }
      return payload.data
    },
    async uploadMultimodalFetch(studyId, files) {
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
      const token = uni.getStorageSync('token') || ''
      const res = await fetch(resolveApiUrl(`/api/studies/${studyId}/segment/multimodal`), {
        method: 'POST',
        body: form,
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      })
      const payload = await res.json().catch(() => null)
      if (!res.ok || !payload || payload.code !== 0) {
        throw payload || new Error(`HTTP ${res.status}`)
      }
      return payload.data
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

.gtv-area {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.gtv-hero {
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
.download-actions,
.action-row {
  display: flex;
  justify-content: space-between;
  align-items: stretch;
  gap: 12rpx;
  flex-wrap: nowrap;
  margin-top: 14rpx;
}

.segment-actions .mi-btn,
.download-actions .mi-btn {
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


