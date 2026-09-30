import { act, fireEvent, render, screen } from '@testing-library/react'
import { celestialBodies } from '../../data/catalog.js'
import { getLightResult, getScenarioLightResult } from '../../services/api.js'
import { atmosphericPrediction, fallbackPrediction, makePrediction } from '../../test/fixtures.js'
import ResultPanel from './ResultPanel.jsx'

vi.mock('../../services/api.js', () => ({ getLightResult: vi.fn(), getScenarioLightResult: vi.fn() }))

const mars = celestialBodies.find((body) => body.id === 'mars')
const venus = celestialBodies.find((body) => body.id === 'venus')

describe('ResultPanel', () => {
  it('renders destination results, units, and the ML method', async () => {
    getLightResult.mockResolvedValue(atmosphericPrediction)
    render(<ResultPanel body={mars} bodies={celestialBodies} />)
    expect(screen.getByRole('status')).toHaveTextContent('Analyzing Mars')
    expect(await screen.findByRole('heading', { name: 'Mars' })).toBeInTheDocument()
    expect(screen.getByText('Validated ML prediction')).toBeInTheDocument()
    expect(screen.getByText('227,900,000 km')).toBeInTheDocument()
    expect(screen.getByText('760.2 s')).toBeInTheDocument()
    expect(screen.getByText('588.6 W/m²')).toBeInTheDocument()
    expect(screen.getByText('70.0%')).toBeInTheDocument()
    expect(screen.getByText('blue · modeled')).toBeInTheDocument()
  })

  it('recalculates Scenario Mode through the deterministic endpoint', async () => {
    getLightResult.mockResolvedValue(atmosphericPrediction)
    getScenarioLightResult.mockResolvedValue(makePrediction({
      method: undefined,
      results: {
        ...atmosphericPrediction.results,
        scatteredLightColor: {
          label: 'cyan', rgb: [137, 205, 218], spectralBand: 'blue-green-visible',
          confidence: 'supported', basis: 'methane-red-absorption',
        },
      },
    }))
    render(<ResultPanel body={mars} bodies={celestialBodies} />)
    await screen.findByRole('heading', { name: 'Mars' })
    screen.getByText('Scenario Mode').click()
    fireEvent.change(screen.getByLabelText('CH4 fraction'), { target: { value: '0.02' } })
    fireEvent.click(screen.getByText('Recalculate scenario'))
    expect(await screen.findByText('Deterministic scenario')).toBeInTheDocument()
    expect(getScenarioLightResult).toHaveBeenCalledWith(
      'mars',
      expect.objectContaining({ composition: expect.objectContaining({ CH4: expect.any(Number) }) }),
      expect.any(Object),
    )
  })

  it('labels backend deterministic fallback explicitly', async () => {
    getLightResult.mockResolvedValue(fallbackPrediction)
    render(<ResultPanel body={mars} bodies={celestialBodies} />)
    expect(await screen.findByText('Deterministic fallback')).toBeInTheDocument()
    expect(screen.getByTestId('analysis-warning')).toHaveTextContent('missing pressure')
  })

  it('displays unavailable reference measurements honestly', async () => {
    const incompleteBody = {
      ...mars,
      id: 'incomplete',
      name: 'Incomplete',
      light_reference: {
        ...mars.light_reference,
        solar_irradiance_w_m2: null,
        light_travel_time_seconds: null,
      },
    }
    getLightResult.mockResolvedValue(makePrediction({ destination: 'incomplete', name: 'Incomplete' }))
    render(<ResultPanel body={incompleteBody} bodies={celestialBodies} />)
    expect(await screen.findByRole('heading', { name: 'Incomplete' })).toBeInTheDocument()
    expect(screen.getAllByText('Data unavailable')).toHaveLength(2)
  })

  it('shows a clean invalid-destination error', async () => {
    getLightResult.mockRejectedValue(Object.assign(new Error('missing'), { status: 404 }))
    render(<ResultPanel body={mars} bodies={celestialBodies} />)
    expect(await screen.findByRole('alert')).toHaveTextContent('selected destination was not found')
  })

  it('prevents an older response from replacing a newer selection', async () => {
    let resolveMars
    let resolveVenus
    getLightResult.mockImplementation((id) => new Promise((resolve) => {
      if (id === 'mars') resolveMars = resolve
      if (id === 'venus') resolveVenus = resolve
    }))

    const { rerender } = render(<ResultPanel body={mars} bodies={celestialBodies} />)
    rerender(<ResultPanel body={venus} bodies={celestialBodies} />)
    await act(async () => {
      resolveVenus(makePrediction({ destination: 'venus', name: 'Venus' }))
    })
    expect(screen.getByRole('heading', { name: 'Venus' })).toBeInTheDocument()

    await act(async () => {
      resolveMars(atmosphericPrediction)
    })
    expect(screen.getByRole('heading', { name: 'Venus' })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Mars' })).not.toBeInTheDocument()
  })

  it('clears a completed result safely when the scene selection is removed', async () => {
    getLightResult.mockResolvedValue(atmosphericPrediction)
    const { rerender } = render(<ResultPanel body={mars} bodies={celestialBodies} />)
    expect(await screen.findByRole('heading', { name: 'Mars' })).toBeInTheDocument()

    rerender(<ResultPanel body={null} bodies={celestialBodies} />)

    expect(screen.getByRole('heading', { name: 'Choose a destination' })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Mars' })).not.toBeInTheDocument()
  })
})
