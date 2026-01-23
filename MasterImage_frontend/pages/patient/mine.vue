<template>
  <view class="page">
    <view class="safe-area">
      <view class="card profile-card">
        <view class="section-title">我的</view>
        <view class="divider"></view>
        <view class="profile">
          <view class="avatar">{{ initials }}</view>
          <view>
            <text class="name">{{ profile.name || '医生' }}</text>
            <text class="subtle">{{ profile.hospital || '-' }} · {{ profile.dept || '-' }}</text>
          </view>
        </view>
        <view class="stats">
          <view class="stat-item">
            <text class="stat-number">{{ profile.done || 0 }}</text>
            <text class="subtle">已完成</text>
          </view>
          <view class="stat-item">
            <text class="stat-number">{{ profile.pending || 0 }}</text>
            <text class="subtle">待复核</text>
          </view>
          <view class="stat-item">
            <text class="stat-number">{{ profile.saved || 0 }}h</text>
            <text class="subtle">工作时长</text>
          </view>
        </view>
      </view>

      <view class="card">
        <view class="section-title">快捷操作</view>
        <wd-cell-group>
          <wd-cell title="账户与安全" label="待接入接口配置" is-link />
          <wd-cell title="使用指南" label="查看产品提示与流程" is-link />
          <wd-cell title="关于智影" label="基于多模态分割的放疗助手" is-link />
          <wd-cell title="退出登录" label="返回登录页" is-link @click="logout" />
        </wd-cell-group>
      </view>
    </view>
  </view>
</template>

<script>
import { logout as logoutApi } from '../../common/api'

export default {
  data() {
    return {
      profile: {
        name: '',
        hospital: '',
        dept: '',
        done: 0,
        pending: 0,
        saved: 0
      }
    }
  },
  computed: {
    initials() {
      if (!this.profile.name) return '医'
      return this.profile.name.slice(0, 1)
    }
  },
  onShow() {
    const cache = uni.getStorageSync('userProfile') || {}
    this.profile = {
      ...this.profile,
      ...cache
    }
  },
  methods: {
    logout() {
      logoutApi()
      uni.reLaunch({ url: '/pages/auth/login' })
    }
  }
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: #f7f7f8;
}

.profile-card {
  margin-bottom: 18rpx;
}

.profile {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;
  background: #0f1012;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36rpx;
  font-weight: 700;
}

.name {
  display: block;
  font-size: 34rpx;
  font-weight: 700;
  color: #0c0d0f;
}

.stats {
  display: flex;
  justify-content: space-between;
  gap: 14rpx;
  margin-top: 18rpx;
}

.stat-item {
  flex: 1;
  background: #fafafa;
  border-radius: 18rpx;
  padding: 18rpx;
  text-align: center;
  border: 1rpx solid #e6e7eb;
}

.stat-number {
  font-size: 32rpx;
  font-weight: 700;
  display: block;
  margin-bottom: 4rpx;
  color: #0c0d0f;
}
</style>
