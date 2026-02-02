'use client'

import { useState } from 'react'

export default function Home() {
  const [response, setResponse] = useState('')

  const handlePing = async () => {
    try {
      const res = await fetch('/api/ping')
      const data = await res.json()
      setResponse(data.message)
    } catch (error) {
      setResponse('Error: Could not connect to backend')
    }
  }

  return (
    <main style={{ padding: '2rem', fontFamily: 'Arial, sans-serif' }}>
      <h1>Ping Application</h1>
      <div style={{ marginTop: '2rem' }}>
        <button 
          onClick={handlePing}
          style={{
            padding: '0.5rem 1rem',
            fontSize: '1rem',
            cursor: 'pointer',
            marginRight: '1rem'
          }}
        >
          ping
        </button>
        <input
          type="text"
          value={response}
          readOnly
          placeholder="Response will appear here..."
          style={{
            padding: '0.5rem',
            fontSize: '1rem',
            minWidth: '300px'
          }}
        />
      </div>
    </main>
  )
}

