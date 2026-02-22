'use client'

import { useState } from 'react'

interface InsomniacActionProps {
  gameId: string
  playerId: string
  nightInfo?: {
    role: string
    current_role?: string
    night_action_completed?: boolean
  }
  onActionComplete: () => void
}

export default function InsomniacAction({
  gameId,
  playerId,
  nightInfo,
  onActionComplete
}: InsomniacActionProps) {
  const [actionLoading, setActionLoading] = useState(false)
  const [actionError, setActionError] = useState('')

  const completed = nightInfo?.night_action_completed ?? false
  const currentRole = nightInfo?.current_role ?? 'Insomniac'

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

  // Always show content + OK so play never halts if nightInfo is slow or missing
  return (
    <div>
      <div style={{ color: '#ffffff', fontWeight: 'bold', marginBottom: '0.75rem', fontSize: '1.2rem' }}>
        You are the Insomniac. Check your current card.
      </div>
      <div style={{ color: '#a8ffef', fontWeight: 'bold', textAlign: 'center', marginBottom: '1rem', fontSize: '1.1rem' }}>
        Your current role is: {nightInfo ? currentRole : '…'}
      </div>
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
