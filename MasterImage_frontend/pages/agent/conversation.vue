<template>
  <view class="page">
    <view class="header">
      <view class="back" @click="goBack">
        <wd-icon name="arrow-left" />
      </view>
      <image class="header-avatar" src="/static/project_icon.jpg" mode="aspectFill" />
      <view class="header-info">
        <text class="header-name">智能体助手</text>
        <text class="header-status">在线</text>
      </view>
    </view>

    <scroll-view
      class="message-list"
      scroll-y
      :scroll-with-animation="true"
      :scroll-into-view="scrollTarget"
    >
      <view
        v-for="message in messages"
        :key="message.id"
        :id="message.id"
        class="message"
        :class="message.role"
      >
        <image
          class="avatar"
          :class="message.role"
          :src="message.role === 'user' ? userAvatar : agentAvatar"
          mode="aspectFill"
        />
        <view class="bubble">
          <image
            v-if="message.imageUrl"
            class="message-image"
            :src="message.imageUrl"
            mode="aspectFill"
          />
          <view v-if="isTyping(message)" class="typing">
            <view class="typing-dot"></view>
            <view class="typing-dot"></view>
            <view class="typing-dot"></view>
          </view>
          <view
            v-else
            v-for="(block, blockIndex) in getMessageBlocks(message.content)"
            :key="`${message.id}-block-${blockIndex}`"
            class="block"
          >
            <text v-if="block.type === 'heading'" class="msg-heading" space="preserve" selectable>
              <text
                v-for="(seg, segIndex) in getInlineSegments(block.text)"
                :key="`${message.id}-heading-${blockIndex}-${segIndex}`"
                space="preserve"
              >
                <text v-if="seg.type === 'link'" class="msg-link" space="preserve" @click="openLink(seg.href)">
                  {{ seg.text }}
                </text>
                <text v-else :class="getInlineClass(seg.type)" space="preserve">
                  {{ seg.text }}
                </text>
              </text>
            </text>
            <view v-else-if="block.type === 'list'" class="msg-list">
              <view
                v-for="(item, itemIndex) in block.items"
                :key="`${message.id}-item-${blockIndex}-${itemIndex}`"
                class="msg-list-item"
              >
                <text class="msg-list-bullet">{{ item.marker }}</text>
                <text class="msg-list-text" space="preserve" selectable>
                  <text
                    v-for="(seg, segIndex) in getInlineSegments(item.text)"
                    :key="`${message.id}-item-${blockIndex}-${itemIndex}-${segIndex}`"
                    space="preserve"
                  >
                    <text v-if="seg.type === 'link'" class="msg-link" space="preserve" @click="openLink(seg.href)">
                      {{ seg.text }}
                    </text>
                    <text v-else :class="getInlineClass(seg.type)" space="preserve">
                      {{ seg.text }}
                    </text>
                  </text>
                </text>
              </view>
            </view>
            <text v-else-if="block.type === 'code'" class="msg-code" space="preserve" selectable>{{ block.text }}</text>
            <text v-else class="msg-paragraph" space="preserve" selectable>
              <text
                v-for="(seg, segIndex) in getInlineSegments(block.text)"
                :key="`${message.id}-para-${blockIndex}-${segIndex}`"
                space="preserve"
              >
                <text v-if="seg.type === 'link'" class="msg-link" space="preserve" @click="openLink(seg.href)">
                  {{ seg.text }}
                </text>
                <text v-else :class="getInlineClass(seg.type)" space="preserve">
                  {{ seg.text }}
                </text>
              </text>
            </text>
          </view>
        </view>
      </view>
    </scroll-view>

    <view v-if="pendingImage" class="input-preview">
      <image class="preview-image" :src="pendingImage.path" mode="aspectFill" />
      <view class="preview-meta">
        <text class="preview-label">已选择图片</text>
        <text class="preview-name">{{ pendingImage.name || 'image' }}</text>
      </view>
      <wd-icon name="close" class="preview-remove" @click="clearImage" />
    </view>
    <view class="input-bar">
      <view class="image-picker" @click="chooseImage">
        <wd-icon name="add" />
      </view>
      <wd-input
        v-model="input"
        placeholder="输入消息"
        confirm-type="send"
        :disabled="loading"
        @confirm="handleConfirm"
        @compositionstart="onCompositionStart"
        @compositionend="onCompositionEnd"
      />
      <wd-button
        size="small"
        type="primary"
        :loading="loading"
        :disabled="loading || (!input.trim() && !pendingImage)"
        @click="send"
      >
        发送
      </wd-button>
    </view>
  </view>
