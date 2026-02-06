'use client'

interface Action {
  action_type: string
  description: string
}

interface AccruedActionsDisplayProps {
  actions: Action[]
}

export default function AccruedActionsDisplay({ actions }: AccruedActionsDisplayProps) {
  if (actions.length === 0) {
    return (
      <div style={{
        backgroundColor: '#0f3460',
        padding: '1.5rem',
        borderRadius: '12px',
        border: '2px solid #e94560'
      }}>
        <div style={{
          fontSize: '1.2rem',
          color: '#ffffff',
          marginBottom: '0.75rem',
          fontWeight: 'bold'
        }}>
          Your Information
        </div>
        <div style={{ color: '#6c7a96' }}>No information yet.</div>
      </div>
    )
  }

  return (
    <div style={{
      backgroundColor: '#0f3460',
      padding: '1.5rem',
      borderRadius: '12px',
      border: '2px solid #e94560'
    }}>
      <div style={{
        fontSize: '1.2rem',
        color: '#ffffff',
        marginBottom: '0.75rem',
        fontWeight: 'bold'
      }}>
        Your Information
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {actions.map((action, index) => (
          <div key={index} style={{ color: '#a8b2d1', lineHeight: '1.6' }}>
            • {action.description}
          </div>
        ))}
      </div>
    </div>
  )
}
