import catalog from '../../../data/celestialBodies.json'
import environmentCatalog from '../../../data/solarEnvironment.v1.json'

const environmentById = new Map(environmentCatalog.records.map((record) => [record.id, record]))

export const celestialBodies = catalog.bodies.map((body) => ({
  ...body,
  solarEnvironment: environmentById.get(body.id),
}))

export const sun = {
  id: 'sun',
  name: 'Sun',
  type: 'star',
  parent: null,
  isDestination: false,
  visual: {
    baseColor: '#ffb52e',
    texture: null,
    material: 'emissive-star',
  },
}

