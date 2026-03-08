<template>
  <view class="page">
    <view class="header">
      <view class="back" @click="goBack">
        <wd-icon name="arrow-left" />
      </view>
      <image class="header-avatar" src="/static/project_icon.jpg" mode="aspectFill" />
      <view class="header-info">
        <text class="header-name">{{ headerTitle }}</text>
        <text class="header-status">{{ headerStatus }}</text>
      </view>
      <text v-if="isConsultation" class="member-entry" @click="toggleMemberPanel">成员</text>
    </view>

    <view class="context-strip">
      <text class="context-chip">{{ isConsultation ? '联合会诊' : '灵犀智影AI助手' }}</text>
      <text class="context-chip">{{ isConsultation ? `成员 ${members.length}` : '医学影像模式' }}</text>
      <text v-if="isConsultation && consultationId" class="context-chip">#{{ consultationId }}</text>
    </view>

    <view v-if="showMemberPanel && isConsultation" class="member-panel">
      <view class="member-panel-head">
        <text class="member-panel-title">会诊成员</text>
        <text class="member-panel-action" @click="loadConsultationContext">刷新</text>
      </view>

      <view class="member-list">
        <view v-for="member in members" :key="member.doctorId" class="member-item">
          <view>
            <text class="member-name">{{ member.name || `医生${member.doctorId}` }}</text>
            <text class="member-meta">{{ member.hospital || '-' }} / {{ member.dept || '-' }} / {{ member.role || 'MEMBER' }}</text>
          </view>
          <text v-if="canOperateMember(member)" class="member-remove" @click="removeMemberFromConsultation(member)">移除</text>
        </view>
      </view>

      <view class="member-panel-head member-panel-head--sub">
        <text class="member-panel-title">从好友中添加</text>
      </view>
      <view class="friend-list">
        <view v-for="friend in addableFriends" :key="friend.id" class="friend-item">
          <view>
            <text class="friend-name">{{ friend.name || `医生${friend.id}` }}</text>
            <text class="friend-meta">{{ friend.hospital || '-' }} / {{ friend.dept || '-' }}</text>
          </view>
          <text class="friend-add" @click="addMemberToConsultation(friend)">添加</text>
        </view>
      </view>
    </view>

    <scroll-view class="message-list" scroll-y :scroll-with-animation="true" :scroll-into-view="scrollTarget">
      <view
        v-for="message in messages"
        :key="message.id"
        :id="String(message.id)"
        class="message"
        :class="message.self ? 'user' : 'other'"
      >
        <image class="avatar" :class="message.self ? 'user' : 'other'" :src="message.self ? userAvatar : agentAvatar" mode="aspectFill" />

        <view class="bubble-wrap">
          <view class="bubble" :class="message.self ? 'user' : 'other'">
            <view v-if="message.type === 'typing'" class="typing">
              <view class="typing-dot"></view>
              <view class="typing-dot"></view>
              <view class="typing-dot"></view>
            </view>

            <template v-else>
              <text v-if="message.senderName && !message.self && isConsultation" class="sender-name">{{ message.senderName }}</text>

              <image
                v-if="message.type === 'IMAGE' && message.ossPath"
                class="message-image"
                :src="message.ossPath"
                mode="aspectFill"
                @click="openOssPath(message.ossPath)"
              />

              <view v-if="message.type !== 'TEXT' && message.type !== 'IMAGE'" class="file-box" @click="openOssPath(message.ossPath)">
                <wd-icon name="folder" size="20" color="#2f78d8" />
                <view class="file-meta">
                  <text class="file-name">{{ message.fileName || message.type || '附件' }}</text>
                  <text class="file-sub">点击查看</text>
                </view>
              </view>

              <text v-if="message.content" class="msg-text" space="preserve">{{ message.content }}</text>
            </template>
          </view>

          <text v-if="message.createdAt" class="msg-time">{{ shortTime(message.createdAt) }}</text>
        </view>
      </view>
    </scroll-view>

    <view v-if="pendingAttachment" class="input-preview">
      <view class="preview-main">
        <wd-icon name="folder" size="18" color="#2f78d8" />
        <view class="preview-meta">
          <text class="preview-label">待发送附件</text>
          <text class="preview-name">{{ pendingAttachment.name || pendingAttachment.path }}</text>
        </view>
      </view>
      <wd-icon name="close" class="preview-remove" @click="clearAttachment" />
    </view>

    <view class="input-bar">
      <view class="image-picker" @click="chooseAttachment">
        <wd-icon name="add" />
      </view>
      <wd-input
        v-model="input"
        placeholder="输入消息"
        confirm-type="send"
        :disabled="loading"
        @confirm="handleConfirm"
      />
      <wd-button
        size="small"
        type="primary"
        class="send-btn"
        :loading="loading"
        :disabled="loading || (!input.trim() && !pendingAttachment)"
        @click="send"
      >
        发送
      </wd-button>
    </view>
  </view>
