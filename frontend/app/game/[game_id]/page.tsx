'use client'

import { useParams, useSearchParams } from 'next/navigation'
import GameBoard from '../../../components/game/GameBoard'

export default function Game() {
  const params = useParams()
  const searchParams = useSearchParams()
  const gameId = params.game_id as string

  // Get current player ID from URL first, then fall back to sessionStorage
  const currentPlayerId = searchParams.get('player_id') ||
    (typeof window !== 'undefined' ? sessionStorage.getItem('player_id') : null)

  return <GameBoard gameId={gameId} currentPlayerId={currentPlayerId} />
}
