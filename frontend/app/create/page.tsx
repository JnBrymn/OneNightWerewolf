'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

const AVAILABLE_ROLES = [
  'Werewolf',
  'Villager',
  'Seer',
  'Robber',
  'Troublemaker',
  'Drunk',
  'Insomniac',
  'Minion',
  'Mason',
  'Tanner',
  'Hunter'
]

export default function CreateGame() {
  const router = useRouter()
  const [numPlayers, setNumPlayers] = useState(5)
  const [discussionTimer, setDiscussionTimer] = useState(300)
  const [selectedRoles, setSelectedRoles] = useState<{ [key: string]: number }>({
    'Werewolf': 2,
    'Villager': 3,
    'Seer': 1,
    'Robber': 1,
    'Troublemaker': 1,
  })
  const [error, setError] = useState('')
  const [isCreating, setIsCreating] = useState(false)

  const totalRoles = Object.values(selectedRoles).reduce((sum, count) => sum + count, 0)
  const requiredRoles = numPlayers + 3

  const handleRoleChange = (role: string, value: number) => {
    const newValue = Math.max(0, value)
    setSelectedRoles(prev => ({
      ...prev,
      [role]: newValue
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (totalRoles !== requiredRoles) {
      setError(`Total roles (${totalRoles}) must equal players + 3 (${requiredRoles})`)
      return
    }

    // Build roles array
    const rolesArray: string[] = []
    Object.entries(selectedRoles).forEach(([role, count]) => {
      for (let i = 0; i < count; i++) {
        rolesArray.push(role)
      }
    })

    setIsCreating(true)
    try {
      const response = await fetch('/api/game-sets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          num_players: numPlayers,
          selected_roles: rolesArray,
          discussion_timer_seconds: discussionTimer
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to create game')
      }

      const data = await response.json()
      // Redirect to lobby page with game_set_id
      router.push(`/lobby/${data.game_set_id}`)
    } catch (err: any) {
      setError(err.message || 'Failed to create game')
      setIsCreating(false)
    }
  }

  return (
    <main style={{
      padding: '2rem',
      fontFamily: 'Arial, sans-serif',
      maxWidth: '800px',
      margin: '0 auto'
    }}>
      <h1 style={{ fontSize: '2rem', marginBottom: '2rem', color: '#2c3e50' }}>
        Create New Game
      </h1>

      <form onSubmit={handleSubmit}>
        {/* Number of Players */}
        <div style={{ marginBottom: '2rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
            Number of Players: {numPlayers}
          </label>
          <input
            type="range"
            min="3"
            max="10"
            value={numPlayers}
            onChange={(e) => setNumPlayers(Number(e.target.value))}
            style={{ width: '100%' }}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', color: '#7f8c8d' }}>
            <span>3</span>
            <span>10</span>
          </div>
        </div>

        {/* Discussion Timer */}
        <div style={{ marginBottom: '2rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
            Discussion Timer: {Math.floor(discussionTimer / 60)}:{String(discussionTimer % 60).padStart(2, '0')}
          </label>
          <input
            type="range"
            min="60"
            max="600"
            step="30"
            value={discussionTimer}
            onChange={(e) => setDiscussionTimer(Number(e.target.value))}
            style={{ width: '100%' }}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', color: '#7f8c8d' }}>
            <span>1:00</span>
            <span>10:00</span>
          </div>
        </div>

        {/* Role Selection */}
        <div style={{ marginBottom: '2rem' }}>
          <h3 style={{ marginBottom: '1rem' }}>
            Select Roles (Total: {totalRoles} / Required: {requiredRoles})
          </h3>
          <div style={{
            backgroundColor: totalRoles === requiredRoles ? '#d4edda' : '#f8d7da',
            padding: '0.5rem',
            borderRadius: '4px',
            marginBottom: '1rem',
            color: totalRoles === requiredRoles ? '#155724' : '#721c24'
          }}>
            {totalRoles === requiredRoles
              ? '✓ Role count is correct!'
              : `Need ${requiredRoles - totalRoles > 0 ? 'more' : 'fewer'} ${Math.abs(requiredRoles - totalRoles)} role(s)`
            }
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1rem' }}>
            {AVAILABLE_ROLES.map(role => (
              <div key={role} style={{
                padding: '1rem',
                backgroundColor: '#f8f9fa',
                borderRadius: '8px',
                border: '1px solid #dee2e6'
              }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                  {role}
                </label>
                <input
                  type="number"
                  min="0"
                  max="10"
                  value={selectedRoles[role] || 0}
                  onChange={(e) => handleRoleChange(role, Number(e.target.value))}
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    fontSize: '1rem',
                    border: '1px solid #ced4da',
                    borderRadius: '4px'
                  }}
                />
              </div>
            ))}
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div style={{
            padding: '1rem',
            backgroundColor: '#f8d7da',
            color: '#721c24',
            borderRadius: '4px',
            marginBottom: '1rem'
          }}>
            {error}
          </div>
        )}

        {/* Submit Button */}
        <div style={{ display: 'flex', gap: '1rem' }}>
          <button
            type="submit"
            disabled={isCreating || totalRoles !== requiredRoles}
            style={{
              padding: '1rem 2rem',
              fontSize: '1.2rem',
              cursor: isCreating || totalRoles !== requiredRoles ? 'not-allowed' : 'pointer',
              backgroundColor: isCreating || totalRoles !== requiredRoles ? '#95a5a6' : '#3498db',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontWeight: 'bold'
            }}
          >
            {isCreating ? 'Creating...' : 'Create Game'}
          </button>

          <button
            type="button"
            onClick={() => router.push('/')}
            style={{
              padding: '1rem 2rem',
              fontSize: '1.2rem',
              cursor: 'pointer',
              backgroundColor: '#95a5a6',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontWeight: 'bold'
            }}
          >
            Cancel
          </button>
        </div>
      </form>
    </main>
  )
}