</template>

<script>
import {
  sendAgentMessage,
  getAgentHistory,
  sendAgentMessageWithImage,
  listConsultationMessages,
  sendConsultationMessage,
  uploadConsultationAttachment,
  listConsultationMembers,
  listFriends,
  addConsultationMember,
  removeConsultationMember
} from '../../common/api'
import { resolveModelUrl, getToken } from '../../common/request'

export default {
  data() {
    return {
      input: '',
      loading: false,
      scrollTarget: '',
      userAvatar: '/static/logo.png',
      agentAvatar: '/static/project_icon.jpg',
      pendingAttachment: null,
      messages: [],
      mode: 'ai',
      consultationId: null,
      consultationTitle: '',
      currentUserId: null,
      members: [],
      friends: [],
      showMemberPanel: false
    }
  },
  computed: {
    isConsultation() {
      return this.mode === 'consultation'
    },
    headerTitle() {
      return this.isConsultation ? (this.consultationTitle || '联合会诊') : '灵犀智影AI助手'
    },
    headerStatus() {
      if (this.isConsultation) {
        return `${this.members.length || 0} 位医生协作中`
      }
      return '在线'
    },
    addableFriends() {
      const current = new Set((this.members || []).map((m) => Number(m.doctorId)))
      return (this.friends || []).filter((friend) => !current.has(Number(friend.id)))
    }
  },
  async onLoad(options) {
    this.loadUserProfile()
    const consultationId = options?.consultationId ? Number(options.consultationId) : null
    if (consultationId && !Number.isNaN(consultationId)) {
      this.mode = 'consultation'
      this.consultationId = consultationId
      this.consultationTitle = options?.title ? decodeURIComponent(options.title) : ''
      await this.loadConsultationContext()
      return
    }

    this.mode = 'ai'
    this.appendLocalMessage({
      id: `welcome-${Date.now()}`,
      self: false,
      type: 'TEXT',
      content: '你好，我是灵犀智影AI助手，请输入你的问题。',
      createdAt: ''
    })
    await this.loadAiHistory()
  },
  methods: {
    loadUserProfile() {
      const profile = uni.getStorageSync('userProfile') || {}
      const id = profile?.id || profile?.userId || profile?.doctorId
      if (id !== undefined && id !== null && id !== '') {
        const parsed = Number(id)
        this.currentUserId = Number.isNaN(parsed) ? null : parsed
      }
      const name = profile?.name ? String(profile.name).trim() : ''
      if (name) {
        this.userAvatar = this.buildInitialsAvatar(name)
      }
    },
    buildInitialsAvatar(name) {
      const initial = name.slice(0, 1)
      const size = 120
      if (typeof document === 'undefined') return this.userAvatar
      const canvas = document.createElement('canvas')
      canvas.width = size
      canvas.height = size
      const ctx = canvas.getContext('2d')
      if (!ctx) return this.userAvatar
      ctx.fillStyle = '#0f1012'
      ctx.fillRect(0, 0, size, size)
      ctx.fillStyle = '#ffffff'
      ctx.font = 'bold 64px sans-serif'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(initial, size / 2, size / 2 + 2)
      return canvas.toDataURL('image/png')
    },
    async loadAiHistory() {
      try {
        const payload = await getAgentHistory()
        const items = Array.isArray(payload) ? payload : payload?.messages
        const normalized = this.normalizeAiHistory(items)
        if (normalized.length) {
          this.messages = normalized
          this.scrollToBottom()
        }
      } catch (err) {
        console.error('agent history error', err)
      }
    },
    normalizeAiHistory(items) {
      if (!Array.isArray(items)) return []
      const stamp = Date.now()
      return items
        .map((item, index) => {
          if (!item) return null
          const rawRole = String(item.role || '').toLowerCase()
          const self = rawRole === 'user'
          const content = String(item.content || '').trim()
          if (!content) return null
          return {
            id: `history-${stamp}-${index}`,
            self,
            type: 'TEXT',
            content,
            createdAt: ''
          }
        })
        .filter(Boolean)
    },
    async loadConsultationContext() {
      if (!this.consultationId) return
      try {
        const [messages, members, friends] = await Promise.all([
          listConsultationMessages(this.consultationId, { limit: 100 }),
          listConsultationMembers(this.consultationId),
          listFriends()
        ])
        const list = Array.isArray(messages) ? messages.slice().reverse() : []
        this.messages = list.map((item) => this.mapConsultationMessage(item))
        this.members = Array.isArray(members) ? members : []
        this.friends = Array.isArray(friends) ? friends : []
        this.scrollToBottom()
      } catch (err) {
        console.error('load consultation context failed', err)
      }
    },
    mapConsultationMessage(item) {
      const messageType = String(item?.messageType || 'TEXT').toUpperCase()
      const senderId = Number(item?.senderId)
      return {
        id: item?.id || `msg-${Date.now()}-${Math.random().toString(16).slice(2)}`,
        self: this.currentUserId !== null && senderId === this.currentUserId,
        senderName: item?.senderName || '',
        type: messageType,
        content: String(item?.textContent || ''),
        ossPath: item?.ossPath || '',
        fileName: item?.fileName || '',
        createdAt: item?.createdAt || ''
      }
    },
    goBack() {
      const pages = getCurrentPages()
      if (pages.length > 1) {
        uni.navigateBack()
        return
      }
      uni.switchTab({ url: '/pages/agent/chat' })
    },
    toggleMemberPanel() {
      this.showMemberPanel = !this.showMemberPanel
    },
    canOperateMember(member) {
      if (!member) return false
      if (String(member.role || '').toUpperCase() === 'OWNER') return false
      return true
    },
    async addMemberToConsultation(friend) {
      if (!this.consultationId || !friend?.id) return
      try {
        await addConsultationMember(this.consultationId, friend.id)
        uni.showToast({ title: '成员已添加', icon: 'success' })
        await this.loadConsultationContext()
      } catch (err) {
        console.error('add member failed', err)
      }
    },
    async removeMemberFromConsultation(member) {
      if (!this.consultationId || !member?.doctorId) return
      uni.showModal({
        title: '提示',
        content: `确认移除 ${member.name || '该成员'} 吗？`,
        success: async (res) => {
          if (!res.confirm) return
          try {
            await removeConsultationMember(this.consultationId, member.doctorId)
            uni.showToast({ title: '成员已移除', icon: 'success' })
            await this.loadConsultationContext()
          } catch (err) {
            console.error('remove member failed', err)
          }
        }
      })
    },
    chooseAttachment() {
      if (this.loading) return
      const itemList = this.isConsultation ? ['选择图片', '选择文件'] : ['选择图片']
      uni.showActionSheet({
        itemList,
        success: (res) => {
          if (res.tapIndex === 0) {
            this.pickImage()
            return
          }
          if (this.isConsultation && res.tapIndex === 1) {
            this.pickFile()
          }
        }
      })
    },
    pickImage() {
      uni.chooseImage({
        count: 1,
        sizeType: ['compressed'],
        success: (res) => {
          const path = res.tempFilePaths && res.tempFilePaths[0]
          if (!path) return
          const file = res.tempFiles && res.tempFiles[0]
          this.pendingAttachment = {
            path,
            name: file?.name || this.extractFileName(path),
            type: 'IMAGE'
          }
        }
      })
    },
    pickFile() {
      if (typeof uni.chooseMessageFile !== 'function') {
        uni.showToast({ title: '当前端不支持文件选择', icon: 'none' })
        return
      }
      uni.chooseMessageFile({
        count: 1,
        type: 'file',
        success: (res) => {
          const file = res.tempFiles && res.tempFiles[0]
          if (!file?.path) return
          this.pendingAttachment = {
            path: file.path,
            name: file.name || this.extractFileName(file.path),
            type: this.detectAttachmentType(file.name || file.path)
          }
        }
      })
    },
    clearAttachment() {
      this.pendingAttachment = null
    },
    handleConfirm() {
      this.send()
    },
    async send() {
      const text = String(this.input || '').trim()
      if (this.loading) return
      if (!text && !this.pendingAttachment) return

      if (this.isConsultation) {
        await this.sendConsultation(text)
        return
      }
      await this.sendAi(text)
    },
    async sendAi(text) {
      if (this.pendingAttachment) {
        const file = this.pendingAttachment
        this.appendLocalMessage({
          id: `local-${Date.now()}`,
          self: true,
          type: file.type || 'IMAGE',
          content: text || '',
          ossPath: file.path,
          fileName: file.name || '',
          createdAt: ''
        })
        this.input = ''
        this.pendingAttachment = null

        const typingId = this.appendTyping()
        this.loading = true
        try {
          const data = await sendAgentMessageWithImage(text, file.path)
          const reply = this.normalizeAgentReply(data)
          this.replaceTyping(typingId, reply)
        } catch (err) {
          console.error('agent image chat error', err)
          this.replaceTyping(typingId, '抱歉，智能体暂时无法响应，请稍后重试。')
        } finally {
          this.loading = false
        }
        return
      }

      this.appendLocalMessage({
        id: `local-${Date.now()}`,
        self: true,
        type: 'TEXT',
        content: text,
        createdAt: ''
      })
      this.input = ''
      const typingId = this.appendTyping()
      this.loading = true

      try {
        if (this.canStream()) {
          await this.streamFromModel(text, typingId)
        } else {
          const data = await sendAgentMessage(text)
          const reply = this.normalizeAgentReply(data)
          this.replaceTyping(typingId, reply)
        }
      } catch (err) {
        console.error('agent chat error', err)
        this.replaceTyping(typingId, '抱歉，智能体暂时无法响应，请稍后重试。')
      } finally {
        this.loading = false
      }
    },
    async sendConsultation(text) {
      const attachment = this.pendingAttachment
      this.loading = true
      try {
        if (attachment) {
          const uploaded = await uploadConsultationAttachment(this.consultationId, attachment.path, {
            messageType: attachment.type || 'FILE'
          })
          const uploadedMessage = this.mapConsultationMessage(uploaded)
          uploadedMessage.self = true
          this.appendLocalMessage(uploadedMessage)
          this.pendingAttachment = null
        }

        if (text) {
          const sent = await sendConsultationMessage(this.consultationId, {
            messageType: 'TEXT',
            textContent: text
          })
          const sentMessage = this.mapConsultationMessage(sent)
          sentMessage.self = true
          this.appendLocalMessage(sentMessage)
        }

        this.input = ''
      } catch (err) {
        console.error('send consultation message failed', err)
      } finally {
        this.loading = false
      }
    },
    canStream() {
      return typeof fetch === 'function' && typeof ReadableStream !== 'undefined'
    },
    async streamFromModel(text, typingId) {
      const token = getToken()
      const response = await fetch(resolveModelUrl('/api/agent/chat/stream'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ prompt: text })
      })
      if (!response.ok || !response.body) {
        throw new Error(`HTTP ${response.status}`)
      }
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let content = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        let lineEnd = buffer.indexOf('\n')
        while (lineEnd !== -1) {
          const line = buffer.slice(0, lineEnd)
          buffer = buffer.slice(lineEnd + 1)
          if (line.startsWith('data:')) {
            let chunk = line.slice(5)
            if (chunk.startsWith(' ')) chunk = chunk.slice(1)
            if (chunk.endsWith('\r')) chunk = chunk.slice(0, -1)
            if (chunk === '[DONE]') {
              this.replaceTyping(typingId, content)
              return
            }
            if (!chunk.startsWith('[ERROR]')) {
              content += chunk
              this.replaceTyping(typingId, content, true)
            }
          }
          lineEnd = buffer.indexOf('\n')
        }
      }
      this.replaceTyping(typingId, content)
    },
    normalizeAgentReply(payload) {
      if (typeof payload === 'string') return payload
      if (payload && typeof payload.content === 'string') return payload.content
      if (payload && typeof payload.reply === 'string') return payload.reply
      if (payload && typeof payload.message === 'string') return payload.message
      if (payload && payload.content && typeof payload.content === 'object') return JSON.stringify(payload.content, null, 2)
      if (payload && payload.reply && typeof payload.reply === 'object') return JSON.stringify(payload.reply, null, 2)
      return '已收到请求，但未返回有效内容。'
    },
    appendTyping() {
      const id = `typing-${Date.now()}-${Math.random().toString(16).slice(2)}`
      this.messages.push({
        id,
        self: false,
        type: 'typing',
        content: '',
        createdAt: ''
      })
      this.scrollToBottom(id)
      return id
    },
    replaceTyping(id, content) {
      const target = this.messages.find((message) => message.id === id)
      if (!target) return
      target.type = 'TEXT'
      target.content = content || ' '
      this.scrollToBottom(id)
    },
    appendLocalMessage(message) {
      if (!message) return
      this.messages.push(message)
      this.scrollToBottom(message.id)
    },
    scrollToBottom(id) {
      this.$nextTick(() => {
        const target = id || (this.messages.length ? this.messages[this.messages.length - 1].id : '')
        if (target !== undefined && target !== null) {
          this.scrollTarget = String(target)
        }
      })
    },
    extractFileName(path) {
      if (!path) return ''
      const normalized = String(path).replace(/\\/g, '/')
      const arr = normalized.split('/')
      return arr[arr.length - 1] || ''
    },
    detectAttachmentType(nameOrPath) {
      const text = String(nameOrPath || '').toLowerCase()
      const imageExt = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']
      const modelExt = ['.stl', '.obj', '.nrrd', '.mha', '.nii', '.nii.gz']
      if (imageExt.some((ext) => text.endsWith(ext))) return 'IMAGE'
      if (modelExt.some((ext) => text.endsWith(ext))) return 'MODEL'
      return 'FILE'
    },
    openOssPath(url) {
      if (!url) return
      if (typeof plus !== 'undefined' && plus.runtime?.openURL) {
        plus.runtime.openURL(url)
        return
      }
      if (typeof window !== 'undefined' && window.open) {
        window.open(url, '_blank')
        return
      }
      uni.setClipboardData({
        data: url,
        success: () => {
          uni.showToast({ title: '链接已复制', icon: 'none' })
        }
      })
    },
    shortTime(value) {
      if (!value) return ''
      const text = String(value)
      if (text.includes(' ')) {
        const [date, time] = text.split(' ')
        return `${date.slice(5)} ${time.slice(0, 5)}`
      }
      return text
    }
  }
}
</script>

