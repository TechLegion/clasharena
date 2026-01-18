'use client'

import { useState, useEffect } from 'react'
import {
  ChartBarIcon,
  UsersIcon,
  CurrencyDollarIcon,
  TrophyIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon
} from '@heroicons/react/24/outline'

interface AnalyticsData {
  users: {
    total: number
    active: number
    new_today: number
    growth_rate: number
  }
  matches: {
    total: number
    active: number
    completed: number
    avg_bet: number
  }
  transactions: {
    total: number
    deposits: number
    withdrawals: number
    total_volume: number
  }
  revenue: {
    total_bets: number
    total_winnings: number
    net_revenue: number
    profit_margin: number
  }
}

export default function AdminAnalytics() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [timeRange, setTimeRange] = useState('7d')

  useEffect(() => {
    fetchAnalytics()
  }, [timeRange])

  const fetchAnalytics = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      const response = await fetch(`http://localhost:8001/api/v1/admin/analytics?range=${timeRange}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        const data = await response.json()
        setAnalytics(data)
      } else {
        console.error('Failed to fetch analytics')
        // Set empty/zero data instead of mock data
        setAnalytics({
          users: {
            total: 0,
            active: 0,
            new_today: 0,
            growth_rate: 0
          },
          matches: {
            total: 0,
            active: 0,
            completed: 0,
            avg_bet: 0
          },
          transactions: {
            total: 0,
            deposits: 0,
            withdrawals: 0,
            total_volume: 0
          },
          revenue: {
            total_bets: 0,
            total_winnings: 0,
            net_revenue: 0,
            profit_margin: 0
          }
        })
      }
    } catch (error) {
      console.error('Error fetching analytics:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-white text-xl">Loading analytics...</div>
      </div>
    )
  }

  const kpiCards = [
    {
      name: 'Total Users',
      value: analytics?.users.total || 0,
      change: `+${analytics?.users.new_today || 0} today`,
      changeType: 'positive',
      icon: UsersIcon
    },
    {
      name: 'Active Matches',
      value: analytics?.matches.active || 0,
      change: `${analytics?.matches.completed || 0} completed`,
      changeType: 'neutral',
      icon: TrophyIcon
    },
    {
      name: 'Total Revenue',
      value: `₦${(analytics?.revenue.net_revenue || 0).toLocaleString()}`,
      change: `${analytics?.revenue.profit_margin || 0}% margin`,
      changeType: 'positive',
      icon: CurrencyDollarIcon
    },
    {
      name: 'Transaction Volume',
      value: `₦${(analytics?.transactions.total_volume || 0).toLocaleString()}`,
      change: `${analytics?.transactions.total || 0} transactions`,
      changeType: 'positive',
      icon: ChartBarIcon
    }
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Analytics Dashboard</h1>
          <p className="mt-2 text-gray-300">Platform performance and business insights</p>
        </div>
        <div className="flex space-x-2">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="bg-gray-700 border border-gray-600 rounded-md text-white px-3 py-2 focus:outline-none focus:ring-2 focus:ring-orange-500"
          >
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
          </select>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {kpiCards.map((card) => (
          <div key={card.name} className="bg-gray-800 overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <card.icon className="h-6 w-6 text-orange-500" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-400 truncate">
                      {card.name}
                    </dt>
                    <dd className="text-2xl font-bold text-white">
                      {card.value}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
            <div className="bg-gray-700 px-5 py-3">
              <div className="text-sm">
                <span className={`font-medium ${
                  card.changeType === 'positive' ? 'text-green-400' :
                  card.changeType === 'negative' ? 'text-red-400' :
                  'text-gray-400'
                }`}>
                  {card.changeType === 'positive' && <ArrowTrendingUpIcon className="inline h-4 w-4 mr-1" />}
                  {card.changeType === 'negative' && <ArrowTrendingDownIcon className="inline h-4 w-4 mr-1" />}
                  {card.change}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Detailed Analytics */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* User Analytics */}
        <div className="bg-gray-800 shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4">User Analytics</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Total Users</span>
              <span className="text-white font-semibold">{analytics?.users.total || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Active Users</span>
              <span className="text-green-400 font-semibold">{analytics?.users.active || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">New Today</span>
              <span className="text-orange-400 font-semibold">{analytics?.users.new_today || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Growth Rate</span>
              <span className="text-green-400 font-semibold">+{(analytics?.users.growth_rate || 0).toFixed(1)}%</span>
            </div>
          </div>
        </div>

        {/* Match Analytics */}
        <div className="bg-gray-800 shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4">Match Analytics</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Total Matches</span>
              <span className="text-white font-semibold">{analytics?.matches.total || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Active Matches</span>
              <span className="text-orange-400 font-semibold">{analytics?.matches.active || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Completed</span>
              <span className="text-green-400 font-semibold">{analytics?.matches.completed || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Average Bet</span>
              <span className="text-white font-semibold">₦{(analytics?.matches.avg_bet || 0).toLocaleString()}</span>
            </div>
          </div>
        </div>

        {/* Financial Analytics */}
        <div className="bg-gray-800 shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4">Financial Analytics</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Total Deposits</span>
              <span className="text-green-400 font-semibold">{analytics?.transactions.deposits || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Total Withdrawals</span>
              <span className="text-red-400 font-semibold">{analytics?.transactions.withdrawals || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Transaction Volume</span>
              <span className="text-white font-semibold">₦{(analytics?.transactions.total_volume || 0).toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Net Revenue</span>
              <span className="text-green-400 font-semibold">₦{(analytics?.revenue.net_revenue || 0).toLocaleString()}</span>
            </div>
          </div>
        </div>

        {/* Revenue Breakdown */}
        <div className="bg-gray-800 shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4">Revenue Breakdown</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Total Bets</span>
              <span className="text-white font-semibold">₦{(analytics?.revenue.total_bets || 0).toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Total Winnings</span>
              <span className="text-orange-400 font-semibold">₦{(analytics?.revenue.total_winnings || 0).toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Platform Profit</span>
              <span className="text-green-400 font-semibold">₦{(analytics?.revenue.net_revenue || 0).toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Profit Margin</span>
              <span className="text-green-400 font-semibold">{(analytics?.revenue.profit_margin || 0).toFixed(1)}%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="bg-gray-800 shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-white mb-4">Key Performance Indicators</h3>
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-400">
              {analytics?.users.total > 0 
                ? ((analytics.users.active / analytics.users.total) * 100).toFixed(1) + '%'
                : '0.0%'
              }
            </div>
            <div className="text-sm text-gray-400">User Activity Rate</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-400">
              {analytics?.matches.total > 0 
                ? ((analytics.matches.completed / analytics.matches.total) * 100).toFixed(1) + '%'
                : '0.0%'
              }
            </div>
            <div className="text-sm text-gray-400">Match Completion Rate</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-400">
              ₦{(analytics?.matches.avg_bet || 0).toLocaleString()}
            </div>
            <div className="text-sm text-gray-400">Average Bet Size</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-400">
              {(analytics?.revenue.profit_margin || 0).toFixed(1)}%
            </div>
            <div className="text-sm text-gray-400">Profit Margin</div>
          </div>
        </div>
      </div>

      {/* Charts Placeholder */}
      <div className="bg-gray-800 shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-white mb-4">Performance Trends</h3>
        <div className="h-64 flex items-center justify-center border-2 border-dashed border-gray-600 rounded-lg">
          <div className="text-center">
            <ChartBarIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-400">Charts Coming Soon</h3>
            <p className="mt-1 text-sm text-gray-500">
              Interactive charts and graphs will be displayed here
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
