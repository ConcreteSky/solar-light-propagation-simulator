import { readFile } from 'node:fs/promises'

const catalogUrl = new URL('../../data/celestialBodies.json', import.meta.url)
const catalog = JSON.parse(await readFile(catalogUrl, 'utf8'))
const bodies = catalog.bodies
const ids = bodies.map((body) => body.id)
const uniqueIds = new Set(ids)

if (ids.length !== uniqueIds.size) throw new Error('Catalog contains duplicate body IDs.')
if (bodies.length !== 32) throw new Error(`Expected 32 destination bodies, found ${bodies.length}.`)

for (const body of bodies) {
  if (!body.id || body.id !== body.id.toLowerCase()) throw new Error(`Invalid clickable ID: ${body.id}`)
  if (!Number.isFinite(body.orbit.semimajor_axis_km)) throw new Error(`${body.id} lacks an orbit scale input.`)
  if (!Number.isFinite(body.orbit.eccentricity)) throw new Error(`${body.id} lacks eccentricity.`)
  if (!body.visual?.baseColor) throw new Error(`${body.id} lacks a fallback color.`)
}

const moonCounts = new Map()
for (const moon of bodies.filter((body) => body.type === 'moon')) {
  if (!uniqueIds.has(moon.parent)) throw new Error(`${moon.id} references unknown parent ${moon.parent}.`)
  moonCounts.set(moon.parent, (moonCounts.get(moon.parent) ?? 0) + 1)
}

for (const [parent, count] of moonCounts) {
  if (count > 4) throw new Error(`${parent} has ${count} moons; maximum is 4.`)
}

console.log(`Validated ${bodies.length} unique clickable destination IDs and ${moonCounts.size} moon systems.`)

