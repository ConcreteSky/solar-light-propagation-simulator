import earthTexture from '../assets/textures/earth-simple.svg'
import jupiterTexture from '../assets/textures/jupiter-bands.svg'
import moonTexture from '../assets/textures/moon-craters.svg'

export const textureRegistry = {
  'textures/earth-simple.svg': earthTexture,
  'textures/jupiter-bands.svg': jupiterTexture,
  'textures/moon-craters.svg': moonTexture,
}

export function resolveTexture(textureKey) {
  return textureRegistry[textureKey] ?? null
}

