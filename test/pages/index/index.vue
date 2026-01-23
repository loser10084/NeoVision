<template>
	<view class="page">
		<view class="panel">
			<text class="title">MHA 3D Reconstruction</text>
			<view class="row">
				<text class="label">Min: {{minValue}}</text>
				<text class="label">Max: {{maxValue}}</text>
				<text class="label">Iso: {{isoValue}}</text>
			</view>
			<slider v-if="sliderReady" class="slider" :min="minValue" :max="maxValue" :value="isoValue"
				:step="1" @change="onIsoChange"></slider>
			<view class="row">
				<text class="label">Triangles: {{triangleCount}}</text>
				<text class="label">{{status}}</text>
			</view>
			<view class="row">
				<text class="label">Decimate: {{decimateRatio}}%</text>
				<text class="label">Smooth: {{smoothingIterations}}</text>
			</view>
			<slider v-if="sliderReady" class="slider" :min="10" :max="100" :value="decimateRatio" :step="5"
				@change="onDecimateChange"></slider>
			<slider v-if="sliderReady" class="slider" :min="0" :max="30" :value="smoothingIterations" :step="1"
				@change="onSmoothChange"></slider>
		</view>
		<view id="glwrap" class="glcanvas"></view>
		<canvas v-if="!useH5Canvas" id="glcanvas" canvas-id="glcanvas" ref="glcanvas" class="glcanvas"
			@touchstart="onTouchStart" @touchmove="onTouchMove" @touchend="onTouchEnd"></canvas>
	</view>
</template>

