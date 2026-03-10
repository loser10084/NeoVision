<template>
  <view class="page">
    <view class="hero">
      <view class="safe-area hero-inner">
        <view class="hero-top">
          <view>
            <text class="hero-title">会诊中心与AI助手</text>
            <text class="hero-subtitle">支持智能问答、医生协作沟通与资料共享</text>
          </view>
          <image class="hero-avatar" src="/static/project_icon_v2.jpg" mode="aspectFill" />
        </view>
      </view>
    </view>

    <view class="safe-area body-area">
      <view class="quick-grid">
        <view class="quick-card" @click="openAiConversation">
          <view class="quick-icon quick-icon--ai">
            <text>AI</text>
          </view>
          <view class="quick-text">
            <text class="quick-title">进入AI问答</text>
            <text class="quick-desc">勾画建议、流程问答、报告辅助</text>
          </view>
          <wd-icon name="arrow-right" size="18" color="#2f78d8" />
        </view>

        <view class="quick-card" @click="openCreateDialog">
          <view class="quick-icon quick-icon--group">
            <text>协</text>
          </view>
          <view class="quick-text">
            <text class="quick-title">发起联合会诊</text>
            <text class="quick-desc">邀请医生好友共同讨论</text>
          </view>
          <wd-icon name="arrow-right" size="18" color="#2f78d8" />
        </view>
      </view>

      <view class="section-head">
        <text class="section-title">我的会诊</text>
        <view class="section-actions">
          <text class="section-count">{{ consultations.length }} 个会诊</text>
          <text class="section-refresh" @click="refreshData">刷新</text>
        </view>
      </view>

      <view v-if="loading" class="state-card">
        <text class="state-text">正在加载会诊列表...</text>
      </view>
      <view v-else-if="!consultations.length" class="state-card">
        <text class="state-text">暂无会诊，请点击上方发起联合会诊</text>
      </view>
      <view v-else class="consultation-list">
        <view v-for="item in consultations" :key="item.id" class="consultation-item" @click="openConsultation(item)">
          <view class="consultation-top">
            <text class="consultation-title">{{ item.title || '未命名会诊' }}</text>
            <text class="consultation-time">{{ formatTime(item.lastMessageAt || item.createdAt) }}</text>
          </view>
          <text class="consultation-meta">{{ formatMeta(item) }}</text>
          <text class="consultation-preview">{{ formatPreview(item) }}</text>
        </view>
      </view>
    </view>

    <view v-if="showCreateDialog" class="overlay" @click="closeCreateDialog">
      <view class="dialog" @click.stop>
        <view class="dialog-header">
          <text class="dialog-title">新建联合会诊</text>
          <view class="dialog-header-actions">
            <text class="dialog-submit" @click="submitCreateConsultation">{{ saving ? '创建中...' : '确定' }}</text>
            <wd-icon name="close" @click="closeCreateDialog" />
          </view>
        </view>

        <view class="dialog-content">
          <view class="dialog-field">
            <text class="dialog-label">会诊标题</text>
            <wd-input v-model="createForm.title" placeholder="请输入会诊标题" />
          </view>

          <view class="dialog-field">
            <text class="dialog-label">患者ID（可选，需存在）</text>
            <wd-input v-model="createForm.patientId" placeholder="例如 1001（可留空）" />
          </view>

          <view class="dialog-field">
            <view class="dialog-label-row">
              <text class="dialog-label">选择成员（好友）</text>
              <text class="dialog-sub">已选 {{ createForm.memberIds.length }} 人</text>
            </view>
            <view v-if="friends.length" class="friend-pills">
              <view
                v-for="friend in friends"
                :key="friend.id"
                class="friend-pill"
                :class="{ 'friend-pill--active': isSelectedMember(friend.id) }"
                @click="toggleMember(friend.id)"
              >
                <text class="friend-pill-name">{{ friend.name || friend.mobile || `医生${friend.id}` }}</text>
                <text class="friend-pill-sub">{{ friend.hospital || '-' }} / {{ friend.dept || '-' }}</text>
              </view>
            </view>
            <view v-else class="friend-empty" @click="openFriendsPage">暂无好友，点击前往“医生好友”页面</view>
          </view>
        </view>


      </view>
    </view>
  </view>
</template>

<script>
import { listConsultations, createConsultation, listFriends } from '../../common/api'