</template>

<script>
import { sendAgentMessage, getAgentHistory, sendAgentMessageWithImage } from '../../common/api'
import { MODEL_BASE_URL, getToken } from '../../common/request'

export default {
  data() {
    return {
      input: '',
      loading: false,
      scrollTarget: '',
      userAvatar: '/static/logo.png',
      agentAvatar: '/static/project_icon.jpg',
      pendingImage: null,
      isComposing: false,
      messages: [
        {
          id: 'welcome',
          role: 'agent',
          content: '你好，我是智能体助手，有什么需要我帮你？'
        }
      ]
    }
  },
  async onLoad() {
    await this.loadHistory()
  },
  methods: {
    async loadHistory() {
      try {
        const payload = await getAgentHistory()
        const items = Array.isArray(payload) ? payload : payload?.messages
        const normalized = this.normalizeHistory(items)
        if (normalized.length) {
          this.messages = normalized
          this.$nextTick(() => {
            const last = this.messages[this.messages.length - 1]
            if (last) {
              this.scrollTarget = last.id
            }
          })
        }
      } catch (err) {
        console.error('agent history error', err)
      }
    },
    normalizeHistory(items) {
      if (!Array.isArray(items)) return []
      const stamp = Date.now()
      return items
        .map((item, index) => {
          if (!item) return null
          const rawRole = String(item.role || '').toLowerCase()
          const role = rawRole === 'assistant' ? 'agent' : rawRole
          if (role !== 'user' && role !== 'agent') return null
          const content = String(item.content || '').trim()
          if (!content) return null
          return { id: `history-${stamp}-${index}`, role, content }
        })
        .filter(Boolean)
    },
    goBack() {
      const pages = getCurrentPages()
      if (pages.length > 1) {
        uni.navigateBack()
        return
      }
      uni.switchTab({ url: '/pages/agent/chat' })
    },
    send() {
      const text = this.input.trim()
      if (this.loading) return
      if (!text && !this.pendingImage) return
      if (this.pendingImage) {
        this.sendImageMessage(text)
        return
      }
      this.appendMessage('user', text)
      this.input = ''
      this.fetchReplyStream(text)
    },
    handleConfirm() {
      if (this.isComposing) return
      this.send()
    },
    onCompositionStart() {
      this.isComposing = true
    },
    onCompositionEnd() {
      this.isComposing = false
    },
    async sendImageMessage(text) {
      const image = this.pendingImage
      if (!image) return
      this.appendMessage('user', text || '[图片]', { imageUrl: image.path })
      this.input = ''
      this.pendingImage = null
      const agentId = this.appendMessage('agent', '')
      this.loading = true
      try {
        const data = await sendAgentMessageWithImage(text, image.path)
        const reply = this.normalizeReply(data)
        this.updateMessage(agentId, reply)
      } catch (err) {
        console.error('agent image chat error', err)
        this.updateMessage(agentId, '抱歉，智能体暂时无法响应，请稍后再试。')
      } finally {
        this.loading = false
      }
    },
    async fetchReply(text) {
      this.loading = true
      try {
        const data = await sendAgentMessage(text)
        const reply = this.normalizeReply(data)
        this.appendMessage('agent', reply)
      } catch (err) {
        console.error('agent chat error', err)
        this.appendMessage('agent', '抱歉，智能体暂时无法响应，请稍后再试。')
      } finally {
        this.loading = false
      }
    },
    async fetchReplyStream(text) {
      const agentId = this.appendMessage('agent', '')
      if (!this.canStream()) {
        await this.fetchReply(text)
        return
      }
      this.loading = true
      try {
        await this.streamFromModel(text, agentId)
      } catch (err) {
        console.error('agent chat error', err)
        const existing = this.getMessageContent(agentId)
        if (!existing) {
          this.updateMessage(agentId, '抱歉，智能体暂时无法响应，请稍后再试。')
        }
      } finally {
        this.loading = false
      }
    },
    appendMessage(role, content, extra = {}) {
      const id = `msg-${Date.now()}-${Math.random().toString(16).slice(2)}`
      this.messages.push({ id, role, content, ...extra })
      this.$nextTick(() => {
        this.scrollTarget = id
      })
      return id
    },
    updateMessage(id, content) {
      const target = this.messages.find((message) => message.id === id)
      if (target) {
        target.content = content
      }
    },
    chooseImage() {
      if (this.loading) return
      uni.chooseImage({
        count: 1,
        sizeType: ['compressed'],
        success: (res) => {
          const path = res.tempFilePaths && res.tempFilePaths[0]
          if (!path) return
          const file = res.tempFiles && res.tempFiles[0]
          this.pendingImage = { path, name: file?.name || '' }
        }
      })
    },
    clearImage() {
      this.pendingImage = null
    },
    getMessageContent(id) {
      const target = this.messages.find((message) => message.id === id)
      return target ? target.content : ''
    },
    finalizeMessage(id, content) {
      this.updateMessage(id, this.normalizeMessageContent(content))
    },
    isTyping(message) {
      return message.role === 'agent' && !message.content && this.loading
    },
    canStream() {
      return typeof fetch === 'function' && typeof ReadableStream !== 'undefined'
    },
    async streamFromModel(text, agentId) {
      const token = getToken()
      const response = await fetch(`${MODEL_BASE_URL}/api/agent/chat/stream`, {
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
            if (chunk.startsWith(' ')) {
              chunk = chunk.slice(1)
            }
            if (chunk.endsWith('\r')) {
              chunk = chunk.slice(0, -1)
            }
            if (chunk === '[DONE]') {
              this.finalizeMessage(agentId, content)
              return
            }
            if (chunk.startsWith('[ERROR]')) {
              if (content.trim()) {
                this.finalizeMessage(agentId, content)
                return
              }
              throw new Error(chunk)
            }
            content += chunk
            this.updateMessage(agentId, this.normalizeMessageContent(content))
            this.scrollTarget = agentId
          } else if (line.length) {
            const extra = line.endsWith('\r') ? line.slice(0, -1) : line
            content += `\n${extra}`
            this.updateMessage(agentId, this.normalizeMessageContent(content))
            this.scrollTarget = agentId
          }
          lineEnd = buffer.indexOf('\n')
        }
      }
      this.finalizeMessage(agentId, content)
    },
    normalizeReply(payload) {
      if (typeof payload === 'string') return payload
      if (payload && typeof payload.content === 'string') return payload.content
      if (payload && payload.content && typeof payload.content === 'object') {
        return JSON.stringify(payload.content, null, 2)
      }
      if (payload && typeof payload.reply === 'string') return payload.reply
      if (payload && payload.reply && typeof payload.reply === 'object') {
        return JSON.stringify(payload.reply, null, 2)
      }
      if (payload && typeof payload.message === 'string') return payload.message
      if (payload && payload.message && typeof payload.message === 'object') {
        return JSON.stringify(payload.message, null, 2)
      }
      return '已收到请求，但未返回有效内容。'
    },
    getMessageBlocks(rawContent) {
      const text = this.normalizeMessageContent(rawContent)
      if (!text) return []
      const lines = text.replace(/\r\n?/g, '\n').split('\n')
      const blocks = []
      let paragraph = []
      let list = null
      let code = []
      let inCode = false

      const flushParagraph = () => {
        if (!paragraph.length) return
        blocks.push({ type: 'paragraph', text: paragraph.join('\n') })
        paragraph = []
      }
      const flushList = () => {
        if (!list) return
        blocks.push(list)
        list = null
      }
      const flushCode = () => {
        if (!code.length) return
        blocks.push({ type: 'code', text: code.join('\n') })
        code = []
      }

      lines.forEach((rawLine) => {
        const line = rawLine.replace(/\s+$/, '')
        if (line.trim().startsWith('```')) {
          if (inCode) {
            flushCode()
            inCode = false
          } else {
            flushParagraph()
            flushList()
            inCode = true
          }
          return
        }

        if (inCode) {
          code.push(rawLine)
          return
        }

        if (!line.trim()) {
          flushParagraph()
          flushList()
          return
        }

        const headingMatch = line.match(/^(#{1,6})\s+(.+)$/)
        if (headingMatch) {
          flushParagraph()
          flushList()
          blocks.push({ type: 'heading', level: headingMatch[1].length, text: headingMatch[2].trim() })
          return
        }

        const labelHeading = line.match(/^(.{2,24})([:：])$/)
        if (labelHeading) {
          flushParagraph()
          flushList()
          blocks.push({ type: 'heading', level: 2, text: `${labelHeading[1]}${labelHeading[2]}` })
          return
        }

        const sectionMatch = line.match(/^([A-E])\)\s+(.+)$/)
        if (sectionMatch) {
          flushParagraph()
          flushList()
          blocks.push({ type: 'heading', level: 2, text: `${sectionMatch[1]}) ${sectionMatch[2].trim()}` })
          return
        }

        const listMatch = line.match(/^(\s*)([-*•]|\d+[.)])\s+(.+)$/)
        if (listMatch) {
          flushParagraph()
          if (!list) {
            list = { type: 'list', items: [] }
          }
          list.items.push({ marker: listMatch[2], text: listMatch[3].trim() })
          return
        }

        paragraph.push(line)
      })

      if (inCode) {
        flushCode()
      } else {
        flushParagraph()
        flushList()
      }

      return blocks
    },
    getInlineSegments(text) {
      return this.parseInlineSegments(String(text || ''))
    },
    getInlineClass(type) {
      if (type === 'bold') return 'msg-inline-bold'
      if (type === 'italic') return 'msg-inline-italic'
      if (type === 'code') return 'msg-inline-code'
      return 'msg-inline-text'
    },
    parseInlineSegments(text) {
      const segments = []
      let lastIndex = 0
      const codeRegex = /`([^`]+)`/g
      let match
      while ((match = codeRegex.exec(text))) {
        const before = text.slice(lastIndex, match.index)
        segments.push(...this.parseEmphasisSegments(before))
        if (match[1]) {
          segments.push({ type: 'code', text: match[1] })
        }
        lastIndex = match.index + match[0].length
      }
      segments.push(...this.parseEmphasisSegments(text.slice(lastIndex)))
      return segments.length ? segments : [{ type: 'text', text }]
    },
    parseEmphasisSegments(text) {
      const segments = []
      let lastIndex = 0
      const boldRegex = /\*\*([^*]+)\*\*/g
      let match
      while ((match = boldRegex.exec(text))) {
        const before = text.slice(lastIndex, match.index)
        segments.push(...this.parseItalicSegments(before))
        if (match[1]) {
          segments.push({ type: 'bold', text: match[1] })
        }
        lastIndex = match.index + match[0].length
      }
      segments.push(...this.parseItalicSegments(text.slice(lastIndex)))
      return segments
    },
    parseItalicSegments(text) {
      const segments = []
      let lastIndex = 0
      const italicRegex = /\*([^*]+)\*/g
      let match
      while ((match = italicRegex.exec(text))) {
        const before = text.slice(lastIndex, match.index)
        if (before) segments.push(...this.parseLinkSegments(before))
        if (match[1]) {
          segments.push({ type: 'italic', text: match[1] })
        }
        lastIndex = match.index + match[0].length
      }
      const tail = text.slice(lastIndex)
      if (tail) segments.push(...this.parseLinkSegments(tail))
      return segments
    },
    parseLinkSegments(text) {
      const segments = []
      let lastIndex = 0
      const linkRegex = /(https?:\/\/[^\s)]+)(?=\s|$)/g
      let match
      while ((match = linkRegex.exec(text))) {
        const before = text.slice(lastIndex, match.index)
        if (before) segments.push({ type: 'text', text: before })
        segments.push({ type: 'link', text: match[1], href: match[1] })
        lastIndex = match.index + match[1].length
      }
      const tail = text.slice(lastIndex)
      if (tail) segments.push({ type: 'text', text: tail })
      return segments
    },
    normalizeMessageContent(rawContent) {
      if (rawContent === null || rawContent === undefined) return ''
      let text = ''
      if (typeof rawContent === 'object') {
        try {
          text = JSON.stringify(rawContent, null, 2)
        } catch (err) {
          text = String(rawContent)
        }
      } else {
        text = String(rawContent)
      }
      const trimmed = text.trim()
      if ((trimmed.startsWith('"') && trimmed.endsWith('"')) || (trimmed.startsWith("'") && trimmed.endsWith("'"))) {
        try {
          text = JSON.parse(trimmed)
        } catch (err) {
          text = text
        }
      }
      if ((trimmed.startsWith('{') && trimmed.endsWith('}')) || (trimmed.startsWith('[') && trimmed.endsWith(']'))) {
        try {
          const parsed = JSON.parse(trimmed)
          const extracted = this.extractContentFromPayload(parsed)
          if (typeof extracted === 'string' && extracted.trim()) {
            text = extracted
          } else {
            text = JSON.stringify(parsed, null, 2)
          }
        } catch (err) {
          text = text
        }
      }
      if (text.includes('\\n') && !text.includes('\n')) {
        text = text.replace(/\\n/g, '\n')
      }
      if (text.includes('\\t')) {
        text = text.replace(/\\t/g, '    ')
      }
      if (text.includes('\\r') && !text.includes('\r')) {
        text = text.replace(/\\r/g, '')
      }
      if (text.includes('\\*')) {
        text = text.replace(/\\\*/g, '*')
      }
      if (text.includes('\\_')) {
        text = text.replace(/\\_/g, '_')
      }
      text = text.replace(/\bdoc_id:\s*\S+/gi, '')
      text = text.replace(/\bsource_uri:\s*\S+/gi, '')
      text = text.replace(/\s{2,}/g, ' ')
      text = text.replace(/(###\s*)/g, '\n$1')
      text = text.replace(/([。！？])\s*(###)/g, '$1\n$2')
      text = text.replace(/([。！？])\s*(-)/g, '$1\n-')
      text = text.replace(/([。！？])\s*(\d+[.)])/g, '$1\n$2')
      text = text.replace(/([。！？])\s*([A-E]\))/g, '$1\n$2')
      text = text.replace(/([：:])\s*([-*•]|\d+[.)])/g, '$1\n$2')
      return text
    },
    extractContentFromPayload(payload) {
      if (!payload) return ''
      if (typeof payload === 'string') return payload
      if (Array.isArray(payload)) {
        const last = payload[payload.length - 1]
        return this.extractContentFromPayload(last)
      }
      if (typeof payload === 'object') {
        const candidates = ['content', 'reply', 'message', 'text', 'output']
        for (const key of candidates) {
          if (typeof payload[key] === 'string') return payload[key]
        }
        if (payload.data) return this.extractContentFromPayload(payload.data)
      }
      return ''
    },
    openLink(url) {
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
    }
  }
}
</script>

<style scoped>
.page {
  height: 100vh;
  background: #f2f2f4;
  display: flex;
  flex-direction: column;
}

.header {
  display: flex;
  align-items: center;
  gap: 14rpx;
  padding: calc(12rpx + env(safe-area-inset-top)) 20rpx 12rpx;
  background: #ffffff;
  border-bottom: 1rpx solid #e6e7eb;
}

.back {
  width: 60rpx;
  height: 60rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 30rpx;
  background: #f3f4f6;
}

.header-avatar {
  width: 60rpx;
  height: 60rpx;
  border-radius: 18rpx;
}

.header-info {
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.header-name {
  font-size: 28rpx;
  font-weight: 600;
  color: #0c0d0f;
}

.header-status {
  font-size: 22rpx;
  color: #12a150;
}

.message-list {
  flex: 1;
  min-height: 0;
  padding: 16rpx 20rpx 4rpx;
  display: flex;
  flex-direction: column;
}

.message {
  display: flex;
  align-items: flex-start;
  gap: 16rpx;
  max-width: 92%;
}

.message + .message {
  margin-top: 28rpx;
}

.message.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.avatar {
  width: 64rpx;
  height: 64rpx;
  border-radius: 18rpx;
  background: #e6e7eb;
  flex-shrink: 0;
}

.bubble {
  padding: 18rpx 20rpx;
  border-radius: 18rpx;
  background: #ffffff;
  border: 1rpx solid #e6e7eb;
  line-height: 1.5;
  font-size: 26rpx;
  color: #202124;
  max-width: 72%;
  word-break: break-word;
  margin-top: 8rpx;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.message-image {
  width: 320rpx;
  height: 200rpx;
  border-radius: 16rpx;
  background: #f3f4f6;
}

.message.user .bubble {
  background: #8bd16b;
  border-color: #8bd16b;
  color: #0c0d0f;
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
  background: #9aa0a6;
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

.block {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.msg-heading {
  font-size: 28rpx;
  font-weight: 600;
  color: #0c0d0f;
}

.msg-paragraph {
  font-size: 26rpx;
  color: inherit;
  white-space: pre-line;
}

.msg-list {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.msg-list-item {
  display: flex;
  align-items: flex-start;
  gap: 10rpx;
}

.msg-list-bullet {
  font-weight: 600;
  color: inherit;
  line-height: 1.5;
}

.msg-list-text {
  flex: 1;
  white-space: pre-line;
  line-height: 1.5;
}

.msg-code {
  font-family: "SFMono-Regular", "SF Mono", Menlo, Consolas, "Liberation Mono", monospace;
  font-size: 24rpx;
  background: #f3f4f6;
  border-radius: 12rpx;
  padding: 12rpx 14rpx;
  white-space: pre-wrap;
}

.msg-inline-text {
  color: inherit;
}

.msg-inline-bold {
  font-weight: 700;
  color: inherit;
}

.msg-inline-italic {
  font-style: italic;
  color: inherit;
}

.msg-inline-code {
  font-family: "SFMono-Regular", "SF Mono", Menlo, Consolas, "Liberation Mono", monospace;
  font-size: 24rpx;
  background: #eef1f6;
  border-radius: 8rpx;
  padding: 2rpx 6rpx;
}

.msg-link {
  color: #1a5ed7;
  text-decoration: underline;
}

.input-bar {
  display: flex;
  align-items: center;
  gap: 12rpx;
  padding: 12rpx 20rpx calc(12rpx + env(safe-area-inset-bottom));
  background: #ffffff;
  border-top: 1rpx solid #e6e7eb;
}

.image-picker {
  width: 64rpx;
  height: 64rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14rpx;
  border: 1rpx solid #e6e7eb;
  background: #ffffff;
  color: #0c0d0f;
}

.input-preview {
  display: flex;
  align-items: center;
  gap: 12rpx;
  padding: 10rpx 20rpx;
  background: #ffffff;
  border-top: 1rpx solid #e6e7eb;
}

.preview-image {
  width: 80rpx;
  height: 80rpx;
  border-radius: 14rpx;
  background: #f3f4f6;
}

.preview-meta {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.preview-label {
  font-size: 24rpx;
  color: #6a6f78;
}

.preview-name {
  font-size: 24rpx;
  color: #0c0d0f;
}

.preview-remove {
  color: #6a6f78;
}

:deep(.wd-input) {
  flex: 1;
  min-height: 72rpx;
  background: #f3f4f6;
  border-radius: 12rpx;
}
</style>
