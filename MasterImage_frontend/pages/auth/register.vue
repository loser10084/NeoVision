<template>
  <view class="page register">
    <view class="bg-blur bg-blur--left"></view>
    <view class="bg-blur bg-blur--right"></view>

    <view class="safe-area content">
      <view class="header">
        <view class="chip">智影 · 账户注册</view>
        <text class="title">创建医生账号</text>
        <text class="subtitle">信息仅用于对接审核与后续登录</text>
      </view>

      <view class="card form-card">
        <view class="form-head">
          <view>
            <view class="section-title">基本信息</view>
            <text class="hint">必填字段，建议使用实名信息</text>
          </view>
          <view class="pill">隐私保护</view>
        </view>

        <wd-form ref="formRef" :model="form" :rules="rules">
          <view class="field">
            <text class="field-label">姓名</text>
            <wd-input v-model="form.name" prop="name" placeholder="请输入真实姓名" clearable />
          </view>
          <view class="field">
            <text class="field-label">医院</text>
            <wd-input v-model="form.hospital" prop="hospital" placeholder="如：省肿瘤医院" clearable />
          </view>
          <view class="field">
            <text class="field-label">科室</text>
            <wd-input v-model="form.dept" prop="dept" placeholder="如：放疗科" clearable />
          </view>
          <view class="field">
            <text class="field-label">手机号</text>
            <wd-input v-model="form.mobile" prop="mobile" type="number" placeholder="11 位手机号" clearable />
          </view>
          <view class="field">
            <text class="field-label">密码</text>
            <wd-input
              v-model="form.password"
              prop="password"
              type="password"
              placeholder="至少 8 位，含数字和字母"
              clearable
            />
          </view>
          <view class="field">
            <text class="field-label">确认</text>
            <wd-input
              v-model="form.confirm"
              prop="confirm"
              type="password"
              placeholder="再次输入密码"
              clearable
            />
          </view>
        </wd-form>

        <view class="action-bar">
          <wd-button
            block
            size="large"
            shape="round"
            type="primary"
            class="primary-btn"
            :loading="loading"
            @click="handleRegister"
          >
            提交注册
          </wd-button>
          <wd-button block size="large" shape="round" type="default" plain class="ghost-btn" @click="back">
            返回登录
          </wd-button>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { registerUser } from '../../common/api'

export default {
  data() {
    return {
      form: {
        name: '',
        hospital: '',
        dept: '',
        mobile: '',
        password: '',
        confirm: ''
      },
      loading: false,
      rules: {
        name: [{ required: true, message: '请输入姓名' }],
        hospital: [{ required: true, message: '请输入医院' }],
        dept: [{ required: true, message: '请输入科室' }],
        mobile: [
          { required: true, message: '请输入手机号' },
          { pattern: /^1\\d{10}$/, message: '请输入 11 位手机号' }
        ],
        password: [
          { required: true, message: '请输入密码' },
          { min: 8, message: '至少 8 位' }
        ],
        confirm: [{ required: true, message: '请确认密码' }]
      }
    }
  },
  methods: {
    handleRegister() {
      this.$refs.formRef
        .validate()
        .then(async () => {
          if (this.loading) return
          if (this.form.confirm !== this.form.password) {
            uni.showToast({ title: '两次输入不一致', icon: 'none' })
            return
          }
          this.loading = true
          try {
            await registerUser({
              name: this.form.name,
              hospital: this.form.hospital,
              dept: this.form.dept,
              mobile: this.form.mobile,
              password: this.form.password
            })
            uni.showToast({ title: '注册成功，已填充登录', icon: 'success', duration: 1200 })
            setTimeout(() => {
              uni.navigateBack()
              uni.$emit('prefill-login', {
                username: this.form.mobile,
                password: this.form.password
              })
            }, 600)
          } catch (err) {
            console.error('register failed', err)
          } finally {
            this.loading = false
          }
        })
        .catch(() => {
          uni.showToast({ title: '请检查注册信息', icon: 'none' })
        })
    },
    back() {
      const pages = getCurrentPages()
      const hasLogin = pages.some((p) => p.route === 'pages/auth/login')
      if (hasLogin) {
        uni.navigateBack()
      } else {
        uni.reLaunch({ url: '/pages/auth/login' })
      }
    }
  }
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: #f7f7f8;
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
}

.title {
  font-size: 52rpx;
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
  background: rgba(255, 255, 255, 0.96);
  border: 1rpx solid #e6e7eb;
  border-radius: 32rpx;
  box-shadow: 0 26rpx 70rpx rgba(0, 0, 0, 0.05);
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
  flex-direction: column;
  gap: 14rpx;
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
  width: 140rpx;
  font-size: 28rpx;
  color: #111318;
}

:deep(.wd-form) {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
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
