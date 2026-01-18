'use client'

import { useState, useEffect } from 'react'
import {
  TrophyIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  EyeIcon,
  PencilIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline'

interface Match {
  id: string
  user_id: string
  game_type: string
  match_type: string
  status: string
  bet_amount: number
  potential_winnings: number
  result?: string
  created_at: string
  updated_at: string
  user?: {
    username: string
    email: string
  }
}

export default function AdminMatches() {
  const [matches, setMatches] = useState<Match[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [selectedMatch, setSelectedMatch] = useState<Match | null>(null)
  const [showModal, setShowModal] = useState(false)

  useEffect(() => {
    fetchMatches()
  }, [])

  const fetchMatches = async () => {
    try {
      setLoading(true)
      // For now, we'll use the existing matches endpoint
      // In production, you'd want a dedicated admin endpoint
      const token = localStorage.getItem('token')
      const response = await fetch('http://localhost:8001/api/v1/matches', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        const data = await response.json()
        setMatches(data.matches || [])
      } else {
        console.error('Failed to fetch matches')
      }
    } catch (error) {
      console.error('Error fetching matches:', error)
    } finally {
      setLoading(false)
    }
  }

  const updateMatchResult = async (matchId: string, result: string) => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`http://localhost:8001/api/v1/matches/${matchId}/result`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ result })
      })

      if (response.ok) {
        // Update match in local state
        setMatches(matches.map(match => 
          match.id === matchId ? { ...match, result, status: 'completed' } : match
        ))
        setShowModal(false)
        setSelectedMatch(null)
      } else {
        console.error('Failed to update match result')
      }
    } catch (error) {
      console.error('Error updating match result:', error)
    }
  }

  const filteredMatches = matches.filter(match => {
    const matchesSearch = !searchTerm || 
      match.user?.username?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      match.game_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
      match.match_type.toLowerCase().includes(searchTerm.toLowerCase())
    
    const matchesStatus = statusFilter === 'all' || match.status === statusFilter
    
    return matchesSearch && matchesStatus
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-900 text-yellow-300'
      case 'in_progress':
        return 'bg-blue-900 text-blue-300'
      case 'completed':
        return 'bg-green-900 text-green-300'
      case 'cancelled':
        return 'bg-red-900 text-red-300'
      default:
        return 'bg-gray-700 text-gray-300'
    }
  }

  const getResultColor = (result?: string) => {
    switch (result) {
      case 'win':
        return 'bg-green-900 text-green-300'
      case 'loss':
        return 'bg-red-900 text-red-300'
      case 'draw':
        return 'bg-gray-700 text-gray-300'
      default:
        return 'bg-gray-700 text-gray-300'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Match Management</h1>
          <p className="mt-2 text-gray-300">Manage matches, verify results, and process payouts</p>
        </div>
        <div className="text-sm text-gray-400">
          Total Matches: {matches.length}
        </div>
      </div>

      {/* Filters */}
      <div className="bg-gray-800 rounded-lg p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search matches by user, game type, or match type..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-orange-500"
              />
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-gray-700 border border-gray-600 rounded-md text-white px-3 py-2 focus:outline-none focus:ring-2 focus:ring-orange-500"
            >
              <option value="all">All Status</option>
              <option value="pending">Pending</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
        </div>
      </div>

      {/* Matches Table */}
      <div className="bg-gray-800 shadow rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-700">
            <thead className="bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Match
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Player
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Result
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Amount
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-gray-800 divide-y divide-gray-700">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-4 text-center text-gray-400">
                    Loading matches...
                  </td>
                </tr>
              ) : filteredMatches.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-4 text-center text-gray-400">
                    No matches found
                  </td>
                </tr>
              ) : (
                filteredMatches.map((match) => (
                  <tr key={match.id} className="hover:bg-gray-700">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <TrophyIcon className="h-5 w-5 text-orange-500 mr-2" />
                        <div>
                          <div className="text-sm font-medium text-white capitalize">
                            {match.game_type} {match.match_type}
                          </div>
                          <div className="text-xs text-gray-400">
                            ID: {match.id.slice(0, 8)}...
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-white">
                        {match.user?.username || 'Unknown'}
                      </div>
                      <div className="text-xs text-gray-400">
                        {match.user?.email || 'No email'}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(match.status)}`}>
                        {match.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {match.result ? (
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getResultColor(match.result)}`}>
                          {match.result}
                        </span>
                      ) : (
                        <span className="text-gray-400 text-xs">Pending</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-white">
                        Bet: ₦{match.bet_amount.toLocaleString()}
                      </div>
                      <div className="text-xs text-orange-400">
                        Win: ₦{match.potential_winnings.toLocaleString()}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                      {new Date(match.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => {
                            setSelectedMatch(match)
                            setShowModal(true)
                          }}
                          className="text-orange-400 hover:text-orange-300"
                          title="Set Result"
                        >
                          <PencilIcon className="h-5 w-5" />
                        </button>
                        <button
                          className="text-gray-400 hover:text-white"
                          title="View Details"
                        >
                          <EyeIcon className="h-5 w-5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Result Modal */}
      {showModal && selectedMatch && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-gray-800">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-white mb-4">
                Set Match Result
              </h3>
              <div className="mb-4">
                <p className="text-gray-300 mb-2">Match: {selectedMatch.game_type} {selectedMatch.match_type}</p>
                <p className="text-gray-300 mb-2">Player: {selectedMatch.user?.username}</p>
                <p className="text-gray-300 mb-4">Bet Amount: ₦{selectedMatch.bet_amount.toLocaleString()}</p>
              </div>
              <div className="flex space-x-2 mb-4">
                <button
                  onClick={() => updateMatchResult(selectedMatch.id, 'win')}
                  className="flex-1 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md font-medium"
                >
                  Win
                </button>
                <button
                  onClick={() => updateMatchResult(selectedMatch.id, 'loss')}
                  className="flex-1 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md font-medium"
                >
                  Loss
                </button>
                <button
                  onClick={() => updateMatchResult(selectedMatch.id, 'draw')}
                  className="flex-1 bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md font-medium"
                >
                  Draw
                </button>
              </div>
              <div className="flex justify-end">
                <button
                  onClick={() => {
                    setShowModal(false)
                    setSelectedMatch(null)
                  }}
                  className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md font-medium"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
