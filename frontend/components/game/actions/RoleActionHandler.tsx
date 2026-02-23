'use client'

import WerewolfAction from './roles/WerewolfAction'
import SeerAction from './roles/SeerAction'
import RobberAction from './roles/RobberAction'
import TroublemakerAction from './roles/TroublemakerAction'
import DrunkAction from './roles/DrunkAction'
import InsomniacAction from './roles/InsomniacAction'
import MinionAction from './roles/MinionAction'
import MasonAction from './roles/MasonAction'

const NIGHT_INFO_ROLES = ['Werewolf', 'Minion', 'Mason', 'Insomniac']

interface RoleActionHandlerProps {
  role: string
  currentRoleStep?: string | null
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
  currentRoleStep,
  gameId,
  playerId,
  nightInfo,
  availableActions,
  onActionComplete
}: RoleActionHandlerProps) {
  // Use current step for night-info roles only when it's this player's turn, so we don't show
  // e.g. Insomniac UI to the Troublemaker when the step moved to Insomniac (bug 6).
  const effectiveRole = (currentRoleStep && role === currentRoleStep && NIGHT_INFO_ROLES.includes(currentRoleStep))
    ? currentRoleStep
    : role
  if (effectiveRole === 'Werewolf') {
    return (
      <WerewolfAction
        gameId={gameId}
        playerId={playerId}
        nightInfo={nightInfo}
        onActionComplete={onActionComplete}
      />
    )
  }
  if (effectiveRole === 'Seer') {
    return (
      <SeerAction
        gameId={gameId}
        playerId={playerId}
        availableActions={availableActions}
        onActionComplete={onActionComplete}
      />
    )
  }
  if (effectiveRole === 'Robber') {
    return (
      <RobberAction
        gameId={gameId}
        playerId={playerId}
        availableActions={availableActions}
        onActionComplete={onActionComplete}
      />
    )
  }
  if (effectiveRole === 'Troublemaker') {
    return (
      <TroublemakerAction
        gameId={gameId}
        playerId={playerId}
        availableActions={availableActions}
        onActionComplete={onActionComplete}
      />
    )
  }
  if (effectiveRole === 'Drunk') {
    return (
      <DrunkAction
        gameId={gameId}
        playerId={playerId}
        availableActions={availableActions}
        onActionComplete={onActionComplete}
      />
    )
  }
  if (effectiveRole === 'Insomniac') {
    return (
      <InsomniacAction
        gameId={gameId}
        playerId={playerId}
        nightInfo={nightInfo}
        onActionComplete={onActionComplete}
      />
    )
  }
  if (effectiveRole === 'Minion') {
    return (
      <MinionAction
        gameId={gameId}
        playerId={playerId}
        nightInfo={nightInfo}
        onActionComplete={onActionComplete}
      />
    )
  }
  if (effectiveRole === 'Mason') {
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
        {effectiveRole} Action
      </div>
      <div style={{ color: '#a8b2d1' }}>
        Action for {effectiveRole} will be implemented in a future step.
      </div>
    </div>
  )
}
