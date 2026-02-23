'use client'

interface PlayerResult {
  player_id: string
  player_name: string
  initial_role: string
  current_role: string
  team: string
  died: boolean
  won: boolean
}

interface ResultsDisplayProps {
  deaths: string[]
  winning_team: string
  players: PlayerResult[]
  vote_summary: { [playerId: string]: number }
  onPlayAgain?: () => void
  onEndSet?: () => void
}

const TEAM_COLORS: { [key: string]: string } = {
  village: '#2ecc71',
  werewolf: '#e74c3c',
  tanner: '#9b59b6',
  minion: '#e67e22',
}

export default function ResultsDisplay({
  deaths,
  winning_team,
  players,
  vote_summary,
  onPlayAgain,
  onEndSet,
}: ResultsDisplayProps) {
  const winnerText =
    winning_team === 'village'
      ? 'VILLAGE WINS!'
      : winning_team === 'werewolf'
        ? 'WEREWOLVES WIN!'
        : winning_team === 'tanner'
          ? 'TANNER WINS!'
          : 'MINION WINS!'

  return (
    <main style={{
      padding: '2rem',
      fontFamily: 'Arial, sans-serif',
      maxWidth: '900px',
      margin: '0 auto',
      minHeight: '100vh',
      backgroundColor: '#1a1a2e',
      color: '#fff',
    }}>
      <h1 style={{ textAlign: 'center', marginBottom: '1.5rem' }}>Results</h1>

      <div style={{
        textAlign: 'center',
        fontSize: '1.75rem',
        fontWeight: 'bold',
        marginBottom: '2rem',
        padding: '1rem',
        borderRadius: '12px',
        backgroundColor: winning_team === 'village' ? 'rgba(46, 204, 113, 0.2)' : winning_team === 'werewolf' ? 'rgba(231, 76, 60, 0.2)' : 'rgba(155, 89, 182, 0.2)',
        color: TEAM_COLORS[winning_team] || '#fff',
      }}>
        {winnerText}
      </div>

      {deaths.length > 0 && (
        <div style={{ marginBottom: '1.5rem', color: '#e74c3c' }}>
          <strong>Eliminated:</strong>{' '}
          {deaths.map(pid => {
            const p = players.find(x => x.player_id === pid)
            return p ? p.player_name : pid
          }).join(', ')}
        </div>
      )}

      <div style={{
        backgroundColor: '#16213e',
        padding: '1.5rem',
        borderRadius: '12px',
        marginBottom: '1.5rem',
      }}>
        <div style={{ fontWeight: 'bold', marginBottom: '0.75rem' }}>Vote counts</div>
        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {players.map(p => (
            <li key={p.player_id} style={{ marginBottom: '0.5rem' }}>
              {p.player_name}: {vote_summary[p.player_id] ?? 0} vote(s)
              {p.died && ' ☠️'}
            </li>
          ))}
        </ul>
      </div>

      <div style={{
        backgroundColor: '#16213e',
        padding: '1.5rem',
        borderRadius: '12px',
        marginBottom: '1.5rem',
      }}>
        <div style={{ fontWeight: 'bold', marginBottom: '0.75rem' }}>Players</div>
        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {players.map(p => (
            <li
              key={p.player_id}
              style={{
                marginBottom: '0.75rem',
                padding: '0.5rem',
                borderRadius: '8px',
                borderLeft: `4px solid ${TEAM_COLORS[p.team] || '#95a5a6'}`,
                backgroundColor: p.won ? 'rgba(46, 204, 113, 0.1)' : 'transparent',
              }}
            >
              <strong>{p.player_name}</strong> — {p.current_role}
              {p.died && ' (died)'} {p.won && ' ✓ Won'}
            </li>
          ))}
        </ul>
      </div>

      <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
        {onPlayAgain && (
          <button
            type="button"
            onClick={onPlayAgain}
            style={{
              padding: '0.75rem 1.5rem',
              fontSize: '1rem',
              backgroundColor: '#3498db',
              color: '#fff',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
            }}
          >
            Play Another Game
          </button>
        )}
        {onEndSet && (
          <button
            type="button"
            onClick={onEndSet}
            style={{
              padding: '0.75rem 1.5rem',
              fontSize: '1rem',
              backgroundColor: '#7f8c8d',
              color: '#fff',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
            }}
          >
            End Game Set
          </button>
        )}
      </div>
    </main>
  )
}
