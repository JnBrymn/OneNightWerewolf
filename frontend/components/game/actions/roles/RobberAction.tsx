'use client'

import { useState } from 'react'
import PlayerButton from '../../PlayerButton'

interface RobberActionProps {
  gameId: string
  playerId: string
  availableActions?: {
    actionable_players: { player_id: string, player_name: string | null }[]
    actionable_center_cards: number[]
    instructions: string
  }
  onActionComplete: () => void
}

export default function RobberAction({
  gameId,
  playerId,
  availableActions,
  onActionComplete
}: RobberActionProps) {
  const [result, setResult] = useState<{ targetName: string, newRole: string } | null>(null)
  const [actionLoading, setActionLoading] = useState(false)
  const [actionError, setActionError] = useState('')

  const otherPlayers = availableActions?.actionable_players || []

  async function handleRobPlayer(targetPlayerId: string) {
    if (actionLoading) return

    setActionLoading(true)
    setActionError('')

    try {
      const response = await fetch(`/api/games/${gameId}/players/${playerId}/robber-action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_player_id: targetPlayerId })
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data?.detail || 'Failed to rob player')
      }

      const data = await response.json()
      const targetName = otherPlayers.find(p => p.player_id === targetPlayerId)?.player_name || targetPlayerId
      setResult({ targetName, newRole: data.new_role })
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setActionLoading(false)
    }
  }

  if (result) {
    return (
      <div>
        <div style={{ color: '#a8ffef', fontWeight: 'bold', textAlign: 'center', marginBottom: '1rem', fontSize: '1.1rem' }}>
          You robbed {result.targetName} and took their card. You are now: {result.newRole}
        </div>
        <div style={{ textAlign: 'center', marginTop: '1rem' }}>
          <button
            onClick={() => onActionComplete()}
            style={{
              padding: '0.75rem 1.5rem',
              backgroundColor: '#e94560',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '1rem',
              fontWeight: 'bold',
              cursor: 'pointer'
            }}
          >
            OK
          </button>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div style={{ color: '#ffffff', fontWeight: 'bold', marginBottom: '1rem', fontSize: '1.2rem' }}>
        {availableActions?.instructions || 'Choose a player to rob (exchange cards):'}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1rem' }}>
        {otherPlayers.map((player) => (
          <PlayerButton
            key={player.player_id}
            playerId={player.player_id}
            playerName={player.player_name || player.player_id}
            isCurrentPlayer={false}
            enabled={!actionLoading}
            onClick={handleRobPlayer}
          />
        ))}
      </div>
      {actionError && (
        <div style={{ color: '#ffb3b3', textAlign: 'center', marginBottom: '1rem' }}>
          {actionError}
        </div>
      )}
    </div>
  )
}
