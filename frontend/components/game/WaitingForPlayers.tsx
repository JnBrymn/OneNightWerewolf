'use client'

interface WaitingForPlayersProps {
  teamColor: string
}

export default function WaitingForPlayers({ teamColor }: WaitingForPlayersProps) {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      padding: '2rem',
      backgroundColor: '#1a1a2e'
    }}>
      <div style={{
        backgroundColor: '#16213e',
        padding: '3rem',
        borderRadius: '16px',
        border: `3px solid ${teamColor}`,
        maxWidth: '600px',
        textAlign: 'center'
      }}>
        <h1 style={{
          color: '#ffffff',
          marginBottom: '1rem',
          fontSize: '2rem'
        }}>
          Getting ready
        </h1>
        <div style={{
          fontSize: '1.2rem',
          color: '#a8b2d1',
          lineHeight: '1.6'
        }}>
          Waiting for all players to acknowledge their roles. The night phase will begin when everyone is ready.
        </div>
      </div>
    </div>
  )
}
