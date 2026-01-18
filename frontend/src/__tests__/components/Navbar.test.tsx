import { render, screen } from '@testing-library/react'
import { Navbar } from '@/components/Navbar'

// Mock the AuthContext
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    user: null,
    isAuthenticated: false,
    login: jest.fn(),
    logout: jest.fn(),
  }),
}))

describe('Navbar', () => {
  it('renders navigation links', () => {
    render(<Navbar />)
    
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Matches')).toBeInTheDocument()
    expect(screen.getByText('Leaderboard')).toBeInTheDocument()
    expect(screen.getByText('Wallet')).toBeInTheDocument()
  })

  it('shows login button when user is not authenticated', () => {
    render(<Navbar />)
    
    expect(screen.getByText('Login')).toBeInTheDocument()
  })

  it('shows user menu when user is authenticated', () => {
    // Mock authenticated user
    jest.doMock('@/contexts/AuthContext', () => ({
      useAuth: () => ({
        user: { email: 'test@example.com', username: 'testuser' },
        isAuthenticated: true,
        login: jest.fn(),
        logout: jest.fn(),
      }),
    }))

    render(<Navbar />)
    
    expect(screen.getByText('testuser')).toBeInTheDocument()
  })
})
