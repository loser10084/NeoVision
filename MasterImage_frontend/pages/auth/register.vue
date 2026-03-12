<template>
  <view class="page">
    <scroll-view class="viewport" scroll-y :show-scrollbar="false" :style="{ height: viewportHeight }">
      <view class="safe-area register-layout">
        <view class="hero-card">
          <view class="hero-row">
            <view class="hero-copy">
              <text class="hero-eyebrow">{{ txt.eyebrow }}</text>
              <text class="hero-title">{{ txt.title }}</text>
              <text class="hero-subtitle">{{ txt.subtitle }}</text>
            </view>
            <image class="hero-logo" src="/static/project_icon_v2.jpg" mode="aspectFill" />
          </view>
          <view class="hero-tags">
            <text class="hero-tag">{{ txt.tag1 }}</text>
            <text class="hero-tag">{{ txt.tag2 }}</text>
            <text class="hero-tag">{{ txt.tag3 }}</text>
          </view>
        </view>

        <view class="card form-card">
          <view class="section-head">
            <text class="section-title">{{ txt.formTitle }}</text>
            <text class="section-hint">{{ txt.formHint }}</text>
          </view>

          <view class="field">
            <text class="label">{{ txt.name }}</text>
            <input
              class="input"
              v-model="form.name"
              :placeholder="txt.namePlaceholder"
              placeholder-class="placeholder"
            />
          </view>

          <view class="field">
            <text class="label">{{ txt.hospital }}</text>
            <input
              class="input"
              v-model="form.hospital"
              :placeholder="txt.hospitalPlaceholder"
              placeholder-class="placeholder"
            />
          </view>

          <view class="field">
            <text class="label">{{ txt.dept }}</text>
            <input
              class="input"
              v-model="form.dept"
              :placeholder="txt.deptPlaceholder"
              placeholder-class="placeholder"
            />
          </view>

          <view class="field">
            <text class="label">{{ txt.mobile }}</text>
            <input
              class="input"
              v-model="form.mobile"
              type="number"
              :placeholder="txt.mobilePlaceholder"
              placeholder-class="placeholder"
            />
          </view>

          <view class="field">
            <text class="label">{{ txt.password }}</text>
            <input
              class="input"
              v-model="form.password"
              password
              :placeholder="txt.passwordPlaceholder"
              placeholder-class="placeholder"
            />
          </view>

          <view class="field">
            <text class="label">{{ txt.confirm }}</text>
            <input
              class="input"
              v-model="form.confirm"
              password
              :placeholder="txt.confirmPlaceholder"
              placeholder-class="placeholder"
            />
          </view>

          <view class="actions">
            <button class="mi-btn primary-btn" :disabled="loading" @click.stop="handleRegister">
              {{ loading ? txt.submitting : txt.submit }}
            </button>
            <button class="mi-btn ghost-btn" :disabled="loading" @click.stop="back">
              {{ txt.back }}
            </button>
          </view>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script>
import { registerUser } from '../../common/api'

const TXT = {
  eyebrow: '\u667a\u5f71\u533b\u751f\u7aef',
  title: '\u6ce8\u518c\u65b0\u8d26\u53f7',
  subtitle: '\u521b\u5efa\u8d26\u53f7\u540e\u53ef\u8fdb\u884c\u5f71\u50cf\u4e0a\u4f20\u3001\u5206\u5272\u4e0e\u4f1a\u8bca',
  tag1: '\u8eab\u4efd\u5ba1\u6838',
  tag2: '\u6570\u636e\u52a0\u5bc6',
  tag3: '\u6d41\u7a0b\u7559\u75d5',
  formTitle: '\u57fa\u672c\u4fe1\u606f',
  formHint: '\u8bf7\u4f7f\u7528\u771f\u5b9e\u4fe1\u606f\uff0c\u4fbf\u4e8e\u540e\u7eed\u4f1a\u8bca\u534f\u4f5c',
  name: '\u59d3\u540d',
  namePlaceholder: '\u8bf7\u8f93\u5165\u771f\u5b9e\u59d3\u540d',
  hospital: '\u533b\u9662',
  hospitalPlaceholder: '\u5982\uff1a\u7701\u80bf\u7624\u533b\u9662',
  dept: '\u79d1\u5ba4',
  deptPlaceholder: '\u5982\uff1a\u653e\u7597\u79d1',
  mobile: '\u624b\u673a\u53f7',
  mobilePlaceholder: '\u8bf7\u8f93\u516511\u4f4d\u624b\u673a\u53f7',
  password: '\u5bc6\u7801',
  passwordPlaceholder: '\u81f3\u5c118\u4f4d\uff0c\u5305\u542b\u5b57\u6bcd\u6216\u6570\u5b57',
  confirm: '\u786e\u8ba4\u5bc6\u7801',
  confirmPlaceholder: '\u8bf7\u518d\u6b21\u8f93\u5165\u5bc6\u7801',
  submit: '\u63d0\u4ea4\u6ce8\u518c',
  submitting: '\u63d0\u4ea4\u4e2d...',
  back: '\u8fd4\u56de\u767b\u5f55',
  msgName: '\u8bf7\u8f93\u5165\u59d3\u540d',
  msgHospital: '\u8bf7\u8f93\u5165\u533b\u9662',
  msgDept: '\u8bf7\u8f93\u5165\u79d1\u5ba4',
  msgMobile: '\u8bf7\u8f93\u5165\u624b\u673a\u53f7',
  msgMobileRule: '\u8bf7\u8f93\u516511\u4f4d\u624b\u673a\u53f7',
  msgPwd: '\u8bf7\u8f93\u5165\u5bc6\u7801',
  msgPwdRule: '\u5bc6\u7801\u81f3\u5c118\u4f4d',
  msgConfirm: '\u8bf7\u786e\u8ba4\u5bc6\u7801',
  msgMismatch: '\u4e24\u6b21\u8f93\u5165\u5bc6\u7801\u4e0d\u4e00\u81f4',
  msgSuccess: '\u6ce8\u518c\u6210\u529f\uff0c\u5df2\u56de\u586b\u767b\u5f55\u4fe1\u606f',
  msgError: '\u6ce8\u518c\u5931\u8d25\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5'
}

