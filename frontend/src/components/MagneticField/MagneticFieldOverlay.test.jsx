import { getMagneticVisualKind, getMagneticVisualScale } from './MagneticFieldOverlay.jsx'
import { celestialBodies } from '../../data/catalog.js'

const environment = (family) => ({ magnetic: { family } })

describe('magnetic visual families', () => {
  it.each([
    'intrinsic_dipole', 'intrinsic_aligned', 'intrinsic_tilted_offset',
    'induced', 'crustal_remnant', 'intrinsic_mini', 'parent_plasma',
  ])('selects a body-specific visual for %s', (family) => {
    expect(getMagneticVisualKind(environment(family))).toBe(family)
  })

  it.each(['unknown', 'negligible'])('does not invent a field visual for %s', (family) => {
    expect(getMagneticVisualKind(environment(family))).toBeNull()
  })

  it('preserves the required special-body mappings', () => {
    const families = Object.fromEntries(celestialBodies.map((body) => [body.id, body.solarEnvironment.magnetic.family]))
    expect(families).toMatchObject({
      venus: 'induced', mars: 'crustal_remnant', moon: 'crustal_remnant',
      uranus: 'intrinsic_tilted_offset', neptune: 'intrinsic_tilted_offset',
      ganymede: 'intrinsic_mini', europa: 'induced', io: 'parent_plasma',
    })
  })

  it('makes an extreme environment larger than a limited one without changing scientific data', () => {
    expect(getMagneticVisualScale({ magnetic: { shielding: 'extreme' } }))
      .toBeGreaterThan(getMagneticVisualScale({ magnetic: { shielding: 'limited' } }))
  })
})
