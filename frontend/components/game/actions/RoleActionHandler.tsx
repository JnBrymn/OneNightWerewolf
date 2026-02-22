'use client'

import WerewolfAction from './roles/WerewolfAction'
import SeerAction from './roles/SeerAction'
import RobberAction from './roles/RobberAction'

interface RoleActionHandlerProps {
  role: string
  gameId: string
  playerId: string
  nightInfo?: any
  availableActions?: {
    actionable_players: { player_id: string, player_name: string | null }[]
    actionable_center_cards: number[]
    instructions: string
  }
  onActionComplete: () => void
}

export default function RoleActionHandler({
  role,
  gameId,
  playerId,
  nightInfo,
  availableActions,
  onActionComplete
}: RoleActionHandlerProps) {
  // Route to appropriate role-specific action component
  if (role === 'Werewolf') {
    return (
      <WerewolfAction
        gameId={gameId}
        playerId={playerId}
        nightInfo={nightInfo}
        onActionComplete={onActionComplete}
      />
    )
  }

  if (role === 'Seer') {
    return (
      <SeerAction
        gameId={gameId}
        playerId={playerId}
        availableActions={availableActions}
        onActionComplete={onActionComplete}
      />
    )
  }

  if (role === 'Robber') {
    return (
      <RobberAction
        gameId={gameId}
        playerId={playerId}
        availableActions={availableActions}
        onActionComplete={onActionComplete}
      />
    )
  }

  // Placeholder for other roles (will be implemented in future steps)
  return (
    <div style={{ color: '#ffffff', textAlign: 'center', padding: '2rem' }}>
      <div style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>
        {role} Action
      </div>
      <div style={{ color: '#a8b2d1' }}>
        Action for {role} will be implemented in a future step.
      </div>
    </div>
  )
}
