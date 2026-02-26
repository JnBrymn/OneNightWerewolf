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
        overflowX: 'auto',
      }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', color: '#fff' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #2ecc71', textAlign: 'left' }}>
              <th style={{ padding: '0.75rem' }}>Player</th>
              <th style={{ padding: '0.75rem' }}>Original role</th>
              <th style={{ padding: '0.75rem' }}>Final role</th>
              <th style={{ padding: '0.75rem' }}>Votes</th>
              <th style={{ padding: '0.75rem' }}>Died</th>
              <th style={{ padding: '0.75rem' }}>Team</th>
              <th style={{ padding: '0.75rem' }}>Result</th>
            </tr>
          </thead>
          <tbody>
            {players.map(p => {
              const votes = vote_summary[p.player_id] ?? 0
              const teamColor = TEAM_COLORS[p.team] || '#95a5a6'
              const isWinner = p.won
              return (
                <tr
                  key={p.player_id}
                  style={{
                    borderBottom: '1px solid rgba(255,255,255,0.1)',
                    borderLeft: `4px solid ${teamColor}`,
                    backgroundColor: isWinner ? 'rgba(46, 204, 113, 0.15)' : 'transparent',
                  }}
                >
                  <td style={{ padding: '0.75rem', fontWeight: 600 }}>{p.player_name}</td>
                  <td style={{ padding: '0.75rem' }}>{p.initial_role}</td>
                  <td style={{ padding: '0.75rem' }}>{p.current_role}</td>
                  <td style={{ padding: '0.75rem' }}>{votes}{p.died ? ' ☠️' : ''}</td>
                  <td style={{ padding: '0.75rem', color: p.died ? '#e74c3c' : undefined }}>
                    {p.died ? 'Yes' : 'No'}
                  </td>
                  <td style={{ padding: '0.75rem', color: teamColor, textTransform: 'capitalize' }}>
                    {p.team}
                  </td>
                  <td style={{ padding: '0.75rem', color: isWinner ? '#2ecc71' : undefined }}>
                    {isWinner ? '✓ Won' : '—'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
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