export default {
  data() {
    return {
      loading: false,
      saving: false,
      consultations: [],
      friends: [],
      showCreateDialog: false,
      createForm: {
        title: '',
        patientId: '',
        memberIds: []
      }
    }
  },
  onShow() {
    this.refreshData()
  },
  methods: {
    async refreshData() {
      if (this.loading) return
      this.loading = true
      try {
        const [consultations, friends] = await Promise.all([listConsultations(), listFriends()])
        this.consultations = Array.isArray(consultations) ? consultations : []
        this.friends = Array.isArray(friends) ? friends : []
      } catch (err) {
        console.error('load consultations failed', err)
      } finally {
        this.loading = false
      }
    },
    openAiConversation() {
      uni.navigateTo({ url: '/pages/agent/conversation' })
    },
    openConsultation(item) {
      if (!item || !item.id) return
      const title = encodeURIComponent(item.title || '联合会诊')
      uni.navigateTo({ url: `/pages/agent/conversation?consultationId=${item.id}&title=${title}` })
    },
    openCreateDialog() {
      this.showCreateDialog = true
    },
    openFriendsPage() {
      uni.navigateTo({ url: '/pages/patient/friends' })
    },
    closeCreateDialog() {
      this.showCreateDialog = false
      this.saving = false
      this.createForm = {
        title: '',
        patientId: '',
        memberIds: []
      }
    },
    isSelectedMember(doctorId) {
      return this.createForm.memberIds.includes(doctorId)
    },
    toggleMember(doctorId) {
      const ids = this.createForm.memberIds
      const index = ids.indexOf(doctorId)
      if (index >= 0) {
        ids.splice(index, 1)
        return
      }
      ids.push(doctorId)
    },
    async submitCreateConsultation() {
      const title = String(this.createForm.title || '').trim()
      if (!title) {
        uni.showToast({ title: '请填写会诊标题', icon: 'none' })
        return
      }
      const rawPatientId = String(this.createForm.patientId || '').trim()
      if (rawPatientId && !/^[1-9]\d*$/.test(rawPatientId)) {
        uni.showToast({ title: '患者ID需为正整数', icon: 'none' })
        return
      }
      if (this.saving) return
      this.saving = true
      const patientId = rawPatientId ? Number(rawPatientId) : null
      const payload = {
        title,
        memberIds: this.createForm.memberIds.slice()
      }
      if (patientId !== null) {
        payload.patientId = patientId
      }
      try {
        const created = await createConsultation(payload)
        uni.showToast({ title: '创建成功', icon: 'success' })
        this.closeCreateDialog()
        await this.refreshData()
        if (created?.id) {
          const titleText = encodeURIComponent(created.title || title)
          uni.navigateTo({ url: `/pages/agent/conversation?consultationId=${created.id}&title=${titleText}` })
        }
      } catch (err) {
        console.error('create consultation failed', err)
        uni.showToast({ title: this.resolveCreateConsultationError(err), icon: 'none' })
      } finally {
        this.saving = false
      }
    },
    resolveCreateConsultationError(err) {
      const message = String(err?.message || '').trim()
      if (!message) {
        return '创建失败，请稍后重试'
      }
      if (message.includes('patient not found') || message.includes('fk_consult_patient') || message.includes('Cannot add or update a child row')) {
        return '患者ID不存在，请填写已有患者ID或留空'
      }
      if (message.includes('invalid patientId')) {
        return '患者ID需为正整数'
      }
      if (message.length > 28) {
        return '创建失败，请检查填写信息'
      }
      return message
    },
    formatPreview(item) {
      const text = String(item?.lastMessage || '').trim()
      if (!text) return '暂无消息，点击进入会诊沟通'
      return text
    },
    formatMeta(item) {
      const parts = []
      if (item?.patientId) parts.push(`患者ID: ${item.patientId}`)
      parts.push(this.formatConsultStatus(item?.status))
      return parts.join(' · ')
    },
    formatConsultStatus(status) {
      const key = String(status || '').trim().toUpperCase()
      const map = {
        ACTIVE: '进行中',
        PENDING: '待处理',
        PROCESSING: '处理中',
        COMPLETED: '已完成',
        CLOSED: '已关闭'
      }
      return map[key] || '进行中'
    },
    formatTime(value) {
      if (!value) return '-'
      const text = String(value)
      if (text.includes(' ')) {
        const parts = text.split(' ')
        if (parts.length >= 2) return `${parts[0].slice(5)} ${parts[1].slice(0, 5)}`
      }
      return text
    }
  }
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: #edf4ff;
}

.hero {
  background: linear-gradient(155deg, #2f78d8 0%, #3888ee 44%, #62a6f4 100%);
  border-bottom-left-radius: 26rpx;
  border-bottom-right-radius: 26rpx;
  box-shadow: 0 14rpx 44rpx rgba(42, 106, 188, 0.28);
}

.hero-inner {
  padding-top: calc(20rpx + env(safe-area-inset-top));
  padding-bottom: 20rpx;
}

.hero-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
}

