'use client'

import { useAuth } from '@/contexts/AuthContext'
import { useRouter, useSearchParams } from 'next/navigation'
import { useEffect, useState, Suspense } from 'react'
import Link from 'next/link'
import { 
  WalletIcon, 
  TrophyIcon, 
  UserGroupIcon, 
  CurrencyDollarIcon,
  PlayIcon,
  ArrowRightIcon,
  ChartBarIcon,
  Cog6ToothIcon
} from '@heroicons/react/24/outline'
import { formatCurrency } from '@/lib/utils'
import { walletService } from '@/lib/services/wallet'
import { matchService } from '@/lib/services/matches'
import { Wallet, Match } from '@/lib/types'
import DepositModal from '@/components/DepositModal'
import WithdrawalModal from '@/components/WithdrawalModal'
import { paymentService } from '@/lib/services/payments'

// Component that uses searchParams - needs to be in Suspense
const PaymentVerificationHandler = ({ isAuthenticated, onWalletUpdate }: { isAuthenticated: boolean, onWalletUpdate: () => void }) => {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [verifyingPayment, setVerifyingPayment] = useState(false)

  useEffect(() => {
    const reference = searchParams.get('reference') || searchParams.get('trxref')
    if (reference && isAuthenticated && !verifyingPayment) {
      const verifyPayment = async () => {
        setVerifyingPayment(true)
        try {
          await paymentService.verifyDeposit(reference)
          onWalletUpdate()
          router.replace('/dashboard')
          alert('Payment verified successfully! Your balance has been updated.')
        } catch (error: any) {
          console.error('Payment verification error:', error)
          alert(error.message || 'Payment verification failed. Please contact support.')
        } finally {
          setVerifyingPayment(false)
        }
      }
      verifyPayment()
    }
  }, [searchParams, isAuthenticated, verifyingPayment, router, onWalletUpdate])

  return null
}

