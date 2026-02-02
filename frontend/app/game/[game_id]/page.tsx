'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter, useSearchParams } from 'next/navigation'

interface PlayerRole {
  player_role_id: string
  game_id: string
  player_id: string
  initial_role: string
  current_role: string
  team: string
  was_killed: boolean
}

// Role descriptions to help players understand their role
const ROLE_DESCRIPTIONS: { [key: string]: string } = {
  'Werewolf': 'You are a Werewolf. Wake up and look for other Werewolves. If you are alone, you may view one center card.',
  'Villager': 'You are a Villager. You have no special abilities, but you are on the village team.',
  'Seer': 'You are the Seer. You may look at one other player\'s card, or two center cards.',
  'Robber': 'You are the Robber. You may swap your card with another player and look at your new card.',
  'Troublemaker': 'You are the Troublemaker. You may swap cards between two other players (without looking at them).',
  'Drunk': 'You are the Drunk. You must swap your card with a center card (without looking at it).',
  'Insomniac': 'You are the Insomniac. At the end of the night, you look at your card again.',
  'Minion': 'You are the Minion. Wake up and see who the Werewolves are. You are on the werewolf team.',
  'Mason': 'You are a Mason. Wake up and look for the other Mason.',
  'Tanner': 'You are the Tanner. You want to die. You win if you are killed.',
  'Hunter': 'You are the Hunter. If you are killed, the player you voted for also dies.',
}

// Role team colors
const TEAM_COLORS: { [key: string]: string } = {
  'werewolf': '#e74c3c',
  'village': '#3498db',
  'tanner': '#95a5a6',
}

export default function Game() {
  const router = useRouter()
  const params = useParams()
  const searchParams = useSearchParams()
  const game_id = params.game_id as string

  const [playerRole, setPlayerRole] = useState<PlayerRole | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  // Get current player ID from URL first, then fall back to sessionStorage
  const currentPlayerId = searchParams.get('player_id') ||
    (typeof window !== 'undefined' ? sessionStorage.getItem('player_id') : null)

  // Fetch player's role
  useEffect(() => {
    async function fetchPlayerRole() {
      if (!currentPlayerId) {
        setError('Player ID not found')
        setLoading(false)
        return
      }

      try {
        const response = await fetch(`/api/games/${game_id}/players/${currentPlayerId}/role`)
        if (!response.ok) {
          throw new Error('Failed to fetch your role')
        }
        const data = await response.json()
        setPlayerRole(data)
      } catch (err: any) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    if (game_id && currentPlayerId) {
      fetchPlayerRole()
    }
  }, [game_id, currentPlayerId])

  if (loading) {
    return (
      <main style={{
        padding: '2rem',
        fontFamily: 'Arial, sans-serif',
        textAlign: 'center',
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <h1>Loading your role...</h1>
      </main>
    )
  }

  if (error || !playerRole) {
    return (
      <main style={{
        padding: '2rem',
        fontFamily: 'Arial, sans-serif',
        textAlign: 'center',
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <h1 style={{ color: '#e74c3c', marginBottom: '1rem' }}>Error</h1>
        <p>{error || 'Failed to load your role'}</p>
        <button
          onClick={() => router.push('/')}
          style={{
            marginTop: '1rem',
            padding: '0.75rem 1.5rem',
            backgroundColor: '#3498db',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '1rem'
          }}
        >
          Back to Home
        </button>
      </main>
    )
  }

  const teamColor = TEAM_COLORS[playerRole.team] || '#34495e'
  const roleDescription = ROLE_DESCRIPTIONS[playerRole.initial_role] || 'No description available.'

  return (
    <main style={{
      padding: '2rem',
      fontFamily: 'Arial, sans-serif',
      maxWidth: '600px',
      margin: '0 auto',
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      <div style={{
        backgroundColor: '#f8f9fa',
        padding: '3rem',
        borderRadius: '16px',
        boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
        textAlign: 'center',
        width: '100%'
      }}>
        <h1 style={{
          fontSize: '2.5rem',
          marginBottom: '1rem',
          color: '#2c3e50'
        }}>
          Your Role
        </h1>

        <div style={{
          fontSize: '4rem',
          fontWeight: 'bold',
          color: teamColor,
          marginBottom: '1.5rem',
          padding: '1rem',
          backgroundColor: 'white',
          borderRadius: '12px',
          border: `4px solid ${teamColor}`
        }}>
          {playerRole.initial_role}
        </div>

        <div style={{
          backgroundColor: 'white',
          padding: '1.5rem',
          borderRadius: '8px',
          marginBottom: '1.5rem',
          textAlign: 'left'
        }}>
          <p style={{
            fontSize: '1.1rem',
            lineHeight: '1.6',
            color: '#34495e',
            margin: 0
          }}>
            {roleDescription}
          </p>
        </div>

        <div style={{
          display: 'inline-block',
          padding: '0.75rem 1.5rem',
          backgroundColor: teamColor,
          color: 'white',
          borderRadius: '8px',
          fontWeight: 'bold',
          fontSize: '1.2rem',
          marginBottom: '2rem'
        }}>
          Team: {playerRole.team.charAt(0).toUpperCase() + playerRole.team.slice(1)}
        </div>

        <div style={{
          marginTop: '2rem',
          padding: '1rem',
          backgroundColor: '#fff3cd',
          borderRadius: '8px',
          border: '1px solid #ffc107'
        }}>
          <p style={{ margin: 0, color: '#856404' }}>
            <strong>Remember:</strong> Keep your role secret! The night phase will begin shortly.
          </p>
        </div>
      </div>
    </main>
  )
}