.hero-title {
  display: block;
  font-size: 44rpx;
  font-weight: 700;
  color: #ffffff;
}

.hero-subtitle {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.84);
}

.hero-avatar {
  width: 88rpx;
  height: 88rpx;
  border-radius: 24rpx;
  border: 2rpx solid rgba(255, 255, 255, 0.44);
  background: rgba(255, 255, 255, 0.2);
}

.body-area {
  margin-top: 16rpx;
  padding-top: 10rpx;
  padding-bottom: calc(18rpx + env(safe-area-inset-bottom));
}

.quick-grid {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
  margin-bottom: 22rpx;
}

.quick-card {
  background: #ffffff;
  border-radius: 24rpx;
  border: 1rpx solid #d6e5f7;
  box-shadow: 0 14rpx 36rpx rgba(47, 105, 182, 0.12);
  padding: 22rpx;
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.quick-icon {
  width: 72rpx;
  height: 72rpx;
  border-radius: 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
  font-weight: 700;
  color: #2f78d8;
  border: 1rpx solid #d6e5f7;
}

.quick-icon--ai {
  background: #eaf3ff;
}

.quick-icon--group {
  background: #edf8ff;
}

.quick-text {
  flex: 1;
  min-width: 0;
}

.quick-title {
  display: block;
  font-size: 30rpx;
  font-weight: 650;
  color: #173a64;
}

.quick-desc {
  display: block;
  margin-top: 4rpx;
  font-size: 24rpx;
  color: #6a84a5;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10rpx;
}

.section-title {
  font-size: 34rpx;
  font-weight: 700;
  color: #173a64;
}

.section-actions {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.section-count {
  font-size: 22rpx;
  color: #8aa0bd;
}

.section-refresh {
  font-size: 24rpx;
  color: #2f78d8;
}

.state-card {
  background: #ffffff;
  border-radius: 22rpx;
  border: 1rpx solid #d6e5f7;
  padding: 30rpx 24rpx;
}

.state-text {
  color: #6a84a5;
  font-size: 26rpx;
}

.consultation-list {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.consultation-item {
  background: #ffffff;
  border-radius: 22rpx;
  border: 1rpx solid #d6e5f7;
  box-shadow: 0 12rpx 32rpx rgba(47, 105, 182, 0.1);
  padding: 20rpx;
}

.consultation-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
}

.consultation-title {
  flex: 1;
  min-width: 0;
  font-size: 30rpx;
  font-weight: 650;
  color: #173a64;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.consultation-time {
  font-size: 22rpx;
  color: #8aa0bd;
}

.consultation-meta {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  color: #7090b2;
}

.consultation-preview {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  color: #5f7899;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.overlay {
  position: fixed;
  inset: 0;
  z-index: 99;
  background: rgba(17, 39, 68, 0.38);
  display: flex;
  align-items: flex-end;
}

.dialog {
  width: 100%;
  min-height: 56vh;
  max-height: 88vh;
  background: #ffffff;
  border-top-left-radius: 28rpx;
  border-top-right-radius: 28rpx;
  padding: 24rpx;
  overflow: hidden;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16rpx;
}

.dialog-header-actions {
  display: flex;
  align-items: center;
  gap: 18rpx;
}

.dialog-submit {
  font-size: 28rpx;
  font-weight: 600;
  color: #2f78d8;
}

.dialog-title {
  font-size: 34rpx;
  font-weight: 700;
  color: #173a64;
}

.dialog-content {
  flex: 1;
  min-height: 0;
  max-height: 58vh;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  padding-bottom: 12rpx;
}

.dialog-field {
  margin-bottom: 16rpx;
}

.dialog-label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8rpx;
}

.dialog-label {
  display: block;
  margin-bottom: 8rpx;
  font-size: 26rpx;
  color: #345a84;
}

.dialog-sub {
  font-size: 22rpx;
  color: #7c98b8;
}

.friend-pills {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.friend-pill {
  border: 1rpx solid #d6e5f7;
  border-radius: 18rpx;
  padding: 12rpx 14rpx;
  background: #f8fbff;
}

.friend-pill--active {
  border-color: #88b5ea;
  background: #edf4ff;
}

.friend-pill-name {
  display: block;
  font-size: 26rpx;
  color: #173a64;
  font-weight: 600;
}

.friend-pill-sub {
  display: block;
  margin-top: 4rpx;
  font-size: 22rpx;
  color: #6f89ab;
}

.friend-empty {
  font-size: 24rpx;
  color: #7c98b8;
  padding: 12rpx;
  background: #f8fbff;
  border-radius: 14rpx;
}


</style>