<script>
import { marchingCubes } from './marchingCubes.js'
const mat4 = {
	create() {
		const out = new Float32Array(16)
		out[0] = 1
		out[5] = 1
		out[10] = 1
		out[15] = 1
		return out
	},
	identity(out) {
		out[0] = 1
		out[1] = 0
		out[2] = 0
		out[3] = 0
		out[4] = 0
		out[5] = 1
		out[6] = 0
		out[7] = 0
		out[8] = 0
		out[9] = 0
		out[10] = 1
		out[11] = 0
		out[12] = 0
		out[13] = 0
		out[14] = 0
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
	multiply(out, a, b) {
		const a00 = a[0], a01 = a[1], a02 = a[2], a03 = a[3]
		const a10 = a[4], a11 = a[5], a12 = a[6], a13 = a[7]
		const a20 = a[8], a21 = a[9], a22 = a[10], a23 = a[11]
		const a30 = a[12], a31 = a[13], a32 = a[14], a33 = a[15]
		const b00 = b[0], b01 = b[1], b02 = b[2], b03 = b[3]
		const b10 = b[4], b11 = b[5], b12 = b[6], b13 = b[7]
		const b20 = b[8], b21 = b[9], b22 = b[10], b23 = b[11]
		const b30 = b[12], b31 = b[13], b32 = b[14], b33 = b[15]
		out[0] = b00 * a00 + b01 * a10 + b02 * a20 + b03 * a30
		out[1] = b00 * a01 + b01 * a11 + b02 * a21 + b03 * a31
		out[2] = b00 * a02 + b01 * a12 + b02 * a22 + b03 * a32
		out[3] = b00 * a03 + b01 * a13 + b02 * a23 + b03 * a33
		out[4] = b10 * a00 + b11 * a10 + b12 * a20 + b13 * a30
		out[5] = b10 * a01 + b11 * a11 + b12 * a21 + b13 * a31
		out[6] = b10 * a02 + b11 * a12 + b12 * a22 + b13 * a32
		out[7] = b10 * a03 + b11 * a13 + b12 * a23 + b13 * a33
		out[8] = b20 * a00 + b21 * a10 + b22 * a20 + b23 * a30
		out[9] = b20 * a01 + b21 * a11 + b22 * a21 + b23 * a31
		out[10] = b20 * a02 + b21 * a12 + b22 * a22 + b23 * a32
		out[11] = b20 * a03 + b21 * a13 + b22 * a23 + b23 * a33
		out[12] = b30 * a00 + b31 * a10 + b32 * a20 + b33 * a30
		out[13] = b30 * a01 + b31 * a11 + b32 * a21 + b33 * a31
		out[14] = b30 * a02 + b31 * a12 + b32 * a22 + b33 * a32
		out[15] = b30 * a03 + b31 * a13 + b32 * a23 + b33 * a33
		return out
	},
	translate(out, a, v) {
		const x = v[0], y = v[1], z = v[2]
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

function parseHeader(bytes) {
	const lines = []
	let offset = 0
	while (offset < bytes.length) {
		let end = offset
		while (end < bytes.length && bytes[end] !== 10) {
			end++
		}
		const line = String.fromCharCode.apply(null, bytes.slice(offset, end)).trim()
		lines.push(line)
		offset = end + 1
		if (line.indexOf('ElementDataFile') === 0) {
			break
		}
	}
	const header = {}
	lines.forEach((line) => {
		const parts = line.split('=')
		if (parts.length >= 2) {
			header[parts[0].trim()] = parts.slice(1).join('=').trim()
		}
	})
	return { header, dataOffset: offset }
}

async function decompressIfNeeded(header, dataBytes) {
	if (header.CompressedData === 'True') {
		if (typeof DecompressionStream === 'undefined') {
			throw new Error('DecompressionStream not supported')
		}
		const ds = new DecompressionStream('deflate')
		const stream = new Blob([dataBytes]).stream().pipeThrough(ds)
		return await new Response(stream).arrayBuffer()
	}
	return dataBytes.buffer.slice(dataBytes.byteOffset, dataBytes.byteOffset + dataBytes.byteLength)
}

export default {
	data() {
		return {
			minValue: 0,
			maxValue: 0,
			isoValue: 0,
			triangleCount: 0,
			status: 'loading',
			sliderReady: false,
			glReady: false,
			useH5Canvas: false,
			decimateRatio: 30,
			targetTriangleCount: 80000,
			smoothingIterations: 8,
			meshStep: 2
		}
	},
	onReady() {
		this.useH5Canvas = typeof document !== 'undefined'
		this.boot()
	},
	methods: {
		async boot() {
			try {
				await this.$nextTick()
				let canvas = null
				if (typeof document !== 'undefined') {
					const wrap = document.getElementById('glwrap')
					if (wrap) {
						const created = document.createElement('canvas')
						created.id = 'glcanvas-h5'
						created.style.width = '100%'
						created.style.height = '100%'
						created.style.display = 'block'
						wrap.appendChild(created)
						canvas = created
					}
				}
				if (!canvas) {
					canvas = await this.getCanvasNode()
				}
				if (!canvas && typeof document !== 'undefined') {
					canvas = document.getElementById('glcanvas')
				}
				if (!canvas) {
					this.status = 'canvas not found'
					return
				}
				this.status = 'init gl'
				this.initGL(canvas)
				await this.loadMha()
				this.buildMesh()
				this.startRender()
			} catch (err) {
				this.status = err && err.message ? err.message : 'failed'
			}
		},
		initGL(canvas) {
			if (!canvas || typeof canvas.getContext !== 'function') {
				this.status = 'canvas.getContext not available'
				return
			}
			this.bindCanvasEvents(canvas)
			this.resizeCanvas(canvas)
			let gl = null
			const webgl2 = !!canvas.getContext('webgl2', { antialias: true })
			const webgl1 = !!canvas.getContext('webgl', { antialias: true })
			const webglExp = !!canvas.getContext('experimental-webgl', { antialias: true })
			if (webgl2) {
				gl = canvas.getContext('webgl2', { antialias: true })
			} else if (webgl1) {
				gl = canvas.getContext('webgl', { antialias: true, premultipliedAlpha: false })
			} else if (webglExp) {
				gl = canvas.getContext('experimental-webgl', { antialias: true })
			}
			if (!gl) {
				this.glReady = false
				this.status = 'webgl disabled or unsupported'
				return
			}
			this.gl = gl
			this.glReady = true
			const vsSource = `
attribute vec3 a_position;
attribute vec3 a_normal;
uniform mat4 u_mvp;
varying vec3 v_normal;
void main() {
  v_normal = a_normal;
  gl_Position = u_mvp * vec4(a_position, 1.0);
}`
			const fsSource = `
precision mediump float;
varying vec3 v_normal;
uniform vec3 u_color;
uniform vec3 u_lightDir;
void main() {
  vec3 n = normalize(v_normal);
  float d = max(dot(n, normalize(u_lightDir)), 0.15);
  gl_FragColor = vec4(u_color * d, 1.0);
}`
			const program = this.createProgram(gl, vsSource, fsSource)
			if (!program) {
				this.glReady = false
				return
			}
			gl.useProgram(program)
			this.program = program
			this.attribPosition = gl.getAttribLocation(program, 'a_position')
			this.attribNormal = gl.getAttribLocation(program, 'a_normal')
			this.uniformMvp = gl.getUniformLocation(program, 'u_mvp')
			this.uniformColor = gl.getUniformLocation(program, 'u_color')
			this.uniformLightDir = gl.getUniformLocation(program, 'u_lightDir')
			if (this.attribPosition < 0 || this.attribNormal < 0 || !this.uniformMvp || !this.uniformColor || !this.uniformLightDir) {
				this.glReady = false
				this.status = 'shader vars missing'
				return
			}
			this.vertexBuffer = gl.createBuffer()
			this.normalBuffer = gl.createBuffer()
			gl.enable(gl.DEPTH_TEST)
			gl.clearColor(0.1, 0.1, 0.12, 1.0)
			this.rotation = { x: 0.3, y: 0.6 }
			this.zoom = 2.3
			window.addEventListener('resize', () => {
				this.resizeCanvas(canvas)
			})
		},
		createProgram(gl, vsSource, fsSource) {
			const vs = gl.createShader(gl.VERTEX_SHADER)
			gl.shaderSource(vs, vsSource)
			gl.compileShader(vs)
			if (!gl.getShaderParameter(vs, gl.COMPILE_STATUS)) {
				this.status = 'vs error: ' + gl.getShaderInfoLog(vs)
				return null
			}
			const fs = gl.createShader(gl.FRAGMENT_SHADER)
			gl.shaderSource(fs, fsSource)
			gl.compileShader(fs)
			if (!gl.getShaderParameter(fs, gl.COMPILE_STATUS)) {
				this.status = 'fs error: ' + gl.getShaderInfoLog(fs)
				return null
			}
			const program = gl.createProgram()
			gl.attachShader(program, vs)
			gl.attachShader(program, fs)
			gl.linkProgram(program)
			if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
				this.status = 'link error: ' + gl.getProgramInfoLog(program)
				return null
			}
			return program
		},
		async loadMha() {
			this.status = 'loading mha'
			const arrayBuffer = await new Promise((resolve, reject) => {
				uni.request({
					url: '/static/brain.mha',
					responseType: 'arraybuffer',
					success: (res) => resolve(res.data),
					fail: (err) => reject(err)
				})
			})
			const bytes = new Uint8Array(arrayBuffer)
			const { header, dataOffset } = parseHeader(bytes)
			const raw = bytes.slice(dataOffset)
			const decompressed = await decompressIfNeeded(header, raw)
			const dims = header.DimSize.split(' ').map((n) => parseInt(n, 10))
			const expectedVoxels = dims[0] * dims[1] * dims[2]
			const expectedBytes = expectedVoxels * 2
			if (!decompressed || decompressed.byteLength < expectedBytes) {
				this.status = 'data size mismatch'
				return
			}
			let data = null
			if (header.ElementType === 'MET_SHORT') {
				data = new Int16Array(decompressed)
			} else {
				throw new Error('unsupported ElementType')
			}
			if (data.length < expectedVoxels) {
				this.status = 'volume size mismatch'
				return
			}
			this.volume = {
				data,
				dims
			}
			let min = data[0]
			let max = data[0]
			for (let i = 1; i < expectedVoxels; i++) {
				const v = data[i]
				if (v < min) min = v
				if (v > max) max = v
			}
			this.minValue = min
			this.maxValue = max
			this.isoValue = Math.floor(min + (max - min) * 0.1)
			this.sliderReady = true
			this.status = this.glReady ? 'ready' : 'data ready, webgl not ready'
		},
		buildMesh() {
			if (!this.volume) return
			this.status = 'meshing'
			const { data, dims } = this.volume
			const iso = Number(this.isoValue)
			const mesh = marchingCubes(data, dims, iso, this.meshStep)
			const ratio = Math.max(0.1, Math.min(1, this.decimateRatio / 100))
			const decimated = this.decimateIndices(mesh.indices, ratio, this.targetTriangleCount)
			const smoothed = this.smoothingIterations > 0
				? this.smoothMesh(mesh.vertices, decimated, this.smoothingIterations)
				: mesh.vertices
			const normals = this.computeNormals(smoothed, decimated)
			const expanded = this.expandMesh(smoothed, normals, decimated)
			this.triangleCount = decimated.length / 3
			if (this.glReady) {
				const gl = this.gl
				gl.bindBuffer(gl.ARRAY_BUFFER, this.vertexBuffer)
				gl.bufferData(gl.ARRAY_BUFFER, expanded.positions, gl.STATIC_DRAW)
				gl.bindBuffer(gl.ARRAY_BUFFER, this.normalBuffer)
				gl.bufferData(gl.ARRAY_BUFFER, expanded.normals, gl.STATIC_DRAW)
				this.vertexCount = expanded.positions.length / 3
			}
			this.status = this.glReady ? 'ready' : 'data ready, webgl not ready'
		},
		decimateIndices(indices, ratio, targetTriangleCount) {
			if (!indices || indices.length === 0) return new Uint32Array()
			const triCount = indices.length / 3
			let keepRatio = ratio
			if (targetTriangleCount > 0 && triCount > targetTriangleCount) {
				keepRatio = Math.min(keepRatio, targetTriangleCount / triCount)
			}
			if (keepRatio >= 1) return indices
			const keepEvery = Math.max(1, Math.round(1 / keepRatio))
			const out = []
			for (let i = 0; i < indices.length; i += 3 * keepEvery) {
				out.push(indices[i], indices[i + 1], indices[i + 2])
			}
			return new Uint32Array(out)
		},
		smoothMesh(vertices, indices, iterations) {
			const count = vertices.length / 3
			const neighbors = new Array(count)
			for (let i = 0; i < count; i++) neighbors[i] = new Set()
			for (let i = 0; i < indices.length; i += 3) {
				const a = indices[i]
				const b = indices[i + 1]
				const c = indices[i + 2]
				neighbors[a].add(b)
				neighbors[a].add(c)
				neighbors[b].add(a)
				neighbors[b].add(c)
				neighbors[c].add(a)
				neighbors[c].add(b)
			}
			let pos = new Float32Array(vertices)
			let next = new Float32Array(vertices.length)
			const alpha = 0.5
			for (let iter = 0; iter < iterations; iter++) {
				for (let i = 0; i < count; i++) {
					const n = neighbors[i]
					if (!n || n.size === 0) {
						next[i * 3] = pos[i * 3]
						next[i * 3 + 1] = pos[i * 3 + 1]
						next[i * 3 + 2] = pos[i * 3 + 2]
						continue
					}
					let ax = 0
					let ay = 0
					let az = 0
					n.forEach((j) => {
						ax += pos[j * 3]
						ay += pos[j * 3 + 1]
						az += pos[j * 3 + 2]
					})
					const inv = 1 / n.size
					ax *= inv
					ay *= inv
					az *= inv
					const px = pos[i * 3]
					const py = pos[i * 3 + 1]
					const pz = pos[i * 3 + 2]
					next[i * 3] = px * (1 - alpha) + ax * alpha
					next[i * 3 + 1] = py * (1 - alpha) + ay * alpha
					next[i * 3 + 2] = pz * (1 - alpha) + az * alpha
				}
				const tmp = pos
				pos = next
				next = tmp
			}
			return pos
		},
		computeNormals(vertices, indices) {
			const normals = new Float32Array(vertices.length)
			for (let i = 0; i < indices.length; i += 3) {
				const a = indices[i] * 3
				const b = indices[i + 1] * 3
				const c = indices[i + 2] * 3
				const ax = vertices[a], ay = vertices[a + 1], az = vertices[a + 2]
				const bx = vertices[b], by = vertices[b + 1], bz = vertices[b + 2]
				const cx = vertices[c], cy = vertices[c + 1], cz = vertices[c + 2]
				const abx = bx - ax, aby = by - ay, abz = bz - az
				const acx = cx - ax, acy = cy - ay, acz = cz - az
				const nx = aby * acz - abz * acy
				const ny = abz * acx - abx * acz
				const nz = abx * acy - aby * acx
				normals[a] += nx
				normals[a + 1] += ny
				normals[a + 2] += nz
				normals[b] += nx
				normals[b + 1] += ny
				normals[b + 2] += nz
				normals[c] += nx
				normals[c + 1] += ny
				normals[c + 2] += nz
			}
			for (let i = 0; i < normals.length; i += 3) {
				const nx = normals[i]
				const ny = normals[i + 1]
				const nz = normals[i + 2]
				const len = Math.sqrt(nx * nx + ny * ny + nz * nz) || 1
				normals[i] = nx / len
				normals[i + 1] = ny / len
				normals[i + 2] = nz / len
			}
			return normals
		},
		expandMesh(vertices, normals, indices) {
			const positions = new Float32Array(indices.length * 3)
			const norms = new Float32Array(indices.length * 3)
			for (let i = 0; i < indices.length; i++) {
				const idx = indices[i] * 3
				const out = i * 3
				positions[out] = vertices[idx]
				positions[out + 1] = vertices[idx + 1]
				positions[out + 2] = vertices[idx + 2]
				norms[out] = normals[idx]
				norms[out + 1] = normals[idx + 1]
				norms[out + 2] = normals[idx + 2]
			}
			return { positions, normals: norms }
		},
		startRender() {
			if (!this.glReady) return
			const render = () => {
				this.drawScene()
				this.rafId = requestAnimationFrame(render)
			}
			render()
		},
		drawScene() {
			const gl = this.gl
			if (!gl) return
			const canvas = gl.canvas
			gl.viewport(0, 0, canvas.width, canvas.height)
			gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT)
			gl.useProgram(this.program)
			gl.bindBuffer(gl.ARRAY_BUFFER, this.vertexBuffer)
			gl.enableVertexAttribArray(this.attribPosition)
			gl.vertexAttribPointer(this.attribPosition, 3, gl.FLOAT, false, 0, 0)
			gl.bindBuffer(gl.ARRAY_BUFFER, this.normalBuffer)
			gl.enableVertexAttribArray(this.attribNormal)
			gl.vertexAttribPointer(this.attribNormal, 3, gl.FLOAT, false, 0, 0)
			const aspect = canvas.width / canvas.height
			let mvp = mat4.create()
			mat4.perspective(mvp, 0.9, aspect, 0.1, 100)
			mat4.translate(mvp, mvp, [0, 0, -this.zoom])
			mat4.rotateX(mvp, mvp, this.rotation.x)
			mat4.rotateY(mvp, mvp, this.rotation.y)
			gl.uniformMatrix4fv(this.uniformMvp, false, mvp)
			gl.uniform3f(this.uniformColor, 0.78, 0.9, 1.0)
			gl.uniform3f(this.uniformLightDir, 0.4, 0.8, 0.6)
			gl.drawArrays(gl.TRIANGLES, 0, this.vertexCount || 0)
		},
		onIsoChange(e) {
			this.isoValue = Number(e.detail.value)
			this.buildMesh()
		},
		onDecimateChange(e) {
			this.decimateRatio = Number(e.detail.value)
			this.buildMesh()
		},
		onSmoothChange(e) {
			this.smoothingIterations = Number(e.detail.value)
			this.buildMesh()
		},
		onTouchStart(e) {
			this.touchStart = e.touches
		},
		onTouchMove(e) {
			const touches = e.touches
			if (!this.touchStart || touches.length === 0) return
			if (touches.length === 1 && this.touchStart.length === 1) {
				const dx = touches[0].clientX - this.touchStart[0].clientX
				const dy = touches[0].clientY - this.touchStart[0].clientY
				this.rotation.y += dx * 0.01
				this.rotation.x += dy * 0.01
				this.touchStart = touches
			} else if (touches.length === 2 && this.touchStart.length === 2) {
				const d0 = this.distance(this.touchStart[0], this.touchStart[1])
				const d1 = this.distance(touches[0], touches[1])
				const delta = d0 - d1
				this.zoom += delta * 0.005
				this.zoom = Math.min(Math.max(this.zoom, 1.0), 6.0)
				this.touchStart = touches
			}
		},
		onTouchEnd() {
			this.touchStart = null
		},
		distance(a, b) {
			const dx = a.clientX - b.clientX
			const dy = a.clientY - b.clientY
			return Math.sqrt(dx * dx + dy * dy)
		},
		getCanvasNode() {
			return new Promise((resolve) => {
				if (typeof uni === 'undefined' || !uni.createSelectorQuery) {
					resolve(null)
					return
				}
				uni.createSelectorQuery()
					.in(this)
					.select('#glcanvas')
					.node()
					.exec((res) => {
						const node = res && res[0] && res[0].node ? res[0].node : null
						resolve(node)
					})
			})
		},
		resizeCanvas(canvas) {
			const ratio = window.devicePixelRatio || 1
			let width = 0
			let height = 0
			if (canvas.getBoundingClientRect) {
				const rect = canvas.getBoundingClientRect()
				width = rect.width
				height = rect.height
			}
			if (!width || !height) {
				width = window.innerWidth
				height = Math.max(200, window.innerHeight - 140)
			}
			canvas.width = Math.max(1, Math.floor(width * ratio))
			canvas.height = Math.max(1, Math.floor(height * ratio))
			canvas.style.width = width + 'px'
			canvas.style.height = height + 'px'
		},
		bindCanvasEvents(canvas) {
			if (canvas.__binded) return
			canvas.__binded = true
			canvas.addEventListener('touchstart', (e) => this.onTouchStart(e))
			canvas.addEventListener('touchmove', (e) => this.onTouchMove(e))
			canvas.addEventListener('touchend', (e) => this.onTouchEnd(e))
			canvas.addEventListener('mousedown', (e) => {
				this.mouseDown = true
				this.onTouchStart({ touches: [e] })
			})
			canvas.addEventListener('mousemove', (e) => {
				if (!this.mouseDown) return
				this.onTouchMove({ touches: [e] })
			})
			canvas.addEventListener('mouseup', (e) => {
				this.mouseDown = false
				this.onTouchEnd({ touches: [e] })
			})
		}
	}
}
</script>

<style>
.page {
	display: flex;
	flex-direction: column;
	background: #0d0f14;
	height: 100vh;
}

.panel {
	padding: 20rpx 28rpx;
	color: #e9edf3;
	background: linear-gradient(135deg, #1b2230 0%, #0c1018 100%);
}

.title {
	font-size: 32rpx;
	font-weight: 600;
}

.row {
	display: flex;
	flex-direction: row;
	justify-content: space-between;
	margin-top: 10rpx;
}

.label {
	font-size: 24rpx;
	color: #c9d3e4;
}

.slider {
	margin: 10rpx 0 4rpx;
}

.glcanvas {
	flex: 1;
}
</style>
