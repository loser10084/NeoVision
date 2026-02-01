<template>
  <view class="page">
    <view class="safe-area">
      <view class="card">
        <view class="section-title">&#x5DF2;&#x4E0A;&#x4F20;&#x6A21;&#x6001;</view>
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
            &#x9009;&#x62E9;&#x5E8F;&#x5217;
          </wd-button>
          <text class="subtle">&#x5F53;&#x524D;&#x5E8F;&#x5217;&#xFF1A;{{ activeStudyId || '-' }}</text>
        </view>
      </view>

      <view class="card">
        <view class="section-title">CTV &#x5916;&#x6269;</view>
        <view class="segment-status">
          <text class="label">GTV Label</text>
          <wd-tag plain :type="gtvLabelStatusType">
            {{ gtvLabelStatusText }}
          </wd-tag>
        </view>
        <view class="segment-status">
          <text class="label">&#x5916;&#x6269; Label</text>
          <wd-tag plain :type="refinedLabelStatusType">
            {{ refinedLabelStatusText }}
          </wd-tag>
        </view>
        <view class="segment-actions">
          <wd-button
            size="small"
            shape="round"
            type="primary"
            plain
            :loading="processing"
            :disabled="processing"
            @click="uploadGtvLabel"
          >
            &#x4E0A;&#x4F20; GTV Label
          </wd-button>
          <wd-button
            size="small"
            shape="round"
            type="default"
            plain
            :loading="processing"
            :disabled="processing || !canSubmit"
            @click="submitRefine"
          >
            &#x5F00;&#x59CB;&#x5206;&#x5272;
          </wd-button>
        </view>
      </view>
    </view>
  </view>

  <wd-action-sheet
    v-model="studyPickerVisible"
    title="&#x9009;&#x62E9;&#x5E8F;&#x5217;"
    cancel-text="&#x5173;&#x95ED;"
    :actions="studyPickerActions"
    @select="handleStudyPick"
  />
</template>

<script>
import { getStudiesByPatient, getModel, upsertContour } from '../../common/api'
import { resolveModelUrl, resolveStudyResourceUrl, getToken } from '../../common/request'

