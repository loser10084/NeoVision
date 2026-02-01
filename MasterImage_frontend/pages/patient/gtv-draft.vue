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
        <view class="section-title">GTV &#x521D;&#x7A3F;</view>
        <view class="segment-actions">
          <wd-button
            size="small"
            shape="round"
            type="primary"
            plain
            :loading="processing"
            :disabled="processing || !hasFlair"
            @click="runFlairSegmentation"
          >
            Flair &#x57FA;&#x7840;&#x5206;&#x5272;
          </wd-button>
          <wd-button
            size="small"
            shape="round"
            type="default"
            plain
            :loading="processing"
            :disabled="processing || !hasAllModalities"
            @click="runMultimodalSegmentation"
          >
            &#x591A;&#x6A21;&#x6001;&#x5206;&#x5272;
          </wd-button>
        </view>
        <view class="segment-status">
          <text class="label">Label</text>
          <wd-tag plain :type="labelUrl ? 'success' : 'warning'">
            {{ labelUrl ? '已生成' : '未生成' }}
          </wd-tag>
        </view>
        <view class="download-actions">
          <wd-button
            size="small"
            shape="round"
            type="default"
            plain
            @click="openDownloadSheet"
          >
            &#x4E0B;&#x8F7D;
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


  <wd-action-sheet
    v-model="downloadSheetVisible"
    title="&#x9009;&#x62E9;&#x4E0B;&#x8F7D;&#x5185;&#x5BB9;"
    cancel-text="&#x5173;&#x95ED;"
    :actions="downloadSheetActions"
    @select="handleDownloadPick"
  />
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
      studyPickerVisible: false,
      studyPickerActions: [],
      downloadSheetVisible: false,
      downloadSheetActions: [],
      isH5: false
    }
  },
  computed: {
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
    buildDownloadActions() {
      const actions = []
      actions.push({
        name: 'Label',
        id: 'label',
        disabled: !this.labelUrl
      })
      actions.push({
        name: 'Flair',
        id: 'flair',
        disabled: !this.getModalityFile(this.activeStudyId, 'flair') && !this.volumeUrl
      })
      actions.push({
        name: 'T1',
        id: 't1',
        disabled: !this.getModalityFile(this.activeStudyId, 't1')
      })
      actions.push({
        name: 'T1c',
        id: 't1c',
        disabled: !this.getModalityFile(this.activeStudyId, 't1c')
      })
      actions.push({
        name: 'T2',
        id: 't2',
        disabled: !this.getModalityFile(this.activeStudyId, 't2')
      })
      this.downloadSheetActions = actions
    },
    openDownloadSheet() {
      this.buildDownloadActions()
      this.downloadSheetVisible = true
    },
    handleDownloadPick({ item }) {
      if (!item?.id) return
      if (item.id === 'label') {
        this.downloadLabel()
        return
      }
      this.downloadModality(item.id)
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
      await this.triggerDownload(this.labelUrl, 'label')
    },
    async downloadModality(modality) {
      if (!this.activeStudyId) return
      const file = this.getModalityFile(this.activeStudyId, modality)
      const url = file?.filePath || file?.localPath || ''
      if (!url && modality === 'flair' && this.volumeUrl) {
        await this.triggerDownload(this.volumeUrl, modality)
        return
      }
      if (!url) {
        uni.showToast({ title: '暂无该模态文件', icon: 'none' })
        return
      }
      await this.triggerDownload(url, modality)
    },
    async triggerDownload(url, name) {
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
.download-actions,
.viewer-actions,
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

.label {
  color: #0c0d0f;
  font-weight: 600;
}

.subtle {
  color: #6b7075;
  font-size: 24rpx;
}
</style>
