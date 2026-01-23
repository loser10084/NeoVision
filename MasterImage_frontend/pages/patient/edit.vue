<template>
  <view class="page">
    <view class="safe-area">
      <view class="card form-card">
        <view class="form-head">
          <view>
            <view class="section-title">编辑患者</view>
            <text class="subtle">ID：{{ patientId }}</text>
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
            <wd-input v-model="form.stage" prop="stage" placeholder="如 T3N2M0" clearable />
          </view>
          <view class="field">
            <text class="field-label">诊断</text>
            <wd-input v-model="form.diagnosis" prop="diagnosis" placeholder="如 鼻咽癌" clearable />
          </view>
          <view class="field">
            <text class="field-label">影像号</text>
            <wd-input v-model="form.studyId" prop="studyId" placeholder="ST-XXXX，可留空" clearable />
          </view>
        </wd-form>
        <view class="action-bar column">
          <wd-button block shape="round" type="primary" class="primary-btn" :loading="loading" @click="submit">
            保存修改
          </wd-button>
          <wd-button block shape="round" type="default" plain class="ghost-btn" @click="cancel">返回</wd-button>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { getPatientDetail, updatePatient } from '../../common/api'

export default {
  data() {
    return {
      patientId: '',
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
  async onLoad(query) {
    this.patientId = query.id || ''
    if (!this.patientId) {
      uni.showToast({ title: '缺少患者ID', icon: 'none' })
      return
    }
    await this.fetchDetail()
  },
  methods: {
    async fetchDetail() {
      try {
        const data = await getPatientDetail(this.patientId)
        this.form = {
          name: data.name || '',
          sex: data.sex || '',
          age: data.age || '',
          stage: data.stage || '',
          diagnosis: data.diagnosis || '',
          studyId: data.studyId || ''
        }
      } catch (err) {
        console.error('getPatientDetail error', err)
      }
    },
    submit() {
      this.$refs.formRef
        .validate()
        .then(async () => {
          if (this.loading) return
          this.loading = true
          try {
            await updatePatient(this.patientId, {
              name: this.form.name,
              sex: this.form.sex,
              age: Number(this.form.age),
              stage: this.form.stage,
              diagnosis: this.form.diagnosis,
              studyId: this.form.studyId
            })
            uni.showToast({ title: '已保存', icon: 'success' })
            setTimeout(() => {
              uni.redirectTo({ url: `/pages/patient/detail?id=${this.patientId}` })
            }, 400)
          } catch (err) {
            console.error('updatePatient error', err)
          } finally {
            this.loading = false
          }
        })
        .catch(() => {
          uni.showToast({ title: '请完善必填信息', icon: 'none' })
        })
    },
    cancel() {
      uni.navigateBack()
    }
  }
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: #f7f7f8;
}

.form-card {
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
