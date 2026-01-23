function vertexInterp(iso, p1, p2, v1, v2) {
	if (Math.abs(iso - v1) < 0.00001) return p1
	if (Math.abs(iso - v2) < 0.00001) return p2
	if (Math.abs(v1 - v2) < 0.00001) return p1
	const t = (iso - v1) / (v2 - v1)
	return [
		p1[0] + t * (p2[0] - p1[0]),
		p1[1] + t * (p2[1] - p1[1]),
		p1[2] + t * (p2[2] - p1[2])
	]
}

export function marchingCubes(data, dims, iso, step) {
	const dx = dims[0]
	const dy = dims[1]
	const dz = dims[2]
	const sx = (dx - 1) / 2
	const sy = (dy - 1) / 2
	const sz = (dz - 1) / 2
	const inv = 2 / Math.max(dx, dy, dz)
	const vertices = []
	const indices = []
	const vertCache = new Map()

	const indexOf = (x, y, z) => x + y * dx + z * dx * dy
	const toWorld = (x, y, z) => [(x - sx) * inv, (y - sy) * inv, (z - sz) * inv]

	const addVertex = (p) => {
		const key = p[0].toFixed(4) + ',' + p[1].toFixed(4) + ',' + p[2].toFixed(4)
		if (vertCache.has(key)) {
			return vertCache.get(key)
		}
		const idx = vertices.length / 3
		vertices.push(p[0], p[1], p[2])
		vertCache.set(key, idx)
		return idx
	}

	const tets = [
		[0, 5, 1, 6],
		[0, 5, 6, 4],
		[0, 1, 2, 6],
		[0, 2, 3, 6],
		[0, 3, 7, 6],
		[0, 7, 4, 6]
	]

	for (let z = 0; z < dz - step; z += step) {
		for (let y = 0; y < dy - step; y += step) {
			for (let x = 0; x < dx - step; x += step) {
				const p = [
					toWorld(x, y, z),
					toWorld(x + step, y, z),
					toWorld(x + step, y + step, z),
					toWorld(x, y + step, z),
					toWorld(x, y, z + step),
					toWorld(x + step, y, z + step),
					toWorld(x + step, y + step, z + step),
					toWorld(x, y + step, z + step)
				]
				const v = [
					data[indexOf(x, y, z)],
					data[indexOf(x + step, y, z)],
					data[indexOf(x + step, y + step, z)],
					data[indexOf(x, y + step, z)],
					data[indexOf(x, y, z + step)],
					data[indexOf(x + step, y, z + step)],
					data[indexOf(x + step, y + step, z + step)],
					data[indexOf(x, y + step, z + step)]
				]

				for (let t = 0; t < tets.length; t++) {
					const ids = tets[t]
					const tp = [p[ids[0]], p[ids[1]], p[ids[2]], p[ids[3]]]
					const tv = [v[ids[0]], v[ids[1]], v[ids[2]], v[ids[3]]]

					const inside = []
					const outside = []
					for (let i = 0; i < 4; i++) {
						if (tv[i] < iso) inside.push(i)
						else outside.push(i)
					}
					if (inside.length === 0 || inside.length === 4) continue

					if (inside.length === 1) {
						const a = inside[0]
						const b = outside[0]
						const c = outside[1]
						const d = outside[2]
						const p1 = vertexInterp(iso, tp[a], tp[b], tv[a], tv[b])
						const p2 = vertexInterp(iso, tp[a], tp[c], tv[a], tv[c])
						const p3 = vertexInterp(iso, tp[a], tp[d], tv[a], tv[d])
						const i1 = addVertex(p1)
						const i2 = addVertex(p2)
						const i3 = addVertex(p3)
						indices.push(i1, i2, i3)
					} else if (inside.length === 3) {
						const a = outside[0]
						const b = inside[0]
						const c = inside[1]
						const d = inside[2]
						const p1 = vertexInterp(iso, tp[a], tp[b], tv[a], tv[b])
						const p2 = vertexInterp(iso, tp[a], tp[c], tv[a], tv[c])
						const p3 = vertexInterp(iso, tp[a], tp[d], tv[a], tv[d])
						const i1 = addVertex(p1)
						const i2 = addVertex(p2)
						const i3 = addVertex(p3)
						indices.push(i1, i3, i2)
					} else if (inside.length === 2) {
						const a = inside[0]
						const b = inside[1]
						const c = outside[0]
						const d = outside[1]
						const p1 = vertexInterp(iso, tp[a], tp[c], tv[a], tv[c])
						const p2 = vertexInterp(iso, tp[a], tp[d], tv[a], tv[d])
						const p3 = vertexInterp(iso, tp[b], tp[c], tv[b], tv[c])
						const p4 = vertexInterp(iso, tp[b], tp[d], tv[b], tv[d])
						const i1 = addVertex(p1)
						const i2 = addVertex(p2)
						const i3 = addVertex(p3)
						const i4 = addVertex(p4)
						indices.push(i1, i2, i3)
						indices.push(i2, i4, i3)
					}
				}
			}
		}
	}

	return {
		vertices: new Float32Array(vertices),
		indices: new Uint32Array(indices)
	}
}
