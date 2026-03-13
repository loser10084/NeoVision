<template>
  <view class="page">
    <view class="safe-area">
      <view class="card">
        <view class="section-title">3D重建</view>
        <view class="tips">
          <text>手势：拖动旋转，滚轮/双指缩放。</text>
        </view>
      </view>

      <view class="card">
        <view class="section-title">三维查看</view>
        <view id="glwrap" class="gl-wrap">
          <!-- #ifdef APP-PLUS -->
          <web-view class="gl-webview" :src="appWebViewSrc" />
          <!-- #endif -->

          <!-- #ifndef APP-PLUS -->
          <view v-if="!runtimeSupported" class="placeholder">
            <text>
              当前端不支持直接创建 WebGL 画布，请在 H5 或 WebView 中查看。
            </text>
          </view>
          <view v-else-if="!glReady" class="placeholder">
            <text>{{ statusText }}</text>
          </view>
          <!-- #endif -->
        </view>

        <view class="controls">
          <view class="control-row">
            <text class="label">阈值</text>
            <slider
              :value="thresholdPercent"
              :min="0"
              :max="100"
              :step="1"
              activeColor="#0f1012"
              backgroundColor="#d6e5f7"
              @changing="updateThresholdPreview"
              @change="updateThreshold"
            />
            <text class="value">{{ thresholdValueDisplay }}</text>
          </view>
          <view class="control-row">
            <text class="label">点大小</text>
            <slider
              :value="pointSize"
              :min="1"
              :max="6"
              :step="1"
              activeColor="#0f1012"
              backgroundColor="#d6e5f7"
              @change="updatePointSize"
            />
            <text class="value">{{ pointSize }}</text>
          </view>
          <view class="control-row">
            <text class="label">不透明度</text>
            <slider
              :value="brainAlphaPercent"
              :min="5"
              :max="60"
              :step="1"
              activeColor="#0f1012"
              backgroundColor="#d6e5f7"
              @change="updateBrainAlpha"
            />
            <text class="value">{{ brainAlphaPercent }}%</text>
          </view>
          <view class="control-row">
            <text class="label">最大点数</text>
            <slider
              :value="maxPoints"
              :min="20000"
              :max="400000"
              :step="20000"
              activeColor="#0f1012"
              backgroundColor="#d6e5f7"
              @change="updateMaxPoints"
            />
            <text class="value">{{ maxPoints }}</text>
          </view>
          <view class="action-bar">
            <wd-button shape="round" type="default" plain class="action-btn" @click="rebuildPoints" :disabled="!volume">
              重建
            </wd-button>
            <wd-button shape="round" type="default" plain class="action-btn" @click="resetView" :disabled="!glReady">
              重置视角
            </wd-button>
          </view>
        </view>
      </view>

    </view>
  </view>
</template>

<script>
import { getModel } from '../../common/api'
import { resolveModelUrl, resolveStudyResourceUrl, getEffectiveServiceUrls, getToken } from '../../common/request'

const NRRD_TYPES = {
  'uchar': { bytes: 1, ctor: Uint8Array },
  'unsigned char': { bytes: 1, ctor: Uint8Array },
  'uint8': { bytes: 1, ctor: Uint8Array },
  'int8': { bytes: 1, ctor: Int8Array },
  'short': { bytes: 2, ctor: Int16Array },
  'short int': { bytes: 2, ctor: Int16Array },
  'int16': { bytes: 2, ctor: Int16Array },
  'ushort': { bytes: 2, ctor: Uint16Array },
  'unsigned short': { bytes: 2, ctor: Uint16Array },
  'uint16': { bytes: 2, ctor: Uint16Array },
  'int': { bytes: 4, ctor: Int32Array },
  'int32': { bytes: 4, ctor: Int32Array },
  'uint': { bytes: 4, ctor: Uint32Array },
  'uint32': { bytes: 4, ctor: Uint32Array },
  'float': { bytes: 4, ctor: Float32Array },
  'double': { bytes: 8, ctor: Float64Array }
}

const DEFAULT_NRRD = '/static/VSD.Brain.XX.O.MR_Flair.54193_1.nrrd'

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value))
}

const mat4 = {
  create() {
    const out = new Float32Array(16)
    out[0] = 1
    out[5] = 1
    out[10] = 1
    out[15] = 1
    return out
  },
  perspective(out, fovy, aspect, near, far) {
    const f = 1.0 / Math.tan(fovy / 2)
    const nf = 1 / (near - far)
    out[0] = f / aspect
    out[1] = 0
    out[2] = 0
    out[3] = 0
    out[4] = 0
    out[5] = f
    out[6] = 0
    out[7] = 0
    out[8] = 0
    out[9] = 0
    out[10] = (far + near) * nf
    out[11] = -1
    out[12] = 0
    out[13] = 0
    out[14] = (2 * far * near) * nf
    out[15] = 0
    return out
  },
  translate(out, a, v) {
    const x = v[0]
    const y = v[1]
    const z = v[2]
    if (a === out) {
      out[12] = a[0] * x + a[4] * y + a[8] * z + a[12]
      out[13] = a[1] * x + a[5] * y + a[9] * z + a[13]
      out[14] = a[2] * x + a[6] * y + a[10] * z + a[14]
      out[15] = a[3] * x + a[7] * y + a[11] * z + a[15]
    } else {
      const a00 = a[0], a01 = a[1], a02 = a[2], a03 = a[3]
      const a10 = a[4], a11 = a[5], a12 = a[6], a13 = a[7]
      const a20 = a[8], a21 = a[9], a22 = a[10], a23 = a[11]
      out[0] = a00
      out[1] = a01
      out[2] = a02
      out[3] = a03
      out[4] = a10
      out[5] = a11
      out[6] = a12
      out[7] = a13
      out[8] = a20
      out[9] = a21
      out[10] = a22
      out[11] = a23
      out[12] = a00 * x + a10 * y + a20 * z + a[12]
      out[13] = a01 * x + a11 * y + a21 * z + a[13]
      out[14] = a02 * x + a12 * y + a22 * z + a[14]
      out[15] = a03 * x + a13 * y + a23 * z + a[15]
    }
    return out
  },
  rotateX(out, a, rad) {
    const s = Math.sin(rad)
    const c = Math.cos(rad)
    const a10 = a[4], a11 = a[5], a12 = a[6], a13 = a[7]
    const a20 = a[8], a21 = a[9], a22 = a[10], a23 = a[11]
    if (a !== out) {
      out[0] = a[0]
      out[1] = a[1]
      out[2] = a[2]
      out[3] = a[3]
      out[12] = a[12]
      out[13] = a[13]
      out[14] = a[14]
      out[15] = a[15]
    }
    out[4] = a10 * c + a20 * s
    out[5] = a11 * c + a21 * s
    out[6] = a12 * c + a22 * s
    out[7] = a13 * c + a23 * s
    out[8] = a20 * c - a10 * s
    out[9] = a21 * c - a11 * s
    out[10] = a22 * c - a12 * s
    out[11] = a23 * c - a13 * s
    return out
  },
  rotateY(out, a, rad) {
    const s = Math.sin(rad)
    const c = Math.cos(rad)
    const a00 = a[0], a01 = a[1], a02 = a[2], a03 = a[3]
    const a20 = a[8], a21 = a[9], a22 = a[10], a23 = a[11]
    if (a !== out) {
      out[4] = a[4]
      out[5] = a[5]
      out[6] = a[6]
      out[7] = a[7]
      out[12] = a[12]
      out[13] = a[13]
      out[14] = a[14]
      out[15] = a[15]
    }
    out[0] = a00 * c - a20 * s
    out[1] = a01 * c - a21 * s
    out[2] = a02 * c - a22 * s
    out[3] = a03 * c - a23 * s
    out[8] = a00 * s + a20 * c
    out[9] = a01 * s + a21 * c
    out[10] = a02 * s + a22 * c
    out[11] = a03 * s + a23 * c
    return out
  }
}

