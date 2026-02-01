<template>
  <view class="page">
    <view class="safe-area">
      <view class="toolbar card">
        <wd-search
          v-model="keyword"
          placeholder="搜索姓名 / 影像号"
          shape="round"
          show-action
          :disabled="loading"
          @change="handleSearch"
        />
        <view class="toolbar-actions">
          <wd-button
            class="add-patient-btn"
            block
            size="small"
            shape="round"
            type="primary"
            @click="addPatient"
          >
            新增患者
          </wd-button>
        </view>
      </view>

      <view v-for="patient in patients" :key="patient.id" class="card patient-card" @click="goDetail(patient)">
        <view class="row">
          <view>
            <text class="name">{{ patient.name }}</text>
            <text class="subtle">{{ patient.sex }} · {{ patient.age }} 岁</text>
          </view>
          <wd-tag :type="statusTagType(patient.status)" plain>
            {{ formatStatus(patient.status) }}
          </wd-tag>
        </view>

        <view class="meta">
          <text>ID {{ patient.id }}</text>
          <text>影像号 {{ patient.studyId || '-' }}</text>
        </view>
        <view class="meta">
          <text>{{ patient.diagnosis }} · {{ patient.stage || '未分期' }}</text>
          <text class="subtle">{{ patient.lastUpdate || '-' }}</text>
        </view>

        <view class="divider"></view>
      </view>

      <view v-if="patients.length === 0 && !loading" class="empty">
        <wd-icon name="info" size="24" />
        <text class="subtle">暂无匹配结果，试试其他关键词</text>
      </view>
      <view v-if="loading" class="empty">
        <wd-icon name="loading" size="24" />
        <text class="subtle">加载中...</text>
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
      lastAutoRefreshTs: 0
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
    goDetail(patient) {
      if (!patient || !patient.id) return
      uni.navigateTo({
        url: `/pages/patient/detail?id=${patient.id}`,
        success: () => {
          uni.setStorageSync('currentPatient', patient)
        }
      })
    },
    upload(patient) {
      // 引导到详情页进行上传/登记
      this.goDetail(patient)
      uni.showToast({ title: '请在患者详情页上传/登记影像', icon: 'none' })
    },
    addPatient() {
      uni.navigateTo({ url: '/pages/patient/add' })
    }
  }
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: #f7f7f8;
}

.toolbar {
  margin-bottom: 20rpx;
  background: #ffffff;
  border: 1rpx solid #e6e7eb;
}

.toolbar-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 16rpx;
  gap: 12rpx;
}

.add-patient-btn {
  width: 100%;
}

.patient-card {
  margin-bottom: 18rpx;
  background: #ffffff;
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
  color: #0c0d0f;
}

.meta {
  display: flex;
  justify-content: space-between;
  color: #6b7075;
  font-size: 26rpx;
  margin-top: 12rpx;
}

.progress {
  display: flex;
  justify-content: space-between;
  gap: 12rpx;
}

.progress-item {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f5f6f7;
  padding: 14rpx;
  border-radius: 16rpx;
  border: 1rpx solid #e6e7eb;
}

.label {
  color: #0c0d0f;
  font-weight: 600;
}

.empty {
  margin-top: 40rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10rpx;
  color: #6b7075;
}
</style>
