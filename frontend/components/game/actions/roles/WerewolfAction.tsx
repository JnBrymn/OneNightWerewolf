'use client'

import { useState } from 'react'
import CenterCardButton from '../../CenterCardButton'

interface WerewolfActionProps {
  gameId: string
  playerId: string
  nightInfo?: {
    role: string
    is_lone_wolf?: boolean
    other_werewolves?: { player_id: string, player_name: string | null }[]
    night_action_completed?: boolean
  }
  onActionComplete: () => void
}

export default function WerewolfAction({
  gameId,
  playerId,
  nightInfo,
  onActionComplete
}: WerewolfActionProps) {
  const [viewedCenterRole, setViewedCenterRole] = useState<string | null>(null)
  const [selectedCenterIndex, setSelectedCenterIndex] = useState<number | null>(null)
  const [actionLoading, setActionLoading] = useState(false)
  const [actionError, setActionError] = useState('')

  // If nightInfo isn't loaded yet, show loading state
  if (!nightInfo) {
    return (
      <div style={{ color: '#ffffff', textAlign: 'center', padding: '2rem' }}>
        <div style={{ fontSize: '1.2rem', marginBottom: '1rem' }}>Loading your werewolf information...</div>
      </div>
    )
  }

  const isLoneWolf = nightInfo.is_lone_wolf ?? false
  const otherWerewolves = nightInfo.other_werewolves ?? []
  const actionCompleted = nightInfo.night_action_completed ?? false

  async function handleViewCenter(cardIndex: number) {
    if (actionLoading || actionCompleted) return
    
    setActionLoading(true)
    setActionError('')
    setSelectedCenterIndex(cardIndex)

    try {
      const response = await fetch(`/api/games/${gameId}/players/${playerId}/view-center`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ card_index: cardIndex })
      })
      if (!response.ok) {
        const data = await response.json()
        throw new Error(data?.detail || 'Failed to view center card')
      }
      const data = await response.json()
      setViewedCenterRole(data.role)
      // Action is completed on backend, refresh nightInfo to update state
      // The OK button will appear after this
    } catch (err: any) {
      setActionError(err.message)
    } finally {
      setActionLoading(false)
    }
  }

  async function handleAcknowledge() {
    if (actionLoading || actionCompleted) return
    
    setActionLoading(true)
    setActionError('')

    try {
      const response = await fetch(`/api/games/${gameId}/players/${playerId}/acknowledge`, {
        method: 'POST'
      })
      if (!response.ok) {
        const data = await response.json()
        throw new Error(data?.detail || 'Failed to acknowledge')
      }
      // Immediately close overlay after acknowledging - no need for "Action completed!" step
      // The user has seen who the other werewolves are, that's all they need
      onActionComplete()
    } catch (err: any) {
      setActionError(err.message)
      setActionLoading(false)
    }
  }
  

  if (isLoneWolf) {
    return (
      <div>
        <div style={{ color: '#ffffff', fontWeight: 'bold', marginBottom: '1rem', fontSize: '1.2rem' }}>
          You are the lone Werewolf. Choose one center card to view.
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1rem', justifyContent: 'center' }}>
          {[0, 1, 2].map((index) => (
            <CenterCardButton
              key={index}
              cardIndex={index}
              enabled={!actionLoading && !actionCompleted}
              selected={selectedCenterIndex === index}
              onClick={handleViewCenter}
            />
          ))}
        </div>
        {viewedCenterRole && (
          <>
            <div style={{ color: '#a8ffef', fontWeight: 'bold', textAlign: 'center', marginBottom: '1rem' }}>
              Center card role: {viewedCenterRole}
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
          </>
        )}
        {actionError && (
          <div style={{ color: '#ffb3b3', textAlign: 'center', marginBottom: '1rem' }}>
            {actionError}
          </div>
        )}
      </div>
    )
  }

  return (
    <div>
      <div style={{ color: '#ffffff', fontWeight: 'bold', marginBottom: '0.75rem', fontSize: '1.2rem' }}>
        You are a Werewolf. Your fellow Werewolves:
      </div>
      {otherWerewolves.length > 0 ? (
        <ul style={{ margin: 0, paddingLeft: '1.2rem', color: '#a8b2d1', marginBottom: '1rem' }}>
          {otherWerewolves.map((w) => (
            <li key={w.player_id}>{w.player_name || w.player_id}</li>
          ))}
        </ul>
      ) : (
        <div style={{ color: '#a8b2d1', marginBottom: '1rem' }}>
          None detected (other werewolves are in the center)
        </div>
      )}
      {!actionCompleted && (
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