function findNrrdHeaderEnd(bytes) {
  for (let i = 0; i < bytes.length - 1; i += 1) {
    if (bytes[i] === 10 && bytes[i + 1] === 10) return i + 2
    if (i < bytes.length - 3 && bytes[i] === 13 && bytes[i + 1] === 10 && bytes[i + 2] === 13 && bytes[i + 3] === 10) {
      return i + 4
    }
  }
  return -1
}

function parseNrrdHeader(text) {
  const header = {}
  const lines = text.split(/\r?\n/)
  lines.forEach((line, index) => {
    const trimmed = line.trim()
    if (!trimmed || trimmed.startsWith('#')) return
    if (index === 0 && trimmed.startsWith('NRRD')) {
      header._magic = trimmed
      return
    }
    const sep = trimmed.indexOf(':')
    if (sep < 0) return
    const key = trimmed.slice(0, sep).trim().toLowerCase()
    const value = trimmed.slice(sep + 1).trim()
    header[key] = value
  })
  return header
}

function isLittleEndianSystem() {
  return new Uint8Array(new Uint16Array([1]).buffer)[0] === 1
}

function swapBytesInPlace(bytes, bytesPerElement, elementCount) {
  for (let i = 0; i < elementCount; i += 1) {
    const offset = i * bytesPerElement
    for (let j = 0; j < bytesPerElement / 2; j += 1) {
      const a = offset + j
      const b = offset + bytesPerElement - 1 - j
      const tmp = bytes[a]
      bytes[a] = bytes[b]
      bytes[b] = tmp
    }
  }
}

const LENGTH_BASE = [
  3, 4, 5, 6, 7, 8, 9, 10,
  11, 13, 15, 17, 19, 23, 27, 31,
  35, 43, 51, 59, 67, 83, 99, 115,
  131, 163, 195, 227, 258
]
const LENGTH_EXTRA = [
  0, 0, 0, 0, 0, 0, 0, 0,
  1, 1, 1, 1, 2, 2, 2, 2,
  3, 3, 3, 3, 4, 4, 4, 4,
  5, 5, 5, 5, 0
]
const DIST_BASE = [
  1, 2, 3, 4, 5, 7, 9, 13,
  17, 25, 33, 49, 65, 97, 129, 193,
  257, 385, 513, 769, 1025, 1537, 2049, 3073,
  4097, 6145, 8193, 12289, 16385, 24577
]
const DIST_EXTRA = [
  0, 0, 0, 0, 1, 1, 2, 2,
  3, 3, 4, 4, 5, 5, 6, 6,
  7, 7, 8, 8, 9, 9, 10, 10,
  11, 11, 12, 12, 13, 13
]
const CODE_LENGTH_ORDER = [16, 17, 18, 0, 8, 7, 9, 6, 10, 5, 11, 4, 12, 3, 13, 2, 14, 1, 15]

function reverseBits(value, bitCount) {
  let result = 0
  let v = value
  for (let i = 0; i < bitCount; i += 1) {
    result = (result << 1) | (v & 1)
    v >>>= 1
  }
  return result
}

function buildHuffmanTable(lengths) {
  let maxLen = 0
  for (let i = 0; i < lengths.length; i += 1) {
    if (lengths[i] > maxLen) maxLen = lengths[i]
  }
  const size = 1 << maxLen
  const table = new Int32Array(size)
  const count = new Int32Array(maxLen + 1)
  for (let i = 0; i < lengths.length; i += 1) {
    count[lengths[i]] += 1
  }
  const next = new Int32Array(maxLen + 1)
  let code = 0
  count[0] = 0
  for (let i = 1; i <= maxLen; i += 1) {
    code = (code + count[i - 1]) << 1
    next[i] = code
  }
  for (let sym = 0; sym < lengths.length; sym += 1) {
    const len = lengths[sym]
    if (len === 0) continue
    const codeVal = next[len]++
    const rev = reverseBits(codeVal, len)
    const step = 1 << len
    for (let i = rev; i < size; i += step) {
      table[i] = sym | (len << 16)
    }
  }
  return { table, max: maxLen, mask: size - 1 }
}

const FIXED_LIT_LENGTHS = (() => {
  const lengths = new Array(288)
  for (let i = 0; i <= 143; i += 1) lengths[i] = 8
  for (let i = 144; i <= 255; i += 1) lengths[i] = 9
  for (let i = 256; i <= 279; i += 1) lengths[i] = 7
  for (let i = 280; i <= 287; i += 1) lengths[i] = 8
  return lengths
})()
const FIXED_LIT_TABLE = buildHuffmanTable(FIXED_LIT_LENGTHS)
const FIXED_DIST_TABLE = buildHuffmanTable(new Array(32).fill(5))

