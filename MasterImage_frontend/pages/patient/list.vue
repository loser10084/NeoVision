<template>
  <view class="page">
    <view class="page-content">
      <view class="hero">
        <view class="safe-area hero-inner">
          <view class="hero-top">
            <view class="hero-text">
              <text class="hero-title">你好，{{ doctorName }}</text>
              <text class="hero-subtitle">放疗影像智能勾画工作台</text>
            </view>
          <image class="hero-avatar" src="/static/project_icon_v2.jpg" mode="aspectFill" />
          </view>

          <view class="hero-search-wrap">
            <view class="hero-location">
              <image class="hero-location-icon" src="/static/icons/ic-location.svg" mode="aspectFit" />
              <text>合川</text>
            </view>
            <view class="hero-search-box">
              <image class="hero-search-icon" src="/static/icons/ic-search-case.svg" mode="aspectFit" />
              <input
                v-model="keyword"
                class="hero-search-input"
                placeholder="查患者、病种、检查号"
                placeholder-class="hero-search-placeholder"
                :disabled="loading"
                confirm-type="search"
                @confirm="handleSearch"
                @input="handleSearchInput"
              />
              <view v-if="keyword" class="search-clear" @click="clearSearch">×</view>
            </view>
          </view>
        </view>
      </view>

      <view class="safe-area body-area">
        <view class="promo-card">
          <view class="promo-text">
            <text class="promo-title">放疗勾画协同中心</text>
            <text class="promo-subtitle">统一管理建档、分割、复核与导出流程</text>
          </view>
          <view class="promo-dots">
            <view class="dot active"></view>
            <view class="dot"></view>
            <view class="dot"></view>
          </view>
        </view>

        <view class="quick-grid">
          <view class="quick-card quick-card-blue" @click="addPatient">
            <view class="quick-icon">
              <image class="quick-icon-img" src="/static/icons/ic-new-case.svg" mode="aspectFit" />
            </view>
            <view>
              <text class="quick-title">新建病例</text>
              <text class="quick-desc">快速登记并进入勾画流程</text>
            </view>
          </view>
          <view class="quick-card quick-card-pink" @click="goWorkbenchTask">
            <view class="quick-icon">
              <image class="quick-icon-img" src="/static/icons/ic-review-task.svg" mode="aspectFit" />
            </view>
            <view>
              <text class="quick-title">待复核任务</text>
              <text class="quick-desc">查看今日待确认轮廓</text>
            </view>
          </view>
        </view>

        <view class="service-panel">
          <view v-for="item in serviceEntries" :key="item.key" class="service-item" @click="handleService(item)">
            <view class="service-icon" :class="`service-icon--${item.key}`">
              <image class="service-icon-img" :src="item.icon" mode="aspectFit" />
            </view>
            <text class="service-text">{{ item.title }}</text>
          </view>
        </view>

        <view class="section-head">
          <text class="section-name">方案模板推荐</text>
          <text class="section-more">查看更多</text>
        </view>
        <scroll-view class="doctor-scroll" scroll-x>
          <view class="doctor-row">
            <view v-for="doctor in doctors" :key="doctor.id" class="doctor-card">
              <view class="doctor-top">
                <text class="doctor-follow">模板</text>
              </view>
              <view class="doctor-avatar-mini">{{ doctor.initial }}</view>
              <text class="doctor-name">{{ doctor.name }}</text>
              <text class="doctor-dept">{{ doctor.dept }}</text>
            </view>
          </view>
        </scroll-view>

        <view class="section-head section-head--patient">
          <text class="section-name">患者列表</text>
          <button class="mi-pill-btn" @click="addPatient">新增</button>
        </view>

        <view v-for="patient in patients" :key="patient.id" class="card patient-card" @click="goDetail(patient)">
          <view class="row">
            <view>
              <text class="name">{{ patient.name }}</text>
              <text class="subtle meta-line">{{ patient.sex }} · {{ patient.age }} 岁</text>
            </view>
            <text class="status-pill" :class="statusPillClass(patient.status)">{{ formatStatus(patient.status) }}</text>
          </view>

          <view class="meta">
            <text>ID {{ patient.id }}</text>
            <text>影像号 {{ patient.studyId || '-' }}</text>
          </view>
          <view class="meta">
            <text>{{ patient.diagnosis }} · {{ patient.stage || '未分期' }}</text>
            <text class="subtle">{{ patient.lastUpdate || '-' }}</text>
          </view>
        </view>

        <view v-if="patients.length === 0 && !loading" class="empty">
          <view class="empty-icon">i</view>
          <text class="subtle">暂无匹配患者，试试其它关键词</text>
        </view>
        <view v-if="loading" class="empty">
          <view class="empty-icon empty-icon--loading"></view>
          <text class="subtle">加载中...</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { getPatients } from '../../common/api'

