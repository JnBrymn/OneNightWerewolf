'use client'

import { useEffect, useState } from 'react'
import PlayerGrid from './PlayerGrid'
import AccruedActionsDisplay from './AccruedActionsDisplay'
import PhaseIndicator from './PhaseIndicator'
import ActionOverlay from './ActionOverlay'
import RoleActionHandler from './actions/RoleActionHandler'
import RoleReveal from './RoleReveal'
import WaitingForPlayers from './WaitingForPlayers'

interface Game {
  game_id: string
  game_set_id: string
  state: string | null
  current_role_step: string | null
  all_players_acknowledged_roles?: boolean
}

interface PlayerRole {
  player_role_id: string
  game_id: string
  player_id: string
  initial_role: string
  current_role: string
  team: string
  role_revealed?: boolean
}

interface Player {
  player_id: string
  player_name: string
  avatar_url: string | null
}

interface AvailableActions {
  actionable_players: { player_id: string, player_name: string | null }[]
  actionable_center_cards: number[]
  instructions: string
}

interface Action {
  action_type: string
  description: string
}

const TEAM_COLORS: { [key: string]: string } = {
  'werewolf': '#e74c3c',
  'village': '#3498db',
  'tanner': '#95a5a6',
}

interface GameBoardProps {
  gameId: string
  currentPlayerId: string | null
}