export default {
  data() {
    return {
      txt: TXT,
      loading: false,
      viewportHeight: '100vh',
      form: {
        name: '',
        hospital: '',
        dept: '',
        mobile: '',
        password: '',
        confirm: ''
      }
    }
  },
  onLoad() {
    this.syncViewportHeight()
  },
  onShow() {
    this.syncViewportHeight()
  },
  methods: {
    syncViewportHeight() {
      try {
        const info = uni.getSystemInfoSync()
        if (info && Number(info.windowHeight) > 0) {
          this.viewportHeight = `${info.windowHeight}px`
        }
      } catch (err) {
        console.warn('sync viewport height failed', err)
      }
    },
    validateForm() {
      const f = this.form
      if (!String(f.name || '').trim()) return this.txt.msgName
      if (!String(f.hospital || '').trim()) return this.txt.msgHospital
      if (!String(f.dept || '').trim()) return this.txt.msgDept
      if (!String(f.mobile || '').trim()) return this.txt.msgMobile
      if (!/^1\d{10}$/.test(String(f.mobile || ''))) return this.txt.msgMobileRule
      if (!String(f.password || '')) return this.txt.msgPwd
      if (String(f.password || '').length < 8) return this.txt.msgPwdRule
      if (!String(f.confirm || '')) return this.txt.msgConfirm
      if (String(f.confirm || '') !== String(f.password || '')) return this.txt.msgMismatch
      return ''
    },
    async handleRegister() {
      if (this.loading) return
      const err = this.validateForm()
      if (err) {
        uni.showToast({ title: err, icon: 'none' })
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
        uni.showToast({ title: this.txt.msgSuccess, icon: 'success', duration: 1200 })
        setTimeout(() => {
          uni.navigateBack()
          uni.$emit('prefill-login', {
            username: this.form.mobile,
            password: this.form.password
          })
        }, 550)
      } catch (e) {
        const tip = typeof e?.message === 'string' && e.message ? e.message : this.txt.msgError
        uni.showToast({ title: tip, icon: 'none' })
      } finally {
        this.loading = false
      }
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
  background: transparent;
}

.viewport {
  width: 100%;
}

.register-layout {
  min-height: 100%;
  box-sizing: border-box;
  padding-bottom: calc(18rpx + env(safe-area-inset-bottom));
}

.hero-card {
  border-radius: 26rpx;
  padding: 24rpx 24rpx 18rpx;
  border: 1rpx solid rgba(185, 214, 247, 0.9);
  background: linear-gradient(152deg, #2f78d8 0%, #3f8bec 55%, #69aef4 100%);
  box-shadow: 0 16rpx 42rpx rgba(47, 120, 216, 0.24);
}

.hero-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
}

.hero-copy {
  min-width: 0;
  flex: 1;
}

.hero-eyebrow {
  display: block;
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.78);
}

.hero-title {
  display: block;
  margin-top: 4rpx;
  font-size: 44rpx;
  line-height: 1.22;
  font-weight: 700;
  color: #ffffff;
}

.hero-subtitle {
  display: block;
  margin-top: 8rpx;
  font-size: 23rpx;
  line-height: 1.4;
  color: rgba(255, 255, 255, 0.88);
}

.hero-logo {
  width: 82rpx;
  height: 82rpx;
  border-radius: 20rpx;
  border: 2rpx solid rgba(255, 255, 255, 0.48);
  background: rgba(255, 255, 255, 0.2);
}

.hero-tags {
  margin-top: 14rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
}

.hero-tag {
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.42);
  background: rgba(255, 255, 255, 0.18);
  color: #ffffff;
  font-size: 22rpx;
}

.form-card {
  margin-top: 14rpx;
  padding: 24rpx;
  border-radius: 26rpx;
}

.section-head {
  margin-bottom: 10rpx;
}

.section-title {
  margin: 0;
  font-size: 33rpx;
  font-weight: 650;
  color: #173a64;
}

.section-hint {
  display: block;
  margin-top: 6rpx;
  font-size: 24rpx;
  color: #6a84a6;
}

.field {
  margin-top: 10rpx;
}

.label {
  display: block;
  margin-bottom: 6rpx;
  font-size: 25rpx;
  color: #2f4f73;
}

.input {
  width: 100%;
  height: 70rpx;
  box-sizing: border-box;
  border: 1rpx solid #cfe0f6;
  border-radius: 16rpx;
  padding: 0 16rpx;
  background: #f8fbff;
  color: #0c0d0f;
  font-size: 29rpx;
}

.placeholder {
  color: #9eb2cb;
}

.actions {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
  margin-top: 18rpx;
}

.mi-btn {
  width: 100%;
  height: 82rpx;
  line-height: 82rpx;
  border-radius: 999rpx;
  font-size: 30rpx;
  border: 0;
}

.primary-btn {
  color: #ffffff;
  background: linear-gradient(135deg, #2f78d8 0%, #245eac 100%);
  box-shadow: 0 12rpx 30rpx rgba(47, 120, 216, 0.28);
}

.ghost-btn {
  color: #2f4f73;
  background: #ffffff;
  border: 1rpx solid #c8daf4;
}

.mi-btn[disabled] {
  opacity: 0.65;
}

button::after {
  border: 0;
}
</style>
