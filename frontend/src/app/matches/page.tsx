'use client'

import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { matchService } from '@/lib/services/matches'
import { formatCurrency } from '@/lib/utils'
import api from '@/lib/api'
import { 
  TrophyIcon, 
  PlayIcon, 
  ClockIcon, 
  CurrencyDollarIcon,
  ChartBarIcon,
  UserIcon
} from '@heroicons/react/24/outline'

export default function MatchesPage() {
  const { isAuthenticated, isLoading, user } = useAuth()
  const router = useRouter()
  const queryClient = useQueryClient()

  const { data: matchesData, isLoading: loadingMatches } = useQuery({
    queryKey: ['matches'],
    queryFn: () => matchService.getUserMatches(),
    enabled: isAuthenticated,
  }) as { data: { matches: any[], stats: any } | undefined, isLoading: boolean }


  const { data: gamesData, isLoading: loadingGames } = useQuery({
    queryKey: ['games'],
    queryFn: async () => {
      const response = await api.get('/games')
      return response.data
    },
    enabled: isAuthenticated,
  })

  const createMatchMutation = useMutation({
    mutationFn: matchService.createMatch,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['matches'] })
      setForm({ game_type: 'pubg_mobile', match_type: 'solo', entry_fee: 100 })
    },
  })

  const [form, setForm] = useState({
    game_type: 'pubg_mobile',
    match_type: 'solo',
    entry_fee: 100,
  })

  const [selectedGame, setSelectedGame] = useState<any>(null)

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [isAuthenticated, isLoading, router])

  useEffect(() => {
    if (gamesData?.games) {
      const game = gamesData.games.find((g: any) => g.id === form.game_type)
      setSelectedGame(game)
      
      // Reset match type to first available option when game changes
      if (game && game.supported_match_types && game.supported_match_types.length > 0) {
        const currentMatchType = form.match_type
        const isCurrentMatchTypeSupported = game.supported_match_types.includes(currentMatchType)
        
        if (!isCurrentMatchTypeSupported) {
          setForm(prev => ({
            ...prev,
            match_type: game.supported_match_types[0]
          }))
        }
      }
      
      // Validate and adjust entry fee when game changes
      if (game) {
        setForm(prev => {
          let newEntryFee = prev.entry_fee
          
          // Ensure entry fee is within game limits
          if (newEntryFee < game.min_bet) {
            newEntryFee = game.min_bet
          } else if (newEntryFee > game.max_bet) {
            newEntryFee = game.max_bet
          }
          
          return {
            ...prev,
            entry_fee: newEntryFee
          }
        })
      }
    }
  }, [form.game_type, gamesData])

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    createMatchMutation.mutate({
      game_type: form.game_type,
      match_type: form.match_type,
      entry_fee: form.entry_fee,
    })
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-400'
      case 'completed': return 'text-blue-400'
      case 'pending': return 'text-yellow-400'
      default: return 'text-gray-400'
    }
  }

  const getResultColor = (result: string) => {
    switch (result?.toLowerCase()) {
      case 'win':
      case 'won':
      case 'victory': return 'text-green-400'
      case 'loss':
      case 'lost':
      case 'defeat': return 'text-red-400'
      default: return 'text-gray-400'
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
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Matches</h1>
            <p className="text-gray-400">Create and manage your gaming matches</p>
          </div>
          <div className="flex items-center space-x-2 text-gray-300">
            <UserIcon className="w-5 h-5" />
            <span>{user?.username}</span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Matches List */}
          <div className="lg:col-span-2">
            <div className="bg-gray-900 rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-white">Your Matches</h2>
                {matchesData?.stats && (
                  <div className="flex items-center space-x-4 text-sm">
                    <div className="text-center">
                      <div className="text-orange-400 font-bold">{matchesData.stats.total_matches}</div>
                      <div className="text-gray-400">Total</div>
                    </div>
                    <div className="text-center">
                      <div className="text-green-400 font-bold">{matchesData.stats.wins}</div>
                      <div className="text-gray-400">Wins</div>
                    </div>
                    <div className="text-center">
                      <div className="text-blue-400 font-bold">{matchesData.stats.win_rate}%</div>
                      <div className="text-gray-400">Win Rate</div>
                    </div>
                  </div>
                )}
              </div>

              {loadingMatches ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
                  <span className="ml-2 text-gray-400">Loading matches...</span>
                </div>
              ) : matchesData?.matches && matchesData.matches.length > 0 ? (
                <div className="space-y-3">
                  {matchesData.matches.map((match: any) => (
                    <div key={match.id} className="flex items-center justify-between p-4 bg-gray-800 rounded-lg hover:bg-gray-750 transition-colors">
                      <div className="flex items-center space-x-4">
                        <div className="w-12 h-12 bg-gradient-to-r from-orange-500 to-orange-600 rounded-lg flex items-center justify-center">
                          <TrophyIcon className="w-6 h-6 text-white" />
                        </div>
                        <div>
                          <p className="text-white font-medium capitalize">
                            {match.game_type.replace('_', ' ')} • {match.match_type}
                          </p>
                          <div className="flex items-center space-x-4 text-sm">
                            <span className={getStatusColor(match.status)}>
                              {match.status}
                            </span>
                            {match.result && (
                              <span className={getResultColor(match.result)}>
                                {match.result}
                              </span>
                            )}
                            <span className="text-gray-400">
                              {new Date(match.created_at).toLocaleDateString()}
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-gray-300">
                          Entry: {formatCurrency(match.entry_fee)}
                        </p>
                        <p className="text-sm text-orange-400 font-medium">
                          Prize: {formatCurrency(match.prize_pool)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <TrophyIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                  <p className="text-gray-400 mb-2">No matches yet</p>
                  <p className="text-gray-500 text-sm">Create your first match to get started!</p>
                </div>
              )}
            </div>
          </div>

          {/* Create Match Form */}
          <div>
            <div className="bg-gray-900 rounded-lg shadow p-6 mb-6">
              <h2 className="text-xl font-bold text-white mb-4 flex items-center">
                <PlayIcon className="w-5 h-5 mr-2" />
                Create Match
              </h2>
              <form onSubmit={onSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm text-gray-300 mb-1">Game</label>
                  <select
                    className="w-full bg-gray-800 text-white border border-gray-700 rounded px-3 py-2 focus:border-orange-500 focus:outline-none transition-colors"
                    value={form.game_type}
                    onChange={(e) => setForm({ ...form, game_type: e.target.value })}
                    disabled={loadingGames}
                  >
                    {loadingGames ? (
                      <option value="" disabled>Loading games...</option>
                    ) : (
                      gamesData?.games?.map((game: any) => (
                        <option key={game.id} value={game.id}>
                          {game.name}
                        </option>
                      ))
                    )}
                  </select>
                  {selectedGame && (
                    <p className="text-xs text-gray-500 mt-1">
                      {selectedGame.description}
                    </p>
                  )}
                </div>

                <div>
                  <label className="block text-sm text-gray-300 mb-1">Match Type</label>
                  <select
                    key={`match-type-${form.game_type}`}
                    className="w-full bg-gray-800 text-white border border-gray-700 rounded px-3 py-2 focus:border-orange-500 focus:outline-none transition-colors"
                    value={form.match_type}
                    onChange={(e) => setForm({ ...form, match_type: e.target.value })}
                    disabled={!selectedGame?.supported_match_types || loadingGames}
                  >
                    {loadingGames ? (
                      <option value="" disabled>Loading...</option>
                    ) : !selectedGame?.supported_match_types ? (
                      <option value="" disabled>Select a game first</option>
                    ) : (
                      selectedGame.supported_match_types.map((type: string) => (
                        <option key={type} value={type}>
                          {type.charAt(0).toUpperCase() + type.slice(1).replace('_', ' ')}
                        </option>
                      ))
                    )}
                  </select>
                </div>

                <div>
                  <label className="block text-sm text-gray-300 mb-1">
                    Entry Fee (NGN)
                    {selectedGame && (
                      <span className="text-xs text-gray-500 ml-2">
                        Min: {formatCurrency(selectedGame.min_bet)} - Max: {formatCurrency(selectedGame.max_bet)}
                      </span>
                    )}
                  </label>
                  <input
                    type="number"
                    min={selectedGame?.min_bet || 50}
                    max={selectedGame?.max_bet || 10000}
                    className="w-full bg-gray-800 text-white border border-gray-700 rounded px-3 py-2 focus:border-orange-500 focus:outline-none"
                    value={form.entry_fee}
                    onChange={(e) => setForm({ ...form, entry_fee: Number(e.target.value) })}
                    required
                  />
                </div>

                {selectedGame && (
                  <div className="bg-gray-800 rounded p-3 text-sm">
                    <div className="text-gray-300 mb-1">Prize Pool Estimate:</div>
                    <div className="text-orange-400 font-bold">
                      {formatCurrency(form.entry_fee * 1.8)} - {formatCurrency(form.entry_fee * 2.5)}
                    </div>
                    <div className="text-gray-500 text-xs mt-1">
                      Multiplier varies by match type
                    </div>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={createMatchMutation.isPending}
                  className="w-full bg-gradient-to-r from-orange-500 to-orange-600 text-white px-4 py-3 rounded-md font-medium hover:from-orange-600 hover:to-orange-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                >
                  {createMatchMutation.isPending ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Creating...
                    </>
                  ) : (
                    <>
                      <PlayIcon className="w-4 h-4 mr-2" />
                      Create Match
                    </>
                  )}
                </button>

                {createMatchMutation.isError && (
                  <div className="bg-red-900/50 border border-red-700 rounded p-3">
                    <p className="text-red-300 text-sm">
                      Failed to create match. Check your balance and try again.
                    </p>
                  </div>
                )}

                {createMatchMutation.isSuccess && (
                  <div className="bg-green-900/50 border border-green-700 rounded p-3">
                    <p className="text-green-300 text-sm">
                      Match created successfully! Good luck!
                    </p>
                  </div>
                )}
              </form>
            </div>

            {/* Quick Stats */}
            {matchesData?.stats && (
              <div className="bg-gray-900 rounded-lg shadow p-6">
                <h3 className="text-lg font-bold text-white mb-4 flex items-center">
                  <ChartBarIcon className="w-5 h-5 mr-2" />
                  Your Stats
                </h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Total Bets:</span>
                    <span className="text-white">{formatCurrency(matchesData.stats.total_bets)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Total Winnings:</span>
                    <span className="text-green-400">{formatCurrency(matchesData.stats.total_winnings)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Net Profit:</span>
                    <span className={matchesData.stats.net_profit >= 0 ? 'text-green-400' : 'text-red-400'}>
                      {formatCurrency(matchesData.stats.net_profit)}
                    </span>
                  </div>
                  <div className="border-t border-gray-700 pt-3">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Win Rate:</span>
                      <span className="text-orange-400 font-bold">{matchesData.stats.win_rate}%</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}