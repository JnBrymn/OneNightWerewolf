'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'

interface GameSet {
  game_set_id: string
  num_players: number
  selected_roles: string[]
  discussion_timer_seconds: number
  created_at: string
}

interface Player {
  player_id: string
  player_name: string
  avatar_url: string | null
  created_at: string
}

interface PlayersResponse {
  players: Player[]
  current_count: number
  required_count: number
}

export default function Lobby() {
  const router = useRouter()
  const params = useParams()
  const game_set_id = params.game_set_id as string

  const [gameSet, setGameSet] = useState<GameSet | null>(null)
  const [playersData, setPlayersData] = useState<PlayersResponse | null>(null)
  const [error, setError] = useState('')
  const [isStarting, setIsStarting] = useState(false)

  // Get current player ID from localStorage
  const currentPlayerId = typeof window !== 'undefined' ? localStorage.getItem('player_id') : null

  // Fetch game set details
  useEffect(() => {
    async function fetchGameSet() {
      try {
        const response = await fetch(`/api/game-sets/${game_set_id}`)
        if (!response.ok) throw new Error('Failed to fetch game set')
        const data = await response.json()
        setGameSet(data)
      } catch (err: any) {
        setError(err.message)
      }
    }

    if (game_set_id) {
      fetchGameSet()
    }
  }, [game_set_id])

  // Poll for player updates every 2 seconds
  useEffect(() => {
    async function fetchPlayers() {
      try {
        const response = await fetch(`/api/game-sets/${game_set_id}/players`)
        if (!response.ok) throw new Error('Failed to fetch players')
        const data = await response.json()
        setPlayersData(data)
      } catch (err: any) {
        console.error('Error fetching players:', err)
      }
    }

    if (game_set_id) {
      fetchPlayers() // Fetch immediately
      const interval = setInterval(fetchPlayers, 2000) // Then every 2 seconds
      return () => clearInterval(interval)
    }
  }, [game_set_id])

  const handleStartGame = async () => {
    setIsStarting(true)
    setError('')

    try {
      const response = await fetch(`/api/game-sets/${game_set_id}/start`, {
        method: 'POST'
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to start game')
      }

      const data = await response.json()
      // For now, show success message (in Step 4 we'll redirect to game page)
      alert(`Game started! Game ID: ${data.game_id}`)
    } catch (err: any) {
      setError(err.message)
      setIsStarting(false)
    }
  }

  const handleCopyJoinUrl = () => {
    const joinUrl = `${window.location.origin}/join?game_set_id=${game_set_id}`
    navigator.clipboard.writeText(joinUrl)
    alert('Join URL copied to clipboard!')
  }

  if (error && !gameSet) {
    return (
      <main style={{ padding: '2rem', fontFamily: 'Arial, sans-serif', textAlign: 'center' }}>
        <h1 style={{ color: '#e74c3c' }}>Error</h1>
        <p>{error}</p>
        <button
          onClick={() => router.push('/')}
          style={{
            marginTop: '1rem',
            padding: '0.75rem 1.5rem',
            backgroundColor: '#3498db',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Back to Home
        </button>
      </main>
    )
  }

  if (!gameSet || !playersData) {
    return (
      <main style={{ padding: '2rem', fontFamily: 'Arial, sans-serif', textAlign: 'center' }}>
        <h1>Loading...</h1>
      </main>
    )
  }

  const canStartGame = playersData.current_count === playersData.required_count
  const roleCounts: { [key: string]: number } = {}
  gameSet.selected_roles.forEach(role => {
    roleCounts[role] = (roleCounts[role] || 0) + 1
  })

  return (
    <main style={{
      padding: '2rem',
      fontFamily: 'Arial, sans-serif',
      maxWidth: '900px',
      margin: '0 auto'
    }}>
      <h1 style={{ fontSize: '2rem', marginBottom: '2rem', color: '#2c3e50' }}>
        Game Lobby
      </h1>

      {/* Join URL */}
      <div style={{
        backgroundColor: '#e8f5e9',
        padding: '1.5rem',
        borderRadius: '8px',
        marginBottom: '2rem',
        textAlign: 'center'
      }}>
        <h2 style={{ margin: '0 0 0.5rem 0', fontSize: '1rem', color: '#2c6e49' }}>Invite Players</h2>
        <button
          onClick={handleCopyJoinUrl}
          style={{
            padding: '1rem 2rem',
            backgroundColor: '#27ae60',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '1rem',
            fontWeight: 'bold'
          }}
        >
          📋 Copy Join URL
        </button>
        <div style={{ marginTop: '0.75rem' }}>
          <small style={{ color: '#555' }}>Share this URL with other players to let them join</small>
        </div>
      </div>

      {/* Players Section */}
      <div style={{
        backgroundColor: '#f8f9fa',
        padding: '2rem',
        borderRadius: '8px',
        marginBottom: '2rem'
      }}>
        <h2 style={{ marginBottom: '1rem', color: '#34495e' }}>
          Players ({playersData.current_count}/{playersData.required_count})
        </h2>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
          gap: '1rem',
          marginBottom: '1rem'
        }}>
          {playersData.players.map(player => (
            <div
              key={player.player_id}
              style={{
                padding: '1rem',
                backgroundColor: player.player_id === currentPlayerId ? '#d4edda' : 'white',
                borderRadius: '8px',
                border: player.player_id === currentPlayerId ? '2px solid #28a745' : '1px solid #dee2e6',
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem'
              }}
            >
              {player.avatar_url ? (
                <img
                  src={player.avatar_url}
                  alt={player.player_name}
                  style={{
                    width: '40px',
                    height: '40px',
                    borderRadius: '50%',
                    objectFit: 'cover'
                  }}
                />
              ) : (
                <div style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '50%',
                  backgroundColor: '#6c757d',
                  color: 'white',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 'bold',
                  fontSize: '1.2rem'
                }}>
                  {player.player_name.charAt(0).toUpperCase()}
                </div>
              )}
              <div>
                <div style={{ fontWeight: 'bold' }}>
                  {player.player_name}
                  {player.player_id === currentPlayerId && ' (You)'}
                </div>
              </div>
            </div>
          ))}
        </div>

        {!canStartGame && (
          <div style={{
            padding: '1rem',
            backgroundColor: '#fff3cd',
            color: '#856404',
            borderRadius: '4px',
            textAlign: 'center'
          }}>
            Waiting for {playersData.required_count - playersData.current_count} more player(s)...
          </div>
        )}
      </div>

      {/* Game Details */}
      <div style={{
        backgroundColor: '#f8f9fa',
        padding: '2rem',
        borderRadius: '8px',
        marginBottom: '2rem'
      }}>
        <h2 style={{ marginBottom: '1rem', color: '#34495e' }}>Game Settings</h2>

        <div style={{ marginBottom: '1rem' }}>
          <strong>Discussion Time:</strong> {Math.floor(gameSet.discussion_timer_seconds / 60)}:{String(gameSet.discussion_timer_seconds % 60).padStart(2, '0')}
        </div>

        <div>
          <h3 style={{ marginBottom: '0.5rem', fontSize: '1rem' }}>Roles in Game:</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: '0.5rem' }}>
            {Object.entries(roleCounts).map(([role, count]) => (
              <div key={role} style={{
                padding: '0.5rem',
                backgroundColor: '#e9ecef',
                borderRadius: '4px',
                textAlign: 'center',
                fontSize: '0.9rem'
              }}>
                {role} ×{count}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div style={{
          padding: '1rem',
          backgroundColor: '#f8d7da',
          color: '#721c24',
          borderRadius: '4px',
          marginBottom: '1rem'
        }}>
          {error}
        </div>
      )}

      {/* Start Game Button */}
      <div style={{ display: 'flex', gap: '1rem' }}>
        <button
          onClick={handleStartGame}
          disabled={!canStartGame || isStarting}
          style={{
            padding: '1rem 2rem',
            fontSize: '1.2rem',
            cursor: !canStartGame || isStarting ? 'not-allowed' : 'pointer',
            backgroundColor: !canStartGame || isStarting ? '#95a5a6' : '#27ae60',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            fontWeight: 'bold',
            flex: 1
          }}
        >
          {isStarting ? 'Starting...' : canStartGame ? 'Start Game' : 'Waiting for Players...'}
        </button>

        <button
          onClick={() => router.push('/')}
          style={{
            padding: '1rem 2rem',
            fontSize: '1.2rem',
            cursor: 'pointer',
            backgroundColor: '#95a5a6',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            fontWeight: 'bold'
          }}
        >
          Leave
        </button>
      </div>
    </main>
  )
}
