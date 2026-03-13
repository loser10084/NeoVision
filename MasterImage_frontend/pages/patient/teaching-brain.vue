<template>
  <view class="page">
    <view class="safe-area container">
      <view class="hero card">
        <text class="hero-title">{{ text.title }}</text>
        <text class="hero-subtitle">{{ text.subtitle }}</text>
      </view>

      <view class="card">
        <view class="section-head">
          <text class="section-title">{{ text.fileTitle }}</text>
          <button class="mi-btn mi-btn--ghost mi-btn--mini" @click="pickNrrdFile">{{ fileMeta ? text.reselect : text.selectFile }}</button>
        </view>
        <view v-if="fileMeta" class="file-row">
          <view class="file-name">{{ fileMeta.name }}</view>
          <view class="file-size">{{ readableFileSize }}</view>
        </view>
        <text v-else class="subtle">{{ text.fileHint }}</text>
      </view>

      <view class="card">
        <view class="section-head">
          <text class="section-title">{{ text.module3d }}</text>
          <text class="status-pill" :class="threeDLabelUrl ? 'status-pill--success' : 'status-pill--warning'">
            {{ threeDLabelUrl ? text.ready : text.pending }}
          </text>
        </view>
        <view class="action-row">
          <button class="mi-btn mi-btn--primary" :disabled="busy3d || !fileMeta" @click="generate3D">
            {{ busy3d ? text.processing : text.generate3D }}
          </button>
          <button class="mi-btn mi-btn--ghost" :disabled="!threeDLabelUrl" @click="open3DViewer">{{ text.open3d }}</button>
        </view>
      </view>

      <view class="card">
        <view class="section-head">
          <text class="section-title">{{ text.moduleHeatmap }}</text>
          <text class="status-pill" :class="heatmapUrl ? 'status-pill--success' : 'status-pill--warning'">
            {{ heatmapUrl ? text.ready : text.pending }}
          </text>
        </view>
        <view class="action-row">
          <button class="mi-btn mi-btn--primary" :disabled="busyHeatmap || !fileMeta" @click="generateHeatmap">
            {{ busyHeatmap ? text.processing : text.generateHeatmap }}
          </button>
          <button class="mi-btn mi-btn--ghost" :disabled="!heatmapUrl" @click="downloadHeatmap">{{ text.downloadImage }}</button>
        </view>
        <view v-if="heatmapUrl" class="preview">
          <image :src="heatmapUrl" mode="widthFix" class="preview-image" />
        </view>
      </view>

      <view class="card">
        <view class="section-head">
          <text class="section-title">{{ text.moduleCpdm }}</text>
          <text class="status-pill" :class="`status-pill--${cpdmStatusType}`">{{ cpdmStatusText }}</text>
        </view>
        <view class="action-row">
          <button class="mi-btn mi-btn--primary" :disabled="cpdmSubmitting || !fileMeta" @click="generateCpdm">
            {{ cpdmSubmitting ? text.processing : text.generateCpdm }}
          </button>
          <button class="mi-btn mi-btn--ghost" :disabled="!cpdmPetPngUrl" @click="downloadCpdmImage">{{ text.downloadImage }}</button>
        </view>
        <view v-if="cpdmPetPngUrl" class="preview">
          <image :src="cpdmPetPngUrl" mode="widthFix" class="preview-image" />
        </view>
        <text v-if="cpdmError" class="error-text">{{ cpdmError }}</text>
      </view>
    </view>
  </view>
</template>

<script>
import { getToken, resolveModelUrl } from '../../common/request'
import { downloadWithMobileSupport } from '../../common/mobile-download'

