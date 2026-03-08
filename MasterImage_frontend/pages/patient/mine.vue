<template>
  <view class="page">
    <view class="safe-area">
      <view class="card profile-card">
        <view class="section-title">我的</view>
        <view class="divider"></view>
        <view class="profile">
          <view class="avatar">{{ initials }}</view>
          <view class="profile-main">
            <text class="name">{{ profile.name || '医生' }}</text>
            <text class="subtle">{{ profile.hospital || '-' }} / {{ profile.dept || '-' }}</text>
            <text class="subtle">账号：{{ profile.mobile || '-' }}</text>
          </view>
        </view>

        <view class="stats">
          <view class="stat-item">
            <text class="stat-number">{{ profile.done || 0 }}</text>
            <text class="subtle">已完成</text>
          </view>
          <view class="stat-item">
            <text class="stat-number">{{ consultationsCount }}</text>
            <text class="subtle">我的会诊</text>
          </view>
          <view class="stat-item">
            <text class="stat-number">{{ friends.length }}</text>
            <text class="subtle">医生好友</text>
          </view>
        </view>
      </view>

      <view class="card friends-card">
        <view class="friends-head">
          <text class="section-title section-title--small">医生好友</text>
          <text class="friends-refresh" @click="refreshSocialData">刷新</text>
        </view>

        <view class="search-row">
          <wd-input v-model="doctorKeyword" placeholder="姓名/手机号/医院/科室" @confirm="searchDoctor" />
          <wd-button type="primary" size="small" :loading="searching" @click="searchDoctor">搜索</wd-button>
        </view>

        <view v-if="searchResults.length" class="search-results">
          <view v-for="item in searchResults" :key="item.id" class="doctor-item">
            <view class="doctor-left">
              <text class="doctor-name">{{ item.name || `医生${item.id}` }}</text>
              <text class="doctor-meta">{{ item.hospital || '-' }} / {{ item.dept || '-' }} / {{ item.mobile || '-' }}</text>
            </view>
            <wd-button
              :type="item.friend ? 'success' : 'primary'"
              size="small"
              plain
              :disabled="item.friend"
              @click="handleAddFriend(item)"
            >
              {{ item.friend ? '已添加' : '添加' }}
            </wd-button>
          </view>
        </view>

        <view v-if="friendsLoading" class="state-line">正在加载好友列表...</view>
        <view v-else-if="!friends.length" class="state-line">暂无好友，可通过上方搜索添加</view>
        <view v-else class="friend-list">
          <view v-for="item in friends" :key="item.id" class="doctor-item">
            <view class="doctor-left">
              <text class="doctor-name">{{ item.name || `医生${item.id}` }}</text>
              <text class="doctor-meta">{{ item.hospital || '-' }} / {{ item.dept || '-' }} / {{ item.mobile || '-' }}</text>
            </view>
            <text class="remove-btn" @click="handleRemoveFriend(item)">删除</text>
          </view>
        </view>
      </view>

      <view class="card settings-card">
        <view class="section-title section-title--small">快捷操作</view>
        <view class="setting-list">
          <view v-for="item in actions" :key="item.key" class="setting-item" @click="handleAction(item)">
            <view class="setting-left">
              <view class="setting-icon" :class="`setting-icon--${item.key}`">{{ item.icon }}</view>
              <view class="setting-texts">
                <text class="setting-title">{{ item.title }}</text>
                <text class="setting-sub">{{ item.label }}</text>
              </view>
            </view>
            <text class="setting-arrow">></text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { logout as logoutApi, listFriends, searchDoctors, addFriend, removeFriend, listConsultations } from '../../common/api'