export default {
  data() {
    return {
      patientId: '',
      activeStudyId: '',
      studies: [],
      gtvLabelUrl: '',
      studyFileMap: {},
      refinedLabelMap: {},
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
    refinedLabelFile() {
      return this.refinedLabelMap?.[this.activeStudyId] || null
    },
    refinedLabelStatusText() {
      if (!this.refinedLabelFile) return '未上传'
      if (this.refinedLabelFile.source === 'upload') return '已上传'
      if (this.refinedLabelFile.source === 'model') return '已生成'
      return '已生成'
    },
    refinedLabelStatusType() {
      return this.refinedLabelFile ? 'success' : 'warning'
    },
    gtvLabelFile() {
      return this.studyFileMap?.[this.activeStudyId]?.label || null
    },
    hasGtvLabel() {
      return !!(this.gtvLabelFile || this.gtvLabelUrl)
    },
    gtvLabelStatusText() {
      if (this.gtvLabelFile) return '\u5df2\u4e0a\u4f20'
      return this.gtvLabelUrl ? '\u5df2\u751f\u6210' : '\u672a\u751f\u6210'
    },
    gtvLabelStatusType() {
      return this.hasGtvLabel ? 'success' : 'warning'
    },
    canSubmit() {
      return this.hasAllModalities && this.hasGtvLabel
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
    await this.fetchStudies()
    await this.fetchModel()
  },
  methods: {
    storageKey() {
      return `study_files_${this.patientId || ''}`
    },
    refineStorageKey() {
      return `ctv_refine_${this.patientId || ''}`
    },
    loadStudyFilesFromStorage() {
      const key = this.storageKey()
      if (!key) return
      const cache = uni.getStorageSync(key)
      this.studyFileMap = cache && typeof cache === 'object' ? cache : {}
    },
    saveStudyFilesToStorage() {
      const key = this.storageKey()
      if (!key) return
      uni.setStorageSync(key, this.studyFileMap || {})
    },
    loadRefinedLabelsFromStorage() {
      const key = this.refineStorageKey()
      if (!key) return
      const cache = uni.getStorageSync(key)
      this.refinedLabelMap = cache && typeof cache === 'object' ? cache : {}
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
    getGtvLabelInput() {
      const label = this.studyFileMap?.[this.activeStudyId]?.label || null
      if (label) return label
      if (this.gtvLabelUrl) {
        return {
          name: 'gtv_label.nrrd',
          filePath: this.resolveLabelUrl(this.gtvLabelUrl),
          localPath: ''
        }
      }
      return null
    },
    resolveLabelUrl(url) {
      if (!url) return ''
      if (/^https?:\/\//i.test(url)) return url
      return resolveStudyResourceUrl(url)
    },
    collectModalityFiles() {
      return {
        flair: this.getModalityFile(this.activeStudyId, 'flair'),
        t1: this.getModalityFile(this.activeStudyId, 't1'),
        t1c: this.getModalityFile(this.activeStudyId, 't1c'),
        t2: this.getModalityFile(this.activeStudyId, 't2'),
        gtv: this.getGtvLabelInput()
      }
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
      await this.fetchModel()
    },
    async fetchModel() {
      if (!this.activeStudyId) return
      try {
        const model = await getModel(this.activeStudyId)
        this.gtvLabelUrl = model?.labelUrl || ''
      } catch (err) {
        console.error('getModel error', err)
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
            const fileObj =
              file.file || (typeof File !== 'undefined' && file instanceof File ? file : null)
            resolve({ ...file, path, name, fileObj })
          },
          fail: () => resolve(null)
        })
      })
    },
    async uploadGtvLabel() {
      if (this.processing) return
      const file = await this.pickFile()
      if (!file || !file.path) return
      this.processing = true
      try {
        const current = this.studyFileMap?.[this.activeStudyId] || {}
        this.studyFileMap = {
          ...(this.studyFileMap || {}),
          [this.activeStudyId]: {
            ...current,
            label: {
              name: file.name || '',
              localPath: file.path || '',
              filePath: '',
              source: 'upload'
            }
          }
        }
        this.saveStudyFilesToStorage()
        uni.showToast({ title: '\u4e0a\u4f20\u6210\u529f', icon: 'success' })
      } catch (err) {
        console.error('upload gtv label error', err)
        uni.showToast({ title: '\u4e0a\u4f20\u5931\u8d25', icon: 'none' })
      } finally {
        this.processing = false
      }
    },
    async submitRefine() {
      if (!this.canSubmit) {
        uni.showToast({ title: '缺少多模态数据', icon: 'none' })
        return
      }
      if (this.processing) return
      this.processing = true
      uni.showLoading({ title: '分割中...', mask: true })
      try {
        const files = this.collectModalityFiles()
        const result = await this.uploadMultimodalForRefine(files)
        if (result?.downloadUrl) {
          const url = resolveModelUrl(result.downloadUrl)
          this.refinedLabelMap = {
            ...(this.refinedLabelMap || {}),
            [this.activeStudyId]: {
              name: result.fileName || 'ctv_refined.nrrd',
              filePath: url,
              localPath: '',
              source: 'model'
            }
          }
          this.saveRefinedLabelsToStorage()
          await this.syncContourResult(url)
        }
        uni.showToast({ title: '分割完成', icon: 'success' })
      } catch (err) {
        console.error('submit refine error', err)
        uni.showToast({ title: '模型端未就绪', icon: 'none' })
      } finally {
        this.processing = false
        uni.hideLoading()
      }
    },
    async uploadMultimodalForRefine(files) {
      if (this.isH5) {
        return this.uploadMultimodalFetch('/api/ctv/refine', files)
      }
      return this.uploadMultimodalFile('/api/ctv/refine', files)
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
    },
    async uploadMultimodalFile(endpoint, files) {
      const flairPath = await this.resolveLocalPath(files.flair)
      const t1Path = await this.resolveLocalPath(files.t1)
      const t1cPath = await this.resolveLocalPath(files.t1c)
      const t2Path = await this.resolveLocalPath(files.t2)
      const gtvPath = await this.resolveLocalPath(files.gtv)
      if (!flairPath || !t1Path || !t1cPath || !t2Path || !gtvPath) {
        throw new Error('Missing local file')
      }
      const fileList = [
        { name: 'flair', filePath: flairPath },
        { name: 't1', filePath: t1Path },
        { name: 't1c', filePath: t1cPath },
        { name: 't2', filePath: t2Path },
        { name: 'gtv', filePath: gtvPath }
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
      const gtvBlob = await this.fetchBlob(files.gtv)
      if (!flairBlob || !t1Blob || !t1cBlob || !t2Blob || !gtvBlob) {
        throw new Error('Missing file data')
      }
      const form = new FormData()
      form.append('flair', flairBlob, files.flair?.name || 'flair.nrrd')
      form.append('t1', t1Blob, files.t1?.name || 't1.nrrd')
      form.append('t1c', t1cBlob, files.t1c?.name || 't1c.nrrd')
      form.append('t2', t2Blob, files.t2?.name || 't2.nrrd')
      form.append('gtv', gtvBlob, files.gtv?.name || 'gtv_label.nrrd')
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
