import catalog from '../../../data/celestialBodies.json'

export const celestialBodies = catalog.bodies

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

