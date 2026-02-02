'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'

export default function JoinGame() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const gameSetIdFromUrl = searchParams.get('game_set_id')

  const [gameSetId, setGameSetId] = useState(gameSetIdFromUrl || '')
  const [playerName, setPlayerName] = useState('')
  const [avatarUrl, setAvatarUrl] = useState('')
  const [error, setError] = useState('')
  const [isJoining, setIsJoining] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!gameSetId.trim()) {
      setError('Please enter a game code')
      return
    }

    if (!playerName.trim()) {
      setError('Please enter your name')
      return
    }

    setIsJoining(true)
    try {
      // First, create the player
      const playerResponse = await fetch('/api/players', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          player_name: playerName.trim(),
          avatar_url: avatarUrl.trim() || null
        })
      })

      if (!playerResponse.ok) {
        throw new Error('Failed to create player')
      }

      const playerData = await playerResponse.json()
      const playerId = playerData.player_id

      // Store player ID in sessionStorage (unique per tab)
      sessionStorage.setItem('player_id', playerId)
      sessionStorage.setItem('player_name', playerName.trim())

      // Then join the game set
      const joinResponse = await fetch(`/api/game-sets/${gameSetId}/players/${playerId}/join`, {
        method: 'POST'
      })

      if (!joinResponse.ok) {
        const errorData = await joinResponse.json()
        throw new Error(errorData.detail || 'Failed to join game')
      }

      // Redirect to lobby with player_id in URL
      router.push(`/lobby/${gameSetId}?player_id=${playerId}`)
    } catch (err: any) {
      setError(err.message || 'Failed to join game')
      setIsJoining(false)
    }
  }

  return (
    <main style={{
      padding: '2rem',
      fontFamily: 'Arial, sans-serif',
      maxWidth: '600px',
      margin: '0 auto'
    }}>
      <h1 style={{ fontSize: '2rem', marginBottom: '2rem', color: '#2c3e50' }}>
        Join Game
      </h1>

      {gameSetIdFromUrl && (
        <div style={{
          padding: '1rem',
          backgroundColor: '#d1ecf1',
          color: '#0c5460',
          borderRadius: '4px',
          marginBottom: '1.5rem'
        }}>
          ✓ You're joining a game! Just enter your name below.
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {!gameSetIdFromUrl && (
          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              Game Code *
            </label>
            <input
              type="text"
              value={gameSetId}
              onChange={(e) => setGameSetId(e.target.value)}
              placeholder="Enter game code..."
              style={{
                width: '100%',
                padding: '0.75rem',
                fontSize: '1rem',
                border: '2px solid #ced4da',
                borderRadius: '4px'
              }}
            />
            <small style={{ color: '#7f8c8d' }}>
              Get this from the player who created the game
            </small>
          </div>
        )}

        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
            Your Name *
          </label>
          <input
            type="text"
            value={playerName}
            onChange={(e) => setPlayerName(e.target.value)}
            placeholder="Enter your name..."
            maxLength={50}
            style={{
              width: '100%',
              padding: '0.75rem',
              fontSize: '1rem',
              border: '2px solid #ced4da',
              borderRadius: '4px'
            }}
          />
        </div>

        <div style={{ marginBottom: '2rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
            Avatar URL (optional)
          </label>
          <input
            type="url"
            value={avatarUrl}
            onChange={(e) => setAvatarUrl(e.target.value)}
            placeholder="https://example.com/avatar.jpg"
            style={{
              width: '100%',
              padding: '0.75rem',
              fontSize: '1rem',
              border: '2px solid #ced4da',
              borderRadius: '4px'
            }}
          />
        </div>

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

        <div style={{ display: 'flex', gap: '1rem' }}>
          <button
            type="submit"
            disabled={isJoining}
            style={{
              padding: '1rem 2rem',
              fontSize: '1.2rem',
              cursor: isJoining ? 'not-allowed' : 'pointer',
              backgroundColor: isJoining ? '#95a5a6' : '#2ecc71',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontWeight: 'bold',
              flex: 1
            }}
          >
            {isJoining ? 'Joining...' : 'Join Game'}
          </button>

          <button
            type="button"
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
            Cancel
          </button>
        </div>
      </form>
    </main>
  )
}
