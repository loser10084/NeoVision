<template>
  <view class="page">
    <view class="safe-area detail-area">
      <view class="detail-hero">
        <view class="hero-main">
          <view>
            <text class="hero-name">{{ patient.name || '未命名患者' }}</text>
            <text class="hero-subtitle">{{ patient.sex || '-' }} / {{ patient.age || '-' }} / {{ patient.stage || '-' }}</text>
          </view>
          <button class="mi-btn mi-btn--hero" @click="editProfile">编辑资料</button>
        </view>
        <view class="hero-meta">
          <text>ID {{ patient.id || '-' }}</text>
          <text>影像 {{ patient.studyId || '-' }}</text>
        </view>
        <view class="hero-kpi-grid">
          <view class="hero-kpi-item">
            <text class="hero-kpi-value">{{ studies.length }}</text>
            <text class="hero-kpi-label">影像序列</text>
          </view>
          <view class="hero-kpi-item">
            <text class="hero-kpi-value">{{ contours.length }}</text>
            <text class="hero-kpi-label">轮廓结果</text>
          </view>
          <view class="hero-kpi-item">
            <text class="hero-kpi-value">{{ isConfirmed ? '已确认' : '待确认' }}</text>
            <text class="hero-kpi-label">医生状态</text>
          </view>
        </view>
      </view>

      <view class="card summary-card">
        <view class="row summary-top-row">
          <view>
            <text class="name">病例概览</text>
            <text class="subtle summary-desc">{{ patient.diagnosis || '暂无诊断信息' }}</text>
          </view>
          <text class="status-pill" :class="`status-pill--${confirmButtonType}`">{{ confirmButtonText }}</text>
        </view>
        <view class="meta">
          <text>最近更新</text>
          <text>{{ patient.lastUpdate || '-' }}</text>
        </view>
        <view class="action-bar summary-actions">
          <button class="mi-btn mi-btn--primary" @click="confirmContour">{{ confirmButtonText }}</button>
          <button class="mi-btn mi-btn--ghost" @click="exportRT">导出结构</button>
          <button class="mi-btn mi-btn--danger" @click="confirmDeletePatient">{{ deletePatientText }}</button>
        </view>
      </view>

      <view class="card ai-card">
        <view class="section-title">靶区 AI 结果</view>
        <view class="result-list">
          <view class="result-row" @click="openGtvDraft(patient.studyId)">
            <text class="row-title">GTV 初稿</text>
            <view class="row-right">
              <text class="status-pill" :class="`status-pill--${gtvStatusType}`">{{ gtvStatusText }}</text>
              <text class="row-arrow">></text>
            </view>
          </view>
          <view class="result-row" @click="openCtvRefine(patient.studyId)">
            <text class="row-title">CTV 精修</text>
            <view class="row-right">
              <text class="status-pill" :class="`status-pill--${ctvStatusType}`">{{ ctvStatusText }}</text>
              <text class="row-arrow">></text>
            </view>
          </view>
          <view class="result-row" @click="openCtvExpand(patient.studyId)">
            <text class="row-title">CTV 外扩</text>
            <view class="row-right">
              <text class="status-pill" :class="`status-pill--${ctvExpandStatusType}`">{{ ctvExpandStatusText }}</text>
              <text class="row-arrow">></text>
            </view>
          </view>
          <view class="result-row" @click="openHeatmap(patient.studyId)">
            <text class="row-title">热力图与 CPDM</text>
            <view class="row-right">
              <text class="status-pill status-pill--warning">可查看</text>
              <text class="row-arrow">></text>
            </view>
          </view>
        </view>
      </view>

      <view class="card sequence-card">
        <view class="section-header section-header--edge">
          <view class="section-title">影像序列</view>
          <button class="mi-btn mi-btn--primary" :disabled="uploading" @click="openUploadSheet()">
            {{ uploading ? '上传中...' : '新增影像' }}
          </button>
        </view>

        <view v-for="item in studies" :key="item.id" class="study">
          <view class="row">
            <view>
              <text class="label">{{ item.modality || '-' }}</text>
              <text class="subtle">{{ truncateText(item.desc || '暂无描述', 10) }}</text>
            </view>
            <text class="status-pill status-pill--default">{{ studyStatusText(item.status) }}</text>
          </view>

          <view class="meta">
            <text>序列 {{ item.id }}</text>
            <text>{{ item.time || '-' }}</text>
          </view>

          <view class="study-modalities">
            <view v-for="modality in modalityOrder" :key="modality" class="modality-item">
              <text class="label">{{ modalityLabel(modality) }}</text>
              <text class="status-pill" :class="`status-pill--${modalityTagType(item.id, modality)}`">
                {{ modalityTagText(item.id, modality) }}
              </text>
            </view>
          </view>

          <view class="study-actions-main">
            <button class="mi-btn mi-btn--ghost" :disabled="uploading" @click="openUploadSheet(item)">上传影像</button>
            <button class="mi-btn mi-btn--primary" :disabled="!studyVolumeMap[item.id]" @click="open3DCombined(item.id)">3D 查看</button>
            <button class="mi-btn mi-btn--ghost" @click="openStudyActions(item)">更多</button>
          </view>
        </view>
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
  upsertContour,
  createStudy,
  getModel,
  deletePatient,
  deleteStudy
} from '../../common/api'
import { resolveApiUrl } from '../../common/request'