<style scoped>
.page {
  height: 100vh;
  background: #edf4ff;
  display: flex;
  flex-direction: column;
}

.header {
  display: flex;
  align-items: center;
  gap: 14rpx;
  padding: calc(12rpx + env(safe-area-inset-top)) 22rpx 12rpx;
  background: linear-gradient(155deg, #2f78d8 0%, #3888ee 44%, #62a6f4 100%);
  box-shadow: 0 10rpx 28rpx rgba(42, 106, 188, 0.24);
}

.back {
  width: 60rpx;
  height: 60rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 30rpx;
  background: rgba(255, 255, 255, 0.2);
  color: #ffffff;
}

.header-avatar {
  width: 60rpx;
  height: 60rpx;
  border-radius: 18rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.4);
}

.header-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
  min-width: 0;
}

.header-name {
  font-size: 28rpx;
  font-weight: 700;
  color: #ffffff;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.header-status {
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.84);
}

.member-entry {
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  font-size: 22rpx;
  color: #ffffff;
  border: 1rpx solid rgba(255, 255, 255, 0.4);
}

.context-strip {
  padding: 12rpx 20rpx 10rpx;
  display: flex;
  gap: 10rpx;
  background: #edf4ff;
}

.context-chip {
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  border: 1rpx solid #c6dbf5;
  background: #f5f9ff;
  color: #2f5f97;
  font-size: 22rpx;
}