const DashboardPage = () => {
  const { user, isAuthenticated, isLoading } = useAuth()
  const router = useRouter()
  const [wallet, setWallet] = useState<Wallet | null>(null)
  const [recentMatches, setRecentMatches] = useState<Match[]>([])
  const [loadingData, setLoadingData] = useState(true)
  const [showDepositModal, setShowDepositModal] = useState(false)
  const [showWithdrawalModal, setShowWithdrawalModal] = useState(false)

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login')
      return
    }
  }, [isAuthenticated, isLoading, router])

  // Function to refresh wallet balance
  const refreshWallet = async () => {
    const walletData = await walletService.getBalance()
    setWallet(walletData)
  }

  useEffect(() => {
    const fetchDashboardData = async () => {
      if (isAuthenticated) {
        try {
          setLoadingData(true)
          const [walletData, matchesData] = await Promise.all([
            walletService.getBalance(),
            matchService.getUserMatches()
          ])
          setWallet(walletData)
          setRecentMatches(matchesData.matches.slice(0, 3)) // Show last 3 matches
        } catch (error) {
          console.error('Error fetching dashboard data:', error)
        } finally {
          setLoadingData(false)
        }
      }
    }

    fetchDashboardData()
  }, [isAuthenticated])

  if (isLoading || loadingData) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-orange-500"></div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  // Calculate stats from real data
  const stats = {
    walletBalance: wallet?.balance || 0,
    totalMatches: recentMatches.length,
    wins: recentMatches.filter(m => m.result === 'won').length,
    winRate: recentMatches.length > 0 ? 
      Math.round((recentMatches.filter(m => m.result === 'won').length / recentMatches.length) * 100) : 0,
    totalEarnings: recentMatches.reduce((sum, match) => 
      match.result === 'won' ? sum + (match.potential_winnings - match.bet_amount) : sum, 0),
    referralEarnings: 0 // TODO: Implement referral earnings
  }

  const quickActions = [
    {
      title: 'Create Match',
      description: 'Start a new head-to-head match',
      icon: PlayIcon,
      href: '/matches/create',
      color: 'bg-orange-500'
    },
    {
      title: 'Join Tournament',
      description: 'Participate in ongoing tournaments',
      icon: TrophyIcon,
      href: '/tournaments',
      color: 'bg-orange-500'
    },
    {
      title: 'Add Funds',
      description: 'Top up your wallet',
      icon: WalletIcon,
      href: '/wallet',
      color: 'bg-orange-500'
    },
    {
      title: 'Refer Friends',
      description: 'Invite friends and earn bonuses',
      icon: UserGroupIcon,
      href: '/referrals',
      color: 'bg-orange-500'
    }
  ]

  // Add admin panel to quick actions if user is admin
  if (user?.is_admin) {
    quickActions.unshift({
      title: 'Admin Panel',
      description: 'Manage users, matches, and system settings',
      icon: Cog6ToothIcon,
      href: '/admin',
      color: 'bg-red-500'
    })
  }

  // Don't render dashboard if still loading or not authenticated
  if (isLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-black">
      <Suspense fallback={null}>
        <PaymentVerificationHandler isAuthenticated={isAuthenticated} onWalletUpdate={refreshWallet} />
      </Suspense>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">
            Welcome back, {user?.username || user?.email || 'User'}!
          </h1>
          <p className="mt-2 text-gray-300">
            Ready to dominate the arena? Check your stats and start your next match.
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-gray-900 rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <div className="p-2 bg-orange-100 rounded-lg">
                  <WalletIcon className="w-6 h-6 text-orange-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-300">Wallet Balance</p>
                  <p className="text-2xl font-bold text-white">{formatCurrency(stats.walletBalance)}</p>
                </div>
              </div>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => setShowDepositModal(true)}
                className="flex-1 bg-gradient-to-r from-green-500 to-green-600 text-white py-2 px-3 rounded-lg text-sm font-medium hover:from-green-600 hover:to-green-700 transition-all"
              >
                + Deposit
              </button>
              <button
                onClick={() => setShowWithdrawalModal(true)}
                disabled={stats.walletBalance < 500}
                className="flex-1 bg-gradient-to-r from-orange-500 to-orange-600 text-white py-2 px-3 rounded-lg text-sm font-medium hover:from-orange-600 hover:to-orange-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                - Withdraw
              </button>
            </div>
          </div>

          <div className="bg-gray-900 rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-orange-100 rounded-lg">
                <TrophyIcon className="w-6 h-6 text-orange-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-300">Win Rate</p>
                <p className="text-2xl font-bold text-white">{stats.winRate}%</p>
              </div>
            </div>
          </div>

          <div className="bg-gray-900 rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-orange-100 rounded-lg">
                <ChartBarIcon className="w-6 h-6 text-orange-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-300">Total Matches</p>
                <p className="text-2xl font-bold text-white">{stats.totalMatches}</p>
              </div>
            </div>
          </div>

          <div className="bg-gray-900 rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-orange-100 rounded-lg">
                <CurrencyDollarIcon className="w-6 h-6 text-orange-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-300">Total Earnings</p>
                <p className="text-2xl font-bold text-white">{formatCurrency(stats.totalEarnings)}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Quick Actions */}
          <div className="lg:col-span-2">
            <h2 className="text-xl font-bold text-white mb-6">Quick Actions</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
              {quickActions.map((action, index) => (
                <Link
                  key={index}
                  href={action.href}
                  className="bg-gray-900 rounded-lg shadow p-6 hover:shadow-lg transition-shadow"
                >
                  <div className="flex items-center">
                    <div className={`p-3 ${action.color} rounded-lg`}>
                      <action.icon className="w-6 h-6 text-white" />
                    </div>
                    <div className="ml-4 flex-1">
                      <h3 className="text-lg font-semibold text-white">{action.title}</h3>
                      <p className="text-sm text-gray-300">{action.description}</p>
                    </div>
                    <ArrowRightIcon className="w-5 h-5 text-gray-400" />
                  </div>
                </Link>
              ))}
            </div>

            {/* Recent Matches */}
            <div className="bg-gray-900 rounded-lg shadow">
              <div className="p-6 border-b border-gray-700">
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-bold text-white">Recent Matches</h2>
                  <Link href="/my-matches" className="text-orange-600 hover:text-orange-700 font-medium">
                    View All
                  </Link>
                </div>
              </div>
              <div className="p-6">
                <div className="space-y-4">
                  {recentMatches.length > 0 ? (
                    recentMatches.map((match) => (
                      <div key={match.id} className="flex items-center justify-between p-4 bg-gray-800 rounded-lg">
                        <div className="flex items-center">
                          <div className={`w-3 h-3 rounded-full mr-3 ${
                            match.result === 'won' ? 'bg-green-500' : 'bg-red-500'
                          }`} />
                          <div>
                            <p className="font-medium text-white">{match.game_type}</p>
                            <p className="text-sm text-gray-300">
                              {new Date(match.created_at).toLocaleDateString()}
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className={`font-semibold ${
                            match.result === 'won' ? 'text-green-600' : 'text-red-600'
                          }`}>
                            {match.result === 'won' ? '+' : '-'}{formatCurrency(match.bet_amount)}
                          </p>
                          <p className="text-sm text-gray-300 capitalize">{match.result || 'Pending'}</p>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-8">
                      <p className="text-gray-400">No matches yet. Start playing to see your history!</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Admin Panel - Only show for admin users */}
            {user?.is_admin && (
              <div className="bg-red-900/20 border border-red-500/30 rounded-lg shadow p-6">
                <div className="flex items-center mb-4">
                  <div className="p-2 bg-red-500 rounded-lg">
                    <Cog6ToothIcon className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-lg font-bold text-white ml-3">Admin Panel</h3>
                </div>
                <p className="text-gray-300 text-sm mb-4">
                  Manage users, matches, payments, and system settings
                </p>
                <Link 
                  href="/admin" 
                  className="w-full bg-red-600 hover:bg-red-700 text-white py-2 px-4 rounded-lg font-medium transition-colors flex items-center justify-center"
                >
                  <Cog6ToothIcon className="w-4 h-4 mr-2" />
                  Open Admin Panel
                </Link>
              </div>
            )}

            {/* Performance Chart Placeholder */}
            <div className="bg-gray-900 rounded-lg shadow p-6">
              <h3 className="text-lg font-bold text-white mb-4">Performance</h3>
            <div className="h-64 bg-gray-800 rounded-lg flex items-center justify-center">
              <p className="text-gray-300">Chart coming soon</p>
              </div>
            </div>

            {/* Leaderboard Preview */}
            <div className="bg-gray-900 rounded-lg shadow p-6">
              <h3 className="text-lg font-bold text-white mb-4">Top Players</h3>
              <div className="space-y-3">
                <div className="text-center text-gray-400 py-8">
                  <TrophyIcon className="mx-auto h-12 w-12 text-gray-500 mb-2" />
                  <p>Leaderboard will be available soon</p>
                  <p className="text-sm">Start playing to see rankings!</p>
                </div>
              </div>
              <Link href="/leaderboard" className="block mt-4 text-center text-orange-600 hover:text-orange-700 font-medium">
                View Full Leaderboard
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Payment Modals */}
      <DepositModal 
        isOpen={showDepositModal} 
        onClose={() => setShowDepositModal(false)} 
      />
      <WithdrawalModal 
        isOpen={showWithdrawalModal} 
        onClose={() => setShowWithdrawalModal(false)}
        currentBalance={stats.walletBalance}
      />
    </div>
  )
}

export default DashboardPage