export default {
  data() {
    return {
      keyword: '',
      patients: [],
      loading: false,
      lastScrollTop: 0,
      lastAutoRefreshTs: 0,
      searchTimer: null,
      serviceEntries: [
        { key: 'search', title: '病例检索', icon: '/static/icons/ic-search-case.svg' },
        { key: 'upload', title: '影像上传', icon: '/static/icons/ic-upload-image.svg' },
        { key: 'gtv', title: 'GTV初稿', icon: '/static/icons/ic-gtv.svg' },
        { key: 'ctv', title: 'CTV流程', icon: '/static/icons/ic-ctv.svg' },
        { key: 'consult', title: '会诊中心', icon: '/static/icons/ic-ai-consult.svg' }
      ],
      doctors: [
        { id: 't1', name: '脑胶质瘤模板', dept: 'GTV v3.2', initial: '脑' },
        { id: 't2', name: '鼻咽癌模板', dept: 'CTV v2.4', initial: '鼻' },
        { id: 't3', name: '肺部肿瘤模板', dept: '多模态 v1.9', initial: '肺' },
        { id: 't4', name: '颅脑复核模板', dept: 'RTStruct v2.1', initial: '颅' }
      ]
    }
  },
  computed: {
    doctorName() {
      const profile = uni.getStorageSync('userProfile') || {}
      const name = profile.name || '医生'
      return String(name).endsWith('医生') ? name : `${name}医生`
    }
  },
  onLoad() {
    this.fetchPatients()
  },
  onShow() {
    this.fetchPatients({ keyword: this.keyword, silent: true })
  },
  onPullDownRefresh() {
    this.fetchPatients({ keyword: this.keyword, silent: true })
  },
  onPageScroll(e) {
    const current = typeof e?.scrollTop === 'number' ? e.scrollTop : 0
    if (this.lastScrollTop > 0 && current <= 0) {
      const now = Date.now()
      if (!this.loading && now - this.lastAutoRefreshTs > 3000) {
        this.lastAutoRefreshTs = now
        this.fetchPatients({ keyword: this.keyword, silent: true })
      }
    }
    this.lastScrollTop = current
  },
  onUnload() {
    if (this.searchTimer) {
      clearTimeout(this.searchTimer)
      this.searchTimer = null
    }
  },
  methods: {
    formatStatus(status) {
      if (!status) return '处理中'
      const raw = String(status)
      if (/[\u4e00-\u9fa5]/.test(raw)) return raw
      const key = raw.trim().toUpperCase()
      const map = {
        PENDING: '待处理',
        PROCESSING: '处理中',
        IN_PROGRESS: '处理中',
        RUNNING: '处理中',
        REVIEW: '待复核',
        REVIEW_PENDING: '待复核',
        CONFIRMED: '已确认',
        DONE: '已完成',
        COMPLETED: '已完成',
        FINISHED: '已完成',
        FAILED: '失败',
        ERROR: '异常'
      }
      return map[key] || '处理中'
    },
    statusTagType(status) {
      const label = this.formatStatus(status)
      if (label === '待复核') return 'warning'
      if (label === '已完成' || label === '已确认') return 'success'
      if (label === '失败' || label === '异常') return 'danger'
      return 'primary'
    },
    statusPillClass(status) {
      const type = this.statusTagType(status)
      if (type === 'warning') return 'status-pill--warning'
      if (type === 'success') return 'status-pill--success'
      if (type === 'danger') return 'status-pill--danger'
      return 'status-pill--primary'
    },
    async fetchPatients({ keyword = '', silent = false } = {}) {
      if (!silent) this.loading = true
      try {
        const data = await getPatients(keyword)
        this.patients = Array.isArray(data) ? data : []
      } catch (err) {
        console.error('fetchPatients error', err)
      } finally {
        this.loading = false
        uni.stopPullDownRefresh()
      }
    },
    handleSearch() {
      this.fetchPatients({ keyword: this.keyword })
    },
    handleSearchInput(e) {
      this.keyword = e?.detail?.value ?? this.keyword
      if (this.searchTimer) clearTimeout(this.searchTimer)
      this.searchTimer = setTimeout(() => {
        this.handleSearch()
      }, 220)
    },
    clearSearch() {
      this.keyword = ''
      this.handleSearch()
    },
    goDetail(patient) {
      if (!patient || !patient.id) return
      uni.navigateTo({
        url: `/pages/patient/detail?id=${patient.id}`,
        success: () => {
          uni.setStorageSync('currentPatient', patient)
        }
      })
    },
    addPatient() {
      uni.navigateTo({ url: '/pages/patient/add' })
    },
    goConsult() {
      uni.switchTab({ url: '/pages/agent/chat' })
    },
    goWorkbenchTask() {
      this.handleSearch()
      uni.showToast({ title: '已刷新待处理病例', icon: 'none' })
    },
    handleService(item) {
      if (!item) return
      if (item.key === 'consult') {
        this.goConsult()
        return
      }
      if (item.key === 'search') {
        uni.showToast({ title: '请使用顶部搜索检索病例', icon: 'none' })
        return
      }
      if (item.key === 'upload') {
        this.addPatient()
        return
      }
      if ((item.key === 'gtv' || item.key === 'ctv') && this.patients.length > 0) {
        this.goDetail(this.patients[0])
        return
      }
      uni.showToast({ title: '请先选择病例', icon: 'none' })
    }
  }
}
</script>

