<template>
  <view class="page register">
    <view class="hero">
      <view class="safe-area hero-inner">
        <view class="hero-top">
          <view>
            <text class="hero-title">创建医生账户</text>
            <text class="hero-subtitle">用于放疗影像勾画与复核工作流</text>
          </view>
          <image class="hero-logo" src="/static/project_icon_v2.jpg" mode="aspectFill" />
        </view>
        <view class="hero-chips">
          <text class="hero-chip">身份审核</text>
          <text class="hero-chip">数据加密</text>
          <text class="hero-chip">流程追踪</text>
        </view>
      </view>
    </view>

    <view class="safe-area content">
      <view class="card form-card">
        <view class="form-head">
          <view>
            <view class="section-title">基本信息</view>
            <text class="hint">必填字段，建议使用真实信息</text>
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
            <wd-input v-model="form.mobile" prop="mobile" type="number" placeholder="11位手机号" clearable />
          </view>
          <view class="field">
            <text class="field-label">密码</text>
            <wd-input
              v-model="form.password"
              prop="password"
              type="password"
              placeholder="至少8位，含数字和字母"
              clearable
            />
          </view>
          <view class="field">
            <text class="field-label">确认密码</text>
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
          { pattern: /^1\d{10}$/, message: '请输入11位手机号' }
        ],
        password: [
          { required: true, message: '请输入密码' },
          { min: 8, message: '至少8位' }
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
  font-size: 48rpx;
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
  width: 92rpx;
  height: 92rpx;
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
  gap: 8rpx;
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
