'use client'

import PlayerButton from './PlayerButton'

interface Player {
  player_id: string
  player_name: string
  avatar_url?: string | null
}

interface PlayerGridProps {
  players: Player[]
  currentPlayerId: string | null
  enabledPlayerIds?: string[]
  selectedPlayerIds?: string[]
  onClick?: (playerId: string) => void
  showRoleCards?: boolean
  roleCards?: { [playerId: string]: string }
}

export default function PlayerGrid({
  players,
  currentPlayerId,
  enabledPlayerIds = [],
  selectedPlayerIds = [],
  onClick,
  showRoleCards = false,
  roleCards = {}
}: PlayerGridProps) {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))',
      gap: '0.75rem'
    }}>
      {players.map(player => (
        <PlayerButton
          key={player.player_id}
          playerId={player.player_id}
          playerName={player.player_name}
          isCurrentPlayer={player.player_id === currentPlayerId}
          enabled={enabledPlayerIds.includes(player.player_id)}
          selected={selectedPlayerIds.includes(player.player_id)}
          onClick={onClick}
          roleCard={roleCards[player.player_id]}
          showRoleCard={showRoleCards}
        />
      ))}
    </div>
  )
}