export default function GameBoard({ gameId, currentPlayerId }: GameBoardProps) {
  const [game, setGame] = useState<Game | null>(null)
  const [playerRole, setPlayerRole] = useState<PlayerRole | null>(null)
  const [players, setPlayers] = useState<Player[]>([])
  const [availableActions, setAvailableActions] = useState<AvailableActions | null>(null)
  const [accruedActions, setAccruedActions] = useState<Action[]>([])
  const [nightInfo, setNightInfo] = useState<any>(null)
  const [showRoleReveal, setShowRoleReveal] = useState(true)
  const [showWaitingForPlayers, setShowWaitingForPlayers] = useState(false)
  const [showActionOverlay, setShowActionOverlay] = useState(false)
  const [actionInProgress, setActionInProgress] = useState(false) // Track if user is in middle of action
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Fetch game state
  useEffect(() => {
    if (!gameId) return

    async function fetchGame() {
      try {
        const response = await fetch(`/api/games/${gameId}`)
        if (!response.ok) throw new Error('Failed to fetch game')
        const data = await response.json()
        setGame(data)

        if (data.all_players_acknowledged_roles) {
          setShowWaitingForPlayers(false)
        }
        
        // If game is in NIGHT state but current_role_step is null, initialize night phase
        if (data.state === 'NIGHT' && !data.current_role_step) {
          try {
            await fetch(`/api/games/${gameId}/night-status`)
            // This will trigger initialization on the backend
          } catch (err) {
            console.error('Failed to initialize night phase:', err)
          }
        }
      } catch (err: any) {
        setError(err.message)
      }
    }

    fetchGame()
    // Poll every 1 second to catch simulated role completions quickly
    const interval = setInterval(fetchGame, 1000)
    return () => clearInterval(interval)
  }, [gameId])

  // Fetch player role
  useEffect(() => {
    if (!gameId || !currentPlayerId) return

    async function fetchPlayerRole() {
      try {
        const response = await fetch(`/api/games/${gameId}/players/${currentPlayerId}/role`)
        if (!response.ok) throw new Error('Failed to fetch your role')
        const data = await response.json()
        setPlayerRole(data)
        setShowRoleReveal(!data.role_revealed)
        setLoading(false)
      } catch (err: any) {
        setError(err.message)
        setLoading(false)
      }
    }

    fetchPlayerRole()
  }, [gameId, currentPlayerId])

  // If player already acknowledged role but not everyone has, show waiting screen (e.g. after refresh)
  useEffect(() => {
    if (!game || !playerRole || showRoleReveal) return
    if (playerRole.role_revealed && game.all_players_acknowledged_roles === false) {
      setShowWaitingForPlayers(true)
    }
  }, [game, playerRole, showRoleReveal])

  // Fetch players
  useEffect(() => {
    if (!game?.game_set_id) return

    async function fetchPlayers() {
      try {
        const response = await fetch(`/api/game-sets/${game.game_set_id}/players`)
        if (!response.ok) throw new Error('Failed to fetch players')
        const data = await response.json()
        setPlayers(data.players || [])
      } catch (err) {
        console.error('Failed to fetch players:', err)
      }
    }

    fetchPlayers()
    const interval = setInterval(fetchPlayers, 2000)
    return () => clearInterval(interval)
  }, [game?.game_set_id])

  // Fetch available actions
  useEffect(() => {
    if (!gameId || !currentPlayerId || !game || game.state !== 'NIGHT') {
      setAvailableActions(null)
      // Don't close overlay if action is in progress
      if (!actionInProgress) {
        setShowActionOverlay(false)
      }
      return
    }

    async function fetchAvailableActions() {
      try {
        const response = await fetch(`/api/games/${gameId}/players/${currentPlayerId}/available-actions`)
        if (!response.ok) return
        const data = await response.json()
        setAvailableActions(data)
        
        // Show overlay if it's player's turn (regardless of whether they have actionable items)
        // Even info-display roles (like multiple werewolves) need the overlay
        const isPlayerTurn = game.current_role_step && 
                            playerRole?.current_role && 
                            game.current_role_step === playerRole.current_role
        const isNightInfoRole = playerRole?.current_role && nightInfoRoles.includes(playerRole.current_role)
        const nightActionDone = isNightInfoRole && nightInfo?.night_action_completed

        if (isPlayerTurn && !showRoleReveal && !nightActionDone) {
          // Show overlay when it's the player's turn and (for info roles) they haven't acked yet
          setShowActionOverlay(true)
          setActionInProgress(true)
        } else if (!actionInProgress) {
          // Only close overlay if action is not in progress
          // This prevents auto-closing when action completes but user hasn't clicked OK yet
          setShowActionOverlay(false)
        }
      } catch (err) {
        console.error('Failed to fetch available actions:', err)
      }
    }

    fetchAvailableActions()
    // Poll every 1 second to catch simulated role completions quickly
    const interval = setInterval(fetchAvailableActions, 1000)
    return () => clearInterval(interval)
  }, [gameId, currentPlayerId, game?.state, game?.current_role_step, playerRole?.current_role, showRoleReveal, actionInProgress, nightInfo?.night_action_completed])

  // Fetch accrued actions
  useEffect(() => {
    if (!gameId || !currentPlayerId) return

    async function fetchAccruedActions() {
      try {
        const response = await fetch(`/api/games/${gameId}/players/${currentPlayerId}/actions`)
        if (!response.ok) return
        const data = await response.json()
        setAccruedActions(data.actions || [])
      } catch (err) {
        console.error('Failed to fetch accrued actions:', err)
      }
    }

    fetchAccruedActions()
    const interval = setInterval(fetchAccruedActions, 2000)
    return () => clearInterval(interval)
  }, [gameId, currentPlayerId])

  // Fetch night info for roles that need it (Werewolf, Minion, Mason, Insomniac)
  const nightInfoRoles = ['Werewolf', 'Minion', 'Mason', 'Insomniac']
  useEffect(() => {
    if (!gameId || !currentPlayerId || !game || game.state !== 'NIGHT') {
      setNightInfo(null)
      return
    }
    const isNightInfoRole = playerRole?.current_role && nightInfoRoles.includes(playerRole.current_role)
    if (game.current_role_step !== playerRole?.current_role || !isNightInfoRole) {
      setNightInfo(null)
      return
    }

    async function fetchNightInfo() {
      try {
        const response = await fetch(`/api/games/${gameId}/players/${currentPlayerId}/night-info`)
        if (!response.ok) return
        const data = await response.json()
        setNightInfo(data)
      } catch (err) {
        console.error('Failed to fetch night info:', err)
      }
    }

    fetchNightInfo()
    const interval = setInterval(fetchNightInfo, 1000)
    return () => clearInterval(interval)
  }, [gameId, currentPlayerId, game?.state, game?.current_role_step, playerRole?.current_role])

  async function handleRoleAcknowledge() {
    try {
      const response = await fetch(
        `/api/games/${gameId}/players/${currentPlayerId}/acknowledge-role`,
        { method: 'POST' }
      )
      if (!response.ok) throw new Error('Failed to acknowledge role')
      setShowRoleReveal(false)
      setShowWaitingForPlayers(true)
    } catch (err: any) {
      setError(err?.message ?? 'Something went wrong')
    }
  }

  function handleActionComplete() {
    setActionInProgress(false)
    setShowActionOverlay(false)

    // Mark night-info role as completed locally so the overlay stays closed
    // (polling may still show NIGHT + this role until game state refreshes)
    if (nightInfoRoles.includes(playerRole?.current_role ?? '')) {
      setNightInfo((prev: any) => (prev ? { ...prev, night_action_completed: true } : null))
    }

    setTimeout(() => {
      fetch(`/api/games/${gameId}/players/${currentPlayerId}/available-actions`)
        .then(r => r.json())
        .then(data => setAvailableActions(data))
        .catch(console.error)
    }, 500)
  }

  if (loading || !game || !playerRole) {
    return (
      <main style={{
        padding: '2rem',
        fontFamily: 'Arial, sans-serif',
        textAlign: 'center',
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#1a1a2e'
      }}>
        <h1 style={{ color: '#ffffff' }}>Loading...</h1>
      </main>
    )
  }

  if (error) {
    return (
      <main style={{
        padding: '2rem',
        fontFamily: 'Arial, sans-serif',
        textAlign: 'center',
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#1a1a2e'
      }}>
        <h1 style={{ color: '#e74c3c', marginBottom: '1rem' }}>Error</h1>
        <p style={{ color: '#ffffff' }}>{error}</p>
      </main>
    )
  }

  const teamColor = TEAM_COLORS[playerRole.team] || '#34495e'
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

  // Show role reveal if not yet acknowledged
  if (showRoleReveal) {
    return (
      <RoleReveal
        role={playerRole.initial_role}
        roleDescription={ROLE_DESCRIPTIONS[playerRole.initial_role] || ''}
        teamColor={teamColor}
        onAcknowledge={handleRoleAcknowledge}
      />
    )
  }

  // Waiting for all players to acknowledge their roles before night begins
  if (showWaitingForPlayers) {
    return (
      <WaitingForPlayers teamColor={teamColor} />
    )
  }

  const enabledPlayerIds = availableActions?.actionable_players.map(p => p.player_id) || []
  const isPlayerTurn = game.state === 'NIGHT' && game.current_role_step === playerRole.current_role

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
      <PhaseIndicator state={game.state} currentRoleStep={game.current_role_step} />

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
            Your Role: <span style={{ color: teamColor }}>{playerRole.initial_role}</span>
          </div>
          <div style={{ color: '#a8b2d1', lineHeight: '1.6' }}>
            {ROLE_DESCRIPTIONS[playerRole.initial_role] || 'No description available.'}
          </div>
        </div>

        <AccruedActionsDisplay actions={accruedActions} />
      </div>

      <div style={{
        backgroundColor: '#16213e',
        padding: '1.5rem',
        borderRadius: '12px',
        border: '2px solid #0f3460',
        marginBottom: '2rem'
      }}>
        <div style={{ color: '#ffffff', fontWeight: 'bold', marginBottom: '1rem' }}>
          Players
        </div>
        <PlayerGrid
          players={players}
          currentPlayerId={currentPlayerId}
          enabledPlayerIds={enabledPlayerIds}
        />
      </div>

      {availableActions && !isPlayerTurn && (
        <div style={{
          backgroundColor: '#0f3460',
          padding: '1.5rem',
          borderRadius: '12px',
          textAlign: 'center',
          color: '#a8b2d1'
        }}>
          {availableActions.instructions || `Waiting for ${game.current_role_step || 'other players'} to complete their action...`}
        </div>
      )}

      {showActionOverlay && (
        <ActionOverlay
          isOpen={showActionOverlay}
          onClose={() => {
            const infoRole = playerRole?.current_role && nightInfoRoles.includes(playerRole.current_role)
            if (infoRole && nightInfo?.night_action_completed) setShowActionOverlay(false)
            else if (!infoRole) setShowActionOverlay(false)
          }}
          canClose={nightInfoRoles.includes(playerRole?.current_role ?? '') ? (nightInfo?.night_action_completed ?? false) : true}
          showOkButton={false}
        >
          <RoleActionHandler
            role={playerRole.current_role}
            currentRoleStep={game.current_role_step}
            gameId={gameId}
            playerId={currentPlayerId || ''}
            nightInfo={nightInfo}
            availableActions={availableActions}
            onActionComplete={handleActionComplete}
          />
        </ActionOverlay>
      )}
    </main>
  )
}
