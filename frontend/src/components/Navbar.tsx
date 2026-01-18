'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { useQuery } from '@tanstack/react-query'
import { walletService } from '@/lib/services/wallet'
import { formatCurrency } from '@/lib/utils'
import { 
  Bars3Icon, 
  XMarkIcon, 
  UserCircleIcon,
  WalletIcon,
  TrophyIcon,
  Cog6ToothIcon,
  ArrowRightOnRectangleIcon,
  CurrencyDollarIcon
} from '@heroicons/react/24/outline'

const Navbar = () => {
  const [isOpen, setIsOpen] = useState(false)
  const [isProfileOpen, setIsProfileOpen] = useState(false)
  const { user, isAuthenticated, logout } = useAuth()

  // Fetch wallet balance for authenticated users
  const { data: walletData } = useQuery({
    queryKey: ['wallet'],
    queryFn: () => walletService.getBalance(),
    enabled: isAuthenticated,
    refetchInterval: 30000, // Refetch every 30 seconds
  })
  const router = useRouter()

  const handleLogout = () => {
    logout()
    router.push('/')
    setIsProfileOpen(false)
  }

  const navigation = [
    { name: 'Home', href: '/' },
    { name: 'Matches', href: '/matches' },
    { name: 'Leaderboard', href: '/leaderboard' },
    { name: 'How to Play', href: '/how-to-play' },
  ]

  const userNavigation = [
    { name: 'Dashboard', href: '/dashboard', icon: UserCircleIcon },
    { name: 'Wallet', href: '/wallet', icon: WalletIcon },
    { name: 'My Matches', href: '/my-matches', icon: TrophyIcon },
    { name: 'Settings', href: '/settings', icon: Cog6ToothIcon },
  ]

  return (
    <nav className="bg-black shadow-lg border-b border-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <Link href="/" className="flex items-center space-x-2">
              <img src="/logo.jpg" alt="ClashArena" className="w-8 h-8 rounded" />
              <span className="text-xl font-bold text-white">ClashArena</span>
            </Link>
          </div>

          <div className="hidden md:block">
            <div className="ml-10 flex items-baseline space-x-8">
              {navigation.map((item) => (
                <Link
                  key={item.name}
                  href={item.href}
                  className="text-gray-300 hover:text-[var(--color-brand)] px-3 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  {item.name}
                </Link>
              ))}
            </div>
          </div>

          <div className="hidden md:block">
            {isAuthenticated ? (
              <div className="flex items-center space-x-4">
                {/* Wallet Balance */}
                <div className="flex items-center space-x-2 bg-gray-800 px-3 py-2 rounded-lg">
                  <CurrencyDollarIcon className="w-5 h-5 text-orange-400" />
                  <span className="text-orange-400 font-bold">
                    {walletData ? formatCurrency(walletData.balance) : '₦0.00'}
                  </span>
                </div>

                {/* Profile Dropdown */}
                <div className="relative">
                  <button
                    onClick={() => setIsProfileOpen(!isProfileOpen)}
                    className="flex items-center space-x-2 text-gray-300 hover:text-[var(--color-brand)] transition-colors"
                  >
                    <UserCircleIcon className="w-6 h-6" />
                    <span className="text-sm font-medium">{user?.username}</span>
                  </button>

                  {isProfileOpen && (
                    <div className="absolute right-0 mt-2 w-48 bg-gray-900 rounded-md shadow-lg py-1 z-50 border border-gray-700">
                      {userNavigation.map((item) => (
                        <Link
                          key={item.name}
                          href={item.href}
                          className="flex items-center space-x-2 px-4 py-2 text-sm text-gray-300 hover:bg-gray-800 transition-colors"
                          onClick={() => setIsProfileOpen(false)}
                        >
                          <item.icon className="w-4 h-4" />
                          <span>{item.name}</span>
                        </Link>
                      ))}
                      <hr className="my-1" />
                      <button
                        onClick={handleLogout}
                        className="flex items-center space-x-2 w-full px-4 py-2 text-sm text-red-400 hover:bg-gray-800 transition-colors"
                      >
                        <ArrowRightOnRectangleIcon className="w-4 h-4" />
                        <span>Logout</span>
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="flex items-center space-x-4">
                <Link
                  href="/login"
                  className="text-gray-300 hover:text-[var(--color-brand)] px-3 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  Login
                </Link>
                <Link
                  href="/register"
                  className="text-white px-4 py-2 rounded-md text-sm font-medium transition-all"
                  style={{ background: 'linear-gradient(90deg, var(--color-brand), #C48612)' }}
                >
                  Sign Up
                </Link>
              </div>
            )}
          </div>

          <div className="md:hidden">
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="text-gray-300 hover:text-[var(--color-brand)] focus:outline-none focus:text-[var(--color-brand)]"
            >
              {isOpen ? (
                <XMarkIcon className="w-6 h-6" />
              ) : (
                <Bars3Icon className="w-6 h-6" />
              )}
            </button>
          </div>
        </div>
      </div>

      {isOpen && (
        <div className="md:hidden">
          <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3 bg-gray-900">
            {navigation.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                className="text-gray-300 hover:text-[var(--color-brand)] block px-3 py-2 rounded-md text-base font-medium"
                onClick={() => setIsOpen(false)}
              >
                {item.name}
              </Link>
            ))}
            {isAuthenticated ? (
              <>
                <hr className="my-2" />
                {userNavigation.map((item) => (
                  <Link
                    key={item.name}
                    href={item.href}
                    className="flex items-center space-x-2 text-gray-300 hover:text-[var(--color-brand)] px-3 py-2 rounded-md text-base font-medium"
                    onClick={() => setIsOpen(false)}
                  >
                    <item.icon className="w-4 h-4" />
                    <span>{item.name}</span>
                  </Link>
                ))}
                <button
                  onClick={() => {
                    handleLogout()
                    setIsOpen(false)
                  }}
                  className="flex items-center space-x-2 w-full text-left text-red-400 hover:bg-gray-800 px-3 py-2 rounded-md text-base font-medium"
                >
                  <ArrowRightOnRectangleIcon className="w-4 h-4" />
                  <span>Logout</span>
                </button>
              </>
            ) : (
              <>
                <hr className="my-2" />
                <Link
                  href="/login"
                  className="text-gray-300 hover:text-[var(--color-brand)] block px-3 py-2 rounded-md text-base font-medium"
                  onClick={() => setIsOpen(false)}
                >
                  Login
                </Link>
                <Link
                  href="/register"
                  className="text-white block px-3 py-2 rounded-md text-base font-medium"
                  style={{ background: 'linear-gradient(90deg, var(--color-brand), #C48612)' }}
                  onClick={() => setIsOpen(false)}
                >
                  Sign Up
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </nav>
  )
}

export default Navbar
