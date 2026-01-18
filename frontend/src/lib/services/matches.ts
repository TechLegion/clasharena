import api from '../api'
import { Match } from '../types'
import { taskService } from './tasks'

export const matchService = {
  // Get user's matches
  async getUserMatches(): Promise<{ matches: Match[], stats: any }> {
    try {
      const response = await api.get('/matches')
      
      // Direct response (synchronous)
      return response.data.matches ? { matches: response.data.matches, stats: response.data.stats } : response.data
    } catch (error: any) {
      console.error('❌ Error getting user matches:', error)
      console.error('Error details:', error.response?.data)
      // Return empty object on error
      return { matches: [], stats: null }
    }
  },

  // Create a new match
  async createMatch(matchData: {
    game_type: string
    match_type: string
    entry_fee: number
    game_settings?: any
    player_stats?: any
    match_config?: any
  }): Promise<any> {
    try {
      console.log('🚀 Creating match with data:', matchData)
      const response = await api.post('/matches', matchData)
      
      // If it's a task response, poll for result
      if (response.data.task_id) {
        const result = await taskService.pollTask(response.data.task_id)
        return result.success ? result : { success: false, error: 'Match creation failed' }
      }
      
      return response.data
    } catch (error: any) {
      console.error('❌ Error creating match:', error)
      console.error('Error response:', error.response?.data)
      console.error('Error status:', error.response?.status)
      return { success: false, error: error.response?.data?.detail || error.message || 'Network error' }
    }
  },

  // Get leaderboard
  async getLeaderboard(params?: { game_type?: string; match_type?: string; limit?: number }): Promise<any> {
    try {
      const response = await api.get('/leaderboard', { params })
      
      // If it's a task response, poll for result
      if (response.data.task_id) {
        const result = await taskService.pollTask(response.data.task_id)
        return result.success ? result : { leaderboard: [], count: 0 }
      }
      
      return response.data
    } catch (error) {
      console.error('Error getting leaderboard:', error)
      // Return mock data for development
      return {
        leaderboard: [
          { user_id: '1', wins: 10, total_prizes: 5000, games_played: 15 },
          { user_id: '2', wins: 8, total_prizes: 3200, games_played: 12 },
          { user_id: '3', wins: 6, total_prizes: 2400, games_played: 10 }
        ],
        count: 3
      }
    }
  }
}
