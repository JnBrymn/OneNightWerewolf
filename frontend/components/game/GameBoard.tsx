'use client'

import { useEffect, useState } from 'react'
import PlayerGrid from './PlayerGrid'
import AccruedActionsDisplay from './AccruedActionsDisplay'
import PhaseIndicator from './PhaseIndicator'
import ActionOverlay from './ActionOverlay'
import RoleActionHandler from './actions/RoleActionHandler'
import RoleReveal from './RoleReveal'
import WaitingForPlayers from './WaitingForPlayers'
import TimerDisplay from './TimerDisplay'
import ResultsDisplay from './ResultsDisplay'

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
  const [discussionStatus, setDiscussionStatus] = useState<{
    time_remaining_seconds: number
    state: string
    vote_now_count?: number
    total_players?: number
    vote_now_majority?: number
    current_player_voted_now?: boolean
  } | null>(null)
  const [votes, setVotes] = useState<{ votes_cast: number; total_players: number } | null>(null)
  const [results, setResults] = useState<{
    deaths: string[]
    winning_team: string
    players: { player_id: string; player_name: string; initial_role: string; current_role: string; team: string; died: boolean; won: boolean }[]
    vote_summary: { [playerId: string]: number }
  } | null>(null)
  const [votedFor, setVotedFor] = useState<string | null>(null)

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
    const gameSetId = game?.game_set_id
    if (!gameSetId) return

    async function fetchPlayers() {
      try {
        const response = await fetch(`/api/game-sets/${gameSetId}/players`)
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

    const currentGame = game
    async function fetchAvailableActions() {
      try {
        const response = await fetch(`/api/games/${gameId}/players/${currentPlayerId}/available-actions`)
        if (!response.ok) return
        const data = await response.json()
        setAvailableActions(data)
        
        // Show overlay only when it's this player's turn: match by *initial* role so e.g. Robber who stole Insomniac doesn't act at Insomniac step
        const isPlayerTurn = currentGame.current_role_step && 
                            playerRole?.initial_role && 
                            currentGame.current_role_step === playerRole.initial_role
        const isNightInfoRole = playerRole?.initial_role && nightInfoRoles.includes(playerRole.initial_role)
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
  }, [gameId, currentPlayerId, game?.state, game?.current_role_step, playerRole?.initial_role, showRoleReveal, actionInProgress, nightInfo?.night_action_completed])

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

  // Fetch discussion timer and vote-now status when in DAY_DISCUSSION
  useEffect(() => {
    if (!gameId || !game || game.state !== 'DAY_DISCUSSION') {
      setDiscussionStatus(null)
      return
    }
    async function fetchDiscussion() {
      try {
        const url = currentPlayerId
          ? `/api/games/${gameId}/discussion-status?player_id=${encodeURIComponent(currentPlayerId)}`
          : `/api/games/${gameId}/discussion-status`
        const res = await fetch(url)
        if (res.ok) {
          const data = await res.json()
          setDiscussionStatus(data)
        }
      } catch (e) {
        console.error(e)
      }
    }
    fetchDiscussion()
    const interval = setInterval(fetchDiscussion, 1000)
    return () => clearInterval(interval)
  }, [gameId, game?.state, currentPlayerId])

  // Fetch votes when in DAY_VOTING
  useEffect(() => {
    if (!gameId || !game || game.state !== 'DAY_VOTING') {
      setVotes(null)
      setVotedFor(null)
      return
    }
    async function fetchVotes() {
      try {
        const res = await fetch(`/api/games/${gameId}/votes`)
        if (res.ok) {
          const data = await res.json()
          setVotes({ votes_cast: data.votes_cast, total_players: data.total_players })
          const myVote = data.votes?.find((v: { voter_id: string }) => v.voter_id === currentPlayerId)
          if (myVote) setVotedFor(myVote.target_id)
        }
      } catch (e) {
        console.error(e)
      }
    }
    fetchVotes()
    const interval = setInterval(fetchVotes, 2000)
    return () => clearInterval(interval)
  }, [gameId, game?.state, currentPlayerId])

  // Fetch results when in RESULTS
  useEffect(() => {
    if (!gameId || !game || game.state !== 'RESULTS') {
      setResults(null)
      return
    }
    async function fetchResults() {
      try {
        const res = await fetch(`/api/games/${gameId}/results`)
        if (res.ok) {
          const data = await res.json()
          setResults(data)
        }
      } catch (e) {
        console.error(e)
      }
    }
    fetchResults()
  }, [gameId, game?.state])

  // Fetch night info for roles that need it (Werewolf, Minion, Mason, Insomniac)
  const nightInfoRoles = ['Werewolf', 'Minion', 'Mason', 'Insomniac']
  useEffect(() => {
    if (!gameId || !currentPlayerId || !game || game.state !== 'NIGHT') {
      setNightInfo(null)
      return
    }
    const isNightInfoRole = playerRole?.initial_role && nightInfoRoles.includes(playerRole.initial_role)
    if (game.current_role_step !== playerRole?.initial_role || !isNightInfoRole) {
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
  }, [gameId, currentPlayerId, game?.state, game?.current_role_step, playerRole?.initial_role])

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

  async function handleVoteNow() {
    if (!currentPlayerId || discussionStatus?.current_player_voted_now) return
    try {
      const res = await fetch(`/api/games/${gameId}/players/${currentPlayerId}/vote-now`, {
        method: 'POST',
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        setError(err.detail ?? 'Failed to record vote now')
        return
      }
      const data = await res.json()
      setDiscussionStatus((prev) => prev ? { ...prev, ...data, current_player_voted_now: true } : null)
      if (data.state === 'DAY_VOTING') setGame((g) => g ? { ...g, state: 'DAY_VOTING' } : null)
    } catch (e: any) {
      setError(e?.message ?? 'Failed to record vote now')
    }
  }

  async function handleVote(targetPlayerId: string) {
    const name = players.find(p => p.player_id === targetPlayerId)?.player_name ?? 'this player'
    if (!window.confirm(`Vote to eliminate ${name}?`)) return
    try {
      const res = await fetch(`/api/games/${gameId}/players/${currentPlayerId}/vote`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_player_id: targetPlayerId }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        setError(err.detail ?? 'Failed to vote')
        return
      }
      setVotedFor(targetPlayerId)
    } catch (e: any) {
      setError(e?.message ?? 'Failed to vote')
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

  // Results phase
  if (game.state === 'RESULTS' && results) {
    return (
      <ResultsDisplay
        deaths={results.deaths}
        winning_team={results.winning_team}
        players={results.players}
        vote_summary={results.vote_summary}
        onPlayAgain={undefined}
        onEndSet={undefined}
      />
    )
  }

  // Day voting phase
  if (game.state === 'DAY_VOTING') {
    const voteEnabledIds = players.filter(p => p.player_id !== currentPlayerId).map(p => p.player_id)
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
        <PhaseIndicator state={game.state} currentRoleStep={null} />
        {votes && (
          <div style={{ textAlign: 'center', color: '#a8b2d1', marginBottom: '1rem' }}>
            {votes.votes_cast}/{votes.total_players} players have voted
            {votedFor && ' — You voted for ' + (players.find(p => p.player_id === votedFor)?.player_name ?? '')}
          </div>
        )}
        <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
          <div style={{ backgroundColor: '#16213e', padding: '1.5rem', borderRadius: '12px', border: `2px solid ${teamColor}` }}>
            <div style={{ fontSize: '1.2rem', color: '#ffffff', fontWeight: 'bold' }}>Your Role: <span style={{ color: teamColor }}>{playerRole.initial_role}</span></div>
          </div>
          <AccruedActionsDisplay actions={accruedActions} />
        </div>
        <div style={{ backgroundColor: '#16213e', padding: '1.5rem', borderRadius: '12px', border: '2px solid #0f3460' }}>
          <div style={{ color: '#ffffff', fontWeight: 'bold', marginBottom: '1rem' }}>Vote to eliminate</div>
          <PlayerGrid
            players={players}
            currentPlayerId={currentPlayerId}
            enabledPlayerIds={votedFor ? [] : voteEnabledIds}
            onClick={votedFor ? undefined : handleVote}
          />
        </div>
      </main>
    )
  }

  // Day discussion phase
  if (game.state === 'DAY_DISCUSSION') {
    const votedNow = discussionStatus?.current_player_voted_now ?? false
    const voteNowMajority = discussionStatus?.vote_now_majority ?? 0
    const voteNowCount = discussionStatus?.vote_now_count ?? 0
    const needMore = Math.max(0, voteNowMajority - voteNowCount)
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
        <PhaseIndicator state={game.state} currentRoleStep={null} />
        {discussionStatus && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '1.5rem',
            marginBottom: '1.5rem',
            flexWrap: 'wrap'
          }}>
            <TimerDisplay timeRemainingSeconds={discussionStatus.time_remaining_seconds} />
            <button
              type="button"
              onClick={handleVoteNow}
              disabled={votedNow}
              style={{
                padding: '0.5rem 1rem',
                fontSize: '1rem',
                backgroundColor: votedNow ? '#555' : '#3498db',
                color: '#fff',
                border: 'none',
                borderRadius: '8px',
                cursor: votedNow ? 'default' : 'pointer',
              }}
            >
              {votedNow ? `Waiting for ${needMore} more to have a majority` : 'Vote Now'}
            </button>
          </div>
        )}
        <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
          <div style={{ backgroundColor: '#16213e', padding: '1.5rem', borderRadius: '12px', border: `2px solid ${teamColor}` }}>
            <div style={{ fontSize: '1.2rem', color: '#ffffff', fontWeight: 'bold' }}>Your Role: <span style={{ color: teamColor }}>{playerRole.initial_role}</span></div>
          </div>
          <AccruedActionsDisplay actions={accruedActions} />
        </div>
        <div style={{ backgroundColor: '#16213e', padding: '1.5rem', borderRadius: '12px', border: '2px solid #0f3460' }}>
          <div style={{ color: '#ffffff', fontWeight: 'bold', marginBottom: '1rem' }}>Players</div>
          <PlayerGrid players={players} currentPlayerId={currentPlayerId} enabledPlayerIds={[]} />
        </div>
      </main>
    )
  }

  const enabledPlayerIds = availableActions?.actionable_players.map(p => p.player_id) || []
  const isPlayerTurn = game.state === 'NIGHT' && game.current_role_step === playerRole?.initial_role

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
            const infoRole = playerRole?.initial_role && nightInfoRoles.includes(playerRole.initial_role)
            if (infoRole && nightInfo?.night_action_completed) setShowActionOverlay(false)
            else if (!infoRole) setShowActionOverlay(false)
          }}
          canClose={nightInfoRoles.includes(playerRole?.initial_role ?? '') ? (nightInfo?.night_action_completed ?? false) : true}
          showOkButton={false}
        >
          <RoleActionHandler
            role={game.current_role_step === playerRole?.initial_role ? game.current_role_step : (playerRole?.current_role ?? '')}
            currentRoleStep={game.current_role_step}
            gameId={gameId}
            playerId={currentPlayerId || ''}
            nightInfo={nightInfo}
            availableActions={availableActions ?? undefined}
            onActionComplete={handleActionComplete}
          />
        </ActionOverlay>
      )}
    </main>
  )
}
