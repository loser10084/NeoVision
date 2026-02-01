<template>
  <view class="page">
    <view class="safe-area">
      <view class="card summary-card">
        <view class="row">
          <view>
            <text class="name">{{ patient.name || '未命名' }}</text>
            <text class="subtle">
              {{ patient.sex || '-' }} / {{ patient.age || '-' }} / {{ patient.stage || '-' }}
            </text>
          </view>
          <wd-button size="small" shape="round" type="default" plain @click="editProfile">编辑</wd-button>
        </view>
        <view class="meta">
          <text>ID {{ patient.id || '-' }}</text>
          <text>影像号 {{ patient.studyId || '-' }}</text>
        </view>
        <view class="meta">
          <text>{{ patient.diagnosis || '-' }}</text>
          <text>{{ patient.lastUpdate || '-' }}</text>
        </view>
        <view class="action-bar">
          <wd-button
            size="small"
            shape="round"
            :type="confirmButtonType"
            :plain="!isConfirmed"
            @click="confirmContour"
          >
            {{ confirmButtonText }}
          </wd-button>
          <wd-button size="small" shape="round" type="default" plain @click="exportRT">
            导出结构
          </wd-button>
          <wd-button size="small" shape="round" type="danger" plain @click="confirmDeletePatient">
              {{ deletePatientText }}
            </wd-button>
        </view>
      </view>

      <view class="card ai-card">
        <view class="section-title">靶区 AI 结果</view>
        <wd-cell-group>
          <wd-cell title="GTV 初稿" is-link @click="openGtvDraft(patient.studyId)">
            <wd-tag slot="value" :type="gtvStatusType" plain>{{ gtvStatusText }}</wd-tag>
          </wd-cell>
          <wd-cell title="CTV 外扩" is-link @click="openCtvRefine(patient.studyId)">
            <wd-tag slot="value" :type="ctvExpandStatusType" plain>{{ ctvExpandStatusText }}</wd-tag>
          </wd-cell>
          <wd-cell title="CTV 精修" is-link @click="openCtvExpand(patient.studyId)">
            <wd-tag slot="value" :type="ctvStatusType" plain>{{ ctvStatusText }}</wd-tag>
          </wd-cell>
          <wd-cell title="置信度热力图" is-link @click="openHeatmap(patient.studyId)">
            <wd-tag slot="value" type="warning" plain>可查看</wd-tag>
          </wd-cell>
        </wd-cell-group>
      </view>

      <view class="card">
        <view class="section-header">
          <view class="section-title">影像序列</view>
          <wd-button
            size="small"
            shape="round"
            type="primary"
            plain
            :loading="uploading"
            :disabled="uploading"
            @click="openUploadSheet()"
          >
              新增影像
            </wd-button>
        </view>
        <view v-for="item in studies" :key="item.id" class="study">
          <view class="row">
            <view>
              <text class="label">{{ item.modality || '-' }}</text>
              <text class="subtle">{{ truncateText(item.desc || '暂无描述', 10) }}</text>
            </view>
            <wd-tag plain>{{ item.status || '处理中' }}</wd-tag>
          </view>
          <view class="meta">
            <text>序列号 {{ item.id }}</text>
            <text>{{ item.time || '-' }}</text>
          </view>
          <view class="study-modalities">
            <view v-for="modality in modalityOrder" :key="modality" class="modality-item">
              <text class="label">{{ modalityLabel(modality) }}</text>
              <wd-tag plain :type="modalityTagType(item.id, modality)">
                {{ modalityTagText(item.id, modality) }}
              </wd-tag>
            </view>
          </view>

          <view class="study-status-row">
            <view class="status-item">
              <text class="label">Label</text>
              <wd-tag plain :type="studyLabelMap[item.id] ? 'success' : 'warning'">
                {{ studyLabelMap[item.id] ? '已生成' : '未生成' }}
              </wd-tag>
            </view>
          </view>
          <view class="study-actions-main">
            <wd-button
              size="small"
              shape="round"
              type="default"
              plain
              :loading="uploading"
              :disabled="uploading"
              @click="openUploadSheet(item)"
            >
              上传影像
            </wd-button>
            <wd-button
              size="small"
              shape="round"
              type="primary"
              plain
              :disabled="!studyVolumeMap[item.id]"
              @click="open3DCombined(item.id)"
            >
              3D 查看
            </wd-button>
            <wd-button size="small" shape="round" type="default" plain @click="openStudyActions(item)">
              更多
            </wd-button>
          </view>

          
        </view>
        
      </view>
    </view>
  </view>

  <wd-action-sheet
    v-model="studyActionSheetVisible"
    title="更多操作"
    cancel-text="取消"
    :actions="studyActionSheetActions"
    @select="handleStudyActionSelect"
  />
  <wd-action-sheet
    v-model="uploadSheetVisible"
    title="上传影像"
    cancel-text="关闭"
    :actions="uploadSheetActions"
    @select="handleUploadSheetSelect"
  />
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
      uploadSheetVisible: false,
      uploadSheetActions: [],
      activeUploadStudyId: null,
      studyActionSheetVisible: false,
      studyActionSheetActions: [],
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
      if (this.gtv.status === '已确认') return 'success'
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
      return this.ctv.confidenceMap || this.gtv.confidenceMap || '置信度范围'
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
      return this.patient.status === '已确认' || this.patient.confirmed === true
    },
    confirmButtonText() {
      return this.isConfirmed ? '医生已确认' : '医生确认方案'
    },
    confirmButtonType() {
      return this.isConfirmed ? 'success' : 'primary'
    }
  },
  async onLoad(query) {
    this.patientId = query.id || ''
    const cache = uni.getStorageSync('currentPatient')
    if (!this.patientId && cache) {
      this.patientId = cache.id
    }
    if (!this.patientId) {
      uni.showToast({ title: '缺少患者ID', icon: 'none' })
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
        done: '\u5df2\u5b8c\u6210',
        completed: '\u5df2\u5b8c\u6210',
        success: '\u6210\u529f',
        fail: '\u5931\u8d25',
        failed: '\u5931\u8d25'
      }
      if (!raw) return '\u5904\u7406\u4e2d'
      if (raw.includes('processing')) return '\u5904\u7406\u4e2d'
      return map[raw] || status
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
      return file ? '已上传' : '未上传'
    },
    openUploadSheet(item) {
      this.activeUploadStudyId = item?.id || null
      this.uploadSheetActions = this.buildUploadActions(this.activeUploadStudyId)
      this.uploadSheetVisible = true
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
        name: labelUploaded ? `Label (已上传)` : 'Label',
        id: 'label'
      })
      return actions
    },

    handleUploadSheetSelect({ item }) {
      if (!item?.id) return
      this.handleUploadModality(item.id)
    },
    async handleUploadModality(modality) {
      if (this.uploading) return
      const file = await this.pickFile()
      if (!file || !file.path) return
      uni.showLoading({ title: '上传中...', mask: true })
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
      this.studyActionSheetActions = this.buildStudyActions(studyId)
      this.studyActionSheetVisible = true
    },
    handleStudyActionSelect({ item }) {
      const studyId = this.activeStudyId
      if (!studyId || !item?.id) return
      if (item.id === 'delete') {
        this.confirmDeleteStudy({ id: studyId })
      }
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
        uni.showToast({ title: '主体影像未上传', icon: 'none' })
        return
      }
      uni.navigateTo({
        url: `/pages/model/viewer?studyId=${studyId}&view=volume`
      })
    },
    open3DLabel(studyId) {
      if (!studyId || !this.studyLabelMap?.[studyId]) {
        uni.showToast({ title: 'Label 未生成', icon: 'none' })
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
        uni.showToast({ title: path ? '已返回下载路径' : '已完成请求', icon: 'none' })
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
        title: '删除患者',
        content: '确认删除该患者及其影像序列吗？',
        success: async (res) => {
          if (!res.confirm) return
          try {
            await deletePatient(this.patientId)
            uni.removeStorageSync('currentPatient')
            uni.showToast({ title: '已删除', icon: 'success' })
            uni.navigateBack()
          } catch (err) {
            console.error('deletePatient error', err)
            uni.showToast({ title: '删除失败', icon: 'none' })
          }
        }
      })
    },
    confirmDeleteStudy(item) {
      const studyId = item?.id
      if (!studyId || !this.patientId) return
      uni.showModal({
        title: '删除序列',
        content: '确认删除该影像序列吗？',
        success: async (res) => {
          if (!res.confirm) return
          try {
            await deleteStudy(this.patientId, studyId)
            const { [studyId]: _, ...restLabels } = this.studyLabelMap || {}
            const { [studyId]: __, ...restVolumes } = this.studyVolumeMap || {}
            this.studyLabelMap = restLabels
            this.studyVolumeMap = restVolumes
            await Promise.all([this.fetchStudies(), this.fetchPatient()])
            uni.showToast({ title: '已删除', icon: 'success' })
          } catch (err) {
            console.error('deleteStudy error', err)
            uni.showToast({ title: '删除失败', icon: 'none' })
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

    async createStudyForUpload(file) {
      try {
        const data = await createStudy(this.patientId, {
          modality: this.guessModality(file?.name),
          desc: file?.name || '新影像'
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
  background: #f7f7f8;
}

.summary-card {
  margin-bottom: 18rpx;
}

.ai-card {
  padding-right: 0;
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

.row :deep(.wd-tag) {
  flex: 0 0 auto;
  white-space: nowrap;
  display: inline-flex;
  align-items: center;
}

.card :deep(.wd-cell) {
  align-items: center;
}

.card :deep(.wd-cell__title) {
  flex: 1;
  min-width: 0;
}

.card :deep(.wd-cell__label) {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card :deep(.wd-cell__value) {
  flex: 0 0 auto;
  white-space: nowrap;
}

.card :deep(.wd-cell__value .wd-tag) {
  white-space: nowrap;
  display: inline-flex;
  align-items: center;
}

.card :deep(.wd-cell__right) {
  margin-left: auto;
}

.link {
  color: #1a5ed7;
  text-decoration: underline;
}

.ai-card :deep(.wd-cell) {
  padding-right: 0 !important;
}

.ai-card :deep(.wd-cell__right) {
  margin-right: 0 !important;
}

.ai-card :deep(.wd-cell__value) {
  margin-left: auto;
}

.name {
  display: block;
  font-size: 34rpx;
  font-weight: 700;
  color: #0c0d0f;
}

.meta {
  display: flex;
  justify-content: space-between;
  color: #6b7075;
  font-size: 26rpx;
  margin-top: 12rpx;
}

.study {
  padding: 10rpx 0 16rpx;
}

.study-modalities {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12rpx;
  margin-top: 10rpx;
}

.modality-item {
  padding: 10rpx;
  background: #f7f7f9;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
  border: 1rpx solid #e6e7eb;
}

.study-status-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12rpx;
  margin-top: 10rpx;
}

.status-item {
  padding: 12rpx;
  background: #f7f7f9;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
}

.study-actions-main {
  display: flex;
  flex-direction: row;
  flex-wrap: nowrap;
  align-items: center;
  gap: 12rpx;
  margin-top: 10rpx;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.study-actions-main :deep(.wd-button) {
  flex: 0 0 auto;
}
</style>

