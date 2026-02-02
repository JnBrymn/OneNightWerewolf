import { render, screen, fireEvent } from '@testing-library/react'
import Home from '@/app/page'

// Mock useRouter
const mockPush = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}))

describe('Landing Page', () => {
  beforeEach(() => {
    mockPush.mockClear()
  })

  test('renders page title', () => {
    render(<Home />)
    expect(screen.getByText('One Night Werewolf')).toBeInTheDocument()
  })

  test('renders game description', () => {
    render(<Home />)
    expect(screen.getByText('A fast-paced game of deduction and deception')).toBeInTheDocument()
  })

  test('has Create Game button', () => {
    render(<Home />)
    const button = screen.getByText('Create Game')
    expect(button).toBeInTheDocument()
  })

  test('has Join Game button', () => {
    render(<Home />)
    const button = screen.getByText('Join Game')
    expect(button).toBeInTheDocument()
  })

  test('Create Game button navigates to /create', () => {
    render(<Home />)
    const button = screen.getByText('Create Game')
    fireEvent.click(button)
    expect(mockPush).toHaveBeenCalledWith('/create')
  })

  test('Join Game button navigates to /join', () => {
    render(<Home />)
    const button = screen.getByText('Join Game')
    fireEvent.click(button)
    expect(mockPush).toHaveBeenCalledWith('/join')
  })

  test('renders How to Play section', () => {
    render(<Home />)
    expect(screen.getByText('How to Play')).toBeInTheDocument()
  })
})
