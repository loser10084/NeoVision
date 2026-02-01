<template>
  <view class="page">
    <view class="safe-area">
      <view class="card">
        <view class="section-title">已上传模态</view>
        <view class="study-modalities">
          <view v-for="modality in modalityOrder" :key="modality" class="modality-item">
            <text class="label">{{ modalityLabel(modality) }}</text>
            <wd-tag plain :type="modalityTagType(activeStudyId, modality)">
              {{ modalityTagText(activeStudyId, modality) }}
            </wd-tag>
          </view>
        </view>
        <view class="action-row">
          <wd-button size="small" shape="round" type="default" plain @click="openStudyPicker">
            选择序列
          </wd-button>
          <text class="subtle">当前序列：{{ activeStudyId || '-' }}</text>
        </view>
      </view>

      <view class="card">
        <view class="section-title">置信度热力图</view>
        <view class="segment-actions">
          <wd-button
            size="small"
            shape="round"
            type="primary"
            plain
            :loading="processing"
            :disabled="processing || !hasAllModalities"
            @click="generateHeatmap"
          >
            生成热力图
          </wd-button>
          <wd-button
            size="small"
            shape="round"
            type="default"
            plain
            :disabled="!heatmapUrl"
            @click="downloadHeatmap"
          >
            下载
          </wd-button>
        </view>
        <view v-if="heatmapUrl" class="preview">
          <image :src="heatmapUrl" mode="widthFix" class="heatmap-image" />
        </view>
        <view v-else class="hint">
          <text class="subtle">暂无热力图，请先生成。</text>
        </view>
      </view>
    </view>
  </view>

  <wd-action-sheet
    v-model="studyPickerVisible"
    title="选择序列"
    cancel-text="关闭"
    :actions="studyPickerActions"
    @select="handleStudyPick"
  />
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
      modalityOrder: ['flair', 't1', 't1c', 't2'],
      studyPickerVisible: false,
      studyPickerActions: [],
      processing: false,
      isH5: false
    }
  },
  computed: {
    hasAllModalities() {
      return this.modalityOrder.every((m) => !!this.getModalityFile(this.activeStudyId, m))
    },
    heatmapUrl() {
      const entry = this.heatmapMap?.[this.activeStudyId]
      return entry?.filePath || ''
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
    await this.fetchStudies()
  },
  methods: {
    storageKey() {
      return `study_files_${this.patientId || ''}`
    },
    heatmapStorageKey() {
      return `ctv_heatmap_${this.patientId || ''}`
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
        this.buildStudyPicker()
      } catch (err) {
        console.error('getStudies error', err)
      }
    },
    buildStudyPicker() {
      this.studyPickerActions = (this.studies || []).map((study) => ({
        name: `序列 ${study.id}`,
        id: study.id
      }))
    },
    openStudyPicker() {
      if (!this.studies.length) return
      this.studyPickerVisible = true
    },
    async handleStudyPick({ item }) {
      if (!item?.id) return
      this.activeStudyId = item.id
    },
    async generateHeatmap() {
      if (!this.hasAllModalities || !this.activeStudyId) {
        uni.showToast({ title: '缺少多模态数据', icon: 'none' })
        return
      }
      if (this.processing) return
      this.processing = true
      uni.showLoading({ title: '生成中...', mask: true })
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
        uni.showToast({ title: '已生成', icon: 'success' })
      } catch (err) {
        console.error('generate heatmap error', err)
        uni.showToast({ title: '模型端未就绪', icon: 'none' })
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
      uni.showLoading({ title: '下载中...', mask: true })
      uni.downloadFile({
        url,
        success: () => {
          uni.hideLoading()
          uni.showToast({ title: '已下载', icon: 'success' })
        },
        fail: () => {
          uni.hideLoading()
          uni.showToast({ title: '下载失败', icon: 'none' })
        }
      })
    },
    async uploadMultimodalForHeatmap(files) {
      if (this.isH5) {
        return this.uploadMultimodalFetch('/api/ctv/heatmap', files)
      }
      return this.uploadMultimodalFile('/api/ctv/heatmap', files)
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
  background: #f7f7f8;
}

.study-modalities {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12rpx;
  margin-top: 12rpx;
}

.modality-item {
  padding: 12rpx;
  background: #f7f7f9;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
  border: 1rpx solid #e6e7eb;
}

.section-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #111318;
  margin-bottom: 12rpx;
}

.segment-actions,
.action-row {
  display: flex;
  gap: 12rpx;
  flex-wrap: wrap;
  align-items: center;
}

.segment-status {
  margin-top: 12rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
}

.preview {
  margin-top: 12rpx;
}

.heatmap-image {
  width: 100%;
  border-radius: 12rpx;
  border: 1rpx solid #e6e7eb;
}

.hint {
  margin-top: 12rpx;
}

.label {
  color: #0c0d0f;
  font-weight: 600;
}

.subtle {
  color: #6b7075;
  font-size: 24rpx;
}
</style>
