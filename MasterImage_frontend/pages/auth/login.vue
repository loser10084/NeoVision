<template>
  <view class="page login">
    <view class="hero">
      <view class="safe-area hero-inner">
        <view class="hero-top">
          <view>
            <text class="hero-title">智影医生端</text>
            <text class="hero-subtitle">放疗影像智能勾画协作平台</text>
          </view>
          <image class="hero-logo" src="/static/project_icon.jpg" mode="aspectFill" />
        </view>
        <view class="hero-chips">
          <text class="hero-chip">影像管理</text>
          <text class="hero-chip">AI勾画</text>
          <text class="hero-chip">医生复核</text>
        </view>
      </view>
    </view>

    <view class="safe-area content">
      <view class="card form-card">
        <view class="form-head">
          <view>
            <view class="section-title">欢迎回来</view>
            <text class="hint">使用注册手机号或工号登录</text>
          </view>
          <view class="pill">安全加密</view>
        </view>

        <wd-form ref="formRef" :model="form" :rules="rules">
          <view class="field">
            <text class="field-label">账户</text>
            <wd-input
              v-model="form.username"
              prop="username"
              placeholder="请输入手机号或工号"
              clearable
              size="large"
            />
          </view>
          <view class="field">
            <text class="field-label">密码</text>
            <wd-input
              v-model="form.password"
              prop="password"
              type="password"
              placeholder="请输入密码"
              clearable
              size="large"
            />
          </view>
        </wd-form>

        <view class="action-bar column">
          <wd-button
            block
            size="large"
            shape="round"
            type="primary"
            class="primary-btn"
            :loading="loading"
            @tap="handleLogin"
          >
            进入工作台
          </wd-button>
          <wd-button block size="large" shape="round" type="default" plain class="ghost-btn" @tap="goRegister">
            注册新账号
          </wd-button>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { login } from '../../common/api'

export default {
  data() {
    return {
      form: {
        username: '',
        password: ''
      },
      loading: false,
      rules: {
        username: [{ required: true, message: '请输入账号' }],
        password: [
          { required: true, message: '请输入密码' },
          { min: 6, message: '不少于 6 位字符' }
        ]
      }
    }
  },
  onLoad() {
    uni.$on('prefill-login', this.fillFromRegister)
  },
  onUnload() {
    uni.$off('prefill-login', this.fillFromRegister)
  },
  methods: {
    async handleLogin() {
      this.$refs.formRef
        .validate()
        .then(async () => {
          if (this.loading) return
          this.loading = true
          try {
            await login({ username: this.form.username, password: this.form.password })
            uni.showToast({ title: '登录成功', icon: 'success', duration: 600 })
            setTimeout(() => {
              uni.switchTab({ url: '/pages/patient/list' })
            }, 260)
          } catch (err) {
            console.error('login failed', err)
          } finally {
            this.loading = false
          }
        })
        .catch(() => {
          uni.showToast({ title: '请检查账号和密码', icon: 'none' })
        })
    },
    goRegister() {
      uni.navigateTo({ url: '/pages/auth/register' })
    },
    fillFromRegister(payload) {
      if (!payload) return
      this.form.username = payload.username || ''
      this.form.password = payload.password || ''
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
  border-bottom-left-radius: 30rpx;
  border-bottom-right-radius: 30rpx;
  box-shadow: 0 16rpx 44rpx rgba(42, 106, 188, 0.3);
}

.hero-inner {
  padding-top: calc(24rpx + env(safe-area-inset-top));
  padding-bottom: 20rpx;
}

.hero-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
}

.hero-title {
  display: block;
  font-size: 50rpx;
  font-weight: 700;
  color: #ffffff;
}

.hero-subtitle {
  display: block;
  margin-top: 8rpx;
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.86);
}

.hero-logo {
  width: 96rpx;
  height: 96rpx;
  border-radius: 24rpx;
  border: 2rpx solid rgba(255, 255, 255, 0.45);
  background: rgba(255, 255, 255, 0.24);
}

.hero-chips {
  margin-top: 16rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.hero-chip {
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.36);
  background: rgba(255, 255, 255, 0.18);
  color: #ffffff;
  font-size: 22rpx;
}

.content {
  margin-top: 18rpx;
  display: flex;
  flex-direction: column;
}

.form-card {
  background: rgba(255, 255, 255, 0.96);
  border: 1rpx solid #d6e5f7;
  border-radius: 32rpx;
  box-shadow: 0 26rpx 68rpx rgba(43, 104, 186, 0.16);
  display: flex;
  flex-direction: column;
  gap: 18rpx;
  padding: 30rpx 26rpx 26rpx;
}

.form-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-title {
  font-size: 34rpx;
  font-weight: 650;
  letter-spacing: 0.3rpx;
}

.hint {
  color: #627d9f;
  font-size: 26rpx;
}

.pill {
  padding: 12rpx 18rpx;
  border-radius: 999rpx;
  background: #eef5ff;
  color: #245eac;
  font-size: 24rpx;
  border: 1rpx solid #c8dcf6;
}

.action-bar {
  display: flex;
  width: 100%;
}

.column {
  flex-direction: column;
  gap: 14rpx;
  margin-top: 6rpx;
}

.primary-btn {
  box-shadow: 0 12rpx 30rpx rgba(47, 120, 216, 0.28);
}

.ghost-btn {
  border: 1rpx solid #c8daf4;
  color: #2f4f73;
  background: #ffffff;
  box-shadow: 0 8rpx 20rpx rgba(47, 120, 216, 0.12);
}

.field {
  display: block;
  padding: 4rpx 2rpx;
}

.field-label {
  display: block;
  margin-bottom: 8rpx;
  font-size: 26rpx;
  color: #2f4f73;
}

:deep(.wd-form) {
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

:deep(.wd-input) {
  flex: 1;
  height: 80rpx;
  border: 1rpx solid #cfe0f6;
  border-radius: 18rpx;
  padding: 0 18rpx;
  background: #f8fbff;
  color: #0c0d0f;
  box-sizing: border-box;
}

:deep(.wd-input__inner) {
  line-height: 80rpx;
  font-size: 30rpx;
  padding: 0;
}

:deep(.wd-input__clear) {
  line-height: 80rpx;
}
</style>
