'use client'

import { useState } from 'react'

interface MinionActionProps {
  gameId: string
  playerId: string
  nightInfo?: {
    role: string
    werewolves?: { player_id: string, player_name: string | null }[]
    night_action_completed?: boolean
  }
  onActionComplete: () => void
}

export default function MinionAction({
  gameId,
  playerId,
  nightInfo,
  onActionComplete
}: MinionActionProps) {
  const [actionLoading, setActionLoading] = useState(false)
  const [actionError, setActionError] = useState('')

  const completed = nightInfo?.night_action_completed ?? false
  const werewolves = nightInfo?.werewolves ?? []

  async function handleAcknowledge() {
    if (actionLoading || completed) return
    setActionLoading(true)
    setActionError('')
    try {
      const response = await fetch(`/api/games/${gameId}/players/${playerId}/acknowledge`, { method: 'POST' })
      if (!response.ok) {
        const data = await response.json()
        throw new Error(data?.detail || 'Failed to acknowledge')
      }
      onActionComplete()
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setActionLoading(false)
    }
  }

  if (!nightInfo) {
    return (
      <div style={{ color: '#ffffff', textAlign: 'center', padding: '2rem' }}>
        Loading...
      </div>
    )
  }

  return (
    <div>
      <div style={{ color: '#ffffff', fontWeight: 'bold', marginBottom: '0.75rem', fontSize: '1.2rem' }}>
        You are the Minion. The Werewolves are:
      </div>
      {werewolves.length > 0 ? (
        <ul style={{ margin: 0, paddingLeft: '1.2rem', color: '#a8b2d1', marginBottom: '1rem' }}>
          {werewolves.map((w) => (
            <li key={w.player_id}>{w.player_name || w.player_id}</li>
          ))}
        </ul>
      ) : (
        <div style={{ color: '#a8b2d1', marginBottom: '1rem' }}>
          There are no Werewolves among the players (they are in the center).
        </div>
      )}
      {!completed && (
        <div style={{ textAlign: 'center', marginTop: '1rem' }}>
          <button
            onClick={handleAcknowledge}
            disabled={actionLoading}
            style={{
              padding: '0.75rem 1.5rem',
              backgroundColor: '#e94560',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '1rem',
              fontWeight: 'bold',
              cursor: actionLoading ? 'not-allowed' : 'pointer',
              opacity: actionLoading ? 0.6 : 1
            }}
          >
            {actionLoading ? 'Processing...' : 'OK'}
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