export default {
  data() {
    return {
      profile: {
        name: '',
        hospital: '',
        dept: '',
        mobile: '',
        done: 0,
        pending: 0,
        saved: 0
      },
      consultationsCount: 0,
      friends: [],
      friendsLoading: false,
      searching: false,
      doctorKeyword: '',
      searchResults: [],
      actions: [
        { key: 'consult', icon: '诊', title: '进入联合会诊', label: '在智能体页面查看会诊与聊天' },
        { key: 'about', icon: '智', title: '关于灵犀智影', label: '面向放疗影像勾画的智能助手' },
        { key: 'logout', icon: '退', title: '退出登录', label: '返回登录页' }
      ]
    }
  },
  computed: {
    initials() {
      if (!this.profile.name) return '医'
      return this.profile.name.slice(0, 1)
    }
  },
  onShow() {
    this.loadProfile()
    this.refreshSocialData()
  },
  methods: {
    loadProfile() {
      const cache = uni.getStorageSync('userProfile') || {}
      this.profile = {
        ...this.profile,
        ...cache
      }
    },
    async refreshSocialData() {
      this.friendsLoading = true
      try {
        const [friends, consultations] = await Promise.all([listFriends(), listConsultations()])
        this.friends = Array.isArray(friends) ? friends : []
        this.consultationsCount = Array.isArray(consultations) ? consultations.length : 0
      } catch (err) {
        console.error('refresh social data failed', err)
      } finally {
        this.friendsLoading = false
      }
    },
    async searchDoctor() {
      const keyword = String(this.doctorKeyword || '').trim()
      this.searching = true
      try {
        const result = await searchDoctors(keyword)
        this.searchResults = Array.isArray(result) ? result : []
      } catch (err) {
        console.error('search doctor failed', err)
      } finally {
        this.searching = false
      }
    },
    async handleAddFriend(item) {
      if (!item || !item.id || item.friend) return
      try {
        await addFriend(item.id)
        item.friend = true
        await this.refreshSocialData()
        uni.showToast({ title: '好友已添加', icon: 'success' })
      } catch (err) {
        console.error('add friend failed', err)
      }
    },
    handleRemoveFriend(item) {
      if (!item || !item.id) return
      uni.showModal({
        title: '提示',
        content: `确认删除好友 ${item.name || ''} 吗？`,
        success: async (res) => {
          if (!res.confirm) return
          try {
            await removeFriend(item.id)
            this.friends = this.friends.filter((friend) => Number(friend.id) !== Number(item.id))
            this.searchResults = this.searchResults.map((doctor) => {
              if (Number(doctor.id) === Number(item.id)) {
                return { ...doctor, friend: false }
              }
              return doctor
            })
            uni.showToast({ title: '好友已删除', icon: 'success' })
          } catch (err) {
            console.error('remove friend failed', err)
          }
        }
      })
    },
    handleAction(item) {
      if (!item) return
      if (item.key === 'logout') {
        this.logout()
        return
      }
      if (item.key === 'consult') {
        uni.switchTab({ url: '/pages/agent/chat' })
        return
      }
      uni.showToast({ title: '功能完善中', icon: 'none' })
    },
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
  background: #edf4ff;
}

.profile-card {
  margin-bottom: 18rpx;
}

.profile {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.profile-main {
  min-width: 0;
  flex: 1;
}

.avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 26rpx;
  background: linear-gradient(145deg, #2f78d8 0%, #5da4f0 100%);
  box-shadow: 0 14rpx 28rpx rgba(47, 120, 216, 0.3);
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
  color: #173a64;
}

.stats {
  display: flex;
  justify-content: space-between;
  gap: 14rpx;
  margin-top: 18rpx;
}

.stat-item {
  flex: 1;
  background: #f4f8ff;
  border-radius: 18rpx;
  padding: 18rpx;
  text-align: center;
  border: 1rpx solid #d6e5f7;
  box-shadow: 0 10rpx 24rpx rgba(47, 105, 182, 0.1);
}

.stat-number {
  font-size: 32rpx;
  font-weight: 700;
  display: block;
  margin-bottom: 4rpx;
  color: #0c0d0f;
}

.friends-card {
  margin-bottom: 18rpx;
}

.friends-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10rpx;
}

.friends-refresh {
  font-size: 24rpx;
  color: #2f78d8;
}

.section-title--small {
  margin-bottom: 0;
  font-size: 30rpx;
}

.search-row {
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.search-row :deep(.wd-input) {
  flex: 1;
}

.search-results,
.friend-list {
  margin-top: 12rpx;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.state-line {
  margin-top: 12rpx;
  font-size: 24rpx;
  color: #7c98b8;
  padding: 12rpx;
  border: 1rpx dashed #d1e2f7;
  border-radius: 14rpx;
  background: #f8fbff;
}

.doctor-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10rpx;
  border: 1rpx solid #d6e5f7;
  border-radius: 16rpx;
  padding: 12rpx 14rpx;
  background: #f8fbff;
}

.doctor-left {
  min-width: 0;
  flex: 1;
}

.doctor-name {
  display: block;
  font-size: 28rpx;
  color: #173a64;
  font-weight: 650;
}

.doctor-meta {
  display: block;
  margin-top: 4rpx;
  font-size: 22rpx;
  color: #6a84a6;
}

.remove-btn {
  color: #c14c4c;
  font-size: 24rpx;
}

.setting-list {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14rpx;
  padding: 18rpx;
  border-radius: 20rpx;
  border: 1rpx solid #d6e5f7;
  background: #f8fbff;
  box-shadow: 0 10rpx 24rpx rgba(47, 105, 182, 0.08);
}

.setting-left {
  display: flex;
  align-items: center;
  gap: 14rpx;
  flex: 1;
  min-width: 0;
}

.setting-icon {
  width: 58rpx;
  height: 58rpx;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20rpx;
  font-weight: 700;
  color: #2f78d8;
  border: 1rpx solid #cde0f7;
  background: #edf4ff;
}

.setting-icon--logout {
  color: #b13d3d;
  border-color: #f0cccc;
  background: #fff5f5;
}

.setting-texts {
  flex: 1;
  min-width: 0;
}

.setting-title {
  display: block;
  font-size: 30rpx;
  font-weight: 650;
  color: #173a64;
}

.setting-sub {
  display: block;
  margin-top: 4rpx;
  font-size: 24rpx;
  color: #6a84a6;
}

.setting-arrow {
  color: #7a95b5;
  font-size: 32rpx;
}
</style>