.member-panel {
  margin: 0 20rpx 10rpx;
  padding: 14rpx;
  border-radius: 18rpx;
  border: 1rpx solid #d6e5f7;
  background: #ffffff;
  box-shadow: 0 10rpx 24rpx rgba(47, 105, 182, 0.1);
}

.member-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.member-panel-head--sub {
  margin-top: 10rpx;
}

.member-panel-title {
  font-size: 24rpx;
  font-weight: 700;
  color: #173a64;
}

.member-panel-action {
  font-size: 22rpx;
  color: #2f78d8;
}

.member-list,
.friend-list {
  margin-top: 8rpx;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.member-item,
.friend-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8rpx;
  border: 1rpx solid #e1ecfa;
  border-radius: 14rpx;
  background: #f8fbff;
  padding: 10rpx 12rpx;
}

.member-name,
.friend-name {
  display: block;
  font-size: 24rpx;
  font-weight: 650;
  color: #173a64;
}

.member-meta,
.friend-meta {
  display: block;
  margin-top: 4rpx;
  font-size: 20rpx;
  color: #7893b3;
}

.member-remove {
  color: #c14c4c;
  font-size: 22rpx;
}

.friend-add {
  color: #2f78d8;
  font-size: 22rpx;
}

.message-list {
  flex: 1;
  min-height: 0;
  padding: 12rpx 20rpx 8rpx;
}

