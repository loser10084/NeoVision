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
        <view class="section-title">CTV 精修</view>
        <view class="segment-status">
          <text class="label">外扩 Label</text>
          <wd-tag plain :type="expandLabelFile ? 'success' : 'warning'">
            {{ expandLabelFile ? '已生成' : '未生成' }}
          </wd-tag>
        </view>
        <view class="segment-status">
          <text class="label">精修 Label</text>
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
            @click="downloadRefinedLabel"
          >
            下载精修 Label
          </wd-button>
          <wd-button
            size="small"
            shape="round"
            type="default"
            plain
            :loading="processing"
            :disabled="processing || !canSubmit"
            @click="submitExpand"
          >
            开始分割
          </wd-button>
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
      return this.expandLabelMap?.[this.activeStudyId] || null
    },
    refinedLabelStatusText() {
      if (!this.refinedLabelFile) return '\u672a\u751f\u6210'
      return '\u5df2\u751f\u6210'
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

    buildExpandPayload() {
      const label = this.refinedLabelFile || {}
      const modalities = {}
      this.modalityOrder.forEach((modality) => {
        const file = this.getModalityFile(this.activeStudyId, modality)
        if (file) {
          modalities[modality] = {
            name: file.name || '',
            filePath: file.filePath || '',
            localPath: file.localPath || ''
          }
        }
      })
      return {
        patientId: this.patientId,
        studyId: this.activeStudyId,
        labelName: label.name || '',
        labelPath: label.filePath || label.localPath || '',
        labelSource: label.source || 'ctv_refine',
        modalities
      }
    },
    async downloadRefinedLabel() {
      const label = this.refinedLabelFile
      const url = label?.filePath || label?.localPath || ''
      if (!url) {
        uni.showToast({ title: '\u6682\u65e0\u7cbe\u4fee Label', icon: 'none' })
        return
      }
      await this.triggerDownload(url)
    },
    async triggerDownload(url) {
      if (!url) return
      const resolvedUrl = this.resolveDownloadUrl(url)
      uni.showLoading({ title: '\u4e0b\u8f7d\u4e2d...', mask: true })
      return new Promise((resolve) => {
        uni.downloadFile({
          url: resolvedUrl,
          success: (res) => {
            if (res.statusCode !== 200) {
              uni.showToast({ title: '\u4e0b\u8f7d\u5931\u8d25', icon: 'none' })
              uni.hideLoading()
              resolve(null)
              return
            }
            if (typeof uni.saveFile === 'function') {
              uni.saveFile({
                tempFilePath: res.tempFilePath,
                success: (saveRes) => {
                  uni.hideLoading()
                  uni.showToast({ title: '\u5df2\u4fdd\u5b58', icon: 'success' })
                  resolve(saveRes.savedFilePath)
                },
                fail: () => {
                  uni.hideLoading()
                  uni.showToast({ title: '\u5df2\u4e0b\u8f7d', icon: 'success' })
                  resolve(res.tempFilePath)
                }
              })
              return
            }
            uni.hideLoading()
            uni.showToast({ title: '\u5df2\u4e0b\u8f7d', icon: 'success' })
            resolve(res.tempFilePath)
          },
          fail: () => {
            uni.hideLoading()
            uni.showToast({ title: '\u4e0b\u8f7d\u5931\u8d25', icon: 'none' })
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
