<template>
  <view class="page">
    <view class="safe-area ctv-area">
      <view class="ctv-hero">
        <view class="hero-main">
          <view>
            <text class="hero-title">CTV 外扩工作台</text>
            <text class="hero-subtitle">基于 GTV 与多模态影像生成外扩靶区建议</text>
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
            <text class="metric-label">外扩 Label</text>
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
      </view>

      <view class="card block-card">
        <view class="section-header">
          <text class="section-title">外扩执行</text>
          <text class="status-pill" :class="`status-pill--${refinedLabelStatusType}`">{{ refinedLabelStatusText }}</text>
        </view>

        <view class="workflow-strip">
          <view class="flow-step">
            <text class="flow-index">1</text>
            <text class="flow-text">模态检查</text>
          </view>
          <view class="flow-link"></view>
          <view class="flow-step">
            <text class="flow-index">2</text>
            <text class="flow-text">上传GTV</text>
          </view>
          <view class="flow-link"></view>
          <view class="flow-step">
            <text class="flow-index">3</text>
            <text class="flow-text">生成外扩</text>
          </view>
        </view>

        <view class="segment-status">
          <text class="label">GTV Label</text>
          <text class="status-pill" :class="`status-pill--${gtvLabelStatusType}`">{{ gtvLabelStatusText }}</text>
        </view>
        <view class="segment-status">
          <text class="label">外扩 Label</text>
          <text class="status-pill" :class="`status-pill--${refinedLabelStatusType}`">{{ refinedLabelStatusText }}</text>
        </view>

        <view class="segment-actions">
          <button class="mi-btn mi-btn--primary" :disabled="processing" @click="uploadGtvLabel">
            {{ processing ? '处理中...' : '上传 GTV Label' }}
          </button>
          <button class="mi-btn mi-btn--ghost" :disabled="processing || !canSubmit" @click="submitRefine">
            开始外扩分割
          </button>
        </view>
      </view>
    </view>
  </view>
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
      if (this.gtvLabelFile) return '已上传'
      return this.gtvLabelUrl ? '已生成' : '未生成'
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
        if (choose) {
          choose({
            count: 1,
            type: 'all',
            success: (res) => {
              const file = res.tempFiles && res.tempFiles[0]
              if (!file) {
                resolve(null)
                return
              }
              const path = this.normalizeNativeFilePath(file.path || file.tempFilePath)
              const name = file.name || (path ? path.split('/').pop() : '')
              const fileObj = file.file || (typeof File !== 'undefined' && file instanceof File ? file : null)
              resolve({ ...file, path, name, fileObj })
            },
            fail: () => resolve(null)
          })
          return
        }
        if (typeof plus !== 'undefined' && plus.io && typeof plus.io.chooseFile === 'function') {
          plus.io.chooseFile(
            { count: 1, multiple: false, filetypes: ['*'], title: 'Select File' },
            (res) => {
              const raw = Array.isArray(res?.files) ? res.files[0] : (Array.isArray(res) ? res[0] : res)
              if (!raw) {
                resolve(null)
                return
              }
              const path = this.normalizeNativeFilePath(raw.path || raw.filePath || raw.tempFilePath || raw.url || String(raw))
              const name = raw.name || (path ? path.split('/').pop() : '')
              resolve({ ...raw, path, name, fileObj: null })
            },
            () => resolve(null)
          )
          return
        }
        this.tryPickByAndroidIntent('*/*').then(resolve).catch(() => resolve(null))
      })
    },
    tryPickByAndroidIntent(mimeType = '*/*') {
      if (!this.isAppPlusRuntime() || String(plus.os?.name || '').toLowerCase() !== 'android') {
        return Promise.resolve(null)
      }
      return new Promise((resolve, reject) => {
        const main = plus.android.runtimeMainActivity()
        if (!main) {
          resolve(null)
          return
        }
        const Intent = plus.android.importClass('android.content.Intent')
        const Activity = plus.android.importClass('android.app.Activity')
        const requestCode = Number(Date.now() % 60000) + 1000
        const previous = main.onActivityResult
        let settled = false
        const finish = (err, value = null) => {
          if (settled) return
          settled = true
          main.onActivityResult = previous
          if (err) {
            reject(err)
            return
          }
          resolve(value)
        }
        const self = this
        main.onActivityResult = function(request, resultCode, data) {
          if (request !== requestCode) {
            if (typeof previous === 'function') previous(request, resultCode, data)
            return
          }
          if (resultCode !== Activity.RESULT_OK || !data) {
            finish(null, null)
            return
          }
          try {
            const uri = data.getData && data.getData()
            if (!uri) {
              finish(null, null)
              return
            }
            plus.android.importClass(uri)
            const uriString = String(uri.toString ? uri.toString() : '')
            if (!uriString) {
              finish(null, null)
              return
            }
            const meta = self.queryContentUriMeta(uriString)
            finish(null, {
              path: uriString,
              tempFilePath: uriString,
              name: meta.name || self.extractLocalFileName(uriString),
              size: Number(meta.size || 0)
            })
          } catch (err) {
            finish(err)
          }
        }
        try {
          const intent = new Intent(Intent.ACTION_GET_CONTENT)
          intent.addCategory(Intent.CATEGORY_OPENABLE)
          intent.setType(mimeType || '*/*')
          intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
          const chooser = Intent.createChooser(intent, 'Select File')
          main.startActivityForResult(chooser, requestCode)
        } catch (err) {
          finish(err)
        }
      })
    },
    normalizeNativeFilePath(path) {
      const raw = String(path || '').trim()
      if (!raw) return ''
      if (/^file:\/\//i.test(raw)) return decodeURIComponent(raw.replace(/^file:\/\//i, ''))
      return raw
    },
    extractLocalFileName(path) {
      const normalized = String(path || '').replace(/\\/g, '/')
      const parts = normalized.split('/')
      return decodeURIComponent(parts[parts.length - 1] || '')
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
        uni.showToast({ title: '上传成功', icon: 'success' })
      } catch (err) {
        console.error('upload gtv label error', err)
        uni.showToast({ title: '上传失败', icon: 'none' })
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
          formData: this.buildStorageFormData(),
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
      const storageMeta = this.buildStorageFormData()
      if (storageMeta.patientId) form.append('patientId', storageMeta.patientId)
      if (storageMeta.studyId) form.append('studyId', storageMeta.studyId)
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
      if (local && !/^https?:\/\//i.test(local)) return this.resolveUploadPath(local, file.name || '')
      const remote = file.filePath || ''
      if (!remote || !/^https?:\/\//i.test(remote)) return this.resolveUploadPath(remote, file.name || '')
      return new Promise((resolve) => {
        uni.downloadFile({
          url: remote,
          success: (res) => resolve(res.tempFilePath),
          fail: () => resolve('')
        })
      })
    },
    async resolveUploadPath(path, name = '') {
      const raw = this.normalizeNativeFilePath(path)
      if (!raw) return ''
      if (!this.isAppPlusRuntime()) return raw
      if (/^content:\/\//i.test(raw)) {
        const copied = await this.copyContentUriToPrivateDoc(raw, name).catch((err) => {
          console.error('copy content uri failed', err)
          return ''
        })
        if (!copied) return ''
        return this.toNativeUploadPath(copied)
      }
      return this.toNativeUploadPath(raw)
    },
    toNativeUploadPath(path) {
      let local = this.normalizeNativeFilePath(path)
      if (!local) return ''
      if (this.isAppPlusRuntime() && typeof plus.io.convertLocalFileSystemURL === 'function') {
        const lower = local.toLowerCase()
        if (lower.startsWith('_doc/') || lower.startsWith('_documents/') || lower.startsWith('_www/')) {
          local = plus.io.convertLocalFileSystemURL(local)
        }
      }
      return local
    },
    isAppPlusRuntime() {
      return typeof plus !== 'undefined' && !!plus.io
    },
    buildSafeCopyName(name = '') {
      const fallback = 'upload.bin'
      const base = String(name || fallback).trim() || fallback
      const sanitized = base.replace(/[\/:*?"<>|]/g, '_')
      const dot = sanitized.lastIndexOf('.')
      const stem = dot > 0 ? sanitized.slice(0, dot) : sanitized
      const ext = dot > 0 ? sanitized.slice(dot) : '.bin'
      return stem + '_' + Date.now() + ext
    },
    copyContentUriToPrivateDoc(contentUri, sourceName = '') {
      if (!this.isAppPlusRuntime()) return Promise.resolve('')
      if (String(plus.os?.name || '').toLowerCase() !== 'android') return Promise.resolve('')
      return new Promise((resolve, reject) => {
        plus.io.requestFileSystem(
          plus.io.PRIVATE_DOC,
          (fs) => {
            fs.root.getDirectory(
              'ctv-upload',
              { create: true },
              () => {
                try {
                  const targetName = this.buildSafeCopyName(sourceName || 'upload.bin')
                  const relativePath = '_doc/ctv-upload/' + targetName
                  const absolutePath = plus.io.convertLocalFileSystemURL(relativePath)
                  this.streamContentUriToFile(contentUri, absolutePath)
                  resolve(relativePath)
                } catch (err) {
                  reject(err)
                }
              },
              (err) => reject(err),
            )
          },
          (err) => reject(err),
        )
      })
    },
    queryContentUriMeta(contentUri) {
      if (!this.isAppPlusRuntime()) return { name: '', size: 0 }
      try {
        const activity = plus.android.runtimeMainActivity()
        const Uri = plus.android.importClass('android.net.Uri')
        const OpenableColumns = plus.android.importClass('android.provider.OpenableColumns')
        const resolver = activity.getContentResolver()
        const uri = Uri.parse(contentUri)
        const cursor = resolver.query(uri, null, null, null, null)
        if (!cursor) return { name: '', size: 0 }
        let name = ''
        let size = 0
        try {
          if (cursor.moveToFirst()) {
            const nameIdx = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
            const sizeIdx = cursor.getColumnIndex(OpenableColumns.SIZE)
            if (nameIdx >= 0) name = String(cursor.getString(nameIdx) || '')
            if (sizeIdx >= 0) size = Number(cursor.getLong(sizeIdx) || 0)
          }
        } finally {
          cursor.close()
        }
        return { name, size }
      } catch (err) {
        console.error('query content uri meta failed', err)
        return { name: '', size: 0 }
      }
    },
    streamContentUriToFile(contentUri, absolutePath) {
      if (!this.isAppPlusRuntime()) return
      const activity = plus.android.runtimeMainActivity()
      const Uri = plus.android.importClass('android.net.Uri')
      const resolver = activity.getContentResolver()
      const uri = Uri.parse(contentUri)
      const inputStream = resolver.openInputStream(uri)
      if (!inputStream) throw new Error('open input stream failed')
      const outputStream = plus.android.newObject('java.io.FileOutputStream', absolutePath)
      try {
        let value = inputStream.read()
        while (value !== -1) {
          outputStream.write(value)
          value = inputStream.read()
        }
        outputStream.flush()
      } finally {
        this.closeJavaStream(outputStream)
        this.closeJavaStream(inputStream)
      }
    },
    closeJavaStream(stream) {
      if (!stream || typeof stream.close !== 'function') return
      try {
        stream.close()
      } catch (err) {
        console.error('close java stream failed', err)
      }
    },
    buildStorageFormData() {
      const formData = {}
      if (this.patientId) formData.patientId = String(this.patientId)
      if (this.activeStudyId) formData.studyId = String(this.activeStudyId)
      return formData
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

.mi-btn--primary[disabled] {
  opacity: 1;
  background: #dce9f9;
  border-color: #c3d8f3;
  color: #3b5f88;
  box-shadow: none;
  -webkit-text-fill-color: currentColor;
}

.mi-btn--ghost[disabled] {
  opacity: 1;
  background: #f4f8fd;
  border-color: #d9e6f7;
  color: #6b86a8;
  box-shadow: none;
  -webkit-text-fill-color: currentColor;
}

.mi-btn[disabled] {
  opacity: 1;
  box-shadow: none;
  -webkit-text-fill-color: currentColor;
}

button::after {
  border: none;
}
</style>

