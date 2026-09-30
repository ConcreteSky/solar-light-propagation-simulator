import { render, screen } from '@testing-library/react'
import LightDiagram from './LightDiagram.jsx'
import { airlessPrediction, atmosphericPrediction } from '../../test/fixtures.js'

describe('LightDiagram', () => {
  it('renders the atmospheric configuration from calculated results', () => {
    render(<LightDiagram analysis={atmosphericPrediction} />)
    const diagram = screen.getByRole('img', { name: /atmospheric light interaction/i })
    expect(diagram).toHaveAttribute('data-mode', 'atmospheric')
    expect(screen.getByTestId('atmosphere-boundary')).toBeInTheDocument()
    expect(screen.getByText('Transmitted')).toBeInTheDocument()
    expect(screen.getByText('Scattered')).toBeInTheDocument()
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
  })
})
