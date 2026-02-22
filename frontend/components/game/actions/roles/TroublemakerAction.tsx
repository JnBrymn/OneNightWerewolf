'use client'

import { useState } from 'react'
import PlayerButton from '../../PlayerButton'

interface TroublemakerActionProps {
  gameId: string
  playerId: string
  availableActions?: {
    actionable_players: { player_id: string, player_name: string | null }[]
    actionable_center_cards: number[]
    instructions: string
  }
  onActionComplete: () => void
}

export default function TroublemakerAction({
  gameId,
  playerId,
  availableActions,
  onActionComplete
}: TroublemakerActionProps) {
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [result, setResult] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState(false)
  const [actionError, setActionError] = useState('')

  const otherPlayers = availableActions?.actionable_players || []

  function togglePlayer(targetPlayerId: string) {
    if (selectedIds.includes(targetPlayerId)) {
      setSelectedIds(selectedIds.filter(id => id !== targetPlayerId))
    } else if (selectedIds.length < 2) {
      setSelectedIds([...selectedIds, targetPlayerId])
    }
  }

  async function handleConfirm() {
    if (selectedIds.length !== 2 || actionLoading) return
    setActionLoading(true)
    setActionError('')
    try {
      const response = await fetch(`/api/games/${gameId}/players/${playerId}/troublemaker-action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ player1_id: selectedIds[0], player2_id: selectedIds[1] })
      })
      if (!response.ok) {
        const data = await response.json()
        throw new Error(data?.detail || 'Failed to swap')
      }
      const data = await response.json()
      setResult(data.message || 'You swapped the cards of the two players.')
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
          {result}
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
        {availableActions?.instructions || 'Choose two players to swap (without looking at their cards):'}
      </div>
      <div style={{ color: '#a8b2d1', marginBottom: '0.5rem' }}>
        Selected: {selectedIds.length}/2
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1rem' }}>
        {otherPlayers.map((player) => (
          <PlayerButton
            key={player.player_id}
            playerId={player.player_id}
            playerName={player.player_name || player.player_id}
            isCurrentPlayer={false}
            enabled={!actionLoading && (selectedIds.length < 2 || selectedIds.includes(player.player_id))}
            selected={selectedIds.includes(player.player_id)}
            onClick={() => togglePlayer(player.player_id)}
          />
        ))}
      </div>
      {selectedIds.length === 2 && (
        <div style={{ textAlign: 'center', marginBottom: '1rem' }}>
          <button
            onClick={handleConfirm}
            disabled={actionLoading}
            style={{
              padding: '0.75rem 1.5rem',
              backgroundColor: '#0f3460',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '1rem',
              fontWeight: 'bold',
              cursor: actionLoading ? 'not-allowed' : 'pointer'
            }}
          >
            {actionLoading ? 'Swapping...' : 'Swap these two players'}
          </button>
        </div>
      )}
      {actionError && (
        <div style={{ color: '#ffb3b3', textAlign: 'center', marginBottom: '1rem' }}>
          {actionError}
        </div>
      )}
    </div>
  )
}
