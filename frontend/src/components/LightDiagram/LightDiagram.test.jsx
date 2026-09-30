import { cleanup, render, screen } from '@testing-library/react'
import LightDiagram from './LightDiagram.jsx'
import { airlessPrediction, atmosphericPrediction, makePrediction } from '../../test/fixtures.js'

describe('LightDiagram', () => {
  it('renders the atmospheric configuration from calculated results', () => {
    render(<LightDiagram analysis={atmosphericPrediction} />)
    const diagram = screen.getByRole('img', { name: /atmospheric light interaction/i })
    expect(diagram).toHaveAttribute('data-mode', 'atmospheric')
    expect(screen.getByTestId('atmosphere-boundary')).toBeInTheDocument()
    expect(screen.getByTestId('surface-boundary').tagName).toBe('circle')
    expect(screen.getByTestId('scattered-fan').querySelectorAll('path')).toHaveLength(4)
    expect(screen.getByTestId('transmitted-beam')).toHaveAttribute('data-fraction', '0.700')
    expect(screen.getByText('Transmitted')).toBeInTheDocument()
    expect(screen.getByText('Scattered')).toBeInTheDocument()
    expect(screen.getByTestId('primary-result')).toHaveTextContent('70.0% transmitted')
    expect(screen.getByText('Light-interaction diagram is schematic.')).toBeInTheDocument()
  })

  it('renders an airless surface without an imaginary atmosphere', () => {
    render(<LightDiagram analysis={airlessPrediction} />)
    const diagram = screen.getByRole('img', { name: /airless surface light interaction/i })
    expect(diagram).toHaveAttribute('data-mode', 'airless')
    expect(screen.queryByTestId('atmosphere-boundary')).not.toBeInTheDocument()
    expect(screen.getByTestId('surface-boundary')).toBeInTheDocument()
    expect(screen.getByTestId('reflected-ray')).toBeInTheDocument()
    expect(screen.getByText('Reaches surface')).toBeInTheDocument()
    expect(screen.getByTestId('primary-result')).toHaveTextContent('85.0% reaches surface')
  })

  it('uses validated fractions to control ray prominence', () => {
    const lowInteraction = makePrediction({
      results: {
        ...atmosphericPrediction.results,
        transmitted: 0.2,
        scattered: 0.05,
        absorbed: 0.75,
      },
    })
    const highInteraction = makePrediction({
      results: {
        ...atmosphericPrediction.results,
        transmitted: 0.8,
        scattered: 0.15,
        absorbed: 0.05,
      },
    })
    const { unmount } = render(<LightDiagram analysis={lowInteraction} />)
    const lowTransmissionWidth = Number(screen.getByTestId('transmitted-beam').getAttribute('stroke-width'))
    const lowScatterWidth = Number(screen.getByTestId('scattered-fan').querySelector('path').getAttribute('stroke-width'))
    unmount()
    render(<LightDiagram analysis={highInteraction} />)
    expect(Number(screen.getByTestId('transmitted-beam').getAttribute('stroke-width'))).toBeGreaterThan(lowTransmissionWidth)
    expect(Number(screen.getByTestId('scattered-fan').querySelector('path').getAttribute('stroke-width'))).toBeGreaterThan(lowScatterWidth)
  })

  it.each([
    ['mars', true, '#b94e2c'],
    ['earth', true, '#2f78c4'],
    ['venus', true, '#dfc47e'],
    ['moon', false, '#85817b'],
    ['titan', true, '#c67b32'],
    ['jupiter', true, '#caa77b'],
    ['pluto', true, '#a7927c'],
  ])('renders the %s destination palette without changing its scientific mode', (destination, hasAtmosphere, surfaceColor) => {
    cleanup()
    const analysis = makePrediction({
      destination,
      name: destination[0].toUpperCase() + destination.slice(1),
      hasAtmosphere,
    })
    render(<LightDiagram analysis={analysis} />)
    expect(screen.getByRole('img')).toHaveAttribute('data-mode', hasAtmosphere ? 'atmospheric' : 'airless')
    expect(screen.getByTestId('surface-boundary')).toHaveAttribute('stroke', surfaceColor)
    expect(Boolean(screen.queryByTestId('atmosphere-boundary'))).toBe(hasAtmosphere)
  })

  it('contains no SVG animation primitives', () => {
    const { container } = render(<LightDiagram analysis={atmosphericPrediction} />)
    expect(container.querySelectorAll('animate, animateMotion, animateTransform')).toHaveLength(0)
  })
})