.message {
  display: flex;
  align-items: flex-start;
  gap: 16rpx;
  max-width: 94%;
}

.message + .message {
  margin-top: 22rpx;
}

.message.user {
  margin-left: auto;
  flex-direction: row-reverse;
}

.avatar {
  width: 64rpx;
  height: 64rpx;
  border-radius: 18rpx;
  background: #d6e5f7;
  flex-shrink: 0;
  border: 1rpx solid #cde0f7;
}

.bubble-wrap {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6rpx;
  max-width: 74%;
}

.message.user .bubble-wrap {
  align-items: flex-end;
}

.bubble {
  padding: 16rpx 18rpx;
  border-radius: 20rpx;
  background: #ffffff;
  border: 1rpx solid #d6e5f7;
  box-shadow: 0 10rpx 24rpx rgba(47, 105, 182, 0.1);
  line-height: 1.5;
  font-size: 26rpx;
  color: #203854;
  word-break: break-word;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.bubble.user {
  background: linear-gradient(140deg, #2f78d8 0%, #4a95ec 100%);
  border-color: transparent;
  color: #ffffff;
  box-shadow: 0 12rpx 24rpx rgba(47, 120, 216, 0.3);
}

.sender-name {
  font-size: 22rpx;
  color: #6b85a5;
}

.msg-text {
  font-size: 26rpx;
  line-height: 1.5;
  white-space: pre-wrap;
  color: inherit;
}

.message-image {
  width: 320rpx;
  height: 200rpx;
  border-radius: 16rpx;
  background: #edf4ff;
}

.file-box {
  display: flex;
  align-items: center;
  gap: 10rpx;
  border: 1rpx solid #d6e5f7;
  background: #f4f8ff;
  border-radius: 12rpx;
  padding: 10rpx;
}

.file-meta {
  min-width: 0;
  flex: 1;
}

.file-name {
  display: block;
  font-size: 24rpx;
  color: #173a64;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-sub {
  display: block;
  margin-top: 2rpx;
  font-size: 20rpx;
  color: #7492b3;
}

.msg-time {
  font-size: 20rpx;
  color: #88a0be;
}

.typing {
  display: flex;
  align-items: center;
  gap: 8rpx;
  min-height: 24rpx;
}

.typing-dot {
  width: 10rpx;
  height: 10rpx;
  border-radius: 999rpx;
  background: #8aa0bd;
  animation: typingPulse 1.2s infinite ease-in-out;
}

.typing-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typingPulse {
  0%,
  80%,
  100% {
    opacity: 0.25;
    transform: translateY(0);
  }
  40% {
    opacity: 1;
    transform: translateY(-4rpx);
  }
}

.input-preview {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
  padding: 10rpx 20rpx;
  background: #ffffff;
  border-top: 1rpx solid #d6e5f7;
}

.preview-main {
  display: flex;
  align-items: center;
  gap: 10rpx;
  min-width: 0;
  flex: 1;
}

.preview-meta {
  min-width: 0;
  flex: 1;
}

.preview-label {
  display: block;
  font-size: 22rpx;
  color: #627d9f;
}

.preview-name {
  display: block;
  font-size: 24rpx;
  color: #0c0d0f;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.preview-remove {
  color: #627d9f;
}

.input-bar {
  display: flex;
  align-items: center;
  gap: 12rpx;
  padding: 12rpx 20rpx calc(12rpx + env(safe-area-inset-bottom));
  background: #ffffff;
  border-top: 1rpx solid #d6e5f7;
  box-shadow: 0 -8rpx 26rpx rgba(47, 105, 182, 0.08);
}

.image-picker {
  width: 64rpx;
  height: 64rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14rpx;
  border: 1rpx solid #d6e5f7;
  background: #f4f8ff;
  color: #2f78d8;
}

.send-btn {
  min-width: 106rpx;
}

:deep(.wd-input) {
  flex: 1;
  min-height: 72rpx;
  background: #f4f8ff;
  border-radius: 14rpx;
  border: 1rpx solid #d6e5f7;
}
</style>
