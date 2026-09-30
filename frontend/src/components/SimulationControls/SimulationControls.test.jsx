import { fireEvent, render, screen } from '@testing-library/react'
import SimulationControls from './SimulationControls.jsx'

describe('SimulationControls', () => {
  it('commits a typed date immediately and exposes playback controls', () => {
    const onDateChange = vi.fn()
    const onTogglePlaying = vi.fn()
    render(
      <SimulationControls
        timestampMs={Date.UTC(2026, 0, 1, 12)}
        playing
        speed="normal"
        onTogglePlaying={onTogglePlaying}
        onSpeedChange={vi.fn()}
        onDateChange={onDateChange}
        onReset={vi.fn()}
      />,
    )
    fireEvent.input(screen.getByLabelText('Set date & time'), { target: { value: '2030-01-01T12:00' } })
    expect(onDateChange).toHaveBeenCalledOnce()
    expect(new Date(onDateChange.mock.calls[0][0]).getFullYear()).toBe(2030)
    fireEvent.click(screen.getByRole('button', { name: 'Pause' }))
    expect(onTogglePlaying).toHaveBeenCalledOnce()
  })
})