function inflateRaw(data) {
  let pos = 0
  let bitbuf = 0
  let bitcnt = 0
  let out = new Uint8Array(1024)
  let outPos = 0

  function ensureBits(count) {
    while (bitcnt < count) {
      if (pos >= data.length) throw new Error('Unexpected EOF')
      bitbuf |= data[pos++] << bitcnt
      bitcnt += 8
    }
  }

  function readBits(count) {
    ensureBits(count)
    const value = bitbuf & ((1 << count) - 1)
    bitbuf >>>= count
    bitcnt -= count
    return value
  }

  function alignByte() {
    bitbuf = 0
    bitcnt = 0
  }

  function pushByte(value) {
    if (outPos >= out.length) {
      const next = new Uint8Array(out.length * 2)
      next.set(out)
      out = next
    }
    out[outPos++] = value
  }

  function copyFromDistance(distance, length) {
    let start = outPos - distance
    for (let i = 0; i < length; i += 1) {
      pushByte(out[start + i])
    }
  }

  function decodeSymbol(table) {
    ensureBits(table.max)
    const value = table.table[bitbuf & table.mask]
    const symbol = value & 0xffff
    const len = value >>> 16
    if (!len) throw new Error('Invalid Huffman code')
    bitbuf >>>= len
    bitcnt -= len
    return symbol
  }

  let finalBlock = false
  while (!finalBlock) {
    finalBlock = readBits(1) === 1
    const blockType = readBits(2)
    if (blockType === 0) {
      alignByte()
      if (pos + 4 > data.length) throw new Error('Unexpected EOF')
      const len = data[pos] | (data[pos + 1] << 8)
      const nlen = data[pos + 2] | (data[pos + 3] << 8)
      pos += 4
      if ((len ^ 0xffff) !== nlen) throw new Error('Stored block length mismatch')
      if (pos + len > data.length) throw new Error('Unexpected EOF')
      for (let i = 0; i < len; i += 1) {
        pushByte(data[pos++])
      }
      continue
    }
    let litTable = FIXED_LIT_TABLE
    let distTable = FIXED_DIST_TABLE
    if (blockType === 2) {
      const hlit = readBits(5) + 257
      const hdist = readBits(5) + 1
      const hclen = readBits(4) + 4
      const codeLengths = new Array(19).fill(0)
      for (let i = 0; i < hclen; i += 1) {
        codeLengths[CODE_LENGTH_ORDER[i]] = readBits(3)
      }
      const codeTable = buildHuffmanTable(codeLengths)
      const lengths = []
      while (lengths.length < hlit + hdist) {
        const sym = decodeSymbol(codeTable)
        if (sym <= 15) {
          lengths.push(sym)
        } else if (sym === 16) {
          const repeat = readBits(2) + 3
          const prev = lengths[lengths.length - 1] || 0
          for (let i = 0; i < repeat; i += 1) lengths.push(prev)
        } else if (sym === 17) {
          const repeat = readBits(3) + 3
          for (let i = 0; i < repeat; i += 1) lengths.push(0)
        } else if (sym === 18) {
          const repeat = readBits(7) + 11
          for (let i = 0; i < repeat; i += 1) lengths.push(0)
        } else {
          throw new Error('Invalid code length symbol')
        }
      }
      litTable = buildHuffmanTable(lengths.slice(0, hlit))
      const distLengths = lengths.slice(hlit)
      if (distLengths.length === 0) distLengths.push(0)
      distTable = buildHuffmanTable(distLengths)
    } else if (blockType !== 1) {
      throw new Error('Unsupported block type')
    }
    while (true) {
      const sym = decodeSymbol(litTable)
      if (sym < 256) {
        pushByte(sym)
      } else if (sym === 256) {
        break
      } else {
        const lenIndex = sym - 257
        if (lenIndex < 0 || lenIndex >= LENGTH_BASE.length) {
          throw new Error('Invalid length symbol')
        }
        const length = LENGTH_BASE[lenIndex] + readBits(LENGTH_EXTRA[lenIndex])
        const distSym = decodeSymbol(distTable)
        if (distSym < 0 || distSym >= DIST_BASE.length) {
          throw new Error('Invalid distance symbol')
        }
        const distance = DIST_BASE[distSym] + readBits(DIST_EXTRA[distSym])
        copyFromDistance(distance, length)
      }
    }
  }
  return out.subarray(0, outPos)
}

