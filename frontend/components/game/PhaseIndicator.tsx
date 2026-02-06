'use client'

interface PhaseIndicatorProps {
  state: string | null
  currentRoleStep?: string | null
}

export default function PhaseIndicator({ state, currentRoleStep }: PhaseIndicatorProps) {
  const getPhaseText = () => {
    if (state === 'NIGHT') {
      return currentRoleStep 
        ? `🌙 Night Phase - ${currentRoleStep} is acting...`
        : '🌙 Night Phase - Waiting to start...'
    } else if (state === 'DAY_DISCUSSION') {
      return '☀️ Day Phase - Discussion'
    } else if (state === 'DAY_VOTING') {
      return '☀️ Day Phase - Voting'
    } else if (state === 'RESULTS') {
      return '🏆 Results'
    }
    return 'Loading...'
  }

  return (
    <div style={{
      fontSize: '1.5rem',
      color: '#e94560',
      marginBottom: '2rem',
      fontWeight: 'bold',
      textTransform: 'uppercase',
      letterSpacing: '0.1em',
      textAlign: 'center'
    }}>
      {getPhaseText()}
    </div>
  )
}
