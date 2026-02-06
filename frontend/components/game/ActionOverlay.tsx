'use client'

import { ReactNode } from 'react'

interface ActionOverlayProps {
  isOpen: boolean
  onClose: () => void
  children: ReactNode
  canClose?: boolean
  showOkButton?: boolean
}

export default function ActionOverlay({ isOpen, onClose, children, canClose = true, showOkButton = true }: ActionOverlayProps) {
  if (!isOpen) return null

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.9)',
      zIndex: 1000,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '2rem'
    }}>
      <div style={{
        backgroundColor: '#16213e',
        padding: '2rem',
        borderRadius: '16px',
        border: '2px solid #e94560',
        maxWidth: '800px',
        width: '100%',
        maxHeight: '90vh',
        overflow: 'auto'
      }}>
        {children}
        {canClose && showOkButton && (
          <div style={{ marginTop: '1.5rem', textAlign: 'center' }}>
            <button
              onClick={onClose}
              style={{
                padding: '0.75rem 1.5rem',
                backgroundColor: '#e94560',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontSize: '1rem',
                fontWeight: 'bold',
                cursor: 'pointer'
              }}
            >
              OK
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
