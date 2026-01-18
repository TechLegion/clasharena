'use client'

import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { matchService } from '@/lib/services/matches'
import { formatCurrency } from '@/lib/utils'
import { 
  TrophyIcon, 
  UserGroupIcon,
  StarIcon,
  ChartBarIcon,
  FunnelIcon,
  AcademicCapIcon
} from '@heroicons/react/24/outline'

export default function LeaderboardPage() {
  const { isAuthenticated, isLoading } = useAuth()
  const router = useRouter()
  const [selectedGame, setSelectedGame] = useState<string>('')

  const { data: gamesData } = useQuery({
    queryKey: ['games'],
    queryFn: async () => {
      const response = await fetch('/api/v1/matches/games')
      return response.json()
    },
  })

  const { data: leaderboardData, isLoading: loadingLeaderboard } = useQuery({
    queryKey: ['leaderboard', selectedGame],
    queryFn: () => matchService.getLeaderboard({ game_type: selectedGame || undefined }),
    enabled: isAuthenticated,
  })

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [isAuthenticated, isLoading, router])

  const getRankIcon = (index: number) => {
    switch (index) {
      case 0:
        return <TrophyIcon className="w-6 h-6 text-yellow-500" />
      case 1:
        return <StarIcon className="w-6 h-6 text-gray-400" />
      case 2:
        return <AcademicCapIcon className="w-6 h-6 text-orange-600" />
      default:
        return <span className="w-6 h-6 flex items-center justify-center text-gray-500 font-bold text-sm">
          {index + 1}
        </span>
    }
  }

  const getRankColor = (index: number) => {
    switch (index) {
      case 0:
        return 'bg-gradient-to-r from-yellow-600 to-yellow-500'
      case 1:
        return 'bg-gradient-to-r from-gray-400 to-gray-300'
      case 2:
        return 'bg-gradient-to-r from-orange-600 to-orange-500'
      default:
        return 'bg-gray-700'
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-orange-500"></div>
      </div>
    )
  }

  if (!isAuthenticated) return null

  return (
    <div className="min-h-screen bg-black">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Leaderboard</h1>
            <p className="text-gray-400">Top players across all games</p>
          </div>
          <div className="flex items-center space-x-4">
            <ChartBarIcon className="w-6 h-6 text-orange-400" />
            <span className="text-gray-300">Live Rankings</span>
          </div>
        </div>

        {/* Game Filter */}
        <div className="mb-8">
          <div className="bg-gray-900 rounded-lg p-4">
            <div className="flex items-center space-x-4">
              <FunnelIcon className="w-5 h-5 text-gray-400" />
              <span className="text-gray-300 font-medium">Filter by Game:</span>
              <select
                className="bg-gray-800 text-white border border-gray-700 rounded px-3 py-2 focus:border-orange-500 focus:outline-none"
                value={selectedGame}
                onChange={(e) => setSelectedGame(e.target.value)}
              >
                <option value="">All Games</option>
                {gamesData?.games?.map((game: any) => (
                  <option key={game.id} value={game.id}>
                    {game.icon} {game.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Leaderboard */}
        <div className="bg-gray-900 rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-700">
            <h2 className="text-xl font-bold text-white flex items-center">
              <TrophyIcon className="w-5 h-5 mr-2 text-orange-400" />
              {selectedGame ? 
                `${gamesData?.games?.find((g: any) => g.id === selectedGame)?.name} Rankings` : 
                'Overall Rankings'
              }
            </h2>
          </div>

          {loadingLeaderboard ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
              <span className="ml-2 text-gray-400">Loading leaderboard...</span>
            </div>
          ) : leaderboardData?.leaderboard && leaderboardData.leaderboard.length > 0 ? (
            <div className="divide-y divide-gray-700">
              {leaderboardData.leaderboard.map((player: any, index: number) => (
                <div
                  key={player.user_id}
                  className={`p-6 hover:bg-gray-800 transition-colors ${
                    index < 3 ? 'bg-gradient-to-r from-gray-900 to-gray-800' : ''
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className={`w-12 h-12 rounded-full flex items-center justify-center ${getRankColor(index)}`}>
                        {getRankIcon(index)}
                      </div>
                      <div>
                        <h3 className="text-white font-bold text-lg">
                          Player #{player.user_id}
                        </h3>
                        <div className="flex items-center space-x-4 text-sm text-gray-400">
                          <span>{player.games_played} games played</span>
                          <span>•</span>
                          <span>{player.win_rate}% win rate</span>
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center space-x-6">
                        <div className="text-center">
                          <div className="text-2xl font-bold text-orange-400">
                            {player.wins}
                          </div>
                          <div className="text-xs text-gray-400">Wins</div>
                        </div>
                        <div className="text-center">
                          <div className="text-lg font-bold text-green-400">
                            {formatCurrency(player.total_prizes)}
                          </div>
                          <div className="text-xs text-gray-400">Total Prizes</div>
                        </div>
                        <div className="text-center">
                          <div className={`text-lg font-bold ${player.net_profit >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {formatCurrency(player.net_profit)}
                          </div>
                          <div className="text-xs text-gray-400">Net Profit</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <TrophyIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <p className="text-gray-400 mb-2">No rankings available</p>
              <p className="text-gray-500 text-sm">
                {selectedGame ? 'No matches played in this game yet' : 'No matches have been completed yet'}
              </p>
            </div>
          )}
        </div>

        {/* Statistics Summary */}
        {leaderboardData?.leaderboard && leaderboardData.leaderboard.length > 0 && (
          <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-gray-900 rounded-lg p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm">Total Players</p>
                  <p className="text-2xl font-bold text-white">{leaderboardData.count}</p>
                </div>
                <StarIcon className="w-8 h-8 text-orange-400" />
              </div>
            </div>
            
            <div className="bg-gray-900 rounded-lg p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm">Total Prize Pool</p>
                  <p className="text-2xl font-bold text-green-400">
                    {formatCurrency(
                      leaderboardData.leaderboard.reduce((sum: number, player: any) => sum + player.total_prizes, 0)
                    )}
                  </p>
                </div>
                <TrophyIcon className="w-8 h-8 text-yellow-500" />
              </div>
            </div>
            
            <div className="bg-gray-900 rounded-lg p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm">Top Winner</p>
                  <p className="text-2xl font-bold text-orange-400">
                    {leaderboardData.leaderboard[0]?.wins || 0} wins
                  </p>
                </div>
                <TrophyIcon className="w-8 h-8 text-yellow-500" />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}