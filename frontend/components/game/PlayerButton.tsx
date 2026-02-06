'use client'

interface PlayerButtonProps {
  playerId: string
  playerName: string
  isCurrentPlayer: boolean
  enabled: boolean
  selected?: boolean
  onClick?: (playerId: string) => void
  roleCard?: string | null
  showRoleCard?: boolean
}

export default function PlayerButton({
  playerId,
  playerName,
  isCurrentPlayer,
  enabled,
  selected = false,
  onClick,
  roleCard,
  showRoleCard = false
}: PlayerButtonProps) {
  const handleClick = () => {
    if (enabled && onClick) {
      onClick(playerId)
    }
  }

  return (
    <button
      onClick={handleClick}
      disabled={!enabled}
      style={{
        backgroundColor: isCurrentPlayer 
          ? '#27ae60' 
          : selected 
            ? '#e94560' 
            : enabled 
              ? '#0f3460' 
              : '#34495e',
        color: 'white',
        border: selected ? '2px solid #e94560' : 'none',
        borderRadius: '8px',
        padding: '0.75rem',
        textAlign: 'left',
        cursor: enabled ? 'pointer' : 'default',
        opacity: enabled ? 1 : 0.6,
        transition: 'all 0.2s',
        position: 'relative'
      }}
    >
      <div>{playerName}{isCurrentPlayer && ' (You)'}</div>
      {showRoleCard && roleCard && (
        <div style={{ fontSize: '0.85rem', marginTop: '0.25rem', opacity: 0.8 }}>
          {roleCard}
        </div>
      )}
    </button>
  )
}