export default {
  data() {
    return {
      studyId: '',
      viewMode: 'both',
      modelInfo: {},
      modelUrl: '',
      labelUrl: '',
      heatmapUrl: '',
      sourceLabel: '-',
      appWebViewSrc: '',
      runtimeSupported: false,
      statusText: 'Idle',
      loading: false,
      glReady: false,
      gl: null,
      canvas: null,
      program: null,
      pointBuffer: null,
      volume: null,
      labelVolume: null,
      pointCount: 0,
      dims: [0, 0, 0],
      minValue: '-',
      maxValue: '-',
      thresholdPercent: 5,
      thresholdValue: 0,
      pointSize: 4,
      maxPoints: 300000,
      brainAlpha: 0.25,
      brainAlphaPercent: 25,
      rotationX: 0.3,
      rotationY: 0.6,
      zoom: 2.8,
      dragging: false,
      lastX: 0,
      lastY: 0,
      lastPinch: 0,
      renderPending: false,
      resizeHandler: null,
      inputHandlers: [],
      autoLoaded: false
    }
  },
  computed: {
    dimsText() {
      return this.dims.some((d) => d > 0) ? this.dims.join(' x ') : '-'
    },
    voxelCount() {
      if (!this.dims.some((d) => d > 0)) return '-'
      return this.dims.reduce((acc, v) => acc * v, 1)
    },
    thresholdValueDisplay() {
      if (!this.volume) return '-'
      return this.thresholdValue.toFixed(2)
    }
  },
  async onLoad(query) {
    this.studyId = query.studyId || ''
    this.viewMode = String(query.view || query.mode || 'both').toLowerCase()
    // #ifdef APP-PLUS
    this.appWebViewSrc = this.buildAppWebViewSrc(query)
    return
    // #endif
    if (this.studyId) {
      await this.fetchModel()
      return
    }
    this.modelUrl = this.normalizeIncomingUrl(query.volumeUrl || query.modelUrl || '')
    this.labelUrl = this.normalizeIncomingUrl(query.labelUrl || '')
    this.heatmapUrl = this.normalizeIncomingUrl(query.heatmapUrl || '')
    this.applyViewMode()
  },
  onReady() {
    // #ifndef APP-PLUS
    this.initViewer()
    // #endif
  },
  onUnload() {
    // #ifndef APP-PLUS
    this.disposeViewer()
    // #endif
  },
  methods: {
    async fetchModel() {
      try {
        this.modelInfo = await getModel(this.studyId)
        this.modelUrl = this.resolveModelUrl()
        this.labelUrl = this.resolveLabelUrl()
        this.heatmapUrl = this.resolveHeatmapUrl()
        this.applyViewMode()
        this.autoLoadIfReady()
      } catch (err) {
        console.error('getModel error', err)
      }
    },
    applyViewMode() {
      const mode = this.viewMode || 'both'
      if (mode === 'volume') {
        this.labelUrl = ''
        return
      }
      if (mode === 'label') {
        if (!this.labelUrl) {
          this.modelUrl = ''
          this.setStatus('暂无 Label 数据')
          return
        }
        this.modelUrl = this.labelUrl
        this.labelUrl = ''
      }
    },
    resolveModelUrl() {
      const candidates = [
        'volumeUrl',
        'volumePath',
        'nrrdUrl',
        'nrrdPath',
        'modelPath',
        'filePath',
        'url'
      ]
      const raw = candidates.map((key) => this.modelInfo?.[key]).find(Boolean)
      if (!raw) return ''
      if (/^https?:\/\//i.test(raw)) return raw
      return resolveStudyResourceUrl(raw)
    },
    resolveLabelUrl() {
      const candidates = ['labelUrl', 'labelPath', 'maskUrl', 'maskPath']
      const raw = candidates.map((key) => this.modelInfo?.[key]).find(Boolean)
      if (!raw) return ''
      if (/^https?:\/\//i.test(raw)) return raw
      return resolveStudyResourceUrl(raw)
    },
    resolveHeatmapUrl() {
      const candidates = ['heatmapUrl', 'heatmapPath', 'confidenceMap']
      const raw = candidates.map((key) => this.modelInfo?.[key]).find(Boolean)
      if (!raw) return ''
      if (/^https?:\/\//i.test(raw)) return raw
      return resolveStudyResourceUrl(raw)
    },
    normalizeIncomingUrl(raw) {
      const target = this.decodeIncomingUrl(raw)
      if (!target) return ''
      if (/^https?:\/\//i.test(target)) return target
      return resolveModelUrl(target)
    },
    decodeIncomingUrl(raw) {
      let value = String(raw || '').trim()
      if (!value) return ''
      for (let i = 0; i < 3; i += 1) {
        let decoded = value
        try {
          decoded = decodeURIComponent(value)
        } catch (err) {
          decoded = value
        }
        if (!decoded || decoded === value) break
        value = decoded
        if (/^https?:\/\//i.test(value)) break
      }
      if (/^https?:%2f%2f/i.test(value)) {
        try {
          value = decodeURIComponent(value)
        } catch (err) {}
      }
      if (/^https?:%2f%2f/i.test(value)) {
        value = value.replace(/^(https?):%2f%2f/i, '$1://')
      }
      value = value.replace(/^(https?):\/(?!\/)/i, '$1://')
      return value
    },
    autoLoadIfReady() {
      if (!this.runtimeSupported || !this.glReady || this.autoLoaded) return
      if (!this.modelUrl) return
      this.autoLoaded = true
      this.loadFromModel()
    },
    setStatus(message) {
      this.statusText = message
    },
    getRuntimeWindow() {
      if (typeof window !== 'undefined') return window
      if (typeof globalThis !== 'undefined') return globalThis
      return null
    },
    buildAppWebViewSrc(query = {}) {
      const urls = getEffectiveServiceUrls()
      const token = getToken() || ''
      const volumeUrl = this.decodeIncomingUrl(query.volumeUrl || query.modelUrl || '')
      const labelUrl = this.decodeIncomingUrl(query.labelUrl || '')
      const heatmapUrl = this.decodeIncomingUrl(query.heatmapUrl || '')
      const payload = {
        studyId: query.studyId || this.studyId || '',
        view: query.view || query.mode || this.viewMode || 'both',
        volumeUrl,
        labelUrl,
        heatmapUrl,
        gatewayUrl: urls.gatewayUrl || '',
        modelUrl: urls.modelUrl || '',
        token
      }
      const queryString = Object.keys(payload)
        .filter((key) => payload[key] !== undefined && payload[key] !== null && String(payload[key]) !== '')
        .map((key) => encodeURIComponent(key) + '=' + encodeURIComponent(String(payload[key])))
        .join('&')
      return queryString ? '/hybrid/html/model-viewer/index.html?' + queryString : '/hybrid/html/model-viewer/index.html'
    },
    initViewer() {
      // #ifdef H5
      this.runtimeSupported = true
      // #endif
      // #ifdef APP-PLUS
      this.runtimeSupported = true
      // #endif
      if (!this.runtimeSupported) {
        this.setStatus('\u5f53\u524d\u5e73\u53f0\u4e0d\u652f\u6301 WebGL')
        return
      }
      if (typeof document === 'undefined') {
        this.setStatus('\u5f53\u524d\u8fd0\u884c\u73af\u5883\u4e0d\u652f\u6301 3D \u753b\u5e03')
        return
      }
      this.$nextTick(() => {
        this.createCanvas()
        this.initWebGL()
        this.attachEvents()
        this.resizeCanvas()
        this.render()
        if (!this.studyId) {
          this.loadSample()
        }
      })
    },
    disposeViewer() {
      const runtimeWindow = this.getRuntimeWindow()
      if (this.resizeHandler && runtimeWindow) {
        runtimeWindow.removeEventListener('resize', this.resizeHandler)
      }
      this.inputHandlers.forEach(({ type, handler }) => {
        if (this.canvas) {
          this.canvas.removeEventListener(type, handler)
        }
      })
      this.inputHandlers = []
      if (this.gl) {
        this.gl = null
      }
      this.canvas = null
    },
    createCanvas() {
      const wrap = document.getElementById('glwrap')
      if (!wrap) return
      wrap.innerHTML = ''
      const canvas = document.createElement('canvas')
      canvas.className = 'gl-canvas'
      wrap.appendChild(canvas)
      this.canvas = canvas
    },
    initWebGL() {
      if (!this.canvas) return
      const gl = this.canvas.getContext('webgl', { antialias: true, preserveDrawingBuffer: true })
      if (!gl) {
        this.setStatus('无法创建 WebGL 上下文')
        return
      }
      const vertexShader = this.compileShader(
        gl,
        gl.VERTEX_SHADER,
        `attribute vec3 aPosition;
attribute float aIntensity;
attribute float aLabel;
uniform mat4 uMvp;
uniform float uPointSize;
varying float vIntensity;
varying float vLabel;
void main() {
  gl_Position = uMvp * vec4(aPosition, 1.0);
  gl_PointSize = uPointSize;
  vIntensity = aIntensity;
  vLabel = aLabel;
}`
      )
      const fragmentShader = this.compileShader(
        gl,
        gl.FRAGMENT_SHADER,
        `precision mediump float;
varying float vIntensity;
varying float vLabel;
uniform int uPass;
uniform float uBrainAlpha;
vec3 labelColor(float label) {
  if (label < 1.5) return vec3(1.0, 0.2, 0.2);
  if (label < 2.5) return vec3(0.0, 0.9, 1.0);
  if (label < 3.5) return vec3(1.0, 0.95, 0.0);
  return vec3(0.9, 0.0, 1.0);
}
void main() {
  if (uPass == 1) {
    if (vLabel < 0.5) discard;
    vec3 c = labelColor(vLabel);
    gl_FragColor = vec4(c, 1.0);
  } else {
    if (vLabel > 0.5) discard;
    gl_FragColor = vec4(0.0, 0.0, 0.0, uBrainAlpha);
  }
}`
      )
      if (!vertexShader || !fragmentShader) return
      const program = gl.createProgram()
      gl.attachShader(program, vertexShader)
      gl.attachShader(program, fragmentShader)
      gl.linkProgram(program)
      if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      this.setStatus(`着色器链接失败：${gl.getProgramInfoLog(program)}`)
        return
      }
      gl.useProgram(program)
      gl.enable(gl.DEPTH_TEST)
      gl.depthFunc(gl.LEQUAL)
      gl.enable(gl.BLEND)
      gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA)
      gl.clearColor(0.98, 0.98, 0.99, 1)
      this.gl = gl
      this.program = program
      this.glReady = true
      this.autoLoadIfReady()
      this.setStatus('WebGL 已就绪')
    },
    compileShader(gl, type, source) {
      const shader = gl.createShader(type)
      gl.shaderSource(shader, source)
      gl.compileShader(shader)
      if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
        this.setStatus(`着色器编译失败：${gl.getShaderInfoLog(shader)}`)
        return null
      }
      return shader
    },
    attachEvents() {
      if (!this.canvas) return
      const onMouseDown = (event) => {
        this.dragging = true
        this.lastX = event.clientX
        this.lastY = event.clientY
      }
      const onMouseMove = (event) => {
        if (!this.dragging) return
        const dx = event.clientX - this.lastX
        const dy = event.clientY - this.lastY
        this.lastX = event.clientX
        this.lastY = event.clientY
        this.rotationY += dx * 0.01
        this.rotationX += dy * 0.01
        this.requestRender()
      }
      const onMouseUp = () => {
        this.dragging = false
      }
      const onWheel = (event) => {
        event.preventDefault()
        const delta = Math.sign(event.deltaY)
        this.zoom = clamp(this.zoom + delta * 0.12, 1.0, 6.0)
        this.requestRender()
      }
      const onTouchStart = (event) => {
        event.preventDefault()
        if (event.touches.length === 1) {
          this.dragging = true
          this.lastX = event.touches[0].clientX
          this.lastY = event.touches[0].clientY
        } else if (event.touches.length === 2) {
          this.dragging = false
          this.lastPinch = this.getPinchDistance(event)
        }
      }
      const onTouchMove = (event) => {
        event.preventDefault()
        if (event.touches.length === 1 && this.dragging) {
          const dx = event.touches[0].clientX - this.lastX
          const dy = event.touches[0].clientY - this.lastY
          this.lastX = event.touches[0].clientX
          this.lastY = event.touches[0].clientY
          this.rotationY += dx * 0.01
          this.rotationX += dy * 0.01
          this.requestRender()
        } else if (event.touches.length === 2) {
          const pinch = this.getPinchDistance(event)
          const delta = (this.lastPinch - pinch) * 0.002
          this.zoom = clamp(this.zoom + delta, 1.0, 6.0)
          this.lastPinch = pinch
          this.requestRender()
        }
      }
      const onTouchEnd = () => {
        this.dragging = false
      }
      this.canvas.addEventListener('mousedown', onMouseDown)
      this.canvas.addEventListener('mousemove', onMouseMove)
      this.canvas.addEventListener('mouseup', onMouseUp)
      this.canvas.addEventListener('mouseleave', onMouseUp)
      this.canvas.addEventListener('wheel', onWheel, { passive: false })
      this.canvas.addEventListener('touchstart', onTouchStart, { passive: false })
      this.canvas.addEventListener('touchmove', onTouchMove, { passive: false })
      this.canvas.addEventListener('touchend', onTouchEnd)

      this.inputHandlers = [
        { type: 'mousedown', handler: onMouseDown },
        { type: 'mousemove', handler: onMouseMove },
        { type: 'mouseup', handler: onMouseUp },
        { type: 'mouseleave', handler: onMouseUp },
        { type: 'wheel', handler: onWheel },
        { type: 'touchstart', handler: onTouchStart },
        { type: 'touchmove', handler: onTouchMove },
        { type: 'touchend', handler: onTouchEnd }
      ]

      this.resizeHandler = () => this.resizeCanvas()
      const runtimeWindow = this.getRuntimeWindow()
      if (runtimeWindow) {
        runtimeWindow.addEventListener('resize', this.resizeHandler)
      }
    },
    getPinchDistance(event) {
      const dx = event.touches[0].clientX - event.touches[1].clientX
      const dy = event.touches[0].clientY - event.touches[1].clientY
      return Math.sqrt(dx * dx + dy * dy)
    },
    resizeCanvas() {
      if (!this.canvas || !this.gl) return
      const wrap = document.getElementById('glwrap')
      if (!wrap) return
      const rect = wrap.getBoundingClientRect()
      const runtimeWindow = this.getRuntimeWindow()
      const width = rect.width || runtimeWindow?.innerWidth || 320
      const height = rect.height || 320
      const dpr = runtimeWindow?.devicePixelRatio || 1
      this.canvas.width = width * dpr
      this.canvas.height = height * dpr
      this.canvas.style.width = `${width}px`
      this.canvas.style.height = `${height}px`
      this.gl.viewport(0, 0, this.canvas.width, this.canvas.height)
      this.requestRender()
    },
    requestRender() {
      if (this.renderPending) return
      this.renderPending = true
      const runtimeWindow = this.getRuntimeWindow()
      const raf = runtimeWindow?.requestAnimationFrame || ((cb) => setTimeout(cb, 16))
      raf(() => {
        this.renderPending = false
        this.render()
      })
    },
    render() {
      if (!this.glReady || !this.gl || !this.program) return
      const gl = this.gl
      gl.useProgram(this.program)
      gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT)
      if (!this.pointCount || !this.pointBuffer) return
      gl.bindBuffer(gl.ARRAY_BUFFER, this.pointBuffer)
      const positionLoc = gl.getAttribLocation(this.program, 'aPosition')
      const intensityLoc = gl.getAttribLocation(this.program, 'aIntensity')
      const labelLoc = gl.getAttribLocation(this.program, 'aLabel')
      gl.enableVertexAttribArray(positionLoc)
      gl.vertexAttribPointer(positionLoc, 3, gl.FLOAT, false, 20, 0)
      gl.enableVertexAttribArray(intensityLoc)
      gl.vertexAttribPointer(intensityLoc, 1, gl.FLOAT, false, 20, 12)
      gl.enableVertexAttribArray(labelLoc)
      gl.vertexAttribPointer(labelLoc, 1, gl.FLOAT, false, 20, 16)
      const mvpLoc = gl.getUniformLocation(this.program, 'uMvp')
      const sizeLoc = gl.getUniformLocation(this.program, 'uPointSize')
      const passLoc = gl.getUniformLocation(this.program, 'uPass')
      const brainAlphaLoc = gl.getUniformLocation(this.program, 'uBrainAlpha')
      const aspect = this.canvas.width / this.canvas.height
      const mvp = mat4.create()
      mat4.perspective(mvp, 0.9, aspect, 0.1, 100)
      mat4.translate(mvp, mvp, [0, 0, -this.zoom])
      mat4.rotateX(mvp, mvp, this.rotationX)
      mat4.rotateY(mvp, mvp, this.rotationY)
      gl.uniformMatrix4fv(mvpLoc, false, mvp)
      gl.uniform1f(sizeLoc, Math.max(this.pointSize, 4))
      gl.uniform1f(brainAlphaLoc, this.brainAlpha)
      gl.depthMask(true)
      gl.uniform1i(passLoc, 1)
      gl.drawArrays(gl.POINTS, 0, this.pointCount)
      gl.depthMask(false)
      gl.uniform1i(passLoc, 0)
      gl.drawArrays(gl.POINTS, 0, this.pointCount)
      gl.depthMask(true)
    },
    resetView() {
      this.rotationX = 0.3
      this.rotationY = 0.6
      this.zoom = 2.8
      this.requestRender()
    },
    async loadSample() {
      await this.loadNrrdFromUrl(DEFAULT_NRRD, '示例NRRD')
    },
    async loadFromModel() {
      if (!this.modelUrl) return
      if (this.labelUrl) {
        await this.loadNrrdPair(this.modelUrl, this.labelUrl, '序列NRRD+Label')
        return
      }
      await this.loadNrrdFromUrl(this.modelUrl, '序列NRRD')
    },
    async pickNrrd() {
      if (!this.runtimeSupported) {
        uni.showToast({ title: '当前环境不支持选文件', icon: 'none' })
        return
      }
      const choose = uni.chooseFile || uni.chooseMessageFile
      if (!choose) {
        uni.showToast({ title: '当前环境不支持选文件', icon: 'none' })
        return
      }
      choose({
        count: 1,
        type: 'all',
        success: async (res) => {
          const file = res.tempFiles && res.tempFiles[0]
          if (!file) return
          if (file.file && file.file.arrayBuffer) {
            const buffer = await file.file.arrayBuffer()
              await this.loadNrrdFromBuffer(buffer, file.name || '本地NRRD')
              return
            }
            if (file.path) {
              await this.loadNrrdFromUrl(file.path, file.name || '本地NRRD')
            }
          }
        })
    },
    async loadNrrdFromUrl(url, label) {
      if (!this.runtimeSupported) return
      try {
        this.loading = true
        const targetUrl = this.normalizeUrl(url)
        this.setStatus(`正在加载NRRD...（${targetUrl}）`)
        const buffer = await this.fetchArrayBuffer(targetUrl)
        await this.loadNrrdFromBuffer(buffer, label)
        this.sourceLabel = label
      } catch (err) {
        console.error('loadNrrdFromUrl failed', { url, err })
        this.setStatus(`加载失败：${err.message || err}`)
      } finally {
        this.loading = false
      }
    },
    async loadNrrdFromBuffer(buffer, label) {
      try {
        const volume = await this.parseNrrdBuffer(buffer)
        const { values, dims, min, max } = volume
        this.volume = volume
        this.labelVolume = null
        this.dims = dims
        this.minValue = min.toFixed(2)
        this.maxValue = max.toFixed(2)
        this.thresholdValue = min + 0.1 * (max - min)
        this.thresholdPercent = 10
        this.setStatus('正在构建点云...')
        this.buildPointCloud()
        this.sourceLabel = label
        this.setStatus('渲染就绪')
      } catch (err) {
        console.error('loadNrrdFromBuffer failed', { label, err })
        this.setStatus(`解析失败：${err.message || err}`)
      }
    },
    async loadNrrdPair(flairUrl, labelUrl, label) {
      if (!this.runtimeSupported) return
      try {
        this.loading = true
        const flairTarget = this.normalizeUrl(flairUrl)
        const labelTarget = this.normalizeUrl(labelUrl)
        this.setStatus(`正在加载NRRD...（${flairTarget}）`)
        const [flairBuffer, labelBuffer] = await Promise.all([
          this.fetchArrayBuffer(flairTarget),
          this.fetchArrayBuffer(labelTarget)
        ])
        this.setStatus('正在解析 Flair NRRD...')
        const flairVolume = await this.parseNrrdBuffer(flairBuffer)
        this.setStatus('正在解析 Label NRRD...')
        const labelVolume = await this.parseNrrdBuffer(labelBuffer)
        if (
          flairVolume.dims.length < 3 ||
          labelVolume.dims.length < 3 ||
          flairVolume.dims.some((v, i) => v !== labelVolume.dims[i])
        ) {
          this.setStatus('Label 维度不匹配，仅显示 Flair')
          this.labelVolume = null
        } else {
          this.labelVolume = labelVolume
          this.logLabelStats(labelVolume)
        }
        this.volume = flairVolume
        this.dims = flairVolume.dims
        this.minValue = flairVolume.min.toFixed(2)
        this.maxValue = flairVolume.max.toFixed(2)
        this.thresholdValue = flairVolume.min + 0.1 * (flairVolume.max - flairVolume.min)
        this.thresholdPercent = 10
        this.setStatus('正在构建点云...')
        this.buildPointCloud()
        this.sourceLabel = label
        this.setStatus('渲染就绪')
      } catch (err) {
        console.error('loadNrrdPair failed', { flairUrl, labelUrl, err })
        this.setStatus(`加载失败：${err.message || err}`)
      } finally {
        this.loading = false
      }
    },
    logLabelStats(volume) {
      try {
        const values = volume?.values
        if (!values) return
        let min = Number.POSITIVE_INFINITY
        let max = Number.NEGATIVE_INFINITY
        let nonZero = 0
        for (let i = 0; i < values.length; i += 1) {
          const v = values[i]
          if (v < min) min = v
          if (v > max) max = v
          if (v > 0) nonZero += 1
        }
        console.log('[label] stats', { min, max, nonZero })
      } catch (err) {
        console.error('label stats error', err)
      }
    },
    async fetchArrayBuffer(targetUrl) {
      if (targetUrl.startsWith('blob:')) {
        const response = await fetch(targetUrl)
        if (!response.ok) {
      throw new Error(`请求失败: ${response.status}`)
        }
        return response.arrayBuffer()
      }
      try {
        return await this.requestArrayBuffer(targetUrl)
      } catch (err) {
        console.error('uni.request arraybuffer failed', { url: targetUrl, err })
        const response = await fetch(targetUrl)
        if (!response.ok) {
      throw new Error(`请求失败: ${response.status}`)
        }
        return response.arrayBuffer()
      }
    },
    async parseNrrdBuffer(buffer) {
      this.setStatus('正在解析 NRRD 头...')
      const bytes = new Uint8Array(buffer)
      const headerEnd = findNrrdHeaderEnd(bytes)
      if (headerEnd < 0) {
        throw new Error('Header not found')
      }
      const headerText = new TextDecoder('utf-8').decode(bytes.slice(0, headerEnd))
      const header = parseNrrdHeader(headerText)
      if (!header._magic || !header._magic.startsWith('NRRD')) {
        throw new Error('Invalid NRRD magic')
      }
      const sizeText = header.sizes || header.size || ''
      const sizeTokens = String(sizeText).match(/-?\d+(?:\.\d+)?/g) || []
      const dims = sizeTokens.map((v) => Number(v))
      if (dims.length < 3 || dims.some((v) => Number.isNaN(v))) {
        throw new Error('Invalid sizes')
      }
      const elementType = String(header.type || '').toLowerCase()
      const elementInfo = NRRD_TYPES[elementType]
      if (!elementInfo) {
        throw new Error(`Unsupported NRRD type: ${elementType}`)
      }
      const dataFile = header['data file'] || header.datafile || ''
      if (dataFile && dataFile.toLowerCase() !== 'local') {
        throw new Error('Detached NRRD data is not supported')
      }
      const encoding = String(header.encoding || 'raw').toLowerCase()
      const isAscii = encoding === 'ascii' || encoding === 'txt' || encoding === 'text'
      let payload = bytes.slice(headerEnd)
      if (!isAscii && (encoding === 'gzip' || encoding === 'gz' || encoding === 'deflate')) {
      this.setStatus('正在解压 NRRD 数据...')
        payload = await this.decompress(payload)
      } else if (!isAscii && encoding !== 'raw') {
        throw new Error(`Unsupported NRRD encoding: ${encoding}`)
      }
      const expectedVoxels = dims[0] * dims[1] * dims[2]
      if (isAscii) {
        const text = new TextDecoder('utf-8').decode(payload)
        const tokens = text.trim().split(/\s+/)
        if (tokens.length < expectedVoxels) {
          throw new Error(`Payload length mismatch: ${tokens.length} < ${expectedVoxels}`)
        }
        const typed = new elementInfo.ctor(expectedVoxels)
        for (let i = 0; i < expectedVoxels; i += 1) {
          typed[i] = Number(tokens[i])
        }
        const values = typed
        let min = Number.POSITIVE_INFINITY
        let max = Number.NEGATIVE_INFINITY
        for (let i = 0; i < values.length; i += 1) {
          const v = values[i]
          if (v < min) min = v
          if (v > max) max = v
        }
        return { values, dims, min, max }
      }
      const expectedBytes = expectedVoxels * elementInfo.bytes
      if (payload.byteLength < expectedBytes) {
        throw new Error(`Payload length mismatch: ${payload.byteLength} < ${expectedBytes}`)
      }
      const endian = String(header.endian || 'little').toLowerCase()
      const littleEndian = isLittleEndianSystem()
      let payloadView = payload.slice(0, expectedBytes)
      if (elementInfo.bytes > 1 && endian === 'big' && littleEndian) {
        swapBytesInPlace(payloadView, elementInfo.bytes, expectedVoxels)
      } else if (elementInfo.bytes > 1 && endian === 'little' && !littleEndian) {
        swapBytesInPlace(payloadView, elementInfo.bytes, expectedVoxels)
      }
      const typed = new elementInfo.ctor(
        payloadView.buffer,
        payloadView.byteOffset,
        expectedVoxels
      )
      const values = typed
      let min = Number.POSITIVE_INFINITY
      let max = Number.NEGATIVE_INFINITY
      for (let i = 0; i < values.length; i += 1) {
        const v = values[i]
        if (v < min) min = v
        if (v > max) max = v
      }
      return { values, dims, min, max }
    },
    requestArrayBuffer(url) {
      return new Promise((resolve, reject) => {
        uni.request({
          url,
          method: 'GET',
          responseType: 'arraybuffer',
          success: (res) => {
            if (res.statusCode >= 200 && res.statusCode < 300) {
              resolve(res.data)
              return
            }
            console.error('uni.request non-2xx', { url, statusCode: res.statusCode })
            reject(new Error(`HTTP ${res.statusCode}`))
          },
          fail: (err) => {
            console.error('uni.request failed', { url, err })
            reject(err)
          }
        })
      })
    },
    normalizeUrl(url) {
      if (!url) return ''
      if (/^https?:\/\//i.test(url) || url.startsWith('blob:')) return url
      const runtimeWindow = this.getRuntimeWindow()
      const base = runtimeWindow?.location?.origin || ''
      if (!base) return url
      if (url.startsWith('/')) return `${base}${url}`
      return `${base}/${url}`
    },
    async decompress(payload) {
      if (typeof DecompressionStream !== 'undefined') {
        const formats = ['deflate', 'gzip']
        for (let i = 0; i < formats.length; i += 1) {
          try {
            const stream = new Response(
              new Blob([payload]).stream().pipeThrough(new DecompressionStream(formats[i]))
            )
            const buffer = await stream.arrayBuffer()
            return new Uint8Array(buffer)
          } catch (err) {
            // ignore and fallback to next decoder
          }
        }
      }
      try {
        return inflateRaw(payload)
      } catch (err) {
        throw new Error(`\u89e3\u538b\u5931\u8d25: ${err?.message || err}`)
      }
    },
    buildPointCloud() {
      if (!this.volume || !this.glReady) return
      const { values, dims, min, max } = this.volume
      const labelVolume = this.labelVolume
      const labelValues = labelVolume?.values
      const hasLabel = Boolean(labelValues && labelVolume?.dims?.every((v, i) => v === dims[i]))
      const total = values.length
      const threshold = this.thresholdValue
      let above = 0
      let labelCount = 0
      for (let i = 0; i < total; i += 1) {
        if (values[i] > threshold) above += 1
        if (hasLabel && labelValues[i] > 0) labelCount += 1
      }
      const labelBudget = Math.max(Math.floor(this.maxPoints * 0.25), 20000)
      const labelStride = labelCount > labelBudget ? Math.ceil(labelCount / labelBudget) : 1
      const labelTarget = Math.ceil(labelCount / labelStride)
      const brainBudget = Math.max(this.maxPoints - labelTarget, Math.floor(this.maxPoints * 0.5))
      const brainStride = above > brainBudget ? Math.ceil(above / brainBudget) : 1
      const targetCount = Math.ceil(above / brainStride) + labelTarget
      const data = new Float32Array(targetCount * 5)
      const maxDim = Math.max(dims[0], dims[1], dims[2])
      const scaleX = dims[0] / maxDim
      const scaleY = dims[1] / maxDim
      const scaleZ = dims[2] / maxDim
      const slice = dims[0] * dims[1]
      let seen = 0
      let seenLabel = 0
      let write = 0
      const range = max - min || 1
      const dx = Math.max(dims[0] - 1, 1)
      const dy = Math.max(dims[1] - 1, 1)
      const dz = Math.max(dims[2] - 1, 1)
      for (let i = 0; i < total; i += 1) {
        const v = values[i]
        if (v > threshold) {
          if (seen % brainStride === 0) {
            const z = Math.floor(i / slice)
            const rem = i - z * slice
            const y = Math.floor(rem / dims[0])
            const x = rem - y * dims[0]
            const nx = (x / dx - 0.5) * scaleX
            const ny = (y / dy - 0.5) * scaleY
            const nz = (z / dz - 0.5) * scaleZ
            data[write] = nx
            data[write + 1] = -ny
            data[write + 2] = nz
            data[write + 3] = (v - min) / range
            data[write + 4] = 0
            write += 5
          }
          seen += 1
        }
        if (hasLabel && labelValues[i] > 0) {
          if (seenLabel % labelStride === 0) {
            const z = Math.floor(i / slice)
            const rem = i - z * slice
            const y = Math.floor(rem / dims[0])
            const x = rem - y * dims[0]
            const nx = (x / dx - 0.5) * scaleX
            const ny = (y / dy - 0.5) * scaleY
            const nz = (z / dz - 0.5) * scaleZ
            data[write] = nx
            data[write + 1] = -ny
            data[write + 2] = nz
            data[write + 3] = 1
            data[write + 4] = labelValues[i]
            write += 5
          }
          seenLabel += 1
        }
      }
      this.pointCount = write / 5
      const gl = this.gl
      if (!this.pointBuffer) {
        this.pointBuffer = gl.createBuffer()
      }
      gl.bindBuffer(gl.ARRAY_BUFFER, this.pointBuffer)
      gl.bufferData(gl.ARRAY_BUFFER, data.subarray(0, write), gl.STATIC_DRAW)
      const positionLoc = gl.getAttribLocation(this.program, 'aPosition')
      const intensityLoc = gl.getAttribLocation(this.program, 'aIntensity')
      const labelLoc = gl.getAttribLocation(this.program, 'aLabel')
      gl.enableVertexAttribArray(positionLoc)
      gl.vertexAttribPointer(positionLoc, 3, gl.FLOAT, false, 20, 0)
      gl.enableVertexAttribArray(intensityLoc)
      gl.vertexAttribPointer(intensityLoc, 1, gl.FLOAT, false, 20, 12)
      gl.enableVertexAttribArray(labelLoc)
      gl.vertexAttribPointer(labelLoc, 1, gl.FLOAT, false, 20, 16)
      this.requestRender()
    },
    updateThresholdPreview(event) {
      this.thresholdPercent = Number(event.detail.value)
      if (!this.volume) return
      const { min, max } = this.volume
      this.thresholdValue = min + (this.thresholdPercent / 100) * (max - min)
    },
    updateThreshold(event) {
      this.updateThresholdPreview(event)
      this.buildPointCloud()
    },
    updatePointSize(event) {
      this.pointSize = Number(event.detail.value)
      this.requestRender()
    },
    updateBrainAlpha(event) {
      this.brainAlphaPercent = Number(event.detail.value)
      this.brainAlpha = this.brainAlphaPercent / 100
      this.requestRender()
    },
    updateMaxPoints(event) {
      this.maxPoints = Number(event.detail.value)
      this.buildPointCloud()
    },
    rebuildPoints() {
      this.buildPointCloud()
    }
  }
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: #edf4ff;
}

.gl-webview {
  width: 100%;
  height: 100%;
}

.gl-wrap {
  position: relative;
  width: 100%;
  height: 520rpx;
  border-radius: 24rpx;
  border: 1rpx solid #cfdef4;
  background: radial-gradient(circle at top, #ffffff 0%, #eef4ff 50%, #e6f0ff 100%);
  overflow: hidden;
}

.gl-canvas {
  width: 100%;
  height: 100%;
  display: block;
}


.placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 24rpx;
  color: #627d9f;
}

.controls {
  margin-top: 16rpx;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.control-row {
  display: grid;
  grid-template-columns: 140rpx 1fr 120rpx;
  align-items: center;
  gap: 12rpx;
  color: #111318;
  font-size: 26rpx;
}

.label {
  font-weight: 600;
}

.value {
  text-align: right;
  color: #5e616a;
}

.tips {
  margin-top: 10rpx;
  color: #5e616a;
  font-size: 24rpx;
}

.action-grid,
.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: stretch;
  flex-wrap: wrap;
  gap: 12rpx;
}

.action-btn {
  flex: 1 1 calc(50% - 6rpx);
  min-width: 200rpx;
}

.log {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  color: #5e616a;
  font-size: 24rpx;
}
</style>

