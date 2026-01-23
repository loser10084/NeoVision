<template>
  <view class="page">
    <view class="safe-area">
      <view class="friend-list">
        <view class="friend-item" @click="openChat">
          <image class="avatar" src="/static/project_icon.jpg" mode="aspectFill" />
          <view class="info">
            <view class="top-row">
              <text class="name">智能体助手</text>
              <text class="time">刚刚</text>
            </view>
            <text class="preview">点我进入对话，开始智能体沟通</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  methods: {
    openChat() {
      uni.navigateTo({ url: '/pages/agent/conversation' })
    }
  }
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: #f3f4f6;
}

.safe-area {
  padding: 16rpx 20rpx;
}

.friend-list {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.friend-item {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 18rpx 20rpx;
  background: #ffffff;
  border-radius: 20rpx;
  box-shadow: 0 6rpx 16rpx rgba(15, 16, 18, 0.06);
}

.avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 24rpx;
  background: #e6e7eb;
}

.info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
  min-width: 0;
}

.top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
}

.name {
  font-size: 30rpx;
  font-weight: 600;
  color: #0c0d0f;
}

.time {
  font-size: 22rpx;
  color: #9aa0a6;
}

.preview {
  font-size: 24rpx;
  color: #6b7075;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
