<template>
  <view class="page login">
    <view class="bg-blur bg-blur--left"></view>
    <view class="bg-blur bg-blur--right"></view>

    <view class="safe-area content">
      <view class="header">
        <image class="brand-logo" src="/static/project_icon.jpg" mode="aspectFit" />
      </view>

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
  background: #fefeff;
  position: relative;
  overflow: hidden;
  color: #0c0d0f;
}

.bg-blur {
  position: absolute;
  width: 420rpx;
  height: 420rpx;
  border-radius: 50%;
  filter: blur(68rpx);
  opacity: 0.16;
  background: radial-gradient(circle at 30% 30%, #ffffff, #e9eaed);
}

.bg-blur--left {
  top: -120rpx;
  left: -80rpx;
}

.bg-blur--right {
  bottom: -140rpx;
  right: -120rpx;
  background: radial-gradient(circle at 70% 40%, #f1f2f5, #e4e6ea);
}

.content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 34rpx;
}

.header {
  margin: 12rpx 0 10rpx;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
  align-items: center;
}

.brand-logo {
  width: 160rpx;
  height: 160rpx;
  border-radius: 32rpx;
  background: #fefeff;
}

.title {
  font-size: 60rpx;
  font-weight: 750;
  letter-spacing: 0.3rpx;
}

.subtitle {
  font-size: 30rpx;
  color: #4f545c;
  line-height: 1.6;
}

.form-card {
  margin-top: 6rpx;
  background: transparent;
  border: none;
  border-radius: 32rpx;
  box-shadow: none;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
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
  color: #6a6f78;
  font-size: 26rpx;
}

.pill {
  padding: 12rpx 18rpx;
  border-radius: 999rpx;
  background: #f3f4f6;
  color: #0c0d0f;
  font-size: 26rpx;
  border: 1rpx solid #e6e7eb;
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
  background: #ffffff;
  color: #0f1012;
  border: 1rpx solid #0f1012;
  box-shadow: none;
  border-radius: 999rpx;
}

.ghost-btn {
  border: 1rpx solid #d8dade;
  color: #0c0d0f;
  background: #ffffff;
  border-radius: 999rpx;
}

.field {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 8rpx 6rpx;
}

.field-label {
  width: 120rpx;
  font-size: 28rpx;
  color: #111318;
}

:deep(.wd-form) {
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

:deep(.wd-input) {
  flex: 1;
  height: 80rpx;
  border: 1rpx solid #dee0e5;
  border-radius: 18rpx;
  padding: 0 16rpx;
  background: #ffffff;
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
