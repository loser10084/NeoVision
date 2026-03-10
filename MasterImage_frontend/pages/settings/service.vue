<template>
  <view class="page">
    <view class="safe-area">
      <view class="card section-card">
        <view class="section-head">
          <text class="section-title">运行时服务地址</text>
          <text class="section-sub">安卓上线后可直接修改，无需重新打包</text>
        </view>

        <view class="field-block">
          <text class="field-label">业务网关地址</text>
          <input
            v-model="gatewayUrl"
            class="field-input"
            placeholder="例如：http://192.168.1.20:8080"
            confirm-type="done"
          />
        </view>

        <view class="field-block">
          <text class="field-label">模型服务地址</text>
          <input
            v-model="modelUrl"
            class="field-input"
            placeholder="例如：http://192.168.1.20:5001"
            confirm-type="done"
          />
        </view>

        <view class="runtime-preview">
          <text class="preview-label">当前生效网关：</text>
          <text class="preview-value">{{ effective.gatewayUrl || '-' }}</text>
        </view>
        <view class="runtime-preview">
          <text class="preview-label">当前生效模型：</text>
          <text class="preview-value">{{ effective.modelUrl || '-' }}</text>
        </view>

        <view class="actions">
          <button class="mi-btn mi-btn--primary full-row" @click="saveConfig">保存</button>
          <button class="mi-btn mi-btn--ghost" @click="useLocalhost">一键本机测试</button>
          <button class="mi-btn mi-btn--ghost" @click="useDefault">恢复默认</button>
          <button class="mi-btn mi-btn--ghost full-row" @click="clearConfig">清空本地配置</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import {
  getEffectiveServiceUrls,
  getRuntimeServiceUrls,
  setRuntimeServiceUrls,
  clearRuntimeServiceUrls
} from '../../common/request'

const DEFAULT_GATEWAY_URL = 'http://192.168.1.100:8080'
const DEFAULT_MODEL_URL = 'http://192.168.1.100:5001'
const LOCAL_GATEWAY_URL = 'http://127.0.0.1:8080'
const LOCAL_MODEL_URL = 'http://127.0.0.1:5001'

export default {
  data() {
    return {
      gatewayUrl: '',
      modelUrl: '',
      effective: {
        gatewayUrl: '',
        modelUrl: ''
      }
    }
  },
  onShow() {
    this.loadConfig()
  },
  methods: {
    normalizeUrl(value) {
      return String(value || '').trim().replace(/\/+$/, '')
    },
    isValidUrl(value) {
      return /^https?:\/\//i.test(value)
    },
    loadConfig() {
      const runtime = getRuntimeServiceUrls()
      this.gatewayUrl = runtime.gatewayUrl || ''
      this.modelUrl = runtime.modelUrl || ''
      this.refreshEffective()
    },
    refreshEffective() {
      this.effective = getEffectiveServiceUrls()
    },
    saveConfig() {
      const gatewayUrl = this.normalizeUrl(this.gatewayUrl)
      const modelUrl = this.normalizeUrl(this.modelUrl)

      if (gatewayUrl && !this.isValidUrl(gatewayUrl)) {
        uni.showToast({ title: '网关地址格式错误', icon: 'none' })
        return
      }
      if (modelUrl && !this.isValidUrl(modelUrl)) {
        uni.showToast({ title: '模型地址格式错误', icon: 'none' })
        return
      }

      this.applyConfig(gatewayUrl, modelUrl, '已保存')
    },
    applyConfig(gatewayUrl, modelUrl, title = '已保存') {
      setRuntimeServiceUrls({ gatewayUrl, modelUrl })
      this.gatewayUrl = gatewayUrl
      this.modelUrl = modelUrl
      this.refreshEffective()
      uni.showToast({ title, icon: 'success' })
    },
    useLocalhost() {
      this.applyConfig(LOCAL_GATEWAY_URL, LOCAL_MODEL_URL, '已切换到本机测试')
    },
    useDefault() {
      this.applyConfig(DEFAULT_GATEWAY_URL, DEFAULT_MODEL_URL, '已恢复默认')
    },
    clearConfig() {
      clearRuntimeServiceUrls()
      this.gatewayUrl = ''
      this.modelUrl = ''
      this.refreshEffective()
      uni.showToast({ title: '已清空', icon: 'success' })
    }
  }
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: #edf4ff;
}

.section-card {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.section-head {
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.section-title {
  font-size: 32rpx;
  font-weight: 700;
  color: #173a64;
}

.section-sub {
  font-size: 24rpx;
  color: #6883a5;
}

.field-block {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.field-label {
  font-size: 26rpx;
  color: #1f456f;
  font-weight: 600;
}

.field-input {
  height: 72rpx;
  border-radius: 16rpx;
  border: 1rpx solid #d2e3f8;
  background: #f8fbff;
  padding: 0 18rpx;
  color: #173a64;
  font-size: 26rpx;
}

.runtime-preview {
  border: 1rpx dashed #c7daf2;
  border-radius: 14rpx;
  background: #f6faff;
  padding: 12rpx 14rpx;
}

.preview-label {
  display: block;
  color: #5c789c;
  font-size: 22rpx;
}

.preview-value {
  display: block;
  margin-top: 4rpx;
  color: #234567;
  font-size: 24rpx;
  word-break: break-all;
}

.actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10rpx;
  margin-top: 6rpx;
}

.full-row {
  grid-column: 1 / span 2;
}

.mi-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin: 0;
  height: 68rpx;
  line-height: 68rpx;
  border-radius: 999rpx;
  font-size: 25rpx;
  border: 1rpx solid #c8daf4;
  background: #ffffff;
  color: #2f4f73;
}

.mi-btn--primary {
  background: linear-gradient(135deg, #2f78d8 0%, #245eac 100%);
  border-color: transparent;
  color: #ffffff;
}

.mi-btn--ghost {
  background: #ffffff;
  color: #305377;
}

button::after {
  border: none;
}
</style>
