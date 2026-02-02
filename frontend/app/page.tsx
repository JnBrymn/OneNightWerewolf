'use client'

import { useRouter } from 'next/navigation'

export default function Home() {
  const router = useRouter()
  return (
    <main style={{
      padding: '4rem 2rem',
      fontFamily: 'Arial, sans-serif',
      maxWidth: '800px',
      margin: '0 auto',
      textAlign: 'center'
    }}>
      <h1 style={{
        fontSize: '3rem',
        marginBottom: '1rem',
        color: '#2c3e50'
      }}>
        One Night Werewolf
      </h1>

      <p style={{
        fontSize: '1.2rem',
        color: '#7f8c8d',
        marginBottom: '3rem'
      }}>
        A fast-paced game of deduction and deception
      </p>

      <div style={{
        display: 'flex',
        gap: '2rem',
        justifyContent: 'center',
        flexWrap: 'wrap'
      }}>
        <button
          style={{
            padding: '1rem 2rem',
            fontSize: '1.2rem',
            cursor: 'pointer',
            backgroundColor: '#3498db',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            fontWeight: 'bold',
            minWidth: '200px',
            transition: 'background-color 0.3s'
          }}
          onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#2980b9'}
          onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#3498db'}
          onClick={() => router.push('/create')}
        >
          Create Game
        </button>

        <button
          style={{
            padding: '1rem 2rem',
            fontSize: '1.2rem',
            cursor: 'pointer',
            backgroundColor: '#2ecc71',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            fontWeight: 'bold',
            minWidth: '200px',
            transition: 'background-color 0.3s'
          }}
          onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#27ae60'}
          onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#2ecc71'}
          onClick={() => router.push('/join')}
        >
          Join Game
        </button>
      </div>

      <div style={{
        marginTop: '4rem',
        padding: '2rem',
        backgroundColor: '#ecf0f1',
        borderRadius: '8px'
      }}>
        <h2 style={{ color: '#2c3e50', marginBottom: '1rem' }}>How to Play</h2>
        <p style={{ color: '#34495e', lineHeight: '1.6' }}>
          Each player takes on a role: Villager, Werewolf, or special character.
          During the night phase, roles wake up and perform actions.
          During the day, discuss and vote to eliminate the werewolves!
        </p>
      </div>
    </main>
  )
}

