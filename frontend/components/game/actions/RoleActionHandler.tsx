'use client'

import WerewolfAction from './roles/WerewolfAction'
import SeerAction from './roles/SeerAction'
import RobberAction from './roles/RobberAction'
import TroublemakerAction from './roles/TroublemakerAction'
import DrunkAction from './roles/DrunkAction'
import InsomniacAction from './roles/InsomniacAction'
import MinionAction from './roles/MinionAction'
import MasonAction from './roles/MasonAction'

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
  if (role === 'Troublemaker') {
    return (
      <TroublemakerAction
        gameId={gameId}
        playerId={playerId}
        availableActions={availableActions}
        onActionComplete={onActionComplete}
      />
    )
  }
  if (role === 'Drunk') {
    return (
      <DrunkAction
        gameId={gameId}
        playerId={playerId}
        availableActions={availableActions}
        onActionComplete={onActionComplete}
      />
    )
  }
  if (role === 'Insomniac') {
    return (
      <InsomniacAction
        gameId={gameId}
        playerId={playerId}
        nightInfo={nightInfo}
        onActionComplete={onActionComplete}
      />
    )
  }
  if (role === 'Minion') {
    return (
      <MinionAction
        gameId={gameId}
        playerId={playerId}
        nightInfo={nightInfo}
        onActionComplete={onActionComplete}
      />
    )
  }
  if (role === 'Mason') {
    return (
      <MasonAction
        gameId={gameId}
        playerId={playerId}
        nightInfo={nightInfo}
        onActionComplete={onActionComplete}
      />
    )
  }

  // Placeholder for Doppelgänger and any other unimplemented roles
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
