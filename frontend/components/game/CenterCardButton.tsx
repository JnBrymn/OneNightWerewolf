'use client'

interface CenterCardButtonProps {
  cardIndex: number
  enabled: boolean
  selected?: boolean
  onClick?: (cardIndex: number) => void
}

const CARD_LABELS = ['Left', 'Center', 'Right']

export default function CenterCardButton({
  cardIndex,
  enabled,
  selected = false,
  onClick
}: CenterCardButtonProps) {
  const handleClick = () => {
    if (enabled && onClick) {
      onClick(cardIndex)
    }
  }

  return (
    <button
      onClick={handleClick}
      disabled={!enabled}
      style={{
        backgroundColor: selected ? '#e94560' : enabled ? '#34495e' : '#1a1a2e',
        color: 'white',
        border: selected ? '2px solid #e94560' : '1px solid #1b4b7a',
        borderRadius: '8px',
        padding: '1.5rem 0.5rem',
        textAlign: 'center',
        cursor: enabled ? 'pointer' : 'default',
        opacity: enabled ? 1 : 0.6,
        transition: 'all 0.2s',
        minWidth: '100px'
      }}
    >
      {CARD_LABELS[cardIndex]}
    </button>
  )
}
