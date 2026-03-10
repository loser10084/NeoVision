<template>
  <view class="page">
    <view class="safe-area">
      <view class="card search-card">
        <view class="section-header section-header--edge">
          <text class="section-title">搜索医生</text>
          <wd-button type="primary" size="small" :loading="searching" @click="searchDoctor">搜索</wd-button>
        </view>
        <view class="search-row">
          <wd-input v-model="doctorKeyword" placeholder="姓名/手机号/医院/科室" @confirm="searchDoctor" />
        </view>
        <view v-if="searchResults.length" class="doctor-list">
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
      </view>

      <view class="card friends-card">
        <view class="section-header section-header--edge">
          <text class="section-title">我的好友</text>
          <text class="friends-refresh" @click="refreshFriends">刷新</text>
        </view>
        <view v-if="loading" class="state-line">正在加载好友列表...</view>
        <view v-else-if="!friends.length" class="state-line">暂无好友</view>
        <view v-else class="doctor-list">
          <view v-for="item in friends" :key="item.id" class="doctor-item">
            <view class="doctor-left">
              <text class="doctor-name">{{ item.name || `医生${item.id}` }}</text>
              <text class="doctor-meta">{{ item.hospital || '-' }} / {{ item.dept || '-' }} / {{ item.mobile || '-' }}</text>
            </view>
            <text class="remove-btn" @click="handleRemoveFriend(item)">删除</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { listFriends, searchDoctors, addFriend, removeFriend } from '../../common/api'

export default {
  data() {
    return {
      loading: false,
      searching: false,
      doctorKeyword: '',
      friends: [],
      searchResults: []
    }
  },
  onShow() {
    this.refreshFriends()
  },
  methods: {
    async refreshFriends() {
      this.loading = true
      try {
        const friends = await listFriends()
        this.friends = Array.isArray(friends) ? friends : []
        this.markSearchResultFriend()
      } catch (err) {
        console.error('load friends failed', err)
      } finally {
        this.loading = false
      }
    },
    markSearchResultFriend() {
      const set = new Set((this.friends || []).map((item) => Number(item.id)))
      this.searchResults = (this.searchResults || []).map((item) => ({
        ...item,
        friend: set.has(Number(item.id))
      }))
    },
    async searchDoctor() {
      const keyword = String(this.doctorKeyword || '').trim()
      this.searching = true
      try {
        const result = await searchDoctors(keyword)
        this.searchResults = Array.isArray(result) ? result : []
        this.markSearchResultFriend()
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
        uni.showToast({ title: '好友已添加', icon: 'success' })
        await this.refreshFriends()
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
            this.markSearchResultFriend()
            uni.showToast({ title: '好友已删除', icon: 'success' })
          } catch (err) {
            console.error('remove friend failed', err)
          }
        }
      })
    }
  }
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: #edf4ff;
}

.search-card {
  margin-bottom: 18rpx;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
}

.section-header--edge {
  margin-bottom: 12rpx;
}

.section-title {
  font-size: 30rpx;
  font-weight: 700;
  color: #173a64;
}

.search-row :deep(.wd-input) {
  width: 100%;
}

.doctor-list {
  margin-top: 12rpx;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
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

.friends-refresh {
  font-size: 24rpx;
  color: #2f78d8;
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

.remove-btn {
  color: #c14c4c;
  font-size: 24rpx;
}
</style>
