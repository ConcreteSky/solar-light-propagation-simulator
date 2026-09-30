const SPEEDS = ['slow', 'normal', 'fast']

function toInputValue(timestampMs) {
  const date = new Date(timestampMs)
  const offsetMs = date.getTimezoneOffset() * 60_000
  return new Date(timestampMs - offsetMs).toISOString().slice(0, 16)
}

export default function SimulationControls({
  timestampMs,
  playing,
  speed,
  onTogglePlaying,
  onSpeedChange,
  onDateChange,
  onReset,
}) {
  const handleDateInput = (event) => {
    const next = new Date(event.currentTarget.value)
    if (!Number.isNaN(next.getTime())) onDateChange(next.getTime())
  }

  return (
    <section className="simulation-controls" aria-label="Simulation time controls">
      <div className="simulation-time">
        <span>Simulated time</span>
        <strong>{new Date(timestampMs).toLocaleString(undefined, { timeZoneName: 'short' })}</strong>
      </div>
      <div className="simulation-actions">
        <button type="button" onClick={onTogglePlaying}>{playing ? 'Pause' : 'Play'}</button>
        {SPEEDS.map((option) => (
          <button
            key={option}
            type="button"
            className={speed === option ? 'active' : ''}
            aria-pressed={speed === option}
            onClick={() => onSpeedChange(option)}
          >
            {option}
          </button>
        ))}
        <button type="button" onClick={onReset}>Reset time</button>
      </div>
      <label className="simulation-date">
        <span>Set date &amp; time</span>
        <input
          type="datetime-local"
          value={toInputValue(timestampMs)}
          onInput={handleDateInput}
        />
      </label>
    </section>
  )
}
