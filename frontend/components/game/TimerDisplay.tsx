'use client'

interface TimerDisplayProps {
  timeRemainingSeconds: number
}

function pad(n: number) {
  return n < 10 ? `0${n}` : String(n)
}

export default function TimerDisplay({ timeRemainingSeconds }: TimerDisplayProps) {
  const mins = Math.floor(timeRemainingSeconds / 60)
  const secs = timeRemainingSeconds % 60
  return (
    <div style={{
      fontSize: '2rem',
      fontWeight: 'bold',
      color: timeRemainingSeconds <= 30 ? '#e74c3c' : '#2ecc71',
      fontVariantNumeric: 'tabular-nums'
    }}>
      {pad(mins)}:{pad(secs)}
    </div>
  )
}
