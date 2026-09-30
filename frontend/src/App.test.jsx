import { fireEvent, render, screen } from '@testing-library/react'
import { getLightResult } from './services/api.js'
import { atmosphericPrediction } from './test/fixtures.js'
import App from './App.jsx'

vi.mock('./components/SolarSystem/SolarSystemScene.jsx', () => ({
  default: ({ onSelectBody }) => (
    <button type="button" onClick={() => onSelectBody('mars')}>Select Mars in map</button>
  ),
}))
vi.mock('./services/api.js', () => ({ getLightResult: vi.fn() }))

describe('App destination integration', () => {
  it('connects map selection to the single analysis section', async () => {
    getLightResult.mockResolvedValue(atmosphericPrediction)
    render(<App />)
    fireEvent.click(screen.getByRole('button', { name: 'Select Mars in map' }))
    expect(await screen.findByRole('heading', { name: 'Mars' })).toBeInTheDocument()
    expect(document.querySelector('.analysis-section')).toBeInTheDocument()
    expect(document.querySelectorAll('.analysis-section')).toHaveLength(1)
  })
})
