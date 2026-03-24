<template>
  <view class="page">
    <view class="header">
      <view class="back" @click="goBack">
        <wd-icon name="arrow-left" />
      </view>
      <image class="header-avatar" src="/static/project_icon_v2.jpg" mode="aspectFill" />
      <view class="header-info">
        <text class="header-name">{{ headerTitle }}</text>
        <text class="header-status">{{ headerStatus }}</text>
      </view>
      <text v-if="isConsultation" class="member-entry" @click="toggleMemberPanel">成员</text>
    </view>

    <view class="context-strip">
      <text class="context-chip">{{ isConsultation ? '联合会诊' : 'AI问答' }}</text>
      <text class="context-chip">{{ isConsultation ? `成员 ${members.length}` : agentModeLabel }}</text>
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

    <scroll-view
      class="message-list"
      scroll-y
      :scroll-with-animation="true"
      :scroll-into-view="scrollTarget"
      :style="messageListInlineStyle"
      @scroll="handleMessageScroll"
      @scrolltolower="handleScrollToLower"
    >
      <view
        v-for="message in messages"
        :key="message.id"
        :id="toAnchorId(message.id)"
        class="message"
        :class="message.self ? 'user' : 'other'"
      >
        <view v-if="message.self" class="avatar avatar--mine">{{ userInitial }}</view>
        <image v-else class="avatar" :src="agentAvatar" mode="aspectFill" />

        <view class="bubble-wrap">
          <text v-if="showSenderName(message)" class="sender-name">{{ message.senderName }}</text>

          <view class="bubble" :class="message.self ? 'user' : 'other'">
            <view v-if="message.type === 'typing'" class="typing">
              <view class="typing-dot"></view>
              <view class="typing-dot"></view>
              <view class="typing-dot"></view>
            </view>

            <template v-else>
              <image
                v-if="message.type === 'IMAGE' && message.ossPath"
                class="message-image"
                :src="message.ossPath"
                mode="aspectFill"
                @click="openOssPath(message.ossPath)"
              />

              <view v-if="message.type !== 'TEXT' && message.type !== 'IMAGE'" class="file-box" @click="downloadAttachment(message)">
                <wd-icon name="folder" size="20" color="#2f78d8" />
                <view class="file-meta">
                  <text class="file-name">{{ message.fileName || message.type || '附件' }}</text>
                  <text class="file-sub">点击查看</text>
                </view>
              </view>

              <view v-if="message.content" class="md-content">
                <view
                  v-for="(block, blockIndex) in getMarkdownBlocks(message.content)"
                  :key="`${message.id}-block-${blockIndex}`"
                  class="md-block"
                  :class="`md-block--${block.type}`"
                >
                  <text v-if="block.type === 'heading'" class="md-heading" :class="`md-heading--${block.level}`" selectable space="preserve">
                    <text
                      v-for="(segment, segmentIndex) in getInlineSegments(block.text)"
                      :key="`${message.id}-h-${blockIndex}-${segmentIndex}`"
                      class="md-inline"
                      :class="inlineClass(segment)"
                      selectable
                      @click.stop="handleInlineClick(segment)"
                    >
                      {{ segment.text }}
                    </text>
                  </text>

                  <view v-else-if="block.type === 'list'" class="md-list">
                    <view v-for="(item, itemIndex) in block.items" :key="`${message.id}-l-${blockIndex}-${itemIndex}`" class="md-list-item">
                      <text class="md-list-marker" selectable>{{ block.ordered ? `${itemIndex + 1}.` : '•' }}</text>
                      <text class="md-list-text" selectable space="preserve">
                        <text
                          v-for="(segment, segmentIndex) in getInlineSegments(item)"
                          :key="`${message.id}-li-${blockIndex}-${itemIndex}-${segmentIndex}`"
                          class="md-inline"
                          :class="inlineClass(segment)"
                          selectable
                          @click.stop="handleInlineClick(segment)"
                        >
                          {{ segment.text }}
                        </text>
                      </text>
                    </view>
                  </view>

                  <view v-else-if="block.type === 'code'" class="md-code">
                    <text v-if="block.lang" class="md-code-lang" selectable>{{ block.lang }}</text>
                    <text class="md-code-text" selectable space="preserve">{{ block.text }}</text>
                  </view>

                  <view v-else-if="block.type === 'quote'" class="md-quote">
                    <text class="md-quote-text" selectable space="preserve">
                      <text
                        v-for="(segment, segmentIndex) in getInlineSegments(block.text)"
                        :key="`${message.id}-q-${blockIndex}-${segmentIndex}`"
                        class="md-inline"
                        :class="inlineClass(segment)"
                        selectable
                        @click.stop="handleInlineClick(segment)"
                      >
                        {{ segment.text }}
                      </text>
                    </text>
                  </view>

                  <view v-else-if="block.type === 'hr'" class="md-hr"></view>

                  <text v-else class="md-paragraph" selectable space="preserve">
                    <text
                      v-for="(segment, segmentIndex) in getInlineSegments(block.text)"
                      :key="`${message.id}-p-${blockIndex}-${segmentIndex}`"
                      class="md-inline"
                      :class="inlineClass(segment)"
                      selectable
                      @click.stop="handleInlineClick(segment)"
                    >
                      {{ segment.text }}
                    </text>
                  </text>
                </view>
              </view>
            </template>
          </view>

          <text v-if="message.createdAt" class="msg-time">{{ shortTime(message.createdAt) }}</text>
        </view>
      </view>
    </scroll-view>

    <view class="composer-wrap" :style="composerInlineStyle">
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
          :adjust-position="false"
          :cursor-spacing="0"
          :disabled="loading"
          @keyboardheightchange="handleInputKeyboardHeightChange"
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
import { downloadWithMobileSupport } from '../../common/mobile-download'

const CONSULTATION_POLL_INTERVAL = 2000
const CONSULTATION_POLL_LIMIT = 30
const NEAR_BOTTOM_THRESHOLD = 120
const POLL_ERROR_TOAST_GAP = 12000
const AGENT_PATIENT_SEARCH_KEY = 'agent_patient_search_keyword'

