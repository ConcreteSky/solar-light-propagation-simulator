import { fireEvent, render, screen } from '@testing-library/react'
import { celestialBodies } from '../../data/catalog.js'
import CelestialBody from './CelestialBody.jsx'

vi.mock('@react-three/drei', () => ({
  Html: ({ children }) => <div>{children}</div>,
  useTexture: vi.fn(() => ({})),
}))

const earth = celestialBodies.find((body) => body.id === 'earth')

describe('CelestialBody', () => {
  it('allows the visible destination label to select its body', () => {
    const onSelect = vi.fn()
    render(
      <CelestialBody
        body={earth}
        position={[0, 0, 0]}
        radius={1.5}
        selected={false}
        showLabel
        onSelect={onSelect}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Select Earth' }))

    expect(onSelect).toHaveBeenCalledOnce()
    expect(onSelect).toHaveBeenCalledWith('earth')
  })
})
