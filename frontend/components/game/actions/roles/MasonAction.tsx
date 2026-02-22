'use client'

import { useState } from 'react'

interface MasonActionProps {
  gameId: string
  playerId: string
  nightInfo?: {
    role: string
    other_mason?: { player_id: string, player_name: string | null } | null
    in_center?: boolean
    night_action_completed?: boolean
  }
  onActionComplete: () => void
}

export default function MasonAction({
  gameId,
  playerId,
  nightInfo,
  onActionComplete
}: MasonActionProps) {
  const [actionLoading, setActionLoading] = useState(false)
  const [actionError, setActionError] = useState('')

  const completed = nightInfo?.night_action_completed ?? false
  const otherMason = nightInfo?.other_mason
  const inCenter = nightInfo?.in_center ?? false

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
        You are a Mason. The other Mason is:
      </div>
      {otherMason ? (
        <div style={{ color: '#a8b2d1', marginBottom: '1rem' }}>
          {otherMason.player_name || otherMason.player_id}
        </div>
      ) : inCenter ? (
        <div style={{ color: '#a8b2d1', marginBottom: '1rem' }}>
          In the center (no other Mason among players).
        </div>
      ) : (
        <div style={{ color: '#a8b2d1', marginBottom: '1rem' }}>
          No other Mason in this game.
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