export default {
  data() {
    return {
      patientId: '',
      patient: {},
      studies: [],
      contours: [],
      uploading: false,
      studyLabelMap: {},
      studyVolumeMap: {},
      studyFileMap: {},
      modalityOrder: ['flair', 't1', 't1c', 't2'],
      activeUploadStudyId: null,
      activeStudyId: null,
      deletePatientText: '\u5220\u9664\u60a3\u8005',
      deleteStudyText: '\u5220\u9664\u5e8f\u5217',
      ctvRefineLabelMap: {},
      ctvExpandLabelMap: {}
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
      const status = this.gtv.status
      if (status === 'pending') return '\u5f85\u786e\u8ba4'
      if (this.hasGtvLabel) return status || '\u5df2\u751f\u6210'
      return status || '\u5f85\u751f\u6210'
    },
    gtvStatusType() {
      if (this.gtv.status === '已确�?) return 'success'
      return this.hasGtvLabel ? 'success' : 'primary'
    },
    ctvStatusText() {
      if (this.hasCtvExpandLabel) return '\u5df2\u751f\u6210'
      return '\u672a\u751f\u6210'
    },
    ctvStatusType() {
      if (this.ctv.status === '\u5df2\u786e\u8ba4') return 'success'
      return this.hasCtvExpandLabel ? 'success' : 'warning'
    },
    gtvLabel() {
      return this.gtv.storagePath || '生成后可查看/下载'
    },
    ctvLabel() {
      if (this.hasCtvExpandLabel) return '\u5df2\u751f\u6210\u7cbe\u4fee Label'
      return '\u7b49\u5f85\u533b\u751f\u7cbe\u4fee'
    },
    ctvExpandLabel() {
      const studyId = this.primaryStudyId
      const refine = studyId ? this.ctvRefineLabelMap?.[studyId] : null
      const contourPath =
        this.ctv?.storagePath && (!this.ctv?.studyId || this.ctv.studyId === studyId)
          ? this.ctv.storagePath
          : ''
      if (refine?.name) return `使用精修: ${refine.name}`
      if (refine?.filePath || refine?.localPath) return '默认精修 Label'
      if (contourPath) {
        const name = contourPath.split('/').pop()
        return name ? `使用精修: ${name}` : '使用精修结果'
      }
      return '等待外扩'
    },
    ctvExpandStatusText() {
      const studyId = this.primaryStudyId
      const hasExpand = !!(studyId && this.ctvRefineLabelMap?.[studyId])
      return hasExpand ? '\u5df2\u5916\u6269' : '\u672a\u5916\u6269'
    },
    ctvExpandStatusType() {
      const studyId = this.primaryStudyId
      const hasExpand = !!(studyId && this.ctvRefineLabelMap?.[studyId])
      return hasExpand ? 'success' : 'warning'
    },
    heatmapLabel() {
      return this.ctv.confidenceMap || this.gtv.confidenceMap || '置信度范�?
    },
    primaryStudyId() {
      return this.patient.studyId || this.studies?.[0]?.id || ''
    },
    hasGtvLabel() {
      const studyId = this.primaryStudyId
      return !!(studyId && this.studyLabelMap?.[studyId])
    },
    hasCtvRefineLabel() {
      const studyId = this.primaryStudyId
      return !!(studyId && this.ctvRefineLabelMap?.[studyId])
    },
    hasCtvExpandLabel() {
      const studyId = this.primaryStudyId
      return !!(studyId && this.ctvExpandLabelMap?.[studyId])
    },
    isConfirmed() {
      return this.patient.status === '\u5df2\u786e\u8ba4' || this.patient.confirmed === true
    },
    confirmButtonText() {
      return this.isConfirmed ? '\u533b\u751f\u5df2\u786e\u8ba4' : '\u533b\u751f\u786e\u8ba4\u65b9\u6848'
    },
    confirmButtonType() {
      return this.isConfirmed ? 'success' : 'primary'
    },
  async onLoad(query) {
    this.patientId = query.id || ''
    const cache = uni.getStorageSync('currentPatient')
    if (!this.patientId && cache) {
      this.patientId = cache.id
    }
    if (!this.patientId) {
      uni.showToast({ title: '\u7f3a\u5c11\u60a3\u8005ID', icon: 'none' })
      return
    }
    this.loadStudyFilesFromStorage()
    this.loadCtvRefineLabelsFromStorage()
    this.loadCtvExpandLabelsFromStorage()
    await Promise.all([this.fetchPatient(), this.fetchStudies(), this.fetchContours()])
  },
  onShow() {
    if (!this.patientId) return
    this.fetchPatient()
    this.fetchStudies()
    this.fetchContours()
    this.loadCtvRefineLabelsFromStorage()
    this.loadCtvExpandLabelsFromStorage()
  },
  methods: {
    studyStatusText(status) {
      const raw = (status || '').toString().trim().toLowerCase()
      const map = {
        pending: '\u5f85\u5904\u7406',
        processing: '\u5904\u7406\u4e2d',
        queued: '\u6392\u961f\u4e2d',
        running: '\u5904\u7406\u4e2d',
        in_progress: '\u5904\u7406\u4e2d',
        done: '\u5df2\u5b8c\u6210',
        completed: '\u5df2\u5b8c\u6210',
        success: '\u6210\u529f',
        confirmed: '\u5df2\u786e\u8ba4',
        review: '\u5f85\u590d\u6838',
        fail: '\u5931\u8d25',
        failed: '\u5931\u8d25'
      }
      if (!raw) return '\u5904\u7406\u4e2d'
      if (raw.includes('processing') || raw.includes('in_progress')) return '\u5904\u7406\u4e2d'
      if (map[raw]) return map[raw]
      if (/^[a-z_]+$/.test(raw)) return '\u5904\u7406\u4e2d'
      return status
    },
    truncateText(value, maxLen = 10) {
      if (value === undefined || value === null) return ''
      const text = String(value)
      if (text.length <= maxLen) return text
      return `${text.slice(0, maxLen)}...`
    },
    storageKey() {
      return `study_files_${this.patientId || ''}`
    },
    loadStudyFilesFromStorage() {
      const key = this.storageKey()
      if (!key) return
      const cache = uni.getStorageSync(key)
      this.studyFileMap = cache && typeof cache === 'object' ? cache : {}
    },
    ctvRefineStorageKey() {
      return `ctv_refine_${this.patientId || ''}`
    },
    ctvExpandStorageKey() {
      return `ctv_expand_${this.patientId || ''}`
    },
    loadCtvRefineLabelsFromStorage() {
      const key = this.ctvRefineStorageKey()
      if (!key) return
      const cache = uni.getStorageSync(key)
      this.ctvRefineLabelMap = cache && typeof cache === 'object' ? cache : {}
    },
    loadCtvExpandLabelsFromStorage() {
      const key = this.ctvExpandStorageKey()
      if (!key) return
      const cache = uni.getStorageSync(key)
      this.ctvExpandLabelMap = cache && typeof cache === 'object' ? cache : {}
    },
    saveStudyFilesToStorage() {
      const key = this.storageKey()
      if (!key) return
      uni.setStorageSync(key, this.studyFileMap || {})
    },
    modalityLabel(modality) {
      const key = String(modality || '').toLowerCase()
      const map = { flair: 'Flair', t1: 'T1', t1c: 'T1c', t2: 'T2' }
      return map[key] || key
    },
    modalityTagType(studyId, modality) {
      const file = this.studyFileMap?.[studyId]?.[modality]
      return file ? 'success' : 'default'
    },
    modalityTagText(studyId, modality) {
      const file = this.studyFileMap?.[studyId]?.[modality]
      return file ? '已上�? : '未上�?
    },
    openUploadSheet(item) {
      this.activeUploadStudyId = item?.id || null
      const actions = this.buildUploadActions(this.activeUploadStudyId)
      if (!actions.length) return
      uni.showActionSheet({
        itemList: actions.map((action) => action.name),
        success: ({ tapIndex }) => {
          const selected = actions[tapIndex]
          if (!selected?.id) return
          this.handleUploadModality(selected.id)
        }
      })
    },
    buildUploadActions(studyId) {
      const actions = (this.modalityOrder || []).map((modality) => {
        const uploaded = !!this.studyFileMap?.[studyId]?.[modality]
        const label = this.modalityLabel(modality)
        return {
          name: uploaded ? `${label} (\u5df2\u4e0a\u4f20)` : label,
          id: modality
        }
      })
      const labelUploaded = !!this.studyLabelMap?.[studyId] || !!this.studyFileMap?.[studyId]?.label
      actions.push({
        name: labelUploaded ? `Label (已上�?` : 'Label',
        id: 'label'
      })
      return actions
    },
    async handleUploadModality(modality) {
      if (this.uploading) return
      const file = await this.pickFile()
      if (!file || !file.path) return
      uni.showLoading({ title: '上传�?..', mask: true })
      this.uploading = true
      try {
        let targetStudyId = this.activeUploadStudyId
        if (!targetStudyId) {
          targetStudyId = await this.createStudyForUpload(file)
        }
        if (!targetStudyId) {
          uni.showToast({ title: '序列创建失败', icon: 'none' })
          return
        }
        const payload = await this.uploadToBackend(targetStudyId, file, modality)
        const next = {
          name: file.name || '',
          filePath: payload?.filePath || '',
          localPath: file.path || '',
          fileType: payload?.fileType || modality
        }
        const current = this.studyFileMap?.[targetStudyId] || {}
        this.studyFileMap = {
          ...(this.studyFileMap || {}),
          [targetStudyId]: { ...current, [modality]: next }
        }
        if (modality === 'label') {
          this.studyLabelMap = {
            ...(this.studyLabelMap || {}),
            [targetStudyId]: payload?.filePath || next.filePath || true
          }
        }
        this.saveStudyFilesToStorage()
        await Promise.all([this.fetchStudies(), this.fetchPatient()])
      } catch (err) {
        console.error('handleUploadModality error', err, err?.stack)
      } finally {
        this.uploading = false
        uni.hideLoading()
      }
    },
    openGtvDraft(studyId) {
      const fallbackStudy = this.studies?.[0]?.id || ''
      const targetStudyId = studyId || fallbackStudy
      const query = `patientId=${this.patientId}&studyId=${targetStudyId}`
      uni.navigateTo({ url: `/pages/patient/gtv-draft?${query}` })
    },
    openCtvRefine(studyId) {
      const fallbackStudy = this.studies?.[0]?.id || ''
      const targetStudyId = studyId || fallbackStudy
      const query = `patientId=${this.patientId}&studyId=${targetStudyId}`
      uni.navigateTo({ url: `/pages/patient/ctv-refine?${query}` })
    },
    openCtvExpand(studyId) {
      const fallbackStudy = this.studies?.[0]?.id || ''
      const targetStudyId = studyId || fallbackStudy
      const query = `patientId=${this.patientId}&studyId=${targetStudyId}`
      uni.navigateTo({ url: `/pages/patient/ctv-expand?${query}` })
    },
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
        this.loadStudyFilesFromStorage()
        await this.loadStudyLabels()
      } catch (err) {
        console.error('getStudies error', err)
      }
    },
    async loadStudyLabels() {
      const labels = {}
      const volumes = {}
      const fileMap = { ...(this.studyFileMap || {}) }
      await Promise.all(
        (this.studies || []).map(async (study) => {
          if (!study?.id) return
          try {
            const model = await getModel(study.id)
            if (model?.labelUrl) {
              labels[study.id] = model.labelUrl
              await this.tryUpsertContour(study.id, 'GTV', model.labelUrl)
            }
            if (model?.volumeUrl || model?.modelPath || model?.modelUrl) {
              volumes[study.id] = model.volumeUrl || model.modelPath || model.modelUrl
            }
            const volumePath = volumes[study.id]
            if (volumePath) {
              const current = fileMap[study.id] || {}
              if (!current.flair) {
                fileMap[study.id] = { ...current, flair: { filePath: volumePath } }
              }
            }
          } catch (err) {
            console.error('getModel error', err)
          }
        })
      )
      this.studyLabelMap = labels
      this.studyVolumeMap = volumes
      this.studyFileMap = fileMap
      this.saveStudyFilesToStorage()
    },
    buildStudyActions(studyId) {
      const actions = [
        { name: this.deleteStudyText, id: 'delete', color: '#e65454' }
      ]
      return actions
    },
    openStudyActions(item) {
      const studyId = item?.id
      if (!studyId) return
      this.activeStudyId = studyId
      const actions = this.buildStudyActions(studyId)
      if (!actions.length) return
      uni.showActionSheet({
        itemList: actions.map((action) => action.name),
        success: ({ tapIndex }) => {
          const selected = actions[tapIndex]
          if (!selected?.id) return
          if (selected.id === 'delete') {
            this.confirmDeleteStudy({ id: studyId })
          }
        }
      })
    },
    async fetchContours() {
      try {
        const data = await getContours(this.patientId)
        this.contours = Array.isArray(data) ? data : []
      } catch (err) {
        console.error('getContours error', err)
      }
    },
    open3DCombined(studyId) {
      if (!studyId) {
        uni.showToast({ title: '请先上传主体影像', icon: 'none' })
        return
      }
      uni.navigateTo({
        url: `/pages/model/viewer?studyId=${studyId}&view=both`
      })
    },
    openHeatmap(studyId) {
      const fallbackStudy = this.studies?.[0]?.id || ''
      const targetStudyId = studyId || fallbackStudy
      const query = `patientId=${this.patientId}&studyId=${targetStudyId}`
      uni.navigateTo({ url: `/pages/patient/ctv-heatmap?${query}` })
    },
    open3DVolume(studyId) {
      if (!studyId || !this.studyVolumeMap?.[studyId]) {
        uni.showToast({ title: '主体影像未上�?, icon: 'none' })
        return
      }
      uni.navigateTo({
        url: `/pages/model/viewer?studyId=${studyId}&view=volume`
      })
    },
    open3DLabel(studyId) {
      if (!studyId || !this.studyLabelMap?.[studyId]) {
        uni.showToast({ title: 'Label 未生�?, icon: 'none' })
        return
      }
      uni.navigateTo({
        url: `/pages/model/viewer?studyId=${studyId}&view=label`
      })
    },
    async confirmContour() {
      if (!this.patientId) return
      if (!this.gtv?.id && !this.ctv?.id) {
        await this.trySyncContoursForConfirm()
      }
      if (!this.gtv?.id && !this.ctv?.id) {
        uni.showToast({ title: '暂无可确认结构，请先生成并同步到后端', icon: 'none' })
        return
      }
      try {
        await reviewPatient(this.patientId, true)
        uni.showToast({ title: '已标记为医生确认', icon: 'success' })
        await this.fetchPatient()
      } catch (err) {
        console.error('reviewPatient error', err)
      }
    },
    async tryUpsertContour(studyId, type, storagePath) {
      if (!this.patientId || !studyId || !type || !storagePath) return
      try {
        await upsertContour(this.patientId, {
          studyId,
          type,
          storagePath,
          status: 'pending'
        })
      } catch (err) {
        console.error('upsert contour error', err)
      }
    },
    async trySyncContoursForConfirm() {
      const studyId = this.primaryStudyId
      if (!studyId) return
      const gtvPath = this.studyLabelMap?.[studyId] || ''
      const refine = this.ctvRefineLabelMap?.[studyId]
      const expand = this.ctvExpandLabelMap?.[studyId]
      const ctvPath =
        refine?.filePath || refine?.localPath || expand?.filePath || expand?.localPath || ''
      if (gtvPath) {
        await this.tryUpsertContour(studyId, 'GTV', gtvPath)
      }
      if (ctvPath) {
        await this.tryUpsertContour(studyId, 'CTV', ctvPath)
      }
      await this.fetchContours()
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
        uni.showToast({ title: path ? '\u5df2\u8fd4\u56de\u4e0b\u8f7d\u8def\u5f84' : '\u5df2\u5b8c\u6210\uff0c\u8bf7\u7a0d\u540e\u67e5\u770b', icon: 'none' })
        if (path) {
          uni.setClipboardData({ data: path, success: () => {} })
        }
      } catch (err) {
        console.error('downloadContour error', err)
      }
    },
    confirmDeletePatient() {
      if (!this.patientId) return
      uni.showModal({
        title: '\u5220\u9664\u60a3\u8005',
        content: '\u786e\u8ba4\u5220\u9664\u8be5\u60a3\u8005\u53ca\u5176\u5f71\u50cf\u5e8f\u5217\u5417\uff1f',
        success: async (res) => {
          if (!res.confirm) return
          try {
            await deletePatient(this.patientId)
            uni.removeStorageSync('currentPatient')
            uni.showToast({ title: '\u5df2\u5220\u9664', icon: 'success' })
            uni.navigateBack()
          } catch (err) {
            console.error('deletePatient error', err)
            uni.showToast({ title: '\u5220\u9664\u5931\u8d25', icon: 'none' })
          }
        }
      })
    },
    confirmDeleteStudy(item) {
      const studyId = item?.id
      if (!studyId || !this.patientId) return
      uni.showModal({
        title: '\u5220\u9664\u5e8f\u5217',
        content: '\u786e\u8ba4\u5220\u9664\u8be5\u5f71\u50cf\u5e8f\u5217\u5417\uff1f',
        success: async (res) => {
          if (!res.confirm) return
          try {
            await deleteStudy(this.patientId, studyId)
            const { [studyId]: _, ...restLabels } = this.studyLabelMap || {}
            const { [studyId]: __, ...restVolumes } = this.studyVolumeMap || {}
            this.studyLabelMap = restLabels
            this.studyVolumeMap = restVolumes
            await Promise.all([this.fetchStudies(), this.fetchPatient()])
            uni.showToast({ title: '\u5df2\u5220\u9664', icon: 'success' })
          } catch (err) {
            console.error('deleteStudy error', err)
            uni.showToast({ title: '\u5220\u9664\u5931\u8d25', icon: 'none' })
          }
        }
      })
    },
    editProfile() {
      if (!this.patientId) return
      uni.navigateTo({ url: `/pages/patient/edit?id=${this.patientId}` })
    },
    pickFile() {
      return new Promise((resolve) => {
        const choose = uni.chooseFile || uni.chooseMessageFile
        if (!choose) {
          uni.showToast({ title: '\u5f53\u524d\u7aef\u6682\u4e0d\u652f\u6301\u6587\u4ef6\u9009\u62e9', icon: 'none' })
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

    async createStudyForUpload(file) {
      try {
        const data = await createStudy(this.patientId, {
          modality: this.guessModality(file?.name),
          desc: file?.name || '新影�?
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
    buildFileType(role, name) {
      const ext = this.extractExt(name)
      if (!role) return ext
      if (!ext) return role
      return `${role}.${ext}`
    },
    uploadToBackend(studyId, file, role) {
      const token = uni.getStorageSync('token') || ''
      const fileType = this.buildFileType(role, file?.name)
      return new Promise((resolve, reject) => {
        uni.uploadFile({
          url: resolveApiUrl(`/api/patients/${this.patientId}/studies/${studyId}/upload`),
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
    },
  }
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: #edf4ff;
}

.detail-area {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.detail-hero {
  background: linear-gradient(155deg, #2f78d8 0%, #3888ee 44%, #62a6f4 100%);
  border-radius: 28rpx;
  padding: 24rpx;
  box-shadow: 0 14rpx 44rpx rgba(42, 106, 188, 0.28);
}

.hero-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.hero-name {
  display: block;
  font-size: 38rpx;
  font-weight: 700;
  color: #ffffff;
}

.hero-subtitle {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.84);
}

.hero-meta {
  margin-top: 14rpx;
  display: flex;
  justify-content: space-between;
  gap: 12rpx;
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.88);
}

.hero-kpi-grid {
  margin-top: 16rpx;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10rpx;
}

.hero-kpi-item {
  border-radius: 16rpx;
  padding: 12rpx;
  background: rgba(255, 255, 255, 0.16);
  border: 1rpx solid rgba(255, 255, 255, 0.26);
}

.hero-kpi-value {
  display: block;
  font-size: 30rpx;
  font-weight: 700;
  color: #ffffff;
}

.hero-kpi-label {
  display: block;
  margin-top: 4rpx;
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.84);
}

.summary-card {
  margin-bottom: 2rpx;
}

.summary-top-row {
  margin-bottom: 4rpx;
}

.summary-desc {
  display: block;
  margin-top: 6rpx;
}

.summary-actions {
  display: flex;
  justify-content: space-between;
  align-items: stretch;
  gap: 12rpx;
  flex-wrap: nowrap;
}

.summary-actions .mi-btn {
  flex: 1 1 0;
  min-width: 0;
  text-align: center;
  padding: 0 10rpx;
}

.ai-card {
  padding: 24rpx;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.result-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16rpx;
  border-radius: 16rpx;
  border: 1rpx solid #d6e5f7;
  background: #f8fbff;
}

.row-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #173a64;
}

.row-right {
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.row-arrow {
  color: #7a95b5;
  font-size: 28rpx;
}

.sequence-card {
  padding-bottom: 18rpx;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6rpx;
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
  font-size: 32rpx;
  font-weight: 700;
  color: #173a64;
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

.name {
  display: block;
  font-size: 34rpx;
  font-weight: 700;
  color: #173a64;
}

.label {
  font-size: 28rpx;
  font-weight: 600;
  color: #234567;
}

.meta {
  display: flex;
  justify-content: space-between;
  color: #5f7899;
  font-size: 25rpx;
  margin-top: 12rpx;
}

.study {
  margin-top: 12rpx;
  padding: 16rpx;
  border-radius: 18rpx;
  background: #f8fbff;
  border: 1rpx solid #d8e6f8;
}

.study + .study {
  margin-top: 12rpx;
}

.study-modalities {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12rpx;
  margin-top: 10rpx;
}

.modality-item {
  padding: 10rpx;
  background: #ffffff;
  border-radius: 14rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
  border: 1rpx solid #d6e5f7;
}

.study-status-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12rpx;
  margin-top: 10rpx;
}

.status-item {
  padding: 12rpx;
  background: #ffffff;
  border-radius: 14rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
  border: 1rpx solid #d6e5f7;
}

.study-actions-main {
  display: flex;
  flex-direction: row;
  flex-wrap: nowrap;
  justify-content: space-between;
  align-items: stretch;
  gap: 12rpx;
  margin-top: 10rpx;
}

.study-actions-main .mi-btn {
  flex: 1 1 0;
  min-width: 0;
  text-align: center;
  padding: 0 10rpx;
}

.subtle {
  color: #5f7899;
  font-size: 24rpx;
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

.status-pill--primary {
  color: #245eac;
  border-color: #bfd5ef;
  background: #eaf3ff;
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
  flex: 0 0 auto;
}

.mi-btn--primary {
  background: linear-gradient(135deg, #2f78d8 0%, #245eac 100%);
  border-color: transparent;
  color: #ffffff;
  box-shadow: 0 12rpx 28rpx rgba(47, 120, 216, 0.26);
}

.mi-btn--ghost {
  background: #ffffff;
}

.mi-btn--danger {
  background: #fff5f5;
  border-color: #f3c2c2;
  color: #b13d3d;
  box-shadow: 0 8rpx 18rpx rgba(214, 92, 92, 0.18);
}

.mi-btn--hero {
  background: rgba(255, 255, 255, 0.16);
  border-color: rgba(255, 255, 255, 0.42);
  color: #ffffff;
  box-shadow: none;
}

.mi-btn[disabled] {
  opacity: 0.55;
  box-shadow: none;
}

button::after {
  border: none;
}
</style>