export default {
  data() {
    return {
      input: '',
      loading: false,
      scrollTarget: '',
      userName: '医生',
      agentAvatar: '/static/project_icon_v2.jpg',
      pendingAttachment: null,
      messages: [],
      mode: 'ai',
      consultationId: null,
      consultationTitle: '',
      currentUserId: null,
      members: [],
      friends: [],
      showMemberPanel: false,
      pollTimer: null,
      pollingBusy: false,
      lastRemoteMessageId: 0,
      isNearBottom: true,
      listViewportHeight: 0,
      keyboardHeight: 0,
      baseWindowHeight: 0,
      currentWindowHeight: 0,
      keyboardListenerBound: false,
      keyboardHeightHandler: null,
      windowResizeBound: false,
      windowResizeHandler: null,
      pollErrorToastAt: 0,
      markdownBlockCache: new Map(),
      markdownInlineCache: new Map()
    }
  },
  computed: {
    isConsultation() {
      return this.mode === 'consultation'
    },
    headerTitle() {
      return this.isConsultation ? (this.consultationTitle || '联合会诊') : 'AI问答'
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
    },
    agentModeLabel() {
      return '\u8d28\u91cf\u8bc4\u4f30 / \u64cd\u4f5c\u8f85\u52a9 / \u5f71\u50cf\u5206\u6790 / \u4e34\u5e8a\u6307\u5357\u68c0\u7d22'
    },
    agentWelcomeMessage() {
      return '\u4f60\u597d\uff0c\u6211\u662f\u591a\u667a\u80fd\u4f53AI\u52a9\u624b\uff0c\u5f53\u524d\u652f\u6301\u8d28\u91cf\u8bc4\u4f30\u3001\u64cd\u4f5c\u8f85\u52a9\u3001\u5f71\u50cf\u5206\u6790\u548c\u4e34\u5e8a\u6307\u5357\u68c0\u7d22\uff0c\u8bf7\u8f93\u5165\u4f60\u7684\u95ee\u9898\u3002'
    },
    userInitial() {
      const name = String(this.userName || '').trim()
      if (!name) return '医'
      return name.slice(0, 1)
    },
    keyboardOffset() {
      if (this.keyboardHeight <= 0) return 0
      // Android App-Plus uses adjustResize (pages.json), avoid double-lifting the composer.
      if (typeof plus !== 'undefined' && String(plus?.os?.name || '').toLowerCase() === 'android') {
        return 0
      }
      const shrink = Math.max(0, this.baseWindowHeight - this.currentWindowHeight)
      const offset = this.keyboardHeight - shrink
      return offset > 0 ? offset : 0
    },
    messageListInlineStyle() {
      if (this.keyboardOffset <= 0) return null
      return { paddingBottom: `${this.keyboardOffset + 16}px` }
    },
    composerInlineStyle() {
      if (this.keyboardOffset <= 0) return null
      return { transform: `translateY(-${this.keyboardOffset}px)` }
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
      content: this.agentWelcomeMessage,
      createdAt: ''
    })
    await this.loadAiHistory()
  },
  onShow() {
    this.refreshWindowHeight(true)
    this.bindWindowResize()
    this.measureMessageListViewport()
    this.bindKeyboardHeightChange()
    if (!this.isConsultation || !this.consultationId) return
    this.startConsultationPolling()
    this.pollConsultationMessages({ silent: true, forceScroll: false })
  },
  onHide() {
    this.stopConsultationPolling()
    this.unbindKeyboardHeightChange()
    this.unbindWindowResize()
    this.keyboardHeight = 0
  },
  onUnload() {
    this.stopConsultationPolling()
    this.unbindKeyboardHeightChange()
    this.unbindWindowResize()
    this.keyboardHeight = 0
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
        this.userName = name
      }
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
        const mapped = list.map((item) => this.mapConsultationMessage(item))
        this.messages = mapped
        this.members = Array.isArray(members) ? members : []
        this.friends = Array.isArray(friends) ? friends : []
        this.trackLatestRemoteMessage(mapped)
        this.isNearBottom = true
        this.scrollToBottom()
        this.measureMessageListViewport()
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
    showSenderName(message) {
      if (!this.isConsultation || !message || message.self || message.type === 'typing') return false
      return Boolean(String(message.senderName || '').trim())
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
    startConsultationPolling() {
      if (!this.isConsultation || !this.consultationId || this.pollTimer) return
      this.pollTimer = setInterval(() => {
        this.pollConsultationMessages({ silent: false, forceScroll: false })
      }, CONSULTATION_POLL_INTERVAL)
    },
    stopConsultationPolling() {
      if (!this.pollTimer) return
      clearInterval(this.pollTimer)
      this.pollTimer = null
    },
    async pollConsultationMessages({ silent = false, forceScroll = false } = {}) {
      if (!this.isConsultation || !this.consultationId || this.pollingBusy) return 0
      this.pollingBusy = true
      try {
        const payload = await listConsultationMessages(this.consultationId, { limit: CONSULTATION_POLL_LIMIT })
        const list = Array.isArray(payload) ? payload.slice().reverse() : []
        const mapped = list.map((item) => this.mapConsultationMessage(item))
        const added = this.mergeConsultationMessages(mapped, forceScroll)
        if (!added) {
          this.trackLatestRemoteMessage(mapped)
        }
        return added
      } catch (err) {
        console.error('poll consultation messages failed', err)
        if (!silent) this.notifyPollError()
        return 0
      } finally {
        this.pollingBusy = false
      }
    },
    mergeConsultationMessages(incoming, forceScroll = false) {
      if (!Array.isArray(incoming) || !incoming.length) return 0
      const existingIds = new Set(
        this.messages
          .map((message) => this.toNumberMessageId(message))
          .filter((id) => id !== null)
      )
      const additions = []

      incoming.forEach((message) => {
        const id = this.toNumberMessageId(message)
        if (id !== null) {
          if (existingIds.has(id)) return
          existingIds.add(id)
        }
        additions.push(message)
      })

      if (!additions.length) return 0
      const merged = [...this.messages, ...additions]
      merged.sort((a, b) => {
        const aid = this.toNumberMessageId(a)
        const bid = this.toNumberMessageId(b)
        if (aid !== null && bid !== null) return aid - bid
        if (aid !== null) return -1
        if (bid !== null) return 1
        return 0
      })
      this.messages = merged
      this.trackLatestRemoteMessage(merged)
      const latest = additions[additions.length - 1]
      this.scrollToBottom(latest?.id, forceScroll || this.isNearBottom)
      return additions.length
    },
    trackLatestRemoteMessage(messages) {
      const latest = this.computeLastRemoteMessageId(messages)
      if (latest > this.lastRemoteMessageId) {
        this.lastRemoteMessageId = latest
      }
    },
    computeLastRemoteMessageId(messages) {
      if (!Array.isArray(messages) || !messages.length) return 0
      return messages.reduce((max, message) => {
        const id = this.toNumberMessageId(message)
        if (id === null) return max
        return id > max ? id : max
      }, 0)
    },
    toNumberMessageId(message) {
      const raw = typeof message === 'object' ? message?.id : message
      const num = Number(raw)
      if (!Number.isFinite(num) || num <= 0) return null
      return num
    },
    notifyPollError() {
      const now = Date.now()
      if (now - this.pollErrorToastAt < POLL_ERROR_TOAST_GAP) return
      this.pollErrorToastAt = now
      uni.showToast({ title: '消息同步失败，正在重试', icon: 'none' })
    },
    normalizeKeyboardHeight(rawHeight) {
      const height = Number(rawHeight || 0)
      if (!Number.isFinite(height) || height <= 0) return 0
      const baseline = this.currentWindowHeight || this.baseWindowHeight || 0
      if (!baseline) return height
      const maxReasonable = Math.floor(baseline * 0.6)
      return Math.min(height, maxReasonable)
    },
    refreshWindowHeight(resetBaseline = false) {
      let windowHeight = 0
      if (typeof uni.getWindowInfo === 'function') {
        windowHeight = Number(uni.getWindowInfo()?.windowHeight || 0)
      } else if (typeof uni.getSystemInfoSync === 'function') {
        windowHeight = Number(uni.getSystemInfoSync()?.windowHeight || 0)
      }
      if (windowHeight <= 0) return
      this.currentWindowHeight = windowHeight
      if (resetBaseline || !this.baseWindowHeight || windowHeight > this.baseWindowHeight) {
        this.baseWindowHeight = windowHeight
      }
    },
    handleInputKeyboardHeightChange(detail) {
      const next = this.normalizeKeyboardHeight(detail?.height)
      this.keyboardHeight = next
      this.refreshWindowHeight(false)
    },
    bindWindowResize() {
      if (this.windowResizeBound || typeof uni.onWindowResize !== 'function') return
      this.windowResizeHandler = (res) => {
        const next = Number(res?.size?.windowHeight || res?.windowHeight || 0)
        if (next <= 0) return
        this.currentWindowHeight = next
        if (!this.baseWindowHeight || next > this.baseWindowHeight) {
          this.baseWindowHeight = next
        }
      }
      uni.onWindowResize(this.windowResizeHandler)
      this.windowResizeBound = true
    },
    unbindWindowResize() {
      if (!this.windowResizeBound || typeof uni.offWindowResize !== 'function') return
      uni.offWindowResize(this.windowResizeHandler)
      this.windowResizeBound = false
      this.windowResizeHandler = null
    },
    bindKeyboardHeightChange() {
      if (this.keyboardListenerBound || typeof uni.onKeyboardHeightChange !== 'function') return
      this.keyboardHeightHandler = (res) => {
        const next = this.normalizeKeyboardHeight(res?.height)
        this.keyboardHeight = next
        this.refreshWindowHeight(false)
        if (this.keyboardHeight > 0) {
          this.scrollToBottom(undefined, true)
        } else {
          setTimeout(() => {
            this.refreshWindowHeight(true)
          }, 60)
        }
      }
      uni.onKeyboardHeightChange(this.keyboardHeightHandler)
      this.keyboardListenerBound = true
    },
    unbindKeyboardHeightChange() {
      if (!this.keyboardListenerBound || typeof uni.offKeyboardHeightChange !== 'function') return
      uni.offKeyboardHeightChange(this.keyboardHeightHandler)
      this.keyboardListenerBound = false
      this.keyboardHeightHandler = null
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
    async pickFile() {
      try {
        const picked = await this.chooseSingleAttachmentFile()
        if (!picked) return
        let normalized = this.normalizePickedAttachment(picked)
        normalized = await this.prepareAttachmentForUpload(normalized)
        if (!normalized || !normalized.filePath) {
          uni.showToast({ title: '文件读取失败，请重新选择', icon: 'none' })
          return
        }
        this.pendingAttachment = {
          path: normalized.filePath,
          name: normalized.name || this.extractFileName(normalized.filePath),
          size: Number(normalized.size || 0),
          type: this.detectAttachmentType(normalized.name || normalized.filePath)
        }
      } catch (err) {
        if (this.isChooseCancelled(err)) return
        console.error('pick consultation file failed', err)
        uni.showToast({ title: this.pickErrorText(err) || '文件选择失败', icon: 'none' })
      }
    },
    async chooseSingleAttachmentFile() {
      let lastError = null
      if (this.isAppPlusRuntime()) {
        const byPlus = await this.tryChooseByPlusFile().catch((err) => {
          lastError = err
          return null
        })
        if (byPlus) return byPlus
      }
      const byMessage = await this.tryChooseByUniApi('chooseMessageFile', {
        type: 'file'
      }).catch((err) => {
        lastError = err
        return null
      })
      if (byMessage) return byMessage
      const byFile = await this.tryChooseByUniApi('chooseFile').catch((err) => {
        lastError = err
        return null
      })
      if (byFile) return byFile
      const byIntent = await this.tryChooseByAndroidIntent('*/*').catch((err) => {
        lastError = err
        return null
      })
      if (byIntent) return byIntent
      if (lastError) throw lastError
      throw new Error('choose file api unavailable')
    },
    tryChooseByUniApi(apiName, extraOptions = {}) {
      const choose = uni?.[apiName]
      if (typeof choose !== 'function') return Promise.resolve(null)
      return new Promise((resolve, reject) => {
        choose({
          count: 1,
          ...extraOptions,
          success: (res) => {
            const first = (res.tempFiles || [])[0]
            if (first) {
              resolve(first)
              return
            }
            const fallbackPath = Array.isArray(res.tempFilePaths) ? (res.tempFilePaths[0] || '') : ''
            if (fallbackPath) {
              resolve({
                path: fallbackPath,
                tempFilePath: fallbackPath,
                name: this.extractFileName(fallbackPath)
              })
              return
            }
            resolve(null)
          },
          fail: (err) => {
            if (this.isChooseCancelled(err)) {
              resolve(null)
              return
            }
            reject(err)
          }
        })
      })
    },
    tryChooseByPlusFile() {
      if (typeof plus === 'undefined' || !plus.io || typeof plus.io.chooseFile !== 'function') {
        return Promise.resolve(null)
      }
      return new Promise((resolve, reject) => {
        let settled = false
        const finish = (err, value = null) => {
          if (settled) return
          settled = true
          if (err) {
            if (this.isChooseCancelled(err)) {
              resolve(null)
              return
            }
            reject(err)
            return
          }
          resolve(value)
        }
        const consumeResult = async (result) => {
          try {
            const normalized = await this.normalizePlusChosenResult(result)
            finish(null, normalized)
          } catch (err) {
            finish(err)
          }
        }
        try {
          const maybeTask = plus.io.chooseFile(
            {
              count: 1,
              multiple: false,
              title: 'Select File'
            },
            (res) => consumeResult(res),
            (err) => finish(err)
          )
          if (maybeTask && typeof maybeTask.then === 'function') {
            maybeTask.then((res) => consumeResult(res)).catch((err) => finish(err))
            return
          }
          if (this.looksLikePlusChooseResult(maybeTask)) {
            consumeResult(maybeTask)
          }
        } catch (err) {
          finish(err)
        }
      })
    },
    tryChooseByAndroidIntent(mimeType = '*/*') {
      if (!this.isAppPlusRuntime() || String(plus.os?.name || '').toLowerCase() !== 'android') {
        return Promise.resolve(null)
      }
      return new Promise((resolve, reject) => {
        const main = plus.android.runtimeMainActivity()
        if (!main) {
          resolve(null)
          return
        }
        const Intent = plus.android.importClass('android.content.Intent')
        const Activity = plus.android.importClass('android.app.Activity')
        const requestCode = Number(Date.now() % 60000) + 1000
        const previous = main.onActivityResult
        let settled = false
        const finish = (err, value = null) => {
          if (settled) return
          settled = true
          main.onActivityResult = previous
          if (err) {
            if (this.isChooseCancelled(err)) {
              resolve(null)
              return
            }
            reject(err)
            return
          }
          resolve(value)
        }
        const self = this
        main.onActivityResult = function(request, resultCode, data) {
          if (request !== requestCode) {
            if (typeof previous === 'function') previous(request, resultCode, data)
            return
          }
          if (resultCode !== Activity.RESULT_OK || !data) {
            finish(null, null)
            return
          }
          try {
            const uri = data.getData && data.getData()
            if (!uri) {
              finish(null, null)
              return
            }
            plus.android.importClass(uri)
            const uriString = String(uri.toString ? uri.toString() : '')
            if (!uriString) {
              finish(null, null)
              return
            }
            const meta = self.queryContentUriMeta(uriString)
            finish(null, {
              path: uriString,
              tempFilePath: uriString,
              name: meta.name || self.extractFileName(uriString),
              size: Number(meta.size || 0)
            })
          } catch (err) {
            finish(err)
          }
        }
        try {
          const intent = new Intent(Intent.ACTION_GET_CONTENT)
          intent.addCategory(Intent.CATEGORY_OPENABLE)
          intent.setType(mimeType || '*/*')
          intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
          const chooser = Intent.createChooser(intent, 'Select File')
          main.startActivityForResult(chooser, requestCode)
        } catch (err) {
          finish(err)
        }
      })
    },
    looksLikePlusChooseResult(result) {
      if (!result) return false
      if (typeof result === 'string') return true
      if (Array.isArray(result) && result.length) return true
      if (Array.isArray(result.files) && result.files.length) return true
      return !!(result.path || result.filePath || result.tempFilePath || result.file)
    },
    async normalizePlusChosenResult(result) {
      const first = this.pickFirstChosenFile(result)
      if (!first) return null
      const rawPath = typeof first === 'string'
        ? first
        : first.path || first.filePath || first.tempFilePath || first.url || ''
      const filePath = this.normalizeNativeFilePath(rawPath)
      if (!filePath) return null
      const fallbackName = typeof first === 'string'
        ? this.extractFileName(filePath)
        : first.name || this.extractFileName(filePath)
      const fallbackSize = typeof first === 'string' ? 0 : Number(first.size || 0)
      const localMeta = await this.readLocalFileMeta(filePath)
      return {
        name: localMeta.name || fallbackName || 'attachment',
        size: Number(localMeta.size || fallbackSize || 0),
        path: filePath,
        tempFilePath: filePath
      }
    },
    pickFirstChosenFile(result) {
      if (!result) return null
      if (typeof result === 'string') return result
      if (Array.isArray(result)) return result[0] || null
      if (Array.isArray(result.files)) return result.files[0] || null
      if (result.file) return result.file
      if (result.path || result.filePath || result.tempFilePath || result.url) return result
      return null
    },
    extractPickedPath(file) {
      if (!file) return ''
      const direct = [
        file.filePath,
        file.path,
        file.tempFilePath,
        file.uri,
        file.localPath,
        file.savedFilePath,
        file.apFilePath,
        file.url
      ].find((v) => typeof v === 'string' && v.trim())
      if (direct) return direct
      if (Array.isArray(file.tempFilePaths)) {
        const first = file.tempFilePaths[0]
        if (typeof first === 'string' && first.trim()) return first
      }
      return ''
    },
    normalizePickedAttachment(file) {
      if (!file) return null
      const filePath = this.extractPickedPath(file)
      return {
        name: file.name || file.file?.name || this.extractFileName(filePath) || 'attachment',
        size: Number(file.size || file.file?.size || 0),
        filePath,
        fileObj: file.file || null
      }
    },
    normalizeNativeFilePath(path) {
      const raw = String(path || '').trim()
      if (!raw) return ''
      if (/^file:\/\//i.test(raw)) {
        const pure = raw.replace(/^file:\/\//i, '')
        try {
          return decodeURIComponent(pure)
        } catch (err) {
          return pure
        }
      }
      return raw
    },
    isAppPlusRuntime() {
      return typeof plus !== 'undefined' && !!plus.io
    },
    isAppPrivatePath(path) {
      const value = String(path || '').toLowerCase()
      return value.startsWith('_doc/') || value.startsWith('_documents/') || value.startsWith('_www/')
    },
    toResolvableLocalUrl(path) {
      const value = String(path || '').trim()
      if (!value) return ''
      if (/^(file|content):\/\//i.test(value)) return value
      if (value.startsWith('/')) return `file://${value}`
      return value
    },
    buildSafeCopyName(name = '') {
      const fallback = 'attachment'
      const base = String(name || fallback).trim() || fallback
      const sanitized = base.replace(/[\\/:*?"<>|]/g, '_')
      const dot = sanitized.lastIndexOf('.')
      const stem = dot > 0 ? sanitized.slice(0, dot) : sanitized
      const ext = dot > 0 ? sanitized.slice(dot) : ''
      return `${stem}_${Date.now()}${ext}`
    },
    async prepareAttachmentForUpload(file) {
      if (!file) return null
      const path = this.normalizeNativeFilePath(this.extractPickedPath(file) || file.filePath)
      if (!path) return file
      let next = { ...file, filePath: path }
      const isContentUri = /^content:\/\//i.test(this.toResolvableLocalUrl(path))
      if (isContentUri) {
        throw new Error('当前文件来源不支持，请从文件管理器选择本地文件')
      }
      if (!(Number(next.size || 0) > 0)) {
        const meta = await this.readLocalFileMeta(next.filePath)
        next = {
          ...next,
          name: next.name || meta.name || 'attachment',
          size: Number(meta.size || next.size || 0)
        }
      }
      return next
    },
    copyFileToPrivateDoc(sourcePath, sourceName = '') {
      if (!this.isAppPlusRuntime()) return Promise.resolve(null)
      const targetPath = this.toResolvableLocalUrl(sourcePath)
      if (!targetPath) {
        return Promise.reject(new Error('empty source path'))
      }
      if (/^content:\/\//i.test(targetPath)) {
        return this.copyContentUriToPrivateDoc(targetPath, sourceName)
      }
      return new Promise((resolve, reject) => {
        plus.io.resolveLocalFileSystemURL(
          targetPath,
          (entry) => {
            plus.io.requestFileSystem(
              plus.io.PRIVATE_DOC,
              (fs) => {
                fs.root.getDirectory(
                  'consultation-upload',
                  { create: true },
                  (dirEntry) => {
                    const targetName = this.buildSafeCopyName(sourceName || entry.name || 'attachment')
                    entry.copyTo(
                      dirEntry,
                      targetName,
                      (copiedEntry) => {
                        const copiedPath = copiedEntry?.toLocalURL?.() || copiedEntry?.fullPath || ''
                        copiedEntry.file(
                          (copiedFile) => resolve({
                            filePath: copiedPath,
                            name: copiedFile?.name || targetName,
                            size: Number(copiedFile?.size || 0)
                          }),
                          () => resolve({
                            filePath: copiedPath,
                            name: targetName,
                            size: 0
                          })
                        )
                      },
                      (err) => reject(err)
                    )
                  },
                  (err) => reject(err)
                )
              },
              (err) => reject(err)
            )
          },
          (err) => reject(err)
        )
      })
    },
    copyContentUriToPrivateDoc(contentUri, sourceName = '') {
      if (!this.isAppPlusRuntime()) return Promise.resolve(null)
      if (String(plus.os?.name || '').toLowerCase() !== 'android') {
        return Promise.reject(new Error('content uri copy is android only'))
      }
      return new Promise((resolve, reject) => {
        plus.io.requestFileSystem(
          plus.io.PRIVATE_DOC,
          (fs) => {
            fs.root.getDirectory(
              'consultation-upload',
              { create: true },
              async () => {
                try {
                  const meta = this.queryContentUriMeta(contentUri)
                  const targetName = this.buildSafeCopyName(sourceName || meta.name || 'attachment')
                  const relativePath = `_doc/consultation-upload/${targetName}`
                  const absolutePath = plus.io.convertLocalFileSystemURL(relativePath)
                  const copiedBytes = this.streamContentUriToFile(contentUri, absolutePath)
                  const finalSize = copiedBytes > 0 ? copiedBytes : Number(meta.size || 0)
                  resolve({
                    filePath: relativePath,
                    name: targetName,
                    size: finalSize
                  })
                } catch (err) {
                  reject(err)
                }
              },
              (err) => reject(err)
            )
          },
          (err) => reject(err)
        )
      })
    },
    invokeJavaMethod(target, methodName, ...args) {
      if (!target || !methodName) return null
      try {
        const direct = target[methodName]
        if (typeof direct === 'function') {
          return direct.apply(target, args)
        }
      } catch (err) {
        // Fallback to plus.android.invoke below.
      }
      if (this.isAppPlusRuntime() && plus.android && typeof plus.android.invoke === 'function') {
        try {
          return plus.android.invoke(target, methodName, ...args)
        } catch (err) {
          return null
        }
      }
      return null
    },
    toJavaNumber(value, fallback = 0) {
      const num = Number(value)
      return Number.isFinite(num) ? num : fallback
    },
    queryContentUriMeta(contentUri) {
      if (!this.isAppPlusRuntime()) return { name: '', size: 0 }
      try {
        const activity = plus.android.runtimeMainActivity()
        if (!activity) return { name: '', size: 0 }
        try { plus.android.importClass(activity) } catch (err) {}
        const Uri = plus.android.importClass('android.net.Uri')
        const OpenableColumns = plus.android.importClass('android.provider.OpenableColumns')
        const resolver = this.invokeJavaMethod(activity, 'getContentResolver')
        if (!resolver) return { name: '', size: 0 }
        try { plus.android.importClass(resolver) } catch (err) {}
        const uri = Uri.parse(contentUri)
        const cursor = this.invokeJavaMethod(resolver, 'query', uri, null, null, null, null)
        if (!cursor) return { name: '', size: 0 }
        try { plus.android.importClass(cursor) } catch (err) {}
        let name = ''
        let size = 0
        try {
          if (this.invokeJavaMethod(cursor, 'moveToFirst')) {
            const nameIdx = this.toJavaNumber(this.invokeJavaMethod(cursor, 'getColumnIndex', OpenableColumns.DISPLAY_NAME), -1)
            const sizeIdx = this.toJavaNumber(this.invokeJavaMethod(cursor, 'getColumnIndex', OpenableColumns.SIZE), -1)
            if (nameIdx >= 0) {
              name = String(this.invokeJavaMethod(cursor, 'getString', nameIdx) || '')
            }
            if (sizeIdx >= 0) {
              size = this.toJavaNumber(this.invokeJavaMethod(cursor, 'getLong', sizeIdx), 0)
            }
          }
        } finally {
          this.invokeJavaMethod(cursor, 'close')
        }
        return { name, size }
      } catch (err) {
        console.error('query content uri meta failed', err)
        return { name: '', size: 0 }
      }
    },
    streamContentUriToFile(contentUri, absolutePath) {
      if (!this.isAppPlusRuntime()) return 0
      const activity = plus.android.runtimeMainActivity()
      if (!activity) throw new Error('missing activity')
      try { plus.android.importClass(activity) } catch (err) {}
      const Uri = plus.android.importClass('android.net.Uri')
      const resolver = this.invokeJavaMethod(activity, 'getContentResolver')
      if (!resolver) throw new Error('missing content resolver')
      try { plus.android.importClass(resolver) } catch (err) {}
      const uri = Uri.parse(contentUri)
      const inputStream = this.invokeJavaMethod(resolver, 'openInputStream', uri)
      if (!inputStream) {
        throw new Error('open input stream failed')
      }
      try { plus.android.importClass(inputStream) } catch (err) {}
      const outputStream = plus.android.newObject('java.io.FileOutputStream', absolutePath)
      let copied = 0
      try {
        let value = this.toJavaNumber(this.invokeJavaMethod(inputStream, 'read'), -1)
        while (value !== -1) {
          this.invokeJavaMethod(outputStream, 'write', value)
          copied += 1
          value = this.toJavaNumber(this.invokeJavaMethod(inputStream, 'read'), -1)
        }
        this.invokeJavaMethod(outputStream, 'flush')
      } finally {
        this.closeJavaStream(outputStream)
        this.closeJavaStream(inputStream)
      }
      return copied
    },
    closeJavaStream(stream) {
      if (!stream) return
      try {
        this.invokeJavaMethod(stream, 'close')
      } catch (err) {
        console.error('close java stream failed', err)
      }
    },
    readLocalFileMeta(path) {
      if (!path || !this.isAppPlusRuntime() || typeof plus.io.resolveLocalFileSystemURL !== 'function') {
        return Promise.resolve({ name: this.extractFileName(path), size: 0 })
      }
      return new Promise((resolve) => {
        plus.io.resolveLocalFileSystemURL(
          this.toResolvableLocalUrl(path),
          (entry) => {
            if (!entry || typeof entry.file !== 'function') {
              resolve({ name: this.extractFileName(path), size: 0 })
              return
            }
            entry.file(
              (file) => resolve({
                name: file?.name || this.extractFileName(path),
                size: Number(file?.size || 0)
              }),
              () => resolve({ name: this.extractFileName(path), size: 0 })
            )
          },
          () => resolve({ name: this.extractFileName(path), size: 0 })
        )
      })
    },
    async resolveAttachmentUploadPath(attachment) {
      if (!attachment) return ''
      let local = this.normalizeNativeFilePath(attachment.path)
      if (!local) return ''
      if (/^content:\/\//i.test(this.toResolvableLocalUrl(local))) {
        throw new Error('当前文件来源不支持，请从文件管理器选择本地文件')
      }
      if (!/^https?:\/\//i.test(local)) {
        if (
          this.isAppPlusRuntime()
          && typeof plus.io.convertLocalFileSystemURL === 'function'
          && this.isAppPrivatePath(local)
        ) {
          local = plus.io.convertLocalFileSystemURL(local)
        }
        return local
      }
      return new Promise((resolve) => {
        uni.downloadFile({
          url: local,
          success: (res) => resolve(res.tempFilePath || ''),
          fail: () => resolve('')
        })
      })
    },
    isChooseCancelled(err) {
      const message = String(this.pickErrorText(err) || '').toLowerCase()
      return message.includes('cancel') || message.includes('取消')
    },
    pickErrorText(err) {
      if (!err) return ''
      const code = Number(err.code || err.statusCode || 0)
      const rawMessage = String(err.message || err.error || err.errMsg || '')
      if (code === 413 || /upload size exceeded|maximum upload size exceeded|文件过大/i.test(rawMessage)) {
        return '文件过大，请压缩后重试或改为发送下载链接'
      }
      if (typeof err === 'string') return err
      if (typeof err.errMsg === 'string' && err.errMsg) return err.errMsg
      if (typeof err.error === 'string' && err.error) return err.error
      if (typeof err.message === 'string' && err.message) return err.message
      return ''
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
          const { content: reply, action } = this.resolveAgentPayload(data)
          this.replaceTyping(typingId, reply)
          this.runAgentAction(action)
        } catch (err) {
          console.error('agent image chat error', err)
          this.replaceTyping(typingId, '抱歉，AI助手暂时无法响应，请稍后重试。')
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
        const shouldUseStructured = this.shouldUseStructuredAgentRequest(text)
        if (!shouldUseStructured && this.canStream()) {
          await this.streamFromModel(text, typingId)
        } else {
          const data = await sendAgentMessage(text)
          const { content: reply, action } = this.resolveAgentPayload(data)
          this.replaceTyping(typingId, reply)
          this.runAgentAction(action)
        }
      } catch (err) {
        console.error('agent chat error', err)
        this.replaceTyping(typingId, '抱歉，AI助手暂时无法响应，请稍后重试。')
      } finally {
        this.loading = false
      }
    },
    async sendConsultation(text) {
      const attachment = this.pendingAttachment
      this.loading = true
      try {
        if (attachment) {
          const uploadPath = await this.resolveAttachmentUploadPath(attachment)
          if (!uploadPath) {
            throw new Error('missing upload file path')
          }
          const uploaded = await uploadConsultationAttachment(this.consultationId, uploadPath, {
            messageType: attachment.type || 'FILE',
            fileName: attachment.name || this.extractFileName(uploadPath)
          })
          const uploadedMessage = this.mapConsultationMessage(uploaded)
          uploadedMessage.self = true
          this.appendLocalMessage(uploadedMessage, true)
          this.pendingAttachment = null
        }

        if (text) {
          const sent = await sendConsultationMessage(this.consultationId, {
            messageType: 'TEXT',
            textContent: text
          })
          const sentMessage = this.mapConsultationMessage(sent)
          sentMessage.self = true
          this.appendLocalMessage(sentMessage, true)
        }

        this.input = ''
        await this.pollConsultationMessages({ silent: true, forceScroll: true })
      } catch (err) {
        console.error('send consultation message failed', err)
        uni.showToast({ title: this.pickErrorText(err) || '发送失败', icon: 'none' })
      } finally {
        this.loading = false
      }
    },
    canStream() {
      return typeof fetch === 'function' && typeof ReadableStream !== 'undefined'
    },
    shouldUseStructuredAgentRequest(text) {
      const value = String(text || '').trim()
      if (!value) return false
      return /(患者|病历|数据|信息|资料|查询|检索|搜索|查看|跳转|进入|打开|前往|详情)/.test(value)
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
              this.replaceTyping(typingId, content)
            }
          }
          lineEnd = buffer.indexOf('\n')
        }
      }
      this.replaceTyping(typingId, content)
    },
    resolveAgentPayload(payload) {
      const content = this.normalizeAgentReply(payload)
      const action = payload && typeof payload === 'object' && payload.action && typeof payload.action === 'object'
        ? payload.action
        : null
      return { content, action }
    },
    runAgentAction(action) {
      if (!action || typeof action !== 'object') return
      const type = String(action.type || '').trim().toLowerCase()
      if (!type) return

      if (type === 'open_patient_detail') {
        const patientId = Number(action.patientId || action.patient_id)
        if (!patientId) return
        const patientName = String(action.patientName || action.patient_name || '').trim()
        uni.setStorageSync('currentPatient', patientName ? { id: patientId, name: patientName } : { id: patientId })
        uni.showToast({ title: '正在打开患者详情', icon: 'none' })
        setTimeout(() => {
          uni.navigateTo({ url: `/pages/patient/detail?id=${patientId}` })
        }, 80)
        return
      }

      if (type === 'open_patient_list') {
        const keyword = String(action.keyword || '').trim()
        if (keyword) {
          uni.setStorageSync(AGENT_PATIENT_SEARCH_KEY, keyword)
        }
        uni.showToast({ title: keyword ? `已筛选：${keyword}` : '已打开患者列表', icon: 'none' })
        setTimeout(() => {
          uni.switchTab({ url: '/pages/patient/list' })
        }, 80)
      }
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
    rememberMarkdownCache(cache, key, value, limit = 300) {
      if (!cache || typeof cache.set !== 'function') return
      if (cache.has(key)) {
        cache.set(key, value)
        return
      }
      cache.set(key, value)
      if (cache.size <= limit) return
      const firstKey = cache.keys().next().value
      if (firstKey !== undefined) {
        cache.delete(firstKey)
      }
    },
    getMarkdownBlocks(content) {
      const normalized = String(content || '').replace(/\r\n/g, '\n').replace(/\r/g, '\n')
      const cached = this.markdownBlockCache.get(normalized)
      if (cached) return cached

      const lines = normalized.split('\n')
      const blocks = []
      let index = 0

      while (index < lines.length) {
        const rawLine = lines[index]
        const line = String(rawLine || '')
        const trimmed = line.trim()

        if (!trimmed) {
          index += 1
          continue
        }

        if (/^```/.test(trimmed)) {
          const lang = trimmed.slice(3).trim()
          index += 1
          const codeLines = []
          while (index < lines.length && !/^```/.test(String(lines[index] || '').trim())) {
            codeLines.push(String(lines[index] || ''))
            index += 1
          }
          if (index < lines.length) index += 1
          blocks.push({ type: 'code', lang, text: codeLines.join('\n') })
          continue
        }

        const headingMatch = trimmed.match(/^(#{1,6})\s+(.*)$/)
        if (headingMatch) {
          blocks.push({
            type: 'heading',
            level: headingMatch[1].length,
            text: headingMatch[2] || ''
          })
          index += 1
          continue
        }

        if (/^(-{3,}|\*{3,}|_{3,})$/.test(trimmed)) {
          blocks.push({ type: 'hr' })
          index += 1
          continue
        }

        if (/^>\s?/.test(trimmed)) {
          const quoteLines = []
          while (index < lines.length) {
            const quoteLine = String(lines[index] || '')
            const quoteTrim = quoteLine.trim()
            if (!/^>\s?/.test(quoteTrim)) break
            quoteLines.push(quoteTrim.replace(/^>\s?/, ''))
            index += 1
          }
          blocks.push({ type: 'quote', text: quoteLines.join('\n') })
          continue
        }

        const orderedMarker = /^\d+\.\s+/
        const unorderedMarker = /^[-*+]\s+/
        if (orderedMarker.test(trimmed) || unorderedMarker.test(trimmed)) {
          const ordered = orderedMarker.test(trimmed)
          const items = []
          while (index < lines.length) {
            const itemLine = String(lines[index] || '')
            const itemTrim = itemLine.trim()
            if (ordered) {
              const orderedMatch = itemTrim.match(/^\d+\.\s+(.*)$/)
              if (!orderedMatch) break
              items.push(orderedMatch[1] || '')
              index += 1
              continue
            }
            const unorderedMatch = itemTrim.match(/^[-*+]\s+(.*)$/)
            if (!unorderedMatch) break
            items.push(unorderedMatch[1] || '')
            index += 1
          }
          blocks.push({ type: 'list', ordered, items })
          continue
        }

        const paragraphLines = []
        while (index < lines.length) {
          const paragraphLine = String(lines[index] || '')
          const paragraphTrim = paragraphLine.trim()
          if (!paragraphTrim) break
          if (
            /^```/.test(paragraphTrim) ||
            /^(#{1,6})\s+/.test(paragraphTrim) ||
            /^>\s?/.test(paragraphTrim) ||
            /^(-{3,}|\*{3,}|_{3,})$/.test(paragraphTrim) ||
            orderedMarker.test(paragraphTrim) ||
            unorderedMarker.test(paragraphTrim)
          ) {
            break
          }
          paragraphLines.push(paragraphLine)
          index += 1
        }
        blocks.push({ type: 'paragraph', text: paragraphLines.join('\n') })
      }

      const result = blocks.length ? blocks : [{ type: 'paragraph', text: normalized }]
      this.rememberMarkdownCache(this.markdownBlockCache, normalized, result, 240)
      return result
    },
    getInlineSegments(text) {
      const normalized = String(text || '')
      const cached = this.markdownInlineCache.get(normalized)
      if (cached) return cached

      const segments = []
      const pattern = /(`[^`]+`)|(\[([^\]]+)\]\(([^)]+)\))|(\*\*[^*]+\*\*)|(__[^_]+__)|(\*[^*]+\*)|(_[^_]+_)/g
      let last = 0
      let match = pattern.exec(normalized)
      while (match) {
        if (match.index > last) {
          segments.push({ type: 'text', text: normalized.slice(last, match.index) })
        }

        const token = match[0]
        if (match[1]) {
          segments.push({ type: 'code', text: token.slice(1, -1) })
        } else if (match[2]) {
          segments.push({ type: 'link', text: match[3] || '', href: match[4] || '' })
        } else if (match[5] || match[6]) {
          segments.push({ type: 'bold', text: token.slice(2, -2) })
        } else if (match[7] || match[8]) {
          segments.push({ type: 'italic', text: token.slice(1, -1) })
        } else {
          segments.push({ type: 'text', text: token })
        }

        last = pattern.lastIndex
        match = pattern.exec(normalized)
      }

      if (last < normalized.length) {
        segments.push({ type: 'text', text: normalized.slice(last) })
      }
      if (!segments.length) {
        segments.push({ type: 'text', text: '' })
      }

      this.rememberMarkdownCache(this.markdownInlineCache, normalized, segments, 500)
      return segments
    },
    inlineClass(segment) {
      const type = String(segment?.type || '')
      return {
        'md-inline--bold': type === 'bold',
        'md-inline--italic': type === 'italic',
        'md-inline--code': type === 'code',
        'md-inline--link': type === 'link'
      }
    },
    handleInlineClick(segment) {
      if (!segment || segment.type !== 'link') return
      const href = String(segment.href || '').trim()
      if (!/^https?:\/\//i.test(href)) return
      this.openOssPath(href)
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
      this.scrollToBottom(id, true)
      return id
    },
    replaceTyping(id, content) {
      const target = this.messages.find((message) => message.id === id)
      if (!target) return
      target.type = 'TEXT'
      target.content = content || ' '
      this.scrollToBottom(id, true)
    },
    appendLocalMessage(message, forceScroll = true) {
      if (!message) return
      this.messages.push(message)
      if (this.isConsultation) {
        this.trackLatestRemoteMessage([message])
      }
      this.scrollToBottom(message.id, forceScroll)
    },
    handleMessageScroll(event) {
      const detail = event?.detail || {}
      const scrollTop = Number(detail.scrollTop || 0)
      const scrollHeight = Number(detail.scrollHeight || 0)
      if (!this.listViewportHeight) {
        this.measureMessageListViewport()
      }
      const viewportHeight = Number(this.listViewportHeight || 0)
      if (!scrollHeight || !viewportHeight) return
      const remain = scrollHeight - (scrollTop + viewportHeight)
      this.isNearBottom = remain <= NEAR_BOTTOM_THRESHOLD
    },
    handleScrollToLower() {
      this.isNearBottom = true
    },
    measureMessageListViewport() {
      this.$nextTick(() => {
        const query = uni.createSelectorQuery().in(this)
        query
          .select('.message-list')
          .boundingClientRect((rect) => {
            if (rect?.height) {
              this.listViewportHeight = rect.height
            }
          })
          .exec()
      })
    },
    scrollToBottom(id, force = true) {
      if (!force) return
      this.$nextTick(() => {
        const target = id || (this.messages.length ? this.messages[this.messages.length - 1].id : '')
        if (target === undefined || target === null) return
        const anchor = this.toAnchorId(target)
        if (!anchor) return
        if (this.scrollTarget === anchor) {
          this.scrollTarget = ''
          this.$nextTick(() => {
            this.scrollTarget = anchor
          })
        } else {
          this.scrollTarget = anchor
        }
        this.isNearBottom = true
      })
    },
    toAnchorId(id) {
      const raw = String(id ?? '').trim()
      if (!raw) return ''
      const normalized = raw.replace(/[^a-zA-Z0-9_-]/g, '_')
      return normalized.startsWith('msg-') ? normalized : `msg-${normalized}`
    },
    extractFileName(path) {
      if (!path) return ''
      const normalized = String(path).replace(/\\/g, '/')
      const arr = normalized.split('/')
      try {
        return decodeURIComponent(arr[arr.length - 1] || '')
      } catch (err) {
        return arr[arr.length - 1] || ''
      }
    },
    detectAttachmentType(nameOrPath) {
      const text = String(nameOrPath || '').toLowerCase()
      const imageExt = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']
      const modelExt = ['.stl', '.obj', '.nrrd', '.mha', '.nii', '.nii.gz']
      if (imageExt.some((ext) => text.endsWith(ext))) return 'IMAGE'
      if (modelExt.some((ext) => text.endsWith(ext))) return 'MODEL'
      return 'FILE'
    },
    async downloadAttachment(message) {
      const url = String(message?.ossPath || '').trim()
      if (!url) {
        uni.showToast({ title: '附件地址无效', icon: 'none' })
        return
      }
      const filename = String(message?.fileName || this.extractFileName(url) || 'attachment')
      await downloadWithMobileSupport({
        url,
        filename,
        loadingTitle: '下载中...',
        successTitle: '下载成功',
        failTitle: '下载失败',
        autoOpen: false
      })
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
  background:
    radial-gradient(560rpx 260rpx at -6% -5%, rgba(129, 181, 255, 0.18), transparent 70%),
    radial-gradient(640rpx 280rpx at 108% 2%, rgba(166, 207, 255, 0.14), transparent 68%),
    #edf4ff;
  display: flex;
  flex-direction: column;
  overflow: hidden;
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
  padding: 12rpx 20rpx 8rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
  background: transparent;
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
  margin: 0 20rpx 12rpx;
  padding: 16rpx;
  border-radius: 20rpx;
  border: 1rpx solid #d0e2f7;
  background: #ffffff;
  box-shadow: 0 14rpx 30rpx rgba(47, 105, 182, 0.12);
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
  border-radius: 16rpx;
  background: #f8fbff;
  padding: 12rpx 14rpx;
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
  padding: 16rpx 24rpx 12rpx;
  box-sizing: border-box;
}

.message {
  display: flex;
  align-items: flex-start;
  gap: 14rpx;
  max-width: 96%;
}

.message + .message {
  margin-top: 22rpx;
}

.message.user {
  margin-left: auto;
  margin-right: 0;
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

.avatar--mine {
  background: linear-gradient(145deg, #2f78d8 0%, #5da4f0 100%);
  box-shadow: 0 10rpx 20rpx rgba(47, 120, 216, 0.3);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  font-weight: 700;
  border: 1rpx solid rgba(255, 255, 255, 0.38);
}

.bubble-wrap {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8rpx;
  max-width: 78%;
}

.message.user .bubble-wrap {
  align-items: flex-end;
}

.bubble {
  padding: 16rpx 20rpx;
  border-radius: 22rpx;
  background: #ffffff;
  border: 1rpx solid #d3e4f8;
  box-shadow: 0 12rpx 26rpx rgba(47, 105, 182, 0.11);
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
  box-shadow: 0 12rpx 28rpx rgba(47, 120, 216, 0.3);
}

.sender-name {
  font-size: 22rpx;
  line-height: 1.2;
  color: #5f7da1;
  margin-left: 2rpx;
}

.msg-text {
  font-size: 26rpx;
  line-height: 1.5;
  white-space: pre-wrap;
  color: inherit;
}

.md-content {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  -webkit-user-select: text;
  user-select: text;
}

.md-block {
  width: 100%;
}

.md-paragraph,
.md-heading,
.md-list-text,
.md-quote-text,
.md-code-text {
  display: block;
  font-size: 26rpx;
  line-height: 1.58;
  color: inherit;
  white-space: pre-wrap;
  word-break: break-word;
}

.md-heading {
  font-weight: 700;
  line-height: 1.48;
}

.md-heading--1 {
  font-size: 33rpx;
}

.md-heading--2 {
  font-size: 31rpx;
}

.md-heading--3 {
  font-size: 29rpx;
}

.md-heading--4,
.md-heading--5,
.md-heading--6 {
  font-size: 27rpx;
}

.md-list {
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.md-list-item {
  display: flex;
  align-items: flex-start;
  gap: 8rpx;
}

.md-list-marker {
  min-width: 26rpx;
  font-size: 26rpx;
  line-height: 1.58;
  color: #7a95b8;
}

.md-list-text {
  flex: 1;
  min-width: 0;
}

.md-quote {
  border-left: 6rpx solid #b6d0ef;
  background: #f2f8ff;
  border-radius: 10rpx;
  padding: 10rpx 12rpx;
}

.md-code {
  border-radius: 12rpx;
  border: 1rpx solid #cfe1f5;
  background: #f4f8ff;
  padding: 10rpx 12rpx;
}

.md-code-lang {
  display: block;
  margin-bottom: 4rpx;
  font-size: 20rpx;
  color: #6e89a9;
}

.md-code-text {
  font-family: 'JetBrains Mono', 'SFMono-Regular', 'Consolas', 'Liberation Mono', monospace;
  font-size: 24rpx;
}

.md-hr {
  height: 1rpx;
  margin: 10rpx 0;
  background: linear-gradient(90deg, transparent, #b7d1ef, transparent);
}

.md-inline--bold {
  font-weight: 700;
}

.md-inline--italic {
  font-style: italic;
}

.md-inline--code {
  font-family: 'JetBrains Mono', 'SFMono-Regular', 'Consolas', 'Liberation Mono', monospace;
  padding: 0 6rpx;
  margin: 0 2rpx;
  border-radius: 8rpx;
  background: rgba(31, 67, 111, 0.08);
}

.md-inline--link {
  color: #236ecb;
  text-decoration: underline;
  text-decoration-thickness: 1.5rpx;
}

.bubble.user .md-quote {
  border-left-color: rgba(255, 255, 255, 0.72);
  background: rgba(255, 255, 255, 0.2);
}

.bubble.user .md-code {
  border-color: rgba(255, 255, 255, 0.46);
  background: rgba(255, 255, 255, 0.18);
}

.bubble.user .md-code-lang,
.bubble.user .md-list-marker {
  color: rgba(255, 255, 255, 0.84);
}

.bubble.user .md-inline--code {
  background: rgba(255, 255, 255, 0.25);
}

.bubble.user .md-inline--link {
  color: #eaf4ff;
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
  color: #8199b6;
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

.composer-wrap {
  transition: transform 0.2s ease;
  will-change: transform;
}

.input-preview {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
  padding: 10rpx 20rpx 8rpx;
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
  box-sizing: border-box;
}
</style>
