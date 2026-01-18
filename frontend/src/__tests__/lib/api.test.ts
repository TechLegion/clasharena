import { api } from '@/lib/api'

// Mock fetch
global.fetch = jest.fn()

describe('API', () => {
  beforeEach(() => {
    (fetch as jest.Mock).mockClear()
  })

  describe('auth', () => {
    it('should login user successfully', async () => {
      const mockResponse = {
        access_token: 'mock-token',
        token_type: 'bearer',
        user: { id: 1, email: 'test@example.com' }
      }

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await api.auth.login('test@example.com', 'password123')

      expect(fetch).toHaveBeenCalledWith('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: 'test@example.com',
          password: 'password123'
        })
      })

      expect(result).toEqual(mockResponse)
    })

    it('should handle login error', async () => {
      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Invalid credentials' }),
      })

      await expect(api.auth.login('test@example.com', 'wrongpassword'))
        .rejects.toThrow('Invalid credentials')
    })
  })

  describe('wallet', () => {
    it('should get wallet balance', async () => {
      const mockResponse = { balance: 1000, currency: 'NGN' }

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await api.wallet.getBalance()

      expect(fetch).toHaveBeenCalledWith('/api/wallet/balance', {
        method: 'GET',
        headers: { 'Authorization': 'Bearer null' }
      })

      expect(result).toEqual(mockResponse)
    })
  })

  describe('matches', () => {
    it('should get user matches', async () => {
      const mockResponse = [
        { id: 1, game_type: 'clash_royale', status: 'active' }
      ]

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await api.matches.getMatches()

      expect(fetch).toHaveBeenCalledWith('/api/matches', {
        method: 'GET',
        headers: { 'Authorization': 'Bearer null' }
      })

      expect(result).toEqual(mockResponse)
    })
  })
})
