import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import CreateGame from '@/app/create/page'

const mockPush = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}))

describe('Create Game Page', () => {
  beforeEach(() => {
    mockPush.mockClear()
    global.fetch = jest.fn()
  })

  test('renders page title', () => {
    render(<CreateGame />)
    expect(screen.getByText('Create New Game')).toBeInTheDocument()
  })

  test('has player name input field', () => {
    render(<CreateGame />)
    expect(screen.getByLabelText(/Your Name/i)).toBeInTheDocument()
  })

  test('has number of players slider', () => {
    render(<CreateGame />)
    expect(screen.getByText(/Number of Players:/i)).toBeInTheDocument()
  })

  test('has discussion timer slider', () => {
    render(<CreateGame />)
    expect(screen.getByText(/Discussion Timer:/i)).toBeInTheDocument()
  })

  test('displays role selection grid', () => {
    render(<CreateGame />)
    expect(screen.getByText('Werewolf')).toBeInTheDocument()
    expect(screen.getByText('Villager')).toBeInTheDocument()
    expect(screen.getByText('Seer')).toBeInTheDocument()
  })

  test('shows correct role count validation', () => {
    render(<CreateGame />)
    // Default: 5 players, needs 8 roles, has 8 roles
    expect(screen.getByText(/Total: 8 \/ Required: 8/i)).toBeInTheDocument()
    expect(screen.getByText('✓ Role count is correct!')).toBeInTheDocument()
  })

  test('shows error when name is empty on submit', async () => {
    render(<CreateGame />)
    const submitButton = screen.getByText('Create Game')
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Please enter your name')).toBeInTheDocument()
    })
  })

  test('Create Game button is disabled when role count is wrong', () => {
    render(<CreateGame />)

    // Change player count to 6 (needs 9 roles, but has 8)
    const slider = screen.getByRole('slider', { name: /Number of Players/i })
    fireEvent.change(slider, { target: { value: '6' } })

    const submitButton = screen.getByText('Create Game')
    expect(submitButton).toBeDisabled()
  })

  test('has Cancel button that navigates home', () => {
    render(<CreateGame />)
    const cancelButton = screen.getByText('Cancel')
    fireEvent.click(cancelButton)
    expect(mockPush).toHaveBeenCalledWith('/')
  })

  test('successfully creates game with valid input', async () => {
    const mockGameSetResponse = { game_set_id: 'test-game-123' }
    const mockPlayerResponse = { player_id: 'test-player-123', player_name: 'Alice' }
    const mockJoinResponse = { status: 'joined' }

    ;(global.fetch as jest.Mock)
      .mockResolvedValueOnce({ ok: true, json: async () => mockGameSetResponse })
      .mockResolvedValueOnce({ ok: true, json: async () => mockPlayerResponse })
      .mockResolvedValueOnce({ ok: true, json: async () => mockJoinResponse })

    render(<CreateGame />)

    // Fill in name
    const nameInput = screen.getByLabelText(/Your Name/i)
    fireEvent.change(nameInput, { target: { value: 'Alice' } })

    // Submit
    const submitButton = screen.getByText('Create Game')
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/lobby/test-game-123?player_id=test-player-123')
    })
  })
})
