'use client'

import { useState } from 'react'
import CenterCardButton from '../../CenterCardButton'

interface DrunkActionProps {
  gameId: string
  playerId: string
  availableActions?: {
    actionable_players: { player_id: string, player_name: string | null }[]
    actionable_center_cards: number[]
    instructions: string
  }
  onActionComplete: () => void
}

export default function DrunkAction({
  gameId,
  playerId,
  availableActions,
  onActionComplete
}: DrunkActionProps) {
  const [result, setResult] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState(false)
  const [actionError, setActionError] = useState('')

  const centerCards = availableActions?.actionable_center_cards ?? [0, 1, 2]

  async function handleSelectCenter(cardIndex: number) {
    if (actionLoading) return
    setActionLoading(true)
    setActionError('')
    try {
      const response = await fetch(`/api/games/${gameId}/players/${playerId}/drunk-action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ card_index: cardIndex })
      })
      if (!response.ok) {
        const data = await response.json()
        throw new Error(data?.detail || 'Failed to exchange')
      }
      const data = await response.json()
      setResult(data.message || "You exchanged your card with a center card. You don't know your new role.")
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
        {availableActions?.instructions || 'Choose a center card to exchange with (you will not look at your new card):'}
      </div>
      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1rem', justifyContent: 'center' }}>
        {centerCards.map((index) => (
          <CenterCardButton
            key={index}
            cardIndex={index}
            enabled={!actionLoading}
            selected={false}
            onClick={handleSelectCenter}
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
