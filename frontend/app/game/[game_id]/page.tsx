'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter, useSearchParams } from 'next/navigation'

interface PlayerRole {
  player_role_id: string
  game_id: string
  player_id: string
  initial_role: string
  current_role: string
  team: string
  was_killed: boolean
}

interface NightStatus {
  current_role: string | null
  roles_completed: string[]
  roles_in_game: string[]
}

interface Game {
  game_id: string
  game_set_id: string
  state: string | null
  current_role_step: string | null
}

interface Player {
  player_id: string
  player_name: string
  avatar_url: string | null
}

interface PlayersResponse {
  players: Player[]
  current_count: number
  required_count: number
}

interface NightInfo {
  role: string
  is_lone_wolf?: boolean
  other_werewolves?: { player_id: string, player_name: string | null }[]
  night_action_completed?: boolean
}

// Role descriptions to help players understand their role
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

// Role team colors
const TEAM_COLORS: { [key: string]: string } = {
  'werewolf': '#e74c3c',
  'village': '#3498db',
  'tanner': '#95a5a6',
}

export default function Game() {
  const router = useRouter()
  const params = useParams()
  const searchParams = useSearchParams()
  const game_id = params.game_id as string

  const [playerRole, setPlayerRole] = useState<PlayerRole | null>(null)
  const [game, setGame] = useState<Game | null>(null)
  const [playersData, setPlayersData] = useState<PlayersResponse | null>(null)
  const [nightStatus, setNightStatus] = useState<NightStatus | null>(null)
  const [nightInfo, setNightInfo] = useState<NightInfo | null>(null)
  const [viewedCenterRole, setViewedCenterRole] = useState<string | null>(null)
  const [persistedWerewolfInfo, setPersistedWerewolfInfo] = useState<NightInfo | null>(null)
  const [persistedCenterRole, setPersistedCenterRole] = useState<string | null>(null)
  const [selectedCenterIndex, setSelectedCenterIndex] = useState<number | null>(null)
  const [actionError, setActionError] = useState('')
  const [actionLoading, setActionLoading] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [showRoleReveal, setShowRoleReveal] = useState(true)

  // Get current player ID from URL first, then fall back to sessionStorage
  const currentPlayerId = searchParams.get('player_id') ||
    (typeof window !== 'undefined' ? sessionStorage.getItem('player_id') : null)

  // Fetch game data for game_set_id
  useEffect(() => {
    async function fetchGame() {
      try {
        const response = await fetch(`/api/games/${game_id}`)
        if (!response.ok) {
          throw new Error('Failed to fetch game')
        }
        const data = await response.json()
        setGame(data)
      } catch (err: any) {
        setError(err.message)
      }
    }

    if (game_id) {
      fetchGame()
    }
  }, [game_id])

  // Fetch player's role
  useEffect(() => {
    async function fetchPlayerRole() {
      if (!currentPlayerId) {
        setError('Player ID not found')
        setLoading(false)
        return
      }

      try {
        const response = await fetch(`/api/games/${game_id}/players/${currentPlayerId}/role`)
        if (!response.ok) {
          throw new Error('Failed to fetch your role')
        }
        const data = await response.json()
        setPlayerRole(data)
      } catch (err: any) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    if (game_id && currentPlayerId) {
      fetchPlayerRole()
    }
  }, [game_id, currentPlayerId])

  // Poll players list for unified game screen
  useEffect(() => {
    if (!game?.game_set_id) return

    async function fetchPlayers() {
      try {
        const response = await fetch(`/api/game-sets/${game.game_set_id}/players`)
        if (!response.ok) throw new Error('Failed to fetch players')
        const data = await response.json()
        setPlayersData(data)
      } catch (err) {
        console.error('Failed to fetch players:', err)
      }
    }

    fetchPlayers()
    const interval = setInterval(fetchPlayers, 2000)
    return () => clearInterval(interval)
  }, [game?.game_set_id])

  // Poll night phase status
  useEffect(() => {
    if (!game_id) return

    async function fetchNightStatus() {
      try {
        const response = await fetch(`/api/games/${game_id}/night-status`)
        if (response.ok) {
          const data = await response.json()
          setNightStatus(data)

          // Auto-dismiss role reveal after 5 seconds and show night phase
          if (showRoleReveal) {
            setTimeout(() => setShowRoleReveal(false), 5000)
          }

          // If night phase is over (no current_role), transition to day phase
          if (data.current_role === null) {
            // TODO: Transition to day discussion phase
            console.log('Night phase complete!')
          }
        }
      } catch (err) {
        console.error('Failed to fetch night status:', err)
      }
    }

    // Fetch immediately
    fetchNightStatus()

    // Then poll every 2 seconds
    const interval = setInterval(fetchNightStatus, 2000)

    return () => clearInterval(interval)
  }, [game_id, showRoleReveal])

  // Fetch night info for werewolf during their turn
  useEffect(() => {
    if (!game_id || !currentPlayerId || !nightStatus?.current_role || !playerRole) {
      return
    }

    if (nightStatus.current_role !== 'Werewolf') {
      return
    }

    if (playerRole.current_role !== 'Werewolf') {
      setNightInfo(null)
      return
    }

    async function fetchNightInfo() {
      try {
        const response = await fetch(`/api/games/${game_id}/players/${currentPlayerId}/night-info`)
        if (!response.ok) {
          throw new Error('Failed to fetch night info')
        }
        const data = await response.json()
        setNightInfo(data)
        setPersistedWerewolfInfo((prev) => prev ?? data)
      } catch (err: any) {
        setActionError(err.message)
      }
    }

    fetchNightInfo()
  }, [game_id, currentPlayerId, nightStatus?.current_role, playerRole])

  async function handleViewCenter(cardIndex: number) {
    if (!currentPlayerId || !game_id) return
    setActionLoading(true)
    setActionError('')
    setSelectedCenterIndex(cardIndex)

    try {
      const response = await fetch(`/api/games/${game_id}/players/${currentPlayerId}/view-center`, {
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
      setPersistedCenterRole(data.role)
      setNightInfo((prev) => prev ? { ...prev, night_action_completed: true } : prev)
    } catch (err: any) {
      setActionError(err.message)
    } finally {
      setActionLoading(false)
    }
  }

  async function handleAcknowledge() {
    if (!currentPlayerId || !game_id) return
    setActionLoading(true)
    setActionError('')

    try {
      const response = await fetch(`/api/games/${game_id}/players/${currentPlayerId}/acknowledge`, {
        method: 'POST'
      })
      if (!response.ok) {
        const data = await response.json()
        throw new Error(data?.detail || 'Failed to acknowledge')
      }
      setNightInfo((prev) => prev ? { ...prev, night_action_completed: true } : prev)
      if (nightInfo) {
        setPersistedWerewolfInfo((prev) => prev ?? nightInfo)
      }
    } catch (err: any) {
      setActionError(err.message)
    } finally {
      setActionLoading(false)
    }
  }

  if (loading || !game || !playersData) {
    return (
      <main style={{
        padding: '2rem',
        fontFamily: 'Arial, sans-serif',
        textAlign: 'center',
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <h1>Loading your role...</h1>
      </main>
    )
  }

  if (error || !playerRole) {
    return (
      <main style={{
        padding: '2rem',
        fontFamily: 'Arial, sans-serif',
        textAlign: 'center',
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <h1 style={{ color: '#e74c3c', marginBottom: '1rem' }}>Error</h1>
        <p>{error || 'Failed to load your role'}</p>
        <button
          onClick={() => router.push('/')}
          style={{
            marginTop: '1rem',
            padding: '0.75rem 1.5rem',
            backgroundColor: '#3498db',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '1rem'
          }}
        >
          Back to Home
        </button>
      </main>
    )
  }

  const teamColor = TEAM_COLORS[playerRole.team] || '#34495e'
  const roleDescription = ROLE_DESCRIPTIONS[playerRole.initial_role] || 'No description available.'

  const isWerewolfTurn = nightStatus?.current_role === 'Werewolf'
  const isWerewolfPlayer = playerRole.current_role === 'Werewolf'

  const persistedOtherWerewolves = persistedWerewolfInfo?.other_werewolves || []
  const persistedIsLoneWolf = persistedWerewolfInfo?.is_lone_wolf

  return (
    <main style={{
      padding: '2rem',
      fontFamily: 'Arial, sans-serif',
      maxWidth: '1100px',
      margin: '0 auto',
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      backgroundColor: '#1a1a2e'
    }}>
      <h1 style={{
        color: '#ffffff',
        marginBottom: '1.5rem',
        fontSize: '2rem'
      }}>
        Your role: <span style={{ color: teamColor }}>{playerRole.initial_role}</span>
      </h1>

      <div style={{
        display: 'grid',
        gridTemplateColumns: '1.2fr 1fr',
        gap: '1.5rem',
        marginBottom: '2rem'
      }}>
        <div style={{
          backgroundColor: '#16213e',
          padding: '1.5rem',
          borderRadius: '12px',
          border: `2px solid ${teamColor}`
        }}>
          <div style={{
            fontSize: '1.2rem',
            color: '#ffffff',
            marginBottom: '0.75rem',
            fontWeight: 'bold'
          }}>
            Your Instructions
          </div>
          <div style={{ color: '#a8b2d1', lineHeight: '1.6' }}>
            {roleDescription}
          </div>
        </div>

        <div style={{
          backgroundColor: '#0f3460',
          padding: '1.5rem',
          borderRadius: '12px',
          border: '2px solid #e94560'
        }}>
          <div style={{
            fontSize: '1.2rem',
            color: '#ffffff',
            marginBottom: '0.75rem',
            fontWeight: 'bold'
          }}>
            Your Information
          </div>
          {persistedIsLoneWolf && persistedCenterRole && (
            <div style={{ color: '#a8ffef', marginBottom: '0.75rem' }}>
              Lone Werewolf saw: {persistedCenterRole}
            </div>
          )}
          {!persistedIsLoneWolf && persistedOtherWerewolves.length > 0 && (
            <div style={{ color: '#a8b2d1' }}>
              Other Werewolves: {persistedOtherWerewolves.map(w => w.player_name || w.player_id).join(', ')}
            </div>
          )}
          {!persistedCenterRole && persistedOtherWerewolves.length === 0 && (
            <div style={{ color: '#6c7a96' }}>No stored info yet.</div>
          )}
        </div>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '1.5rem',
        marginBottom: '2rem'
      }}>
        <div style={{
          backgroundColor: '#16213e',
          padding: '1.5rem',
          borderRadius: '12px',
          border: '2px solid #0f3460'
        }}>
          <div style={{ color: '#ffffff', fontWeight: 'bold', marginBottom: '1rem' }}>
            Players
          </div>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))',
            gap: '0.75rem'
          }}>
            {playersData.players.map(player => (
              <button
                key={player.player_id}
                style={{
                  backgroundColor: player.player_id === currentPlayerId ? '#27ae60' : '#0f3460',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  padding: '0.75rem',
                  textAlign: 'left',
                  cursor: 'default'
                }}
              >
                {player.player_name}
                {player.player_id === currentPlayerId && ' (You)'}
              </button>
            ))}
          </div>
        </div>

        <div style={{
          backgroundColor: '#16213e',
          padding: '1.5rem',
          borderRadius: '12px',
          border: '2px solid #0f3460'
        }}>
          <div style={{ color: '#ffffff', fontWeight: 'bold', marginBottom: '1rem' }}>
            Center Cards
          </div>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: '0.75rem'
          }}>
            {['Left', 'Center', 'Right'].map((label) => (
              <div
                key={label}
                style={{
                  backgroundColor: '#0f3460',
                  borderRadius: '8px',
                  padding: '1.5rem 0.5rem',
                  color: '#a8b2d1',
                  textAlign: 'center',
                  border: '1px solid #1b4b7a'
                }}
              >
                {label}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div style={{
        backgroundColor: '#16213e',
        padding: '2rem',
        borderRadius: '16px',
        boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
        textAlign: 'center',
        width: '100%',
        border: '2px solid #0f3460'
      }}>
        <div style={{
          fontSize: '1.5rem',
          color: '#e94560',
          marginBottom: '2rem',
          fontWeight: 'bold',
          textTransform: 'uppercase',
          letterSpacing: '0.1em'
        }}>
          🌙 Night Phase
        </div>

        {nightStatus ? (
          nightStatus.current_role ? (
          <>
            <div style={{
              fontSize: '2.5rem',
              fontWeight: 'bold',
              color: '#ffffff',
              marginBottom: '1.5rem',
              padding: '1.5rem',
              backgroundColor: '#0f3460',
              borderRadius: '12px',
              border: '2px solid #e94560'
            }}>
              {nightStatus.current_role}
            </div>

            <div style={{
              fontSize: '1.2rem',
              color: '#a8b2d1',
              marginBottom: '2rem',
              lineHeight: '1.6'
            }}>
              {isWerewolfTurn && isWerewolfPlayer ? 'Your turn as Werewolf' : (
                <>Waiting for <strong style={{ color: '#ffffff' }}>{nightStatus.current_role}</strong> to complete their action...</>
              )}
            </div>

            {isWerewolfTurn && isWerewolfPlayer ? (
              <div style={{
                marginTop: '1.5rem',
                padding: '1.5rem',
                backgroundColor: '#0f3460',
                borderRadius: '12px',
                textAlign: 'left'
              }}>
                {nightInfo?.is_lone_wolf ? (
                  <>
                    <div style={{ color: '#ffffff', fontWeight: 'bold', marginBottom: '1rem' }}>
                      You are the lone Werewolf. Choose one center card to view.
                    </div>
                    <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1rem' }}>
                      {['Left', 'Center', 'Right'].map((label, index) => (
                        <button
                          key={label}
                          onClick={() => handleViewCenter(index)}
                          disabled={actionLoading || nightInfo?.night_action_completed}
                          style={{
                            padding: '0.5rem 1rem',
                            backgroundColor: selectedCenterIndex === index ? '#e94560' : '#34495e',
                            color: 'white',
                            border: 'none',
                            borderRadius: '6px',
                            cursor: actionLoading ? 'not-allowed' : 'pointer',
                            opacity: nightInfo?.night_action_completed ? 0.6 : 1
                          }}
                        >
                          {label}
                        </button>
                      ))}
                    </div>
                    {viewedCenterRole && (
                      <div style={{ color: '#a8ffef', fontWeight: 'bold' }}>
                        Center card role: {viewedCenterRole}
                      </div>
                    )}
                  </>
                ) : (
                  <>
                    <div style={{ color: '#ffffff', fontWeight: 'bold', marginBottom: '0.75rem' }}>
                      Your fellow Werewolves:
                    </div>
                    <ul style={{ margin: 0, paddingLeft: '1.2rem', color: '#a8b2d1' }}>
                      {nightInfo?.other_werewolves?.length ? nightInfo.other_werewolves.map((w) => (
                        <li key={w.player_id}>{w.player_name || w.player_id}</li>
                      )) : (
                        <li>None detected</li>
                      )}
                    </ul>
                    <button
                      onClick={handleAcknowledge}
                      disabled={actionLoading || nightInfo?.night_action_completed}
                      style={{
                        marginTop: '1rem',
                        padding: '0.6rem 1.2rem',
                        backgroundColor: '#e94560',
                        color: 'white',
                        border: 'none',
                        borderRadius: '6px',
                        cursor: actionLoading ? 'not-allowed' : 'pointer',
                        opacity: nightInfo?.night_action_completed ? 0.6 : 1
                      }}
                    >
                      Continue
                    </button>
                  </>
                )}

                {actionError && (
                  <div style={{ marginTop: '0.75rem', color: '#ffb3b3' }}>
                    {actionError}
                  </div>
                )}
              </div>
            ) : (
              <>
                {/* Loading spinner */}
                <div style={{
                  width: '50px',
                  height: '50px',
                  border: '5px solid #0f3460',
                  borderTop: '5px solid #e94560',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite',
                  margin: '0 auto'
                }} />
                <style jsx>{`
                  @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                  }
                `}</style>
              </>
            )}

            {/* Progress indicator */}
            <div style={{
              marginTop: '2rem',
              padding: '1rem',
              backgroundColor: '#0f3460',
              borderRadius: '8px'
            }}>
              <div style={{ color: '#a8b2d1', fontSize: '0.9rem', marginBottom: '0.5rem' }}>
                Roles Completed: {nightStatus.roles_completed.length} / {nightStatus.roles_in_game.length}
              </div>
              <div style={{
                display: 'flex',
                gap: '0.5rem',
                justifyContent: 'center',
                flexWrap: 'wrap'
              }}>
                {nightStatus.roles_in_game.map((role) => (
                  <span
                    key={role}
                    style={{
                      padding: '0.25rem 0.75rem',
                      borderRadius: '4px',
                      fontSize: '0.85rem',
                      backgroundColor: nightStatus.roles_completed.includes(role) ? '#27ae60' : '#34495e',
                      color: 'white'
                    }}
                  >
                    {role}
                  </span>
                ))}
              </div>
            </div>
          </>
        ) : (
          <div style={{
            fontSize: '1.5rem',
            color: '#27ae60',
            fontWeight: 'bold'
          }}>
            Night phase complete! Transitioning to day discussion...
          </div>
        )
        ) : (
          <div style={{ color: '#a8b2d1' }}>Loading night phase...</div>
        )}
      </div>
    </main>
  )
}
