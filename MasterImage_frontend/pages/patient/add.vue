<template>
  <view class="page">
    <view class="safe-area">
      <view class="card form-card">
        <view class="form-head">
          <view>
            <view class="section-title">新增患者</view>
          </view>
        </view>
        <wd-form ref="formRef" :model="form" :rules="rules">
          <view class="field">
            <text class="field-label">姓名</text>
            <wd-input v-model="form.name" prop="name" placeholder="请输入姓名" clearable />
          </view>
          <view class="field">
            <text class="field-label">性别</text>
            <wd-input v-model="form.sex" prop="sex" placeholder="男 / 女" clearable />
          </view>
          <view class="field">
            <text class="field-label">年龄</text>
            <wd-input v-model="form.age" prop="age" type="number" placeholder="岁数" clearable />
          </view>
          <view class="field">
            <text class="field-label">分期</text>
            <wd-input v-model="form.stage" prop="stage" placeholder="如：T3N2M0" clearable />
          </view>
          <view class="field">
            <text class="field-label">诊断</text>
            <wd-input v-model="form.diagnosis" prop="diagnosis" placeholder="如：鼻咽癌" clearable />
          </view>
          <view class="field">
            <text class="field-label">影像号</text>
            <wd-input v-model="form.studyId" prop="studyId" placeholder="ST-XXXX，可留空" clearable />
          </view>
        </wd-form>
        <view class="action-bar column">
          <wd-button block shape="round" type="primary" class="primary-btn" :loading="loading" @click="submit">
            提交创建
          </wd-button>
          <wd-button block shape="round" type="default" plain class="ghost-btn" @click="toList">返回列表</wd-button>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { createPatient } from '../../common/api'

export default {
  data() {
    return {
      loading: false,
      form: {
        name: '',
        sex: '',
        age: '',
        stage: '',
        diagnosis: '',
        studyId: ''
      },
      rules: {
        name: [{ required: true, message: '请输入姓名' }],
        sex: [{ required: true, message: '请输入性别' }],
        age: [{ required: true, message: '请输入年龄' }],
        diagnosis: [{ required: true, message: '请输入诊断' }]
      }
    }
  },
  methods: {
    submit() {
      this.$refs.formRef
        .validate()
        .then(async () => {
          if (this.loading) return
          this.loading = true
          try {
            const data = await createPatient({
              name: this.form.name,
              sex: this.form.sex,
              age: Number(this.form.age),
              stage: this.form.stage,
              diagnosis: this.form.diagnosis,
              studyId: this.form.studyId
            })
            uni.showToast({ title: '已提交', icon: 'success' })
            if (data && data.id) {
              setTimeout(() => {
                uni.navigateTo({ url: `/pages/patient/detail?id=${data.id}` })
              }, 500)
            } else {
              setTimeout(() => uni.switchTab({ url: '/pages/patient/list' }), 500)
            }
          } catch (err) {
            console.error('createPatient error', err)
          } finally {
            this.loading = false
          }
        })
        .catch(() => {
          uni.showToast({ title: '请完善必填信息', icon: 'none' })
        })
    },
    toList() {
      uni.switchTab({ url: '/pages/patient/list' })
    }
  }
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: #edf4ff;
}

.form-card {
  background: rgba(255, 255, 255, 0.96);
  border: 1rpx solid #d6e5f7;
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
  border: 1rpx solid #cfddf2;
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
  border: 1rpx solid #d0def2;
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