<style scoped>
.page {
  min-height: 100vh;
}

.hero {
  background: linear-gradient(155deg, #2f78d8 0%, #3888ee 44%, #62a6f4 100%);
  border-bottom-left-radius: 26rpx;
  border-bottom-right-radius: 26rpx;
  box-shadow: 0 14rpx 44rpx rgba(42, 106, 188, 0.28);
}

.hero-inner {
  padding-top: calc(22rpx + env(safe-area-inset-top));
}

.hero-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
}

.hero-text {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.hero-title {
  font-size: 52rpx;
  font-weight: 700;
  color: #ffffff;
}

.hero-subtitle {
  font-size: 28rpx;
  color: rgba(255, 255, 255, 0.84);
}

.hero-avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 24rpx;
  border: 2rpx solid rgba(255, 255, 255, 0.48);
  background: rgba(255, 255, 255, 0.22);
}

.hero-search-wrap {
  margin-top: 18rpx;
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.hero-location {
  color: #ffffff;
  min-width: 72rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4rpx;
  font-size: 20rpx;
}

.hero-location-icon {
  width: 28rpx;
  height: 28rpx;
}

.hero-search-box {
  flex: 1;
  height: 74rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.22);
  border: 1rpx solid rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  padding: 0 14rpx 0 18rpx;
  box-sizing: border-box;
}

.hero-search-icon {
  width: 34rpx;
  height: 34rpx;
  margin-right: 10rpx;
  opacity: 0.94;
}

.hero-search-input {
  flex: 1;
  color: #ffffff;
  font-size: 28rpx;
  min-width: 0;
}

.hero-search-placeholder {
  color: rgba(255, 255, 255, 0.78);
}

.search-clear {
  width: 34rpx;
  height: 34rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-left: 8rpx;
  margin-right: 6rpx;
  background: rgba(255, 255, 255, 0.28);
  color: #ffffff;
  font-size: 24rpx;
}

.body-area {
  margin-top: 16rpx;
  padding-top: 20rpx;
}

.promo-card {
  background: linear-gradient(135deg, #fffaf2 0%, #ffe8cc 26%, #fff4e3 100%);
  border: 1rpx solid #ffd7a6;
  border-radius: 24rpx;
  padding: 22rpx 22rpx 16rpx;
  box-shadow: 0 14rpx 36rpx rgba(239, 172, 90, 0.2);
}

.promo-text {
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.promo-title {
  font-size: 34rpx;
  font-weight: 700;
  color: #2a4f8c;
}

.promo-subtitle {
  font-size: 24rpx;
  color: #556b92;
}

.promo-dots {
  margin-top: 14rpx;
  display: flex;
  justify-content: center;
  gap: 10rpx;
}

.dot {
  width: 10rpx;
  height: 10rpx;
  border-radius: 50%;
  background: #b3c4dd;
}

.dot.active {
  background: #2f78d8;
}

.quick-grid {
  margin-top: 18rpx;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14rpx;
}

.quick-card {
  border-radius: 22rpx;
  padding: 20rpx;
  display: flex;
  align-items: center;
  gap: 16rpx;
  border: 1rpx solid;
  box-shadow: 0 10rpx 24rpx rgba(43, 104, 186, 0.12);
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}

.quick-card:active {
  transform: translateY(1rpx);
  box-shadow: 0 6rpx 14rpx rgba(43, 104, 186, 0.14);
}

.quick-card-blue {
  background: #edf2ff;
  border-color: #d7e2ff;
}

.quick-card-pink {
  background: #ffeef5;
  border-color: #ffd8e8;
}

.quick-icon {
  width: 64rpx;
  height: 64rpx;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.78);
  color: #2f78d8;
}

.quick-icon-img {
  width: 54rpx;
  height: 54rpx;
}

.quick-title {
  display: block;
  font-size: 30rpx;
  font-weight: 650;
  color: #25436b;
}

.quick-desc {
  display: block;
  margin-top: 4rpx;
  font-size: 22rpx;
  color: #6d85a4;
}

.service-panel {
  margin-top: 18rpx;
  background: #ffffff;
  border-radius: 24rpx;
  border: 1rpx solid #d6e5f7;
  padding: 18rpx 12rpx;
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 10rpx;
  box-shadow: 0 12rpx 32rpx rgba(43, 104, 186, 0.1);
}

.service-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
}

