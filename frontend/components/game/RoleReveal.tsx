'use client'

interface RoleRevealProps {
  role: string
  roleDescription: string
  teamColor: string
  onAcknowledge: () => void
}

const ROLE_DESCRIPTIONS: { [key: string]: string } = {
  'Werewolf': 'You are a Werewolf. Wake up and look for other Werewolves. If you are alone, you may view one center card.',
  'Villager': 'You are a Villager. You have no special abilities, but you are on the village team.',
  'Seer': 'You are the Seer. You may look at one other player\'s card, or two center cards.',
  'Robber': 'You are the Robber. You may swap your card with another player and look at your new card.',
  'Troublemaker': 'You are the Troublemaker. You may swap cards between two other players (without looking at them).',
  'Drunk': 'You are the Drunk. You must swap your card with a center card (without looking at it).',
  'Insomniac': 'You are the Insomniac. At the end of the night, you look at your card again.',
  'Minion': 'You are the Minion. Wake up and see who the Werewolves are. You are on the werewolf team.',
  'Mason': 'You are a Mason. Wake up and look for the other Mason.',
  'Tanner': 'You are the Tanner. You want to die. You win if you are killed.',
  'Hunter': 'You are the Hunter. If you are killed, the player you voted for also dies.',
}

export default function RoleReveal({ role, roleDescription, teamColor, onAcknowledge }: RoleRevealProps) {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      padding: '2rem',
      backgroundColor: '#1a1a2e'
    }}>
      <div style={{
        backgroundColor: '#16213e',
        padding: '3rem',
        borderRadius: '16px',
        border: `3px solid ${teamColor}`,
        maxWidth: '600px',
        textAlign: 'center'
      }}>
        <h1 style={{
          color: '#ffffff',
          marginBottom: '1rem',
          fontSize: '2.5rem'
        }}>
          Your Role
        </h1>
        
        <div style={{
          fontSize: '3rem',
          fontWeight: 'bold',
          color: teamColor,
          marginBottom: '2rem',
          textTransform: 'uppercase'
        }}>
          {role}
        </div>

        <div style={{
          backgroundColor: '#0f3460',
          padding: '1.5rem',
          borderRadius: '12px',
          marginBottom: '2rem',
          border: `2px solid ${teamColor}`
        }}>
          <div style={{
            fontSize: '1.2rem',
            color: '#ffffff',
            marginBottom: '0.75rem',
            fontWeight: 'bold'
          }}>
            Instructions
          </div>
          <div style={{ color: '#a8b2d1', lineHeight: '1.6' }}>
            {roleDescription || ROLE_DESCRIPTIONS[role] || 'No description available.'}
          </div>
        </div>

        <button
          onClick={onAcknowledge}
          style={{
            padding: '1rem 2rem',
            backgroundColor: teamColor,
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            fontSize: '1.2rem',
            fontWeight: 'bold',
            cursor: 'pointer',
            transition: 'opacity 0.2s'
          }}
          onMouseOver={(e) => e.currentTarget.style.opacity = '0.9'}
          onMouseOut={(e) => e.currentTarget.style.opacity = '1'}
        >
          I Understand
        </button>
      </div>
    </div>
  )
}
