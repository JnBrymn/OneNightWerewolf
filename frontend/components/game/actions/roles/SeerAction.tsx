'use client'

import { useState, useEffect } from 'react'
import PlayerButton from '../../PlayerButton'
import CenterCardButton from '../../CenterCardButton'

interface SeerActionProps {
  gameId: string
  playerId: string
  availableActions?: {
    actionable_players: { player_id: string, player_name: string | null }[]
    actionable_center_cards: number[]
    instructions: string
  }
  onActionComplete: () => void
}

export default function SeerAction({
  gameId,
  playerId,
  availableActions,
  onActionComplete
}: SeerActionProps) {
  const [actionType, setActionType] = useState<'view_player' | 'view_center' | null>(null)
  const [selectedPlayerId, setSelectedPlayerId] = useState<string | null>(null)
  const [selectedCenterCards, setSelectedCenterCards] = useState<number[]>([])
  const [viewedRole, setViewedRole] = useState<string | null>(null)
  const [viewedRoles, setViewedRoles] = useState<string[]>([])
  const [actionLoading, setActionLoading] = useState(false)
  const [actionError, setActionError] = useState('')
  const [actionCompleted, setActionCompleted] = useState(false)

  // Get players excluding self
  const otherPlayers = availableActions?.actionable_players || []
  const centerCards = availableActions?.actionable_center_cards || []

  // Step 1: Action Type Selection
  if (!actionType) {
    return (
      <div>
        <div style={{ color: '#ffffff', fontWeight: 'bold', marginBottom: '1rem', fontSize: '1.2rem' }}>
          You are the Seer. Choose your action:
        </div>
        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
          <button
            onClick={() => setActionType('view_player')}
            style={{
              padding: '1rem 2rem',
              backgroundColor: '#0f3460',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '1rem',
              fontWeight: 'bold',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
            onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#1a4b7a'}
            onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#0f3460'}
          >
            View One Player's Card
          </button>
          <button
            onClick={() => setActionType('view_center')}
            style={{
              padding: '1rem 2rem',
              backgroundColor: '#0f3460',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '1rem',
              fontWeight: 'bold',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
            onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#1a4b7a'}
            onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#0f3460'}
          >
            View Two Center Cards
          </button>
        </div>
      </div>
    )
  }

  // Step 2a: View Player Path
  if (actionType === 'view_player' && !viewedRole && !actionCompleted) {
    const handleViewPlayer = async (targetPlayerId: string) => {
      if (actionLoading) return
      
      setActionLoading(true)
      setActionError('')
      setSelectedPlayerId(targetPlayerId)

      try {
        const response = await fetch(`/api/games/${gameId}/players/${playerId}/seer-action`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            action_type: 'view_player',
            target_player_id: targetPlayerId
          })
        })
        
        if (!response.ok) {
          const data = await response.json()
          throw new Error(data?.detail || 'Failed to view player card')
        }
        
        const data = await response.json()
        setViewedRole(data.role)
        setActionCompleted(true)
      } catch (err: any) {
        setActionError(err.message)
        setSelectedPlayerId(null)
      } finally {
        setActionLoading(false)
      }
    }

    return (
      <div>
        <div style={{ color: '#ffffff', fontWeight: 'bold', marginBottom: '1rem', fontSize: '1.2rem' }}>
          Choose a player to view:
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1rem' }}>
          {otherPlayers.map((player) => (
            <PlayerButton
              key={player.player_id}
              playerId={player.player_id}
              playerName={player.player_name || player.player_id}
              isCurrentPlayer={false}
              enabled={!actionLoading}
              selected={selectedPlayerId === player.player_id}
              onClick={handleViewPlayer}
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

  // Step 2b: View Center Path
  if (actionType === 'view_center' && viewedRoles.length === 0 && !actionCompleted) {
    const handleViewCenter = async (cardIndex: number) => {
      if (actionLoading || selectedCenterCards.includes(cardIndex)) return
      
      const newSelection = [...selectedCenterCards, cardIndex]
      setSelectedCenterCards(newSelection)

      // If we have 2 selections, perform the action
      if (newSelection.length === 2) {
        setActionLoading(true)
        setActionError('')

        try {
          const response = await fetch(`/api/games/${gameId}/players/${playerId}/seer-action`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              action_type: 'view_center',
              card_indices: newSelection.sort()
            })
          })
          
          if (!response.ok) {
            const data = await response.json()
            throw new Error(data?.detail || 'Failed to view center cards')
          }
          
          const data = await response.json()
          setViewedRoles(data.roles)
          setActionCompleted(true)
        } catch (err: any) {
          setActionError(err.message)
          setSelectedCenterCards([])
        } finally {
          setActionLoading(false)
        }
      }
    }

    return (
      <div>
        <div style={{ color: '#ffffff', fontWeight: 'bold', marginBottom: '1rem', fontSize: '1.2rem' }}>
          Choose two center cards to view ({selectedCenterCards.length}/2 selected):
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1rem', justifyContent: 'center' }}>
          {centerCards.map((index) => (
            <CenterCardButton
              key={index}
              cardIndex={index}
              enabled={!actionLoading && !selectedCenterCards.includes(index) && selectedCenterCards.length < 2}
              selected={selectedCenterCards.includes(index)}
              onClick={handleViewCenter}
            />
          ))}
        </div>
        {selectedCenterCards.length > 0 && (
          <div style={{ color: '#a8b2d1', textAlign: 'center', marginBottom: '1rem' }}>
            Selected: {selectedCenterCards.map(idx => ['Left', 'Center', 'Right'][idx]).join(', ')}
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

  // Step 3: Result Display
  const resultMessage = actionType === 'view_player' && viewedRole
    ? `${otherPlayers.find(p => p.player_id === selectedPlayerId)?.player_name || selectedPlayerId}'s card is: ${viewedRole}`
    : actionType === 'view_center' && viewedRoles.length === 2
      ? `You viewed center cards ${selectedCenterCards.map(idx => ['Left', 'Center', 'Right'][idx]).join(' and ')}. They are: ${viewedRoles.join(' and ')}`
      : null

  // Show result and OK button when action is completed
  if (actionCompleted && resultMessage) {
    return (
      <div>
        <div style={{ color: '#a8ffef', fontWeight: 'bold', textAlign: 'center', marginBottom: '1rem', fontSize: '1.1rem' }}>
          {resultMessage}
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

  return null
}