export default {
  data() {
    return {
      text: {
        title: '\u8111\u6559\u5b66\u6a21\u677f',
        subtitle: '\u5355\u6587\u4ef6 NRRD\uff1a3D / \u70ed\u529b\u56fe / CPDM',
        fileTitle: '\u4e0a\u4f20 NRRD \u6587\u4ef6',
        fileHint: '\u8bf7\u5148\u9009\u62e9\u4e00\u4e2a .nrrd \u6587\u4ef6',
        selectFile: '\u9009\u62e9\u6587\u4ef6',
        reselect: '\u91cd\u9009',
        module3d: '3D \u63a5\u53e3',
        moduleHeatmap: '\u7f6e\u4fe1\u5ea6\u70ed\u529b\u56fe\u63a5\u53e3',
        moduleCpdm: 'CPDM \u751f\u6210\u63a5\u53e3',
        generate3D: '3D \u751f\u6210',
        open3d: '\u6253\u5f00 3D',
        generateHeatmap: '\u751f\u6210\u70ed\u529b\u56fe',
        generateCpdm: '\u751f\u6210 CPDM',
        downloadImage: '\u4e0b\u8f7d\u56fe\u7247',
        ready: '\u5df2\u751f\u6210',
        pending: '\u5f85\u751f\u6210',
        processing: '\u5904\u7406\u4e2d...'
      },
      isH5: false,
      fileMeta: null,
      busy3d: false,
      busyHeatmap: false,
      threeDVolumeUrl: '',
      threeDLabelUrl: '',
      heatmapUrl: '',
      cpdmJobId: '',
      cpdmStatus: 'idle',
      cpdmProgress: 0,
      cpdmPetPngUrl: '',
      cpdmError: '',
      cpdmSubmitting: false,
      cpdmPollingTimer: null,
      cpdmNotFoundHandled: false
    }
  },
  computed: {
    readableFileSize() {
      const size = Number(this.fileMeta?.size || 0)
      if (!size || size < 1024) return `${size || 0} B`
      if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
      return `${(size / (1024 * 1024)).toFixed(2)} MB`
    },
    cpdmStatusType() {
      if (this.cpdmStatus === 'completed') return 'success'
      if (this.cpdmStatus === 'failed') return 'danger'
      if (this.cpdmStatus === 'queued' || this.cpdmStatus === 'running') return 'primary'
      return 'warning'
    },
    cpdmStatusText() {
      if (this.cpdmStatus === 'completed') return '\u5df2\u5b8c\u6210'
      if (this.cpdmStatus === 'failed') return this.cpdmError || '\u5931\u8d25'
      if (this.cpdmStatus === 'queued' || this.cpdmStatus === 'running') {
        return `\u6267\u884c\u4e2d ${Number(this.cpdmProgress || 0)}%`
      }
      return '\u5f85\u63d0\u4ea4'
    }
  },
  onLoad() {
    this.isH5 = typeof window !== 'undefined' && typeof document !== 'undefined'
  },
  onUnload() {
    this.stopCpdmPolling()
  },
  methods: {
    async pickNrrdFile() {
      try {
        const picked = await this.chooseSingleFile()
        if (!picked) return
        let normalized = this.normalizePickedFile(picked)
        normalized = await this.preparePickedFileForUpload(normalized)
        if (!normalized || !normalized.name || !/\.nrrd$/i.test(normalized.name)) {
          uni.showToast({ title: '\u8bf7\u9009\u62e9 .nrrd \u6587\u4ef6', icon: 'none' })
          return
        }
        if (!normalized.filePath) {
          uni.showToast({ title: '\u6587\u4ef6\u8bfb\u53d6\u5931\u8d25\uff0c\u8bf7\u91cd\u65b0\u9009\u62e9', icon: 'none' })
          return
        }
        this.fileMeta = normalized
        this.threeDVolumeUrl = ''
        this.threeDLabelUrl = ''
        this.heatmapUrl = ''
        this.cpdmJobId = ''
        this.cpdmStatus = 'idle'
        this.cpdmProgress = 0
        this.cpdmPetPngUrl = ''
        this.cpdmError = ''
        this.cpdmNotFoundHandled = false
        this.stopCpdmPolling()
      } catch (err) {
        console.error('pick nrrd failed', err)
        uni.showToast({ title: this.pickErrorText(err) || '\u6587\u4ef6\u9009\u62e9\u5931\u8d25', icon: 'none' })
      }
    },
    async chooseSingleFile() {
      let lastError = null
      const byMessage = await this.tryChooseByUniApi('chooseMessageFile', {
        type: 'file',
        extension: ['nrrd']
      }).catch((err) => {
        lastError = err
        return null
      })
      if (byMessage) return byMessage
      const byFile = await this.tryChooseByUniApi('chooseFile').catch((err) => {
        lastError = err
        return null
      })
      if (byFile) return byFile
      const byPlus = await this.tryChooseByPlusFile().catch((err) => {
        lastError = err
        return null
      })
      if (byPlus) return byPlus
      const byIntent = await this.tryChooseByAndroidIntent('*/*').catch((err) => {
        lastError = err
        return null
      })
      if (byIntent) return byIntent
      if (lastError) throw lastError
      throw new Error('choose file api unavailable')
    },
    tryChooseByUniApi(apiName, extraOptions = {}) {
      const choose = uni?.[apiName]
      if (typeof choose !== 'function') return Promise.resolve(null)
      return new Promise((resolve, reject) => {
        choose({
          count: 1,
          ...extraOptions,
          success: (res) => {
            const first = (res.tempFiles || [])[0]
            if (first) {
              resolve(first)
              return
            }
            const fallbackPath = Array.isArray(res.tempFilePaths) ? (res.tempFilePaths[0] || '') : ''
            if (fallbackPath) {
              resolve({
                path: fallbackPath,
                tempFilePath: fallbackPath,
                name: this.extractFileName(fallbackPath)
              })
              return
            }
            resolve(null)
          },
          fail: (err) => {
            if (this.isChooseCancelled(err)) {
              resolve(null)
              return
            }
            reject(err)
          }
        })
      })
    },
    tryChooseByPlusFile() {
      if (typeof plus === 'undefined' || !plus.io || typeof plus.io.chooseFile !== 'function') {
        return Promise.resolve(null)
      }
      return new Promise((resolve, reject) => {
        let settled = false
        const finish = (err, value = null) => {
          if (settled) return
          settled = true
          if (err) {
            if (this.isChooseCancelled(err)) {
              resolve(null)
              return
            }
            reject(err)
            return
          }
          resolve(value)
        }
        const consumeResult = async (result) => {
          try {
            const normalized = await this.normalizePlusChosenResult(result)
            finish(null, normalized)
          } catch (err) {
            finish(err)
          }
        }
        try {
          const maybeTask = plus.io.chooseFile(
            {
              count: 1,
              multiple: false,
              filetypes: ['nrrd'],
              title: 'Select NRRD'
            },
            (res) => consumeResult(res),
            (err) => finish(err)
          )
          if (maybeTask && typeof maybeTask.then === 'function') {
            maybeTask.then((res) => consumeResult(res)).catch((err) => finish(err))
            return
          }
          if (this.looksLikePlusChooseResult(maybeTask)) {
            consumeResult(maybeTask)
          }
        } catch (err) {
          finish(err)
        }
      })
    },
    tryChooseByAndroidIntent(mimeType = '*/*') {
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
            if (this.isChooseCancelled(err)) {
              resolve(null)
              return
            }
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
              name: meta.name || self.extractFileName(uriString),
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
    looksLikePlusChooseResult(result) {
      if (!result) return false
      if (typeof result === 'string') return true
      if (Array.isArray(result) && result.length) return true
      if (Array.isArray(result.files) && result.files.length) return true
      return !!(result.path || result.filePath || result.tempFilePath || result.file)
    },
    async normalizePlusChosenResult(result) {
      const first = this.pickFirstChosenFile(result)
      if (!first) return null
      const rawPath = typeof first === 'string'
        ? first
        : first.path || first.filePath || first.tempFilePath || first.url || ''
      const filePath = this.normalizeNativeFilePath(rawPath)
      if (!filePath) return null
      const fallbackName = typeof first === 'string'
        ? this.extractFileName(filePath)
        : first.name || this.extractFileName(filePath)
      const fallbackSize = typeof first === 'string' ? 0 : Number(first.size || 0)
      const localMeta = await this.readLocalFileMeta(filePath)
      return {
        name: localMeta.name || fallbackName || 'input.nrrd',
        size: Number(localMeta.size || fallbackSize || 0),
        path: filePath,
        tempFilePath: filePath
      }
    },
    pickFirstChosenFile(result) {
      if (!result) return null
      if (typeof result === 'string') return result
      if (Array.isArray(result)) return result[0] || null
      if (Array.isArray(result.files)) return result.files[0] || null
      if (result.file) return result.file
      if (result.path || result.filePath || result.tempFilePath || result.url) return result
      return null
    },
    normalizeNativeFilePath(path) {
      const raw = String(path || '').trim()
      if (!raw) return ''
      if (/^file:\/\//i.test(raw)) {
        const pure = raw.replace(/^file:\/\//i, '')
        try {
          return decodeURIComponent(pure)
        } catch (err) {
          return pure
        }
      }
      return raw
    },
    isAppPlusRuntime() {
      return typeof plus !== 'undefined' && !!plus.io
    },
    isAppPrivatePath(path) {
      const value = String(path || '').toLowerCase()
      return value.startsWith('_doc/') || value.startsWith('_documents/') || value.startsWith('_www/')
    },
    toResolvableLocalUrl(path) {
      const value = String(path || '').trim()
      if (!value) return ''
      if (/^(file|content):\/\//i.test(value)) return value
      if (value.startsWith('/')) return `file://${value}`
      return value
    },
    buildSafeCopyName(name = '') {
      const fallback = 'input.nrrd'
      const base = String(name || fallback).trim() || fallback
      const sanitized = base.replace(/[\\/:*?"<>|]/g, '_')
      const dot = sanitized.lastIndexOf('.')
      const stem = dot > 0 ? sanitized.slice(0, dot) : sanitized
      const ext = dot > 0 ? sanitized.slice(dot) : '.nrrd'
      return `${stem}_${Date.now()}${ext}`
    },
    async preparePickedFileForUpload(file) {
      if (!file) return null
      const path = this.normalizeNativeFilePath(this.extractPickedPath(file))
      if (!path) return file
      let next = { ...file, filePath: path }
      if (!this.isAppPlusRuntime()) return next

      const shouldCopyToPrivate = !this.isAppPrivatePath(path) && !/^https?:\/\//i.test(path)
      if (shouldCopyToPrivate) {
        const copied = await this.copyFileToPrivateDoc(path, next.name).catch((err) => {
          console.error('copy to private doc failed', err)
          return null
        })
        if (copied?.filePath) {
          next = {
            ...next,
            name: copied.name || next.name,
            size: Number(copied.size || next.size || 0),
            filePath: copied.filePath,
            fileObj: null
          }
        }
      }

      if (!(Number(next.size || 0) > 0)) {
        const meta = await this.readLocalFileMeta(next.filePath)
        next = {
          ...next,
          name: next.name || meta.name || 'input.nrrd',
          size: Number(meta.size || next.size || 0)
        }
      }
      return next
    },
    copyFileToPrivateDoc(sourcePath, sourceName = '') {
      if (!this.isAppPlusRuntime()) return Promise.resolve(null)
      const targetPath = this.toResolvableLocalUrl(sourcePath)
      if (!targetPath) {
        return Promise.reject(new Error('empty source path'))
      }
      if (/^content:\/\//i.test(targetPath)) {
        return this.copyContentUriToPrivateDoc(targetPath, sourceName)
      }
      return new Promise((resolve, reject) => {
        plus.io.resolveLocalFileSystemURL(
          targetPath,
          (entry) => {
            plus.io.requestFileSystem(
              plus.io.PRIVATE_DOC,
              (fs) => {
                fs.root.getDirectory(
                  'teaching-brain',
                  { create: true },
                  (dirEntry) => {
                    const targetName = this.buildSafeCopyName(sourceName || entry.name || 'input.nrrd')
                    entry.copyTo(
                      dirEntry,
                      targetName,
                      (copiedEntry) => {
                        const copiedPath = copiedEntry?.toLocalURL?.() || copiedEntry?.fullPath || ''
                        copiedEntry.file(
                          (copiedFile) => resolve({
                            filePath: copiedPath,
                            name: copiedFile?.name || targetName,
                            size: Number(copiedFile?.size || 0)
                          }),
                          () => resolve({
                            filePath: copiedPath,
                            name: targetName,
                            size: 0
                          })
                        )
                      },
                      (err) => reject(err)
                    )
                  },
                  (err) => reject(err)
                )
              },
              (err) => reject(err)
            )
          },
          (err) => reject(err)
        )
      })
    },
    copyContentUriToPrivateDoc(contentUri, sourceName = '') {
      if (!this.isAppPlusRuntime()) return Promise.resolve(null)
      if (String(plus.os?.name || '').toLowerCase() !== 'android') {
        return Promise.reject(new Error('content uri copy is android only'))
      }
      return new Promise((resolve, reject) => {
        plus.io.requestFileSystem(
          plus.io.PRIVATE_DOC,
          (fs) => {
            fs.root.getDirectory(
              'teaching-brain',
              { create: true },
              async () => {
                try {
                  const meta = this.queryContentUriMeta(contentUri)
                  const targetName = this.buildSafeCopyName(sourceName || meta.name || 'input.nrrd')
                  const relativePath = `_doc/teaching-brain/${targetName}`
                  const absolutePath = plus.io.convertLocalFileSystemURL(relativePath)
                  const copiedBytes = this.streamContentUriToFile(contentUri, absolutePath)
                  const finalSize = copiedBytes > 0 ? copiedBytes : Number(meta.size || 0)
                  resolve({
                    filePath: relativePath,
                    name: targetName,
                    size: finalSize
                  })
                } catch (err) {
                  reject(err)
                }
              },
              (err) => reject(err)
            )
          },
          (err) => reject(err)
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
      if (!this.isAppPlusRuntime()) return 0
      const activity = plus.android.runtimeMainActivity()
      const Uri = plus.android.importClass('android.net.Uri')
      const resolver = activity.getContentResolver()
      const uri = Uri.parse(contentUri)
      const inputStream = resolver.openInputStream(uri)
      if (!inputStream) {
        throw new Error('open input stream failed')
      }
      const outputStream = plus.android.newObject('java.io.FileOutputStream', absolutePath)
      let copied = 0
      try {
        let value = inputStream.read()
        while (value !== -1) {
          outputStream.write(value)
          copied += 1
          value = inputStream.read()
        }
        outputStream.flush()
      } finally {
        this.closeJavaStream(outputStream)
        this.closeJavaStream(inputStream)
      }
      return copied
    },
    closeJavaStream(stream) {
      if (!stream || typeof stream.close !== 'function') return
      try {
        stream.close()
      } catch (err) {
        console.error('close java stream failed', err)
      }
    },
    readLocalFileMeta(path) {
      if (!path || typeof plus === 'undefined' || !plus.io || typeof plus.io.resolveLocalFileSystemURL !== 'function') {
        return Promise.resolve({ name: this.extractFileName(path), size: 0 })
      }
      return new Promise((resolve) => {
        plus.io.resolveLocalFileSystemURL(
          this.toResolvableLocalUrl(path),
          (entry) => {
            if (!entry || typeof entry.file !== 'function') {
              resolve({ name: this.extractFileName(path), size: 0 })
              return
            }
            entry.file(
              (file) => resolve({
                name: file?.name || this.extractFileName(path),
                size: Number(file?.size || 0)
              }),
              () => resolve({ name: this.extractFileName(path), size: 0 })
            )
          },
          () => resolve({ name: this.extractFileName(path), size: 0 })
        )
      })
    },
    isChooseCancelled(err) {
      const message = String(this.pickErrorText(err) || '').toLowerCase()
      return message.includes('cancel') || message.includes('\u53d6\u6d88')
    },
    extractFileName(path) {
      const normalized = String(path || '').replace(/\\/g, '/')
      const parts = normalized.split('/')
      try {
        return decodeURIComponent(parts[parts.length - 1] || '')
      } catch (err) {
        return parts[parts.length - 1] || ''
      }
    },
    extractPickedPath(file) {
      if (!file) return ''
      const direct = [
        file.filePath,
        file.path,
        file.tempFilePath,
        file.uri,
        file.localPath,
        file.savedFilePath,
        file.apFilePath,
        file.url
      ].find((v) => typeof v === 'string' && v.trim())
      if (direct) return direct
      if (Array.isArray(file.tempFilePaths)) {
        const first = file.tempFilePaths[0]
        if (typeof first === 'string' && first.trim()) return first
      }
      return ''
    },
    normalizePickedFile(file) {
      if (!file) return null
      const filePath = this.extractPickedPath(file)
      return {
        name: file.name || file.file?.name || this.extractFileName(filePath) || 'input.nrrd',
        size: Number(file.size || file.file?.size || 0),
        filePath,
        fileObj: file.file || null
      }
    },
    async generate3D() {
      if (this.busy3d || !this.fileMeta) return
      this.busy3d = true
      uni.showLoading({ title: '\u751f\u6210\u4e2d...', mask: true })
      try {
        const payload = await this.uploadSingleFile('/api/segment/teaching/3d', 'file')
        this.threeDVolumeUrl = resolveModelUrl(payload?.volumeUrl || '')
        this.threeDLabelUrl = resolveModelUrl(payload?.labelUrl || '')
        uni.showToast({ title: '\u751f\u6210\u6210\u529f', icon: 'success' })
      } catch (err) {
        console.error('generate 3d failed', err)
        uni.showToast({ title: this.pickErrorText(err) || '\u751f\u6210\u5931\u8d25', icon: 'none' })
      } finally {
        this.busy3d = false
        uni.hideLoading()
      }
    },
    open3DViewer() {
      if (!this.threeDVolumeUrl) return
      const volume = encodeURIComponent(this.threeDVolumeUrl)
      const label = encodeURIComponent(this.threeDLabelUrl || '')
      uni.navigateTo({ url: `/pages/model/viewer?volumeUrl=${volume}&labelUrl=${label}&mode=both` })
    },
    async generateHeatmap() {
      if (this.busyHeatmap || !this.fileMeta) return
      this.busyHeatmap = true
      uni.showLoading({ title: '\u751f\u6210\u4e2d...', mask: true })
      try {
        const payload = await this.uploadSingleFile('/api/segment/teaching/heatmap', 'file')
        this.heatmapUrl = resolveModelUrl(payload?.heatmapUrl || '')
        uni.showToast({ title: '\u751f\u6210\u6210\u529f', icon: 'success' })
      } catch (err) {
        console.error('generate heatmap failed', err)
        uni.showToast({ title: this.pickErrorText(err) || '\u751f\u6210\u5931\u8d25', icon: 'none' })
      } finally {
        this.busyHeatmap = false
        uni.hideLoading()
      }
    },
    async downloadHeatmap() {
      if (!this.heatmapUrl) return
      await this.downloadByUrl(this.heatmapUrl, 'heatmap.png')
    },
    async generateCpdm() {
      if (this.cpdmSubmitting || !this.fileMeta) return
      this.cpdmSubmitting = true
      this.cpdmStatus = 'queued'
      this.cpdmProgress = 0
      this.cpdmPetPngUrl = ''
      this.cpdmError = ''
      this.cpdmNotFoundHandled = false
      try {
        const payload = await this.uploadSingleFile('/api/cpdm/ct2pet', 'ct', {
          formData: this.buildCpdmCompatFormData()
        })
        const jobId = payload?.jobId || ''
        if (!jobId) {
          throw new Error('missing jobId')
        }
        this.cpdmJobId = jobId
        this.startCpdmPolling(jobId)
      } catch (err) {
        console.error('generate cpdm failed', err)
        this.cpdmStatus = 'failed'
        this.cpdmError = this.pickErrorText(err) || '\u63d0\u4ea4\u5931\u8d25'
        uni.showToast({ title: this.cpdmError, icon: 'none' })
      } finally {
        this.cpdmSubmitting = false
      }
    },
    startCpdmPolling(jobId) {
      this.stopCpdmPolling()
      if (!jobId) return
      this.queryCpdmJob(jobId)
      this.cpdmPollingTimer = setInterval(() => this.queryCpdmJob(jobId), 3000)
    },
    stopCpdmPolling() {
      if (this.cpdmPollingTimer) {
        clearInterval(this.cpdmPollingTimer)
        this.cpdmPollingTimer = null
      }
    },
    async queryCpdmJob(jobId) {
      try {
        const payload = await this.fetchCpdmJob(jobId)
        if (!payload) return
        this.cpdmStatus = payload.status || this.cpdmStatus
        this.cpdmProgress = Number(payload.progress || this.cpdmProgress || 0)
        if (this.cpdmStatus === 'completed') {
          const result = payload.result || {}
          this.cpdmPetPngUrl = resolveModelUrl(result.petPngUrl || `/api/cpdm/outputs/${jobId}/pet.png`)
          this.stopCpdmPolling()
        } else if (this.cpdmStatus === 'failed') {
          this.cpdmError = payload.error || '\u63a8\u7406\u5931\u8d25'
          this.stopCpdmPolling()
        }
      } catch (err) {
        console.error('cpdm polling failed', err)
        if (String(err?.message || '').includes('404')) {
          if (this.cpdmNotFoundHandled) return
          this.cpdmNotFoundHandled = true
          this.cpdmStatus = 'failed'
          this.cpdmError = '\u4efb\u52a1\u4e0d\u5b58\u5728'
          this.stopCpdmPolling()
          return
        }
        this.cpdmStatus = 'failed'
        this.cpdmError = this.pickErrorText(err) || '\u67e5\u8be2\u5931\u8d25'
        this.stopCpdmPolling()
      }
    },
    fetchCpdmJob(jobId) {
      return new Promise((resolve, reject) => {
        const token = getToken()
        uni.request({
          url: resolveModelUrl(`/api/cpdm/jobs/${jobId}`),
          method: 'GET',
          header: token ? { Authorization: `Bearer ${token}` } : {},
          success: (res) => {
            if (res.statusCode === 404) {
              reject(new Error('404'))
              return
            }
            if (res.statusCode < 200 || res.statusCode >= 300) {
              reject(new Error(`HTTP ${res.statusCode}`))
              return
            }
            resolve(res.data || null)
          },
          fail: (err) => reject(err)
        })
      })
    },
    async downloadCpdmImage() {
      if (!this.cpdmPetPngUrl) return
      await this.downloadByUrl(this.cpdmPetPngUrl, 'cpdm_pet.png')
    },
    buildCpdmCompatFormData() {
      const fallback = { patientId: '1', studyId: '1' }
      try {
        const cache = uni.getStorageSync('currentPatient') || {}
        const patientId = Number(cache.id || 0)
        const studyId = Number(cache.studyId || 0)
        if (patientId > 0 && studyId > 0) {
          return {
            patientId: String(patientId),
            studyId: String(studyId)
          }
        }
      } catch (err) {
        console.error('build cpdm context failed', err)
      }
      // Backward-compat: strict OSS mode in old model service requires IDs.
      return fallback
    },
    async uploadSingleFile(endpoint, fieldName, options = {}) {
      if (!this.fileMeta) throw new Error('missing file')
      if (this.isH5) {
        return this.uploadSingleFetch(endpoint, fieldName, options)
      }
      return this.uploadSingleNative(endpoint, fieldName, options)
    },
    async uploadSingleFetch(endpoint, fieldName, options = {}) {
      const blob = await this.fetchBlob(this.fileMeta)
      if (!blob) throw new Error('missing file data')
      const form = new FormData()
      form.append(fieldName, blob, this.fileMeta.name || 'input.nrrd')
      const extraFormData = options?.formData && typeof options.formData === 'object' ? options.formData : {}
      Object.keys(extraFormData).forEach((key) => {
        const value = extraFormData[key]
        if (value !== undefined && value !== null && String(value) !== '') {
          form.append(key, String(value))
        }
      })
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
    async uploadSingleNative(endpoint, fieldName, options = {}) {
      const localPath = await this.resolveLocalPath(this.fileMeta)
      if (!localPath) throw new Error('missing local file path')
      const token = getToken()
      const extraFormData = options?.formData && typeof options.formData === 'object' ? options.formData : {}
      const formData = {}
      Object.keys(extraFormData).forEach((key) => {
        const value = extraFormData[key]
        if (value !== undefined && value !== null && String(value) !== '') {
          formData[key] = String(value)
        }
      })
      return new Promise((resolve, reject) => {
        uni.uploadFile({
          url: resolveModelUrl(endpoint),
          filePath: localPath,
          name: fieldName,
          formData,
          header: token ? { Authorization: `Bearer ${token}` } : {},
          success: (res) => {
            try {
              const payload = typeof res.data === 'string' ? JSON.parse(res.data) : res.data
              if (!payload || payload.error) {
                reject(payload || new Error('invalid response'))
                return
              }
              resolve(payload)
            } catch (err) {
              reject(err)
            }
          },
          fail: (err) => reject(err)
        })
      })
    },
    async fetchBlob(file) {
      if (!file) return null
      if (file.fileObj) return file.fileObj
      const target = file.filePath || ''
      if (!target) return null
      const res = await fetch(target)
      if (!res.ok) return null
      return res.blob()
    },
    async resolveLocalPath(file) {
      if (!file) return ''
      let local = file.filePath || ''
      if (local && !/^https?:\/\//i.test(local)) {
        if (this.isAppPlusRuntime() && typeof plus.io.convertLocalFileSystemURL === 'function' && this.isAppPrivatePath(local)) {
          local = plus.io.convertLocalFileSystemURL(local)
        }
        return local
      }
      if (!local) return ''
      return new Promise((resolve) => {
        uni.downloadFile({
          url: local,
          success: (res) => resolve(res.tempFilePath || ''),
          fail: () => resolve('')
        })
      })
    },
    async downloadByUrl(url, filename) {
      await downloadWithMobileSupport({
        url,
        filename,
        loadingTitle: '\u4e0b\u8f7d\u4e2d...',
        successTitle: '\u5df2\u4e0b\u8f7d',
        failTitle: '\u4e0b\u8f7d\u5931\u8d25',
        autoOpen: false
      })
    },
    pickErrorText(err) {
      if (!err) return ''
      if (typeof err === 'string') return err
      if (typeof err.error === 'string' && err.error) return err.error
      if (typeof err.message === 'string' && err.message) return err.message
      return ''
    }
  }
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: #edf4ff;
}

.container {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.card {
  border-radius: 24rpx;
  background: #ffffff;
  border: 1rpx solid #d6e5f7;
  box-shadow: 0 12rpx 30rpx rgba(43, 104, 186, 0.12);
  padding: 20rpx;
}

.hero {
  background: linear-gradient(150deg, #2f78d8 0%, #3f88e6 46%, #6baef4 100%);
  border-color: rgba(255, 255, 255, 0.26);
}

.hero-title {
  display: block;
  font-size: 38rpx;
  font-weight: 700;
  color: #ffffff;
}

.hero-subtitle {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.86);
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
  margin-bottom: 12rpx;
}

.section-title {
  font-size: 30rpx;
  font-weight: 700;
  color: #12375f;
}

.file-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
  padding: 14rpx;
  border-radius: 14rpx;
  background: #f6faff;
  border: 1rpx solid #d6e5f7;
}

.file-name {
  color: #14385f;
  font-size: 25rpx;
  font-weight: 700;
  max-width: 72%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  color: #2f4f74;
  font-size: 22rpx;
}

.subtle {
  color: #3f6086;
  font-size: 24rpx;
}

.action-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.action-row .mi-btn {
  flex: 1 1 0;
  min-width: 0;
}

.mi-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin: 0;
  height: 68rpx;
  line-height: 68rpx;
  border-radius: 999rpx;
  border: 1rpx solid #9fbfe6;
  background: #ffffff;
  color: #163f6d !important;
  font-weight: 700;
  font-size: 24rpx;
  padding: 0 22rpx;
}

.mi-btn--primary {
  background: linear-gradient(135deg, #2469ba 0%, #1a4d92 100%);
  color: #ffffff !important;
  border-color: transparent;
  box-shadow: 0 10rpx 20rpx rgba(31, 88, 162, 0.28);
}

.mi-btn--ghost {
  background: #edf4ff;
  border-color: #9fbfe6;
  color: #184a86 !important;
}

.mi-btn--mini {
  height: 56rpx;
  line-height: 56rpx;
  padding: 0 18rpx;
  font-size: 22rpx;
  flex: 0 0 auto;
}

.mi-btn[disabled] {
  opacity: 1;
  color: #7f96b3 !important;
  background: #eef3fa;
  border-color: #d2ddec;
  box-shadow: none;
}

.mi-btn--primary[disabled] {
  color: #e7eef9 !important;
  background: linear-gradient(135deg, #8baad2 0%, #7e9abf 100%);
  border-color: transparent;
}

.mi-btn--ghost[disabled] {
  color: #7f96b3 !important;
  background: #f2f6fb;
  border-color: #d2ddec;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8rpx 16rpx;
  border-radius: 999rpx;
  border: 1rpx solid #d6e5f7;
  font-size: 22rpx;
  color: #2f4f74;
  background: #f5f9ff;
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

.status-pill--primary {
  color: #245eac;
  border-color: #bfd5ef;
  background: #eaf3ff;
}

.status-pill--danger {
  color: #b13d3d;
  border-color: #f2c8c8;
  background: #fff5f5;
}

.preview {
  margin-top: 12rpx;
}

.preview-image {
  width: 100%;
  border-radius: 14rpx;
  border: 1rpx solid #d6e5f7;
  background: #f7fbff;
}

.error-text {
  margin-top: 10rpx;
  color: #b13d3d;
  font-size: 22rpx;
}

button::after {
  border: none;
}
</style>
