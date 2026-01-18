'use client'

import { useState, useEffect } from 'react'
import {
  UsersIcon,
  CurrencyDollarIcon,
  TrophyIcon,
  ChartBarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon
} from '@heroicons/react/24/outline'

interface DashboardStats {
  users: {
    total: number
    active: number
    new_today: number
  }
  matches: {
    total: number
    active: number
    completed: number
  }
  transactions: {
    total: number
    deposits: number
    withdrawals: number
  }
  revenue: {
    total_bets: number
    total_winnings: number
    net_revenue: number
  }
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardStats()
  }, [])

  const fetchDashboardStats = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch('http://localhost:8001/api/v1/admin/dashboard/stats', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        const data = await response.json()
        setStats(data)
      } else {
        console.error('Failed to fetch dashboard stats')
      }
    } catch (error) {
      console.error('Error fetching dashboard stats:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-white text-xl">Loading dashboard...</div>
      </div>
    )
  }

  const statCards = [
    {
      name: 'Total Users',
      value: stats?.users.total || 0,
      icon: UsersIcon,
      change: `+${stats?.users.new_today || 0} today`,
      changeType: 'positive'
    },
    {
      name: 'Active Matches',
      value: stats?.matches.active || 0,
      icon: TrophyIcon,
      change: `${stats?.matches.total || 0} total`,
      changeType: 'neutral'
    },
    {
      name: 'Total Revenue',
      value: `₦${(stats?.revenue.net_revenue || 0).toLocaleString()}`,
      icon: CurrencyDollarIcon,
      change: `₦${(stats?.revenue.total_bets || 0).toLocaleString()} in bets`,
      changeType: 'positive'
    },
    {
      name: 'Transactions',
      value: stats?.transactions.total || 0,
      icon: ChartBarIcon,
      change: `${stats?.transactions.deposits || 0} deposits`,
      changeType: 'neutral'
    }
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Admin Dashboard</h1>
        <p className="mt-2 text-gray-300">Overview of ClashArena platform performance</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {statCards.map((card) => (
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

      {/* Detailed Stats */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* User Stats */}
        <div className="bg-gray-800 shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4">User Statistics</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-400">Total Users</span>
              <span className="text-white font-semibold">{stats?.users.total || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Active Users</span>
              <span className="text-white font-semibold">{stats?.users.active || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">New Today</span>
              <span className="text-green-400 font-semibold">{stats?.users.new_today || 0}</span>
            </div>
          </div>
        </div>

        {/* Match Stats */}
        <div className="bg-gray-800 shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4">Match Statistics</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-400">Total Matches</span>
              <span className="text-white font-semibold">{stats?.matches.total || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Active Matches</span>
              <span className="text-orange-400 font-semibold">{stats?.matches.active || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Completed</span>
              <span className="text-green-400 font-semibold">{stats?.matches.completed || 0}</span>
            </div>
          </div>
        </div>

        {/* Financial Stats */}
        <div className="bg-gray-800 shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4">Financial Overview</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-400">Total Deposits</span>
              <span className="text-green-400 font-semibold">{stats?.transactions.deposits || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Total Withdrawals</span>
              <span className="text-red-400 font-semibold">{stats?.transactions.withdrawals || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Net Revenue</span>
              <span className="text-white font-semibold">₦{(stats?.revenue.net_revenue || 0).toLocaleString()}</span>
            </div>
          </div>
        </div>

        {/* Revenue Stats */}
        <div className="bg-gray-800 shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4">Revenue Breakdown</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-400">Total Bets</span>
              <span className="text-white font-semibold">₦{(stats?.revenue.total_bets || 0).toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Total Winnings</span>
              <span className="text-orange-400 font-semibold">₦{(stats?.revenue.total_winnings || 0).toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Platform Profit</span>
              <span className="text-green-400 font-semibold">₦{(stats?.revenue.net_revenue || 0).toLocaleString()}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-gray-800 shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-white mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <a
            href="/admin/users"
            className="bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-md text-center font-medium transition-colors"
          >
            Manage Users
          </a>
          <a
            href="/admin/matches"
            className="bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-md text-center font-medium transition-colors"
          >
            View Matches
          </a>
          <a
            href="/admin/financial"
            className="bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-md text-center font-medium transition-colors"
          >
            Process Payments
          </a>
          <a
            href="/admin/analytics"
            className="bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-md text-center font-medium transition-colors"
          >
            View Analytics
          </a>
        </div>
      </div>
    </div>
  )
}