.service-icon {
  width: 62rpx;
  height: 62rpx;
  border-radius: 18rpx;
  background: #eff5ff;
  color: #2f78d8;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 18rpx rgba(47, 120, 216, 0.16);
}

.service-icon-img {
  width: 46rpx;
  height: 46rpx;
}

.service-icon--search {
  background: #eef5ff;
}

.service-icon--upload {
  background: #edf7ff;
}

.service-icon--gtv {
  background: #eaf3ff;
}

.service-icon--ctv {
  background: #ecf4ff;
}

.service-icon--consult {
  background: #eff4ff;
}

.service-text {
  font-size: 22rpx;
  color: #4e6588;
}

.section-head {
  margin-top: 22rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-head--patient {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12rpx;
  margin-left: 0;
  margin-right: 0;
  padding-left: 0;
  padding-right: 4rpx;
}

.section-name {
  font-size: 38rpx;
  font-weight: 700;
  color: #173a64;
}

.section-more {
  font-size: 26rpx;
  color: #6f85a4;
}

.mi-pill-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin: 0;
  min-width: 132rpx;
  height: 62rpx;
  border-radius: 999rpx;
  border: none;
  color: #ffffff;
  background: linear-gradient(135deg, #2f78d8 0%, #245eac 100%);
  box-shadow: 0 10rpx 22rpx rgba(47, 120, 216, 0.26);
  font-size: 24rpx;
  line-height: 62rpx;
  padding: 0 24rpx;
  flex: 0 0 auto;
}

.section-head--patient .mi-pill-btn {
  margin-left: auto;
  margin-right: 6rpx;
}

.mi-pill-btn::after {
  border: none;
}

.doctor-scroll {
  margin-top: 14rpx;
  white-space: nowrap;
}

.doctor-row {
  display: inline-flex;
  gap: 12rpx;
}

.doctor-card {
  width: 196rpx;
  border-radius: 20rpx;
  background: #ffffff;
  border: 1rpx solid #d9e6f8;
  box-shadow: 0 10rpx 28rpx rgba(47, 105, 182, 0.1);
  padding: 16rpx;
}

.doctor-top {
  display: flex;
  justify-content: flex-end;
}

.doctor-follow {
  font-size: 22rpx;
  color: #3b82e0;
}

.doctor-avatar-mini {
  width: 76rpx;
  height: 76rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #4d90e8, #76b1f5);
  color: #ffffff;
  font-size: 30rpx;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.doctor-name {
  margin-top: 12rpx;
  display: block;
  font-size: 30rpx;
  font-weight: 650;
  color: #1d3d65;
}

.doctor-dept {
  margin-top: 4rpx;
  display: block;
  font-size: 22rpx;
  color: #6a84a5;
}

.patient-card {
  margin-top: 14rpx;
}

.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
}

.name {
  display: block;
  font-size: 34rpx;
  font-weight: 700;
  color: #163a62;
}

.meta-line {
  margin-top: 6rpx;
  display: block;
}

.meta {
  display: flex;
  justify-content: space-between;
  color: #5f7899;
  font-size: 26rpx;
  margin-top: 12rpx;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8rpx 16rpx;
  border-radius: 999rpx;
  border: 1rpx solid #d6e5f7;
  font-size: 22rpx;
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

.status-pill--danger {
  color: #b13d3d;
  border-color: #f2c8c8;
  background: #fff5f5;
}

.empty {
  margin: 28rpx 0 20rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10rpx;
  color: #6b83a4;
}

.empty-icon {
  width: 54rpx;
  height: 54rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6f86a6;
  background: #eef5ff;
  border: 1rpx solid #d6e5f7;
  font-size: 28rpx;
  font-weight: 600;
}

.empty-icon--loading {
  width: 42rpx;
  height: 42rpx;
  border: 4rpx solid #d2e3f8;
  border-top-color: #2f78d8;
  background: transparent;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>

