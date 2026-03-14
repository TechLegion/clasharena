'use client'

import { useAuth } from '@/contexts/AuthContext'
import Link from 'next/link'
import { useState, useEffect f} from 'react'
import { 
  TrophyIcon, 
  CurrencyDollarIcon, 
  UsersIcon, 
  ArrowRightIcon,
  PlayIcon,
  BoltIcon
} from '@heroicons/react/24/outline'

const HomePage = () => {
  const { isAuthenticated } = useAuth()
  const [isVisible, setIsVisible] = useState(false)

  // Live stats (will be populated from API)
  const liveStats = {
    activePlayers: 0,
    totalPaidOut: 0,
    dailyTournaments: 0,
    recentWinners: []
  }

  const features = [
    {
      icon: TrophyIcon,
      title: 'Compete & Win',
      description: 'Challenge other players in head-to-head matches and tournaments'
    },
    {
      icon: CurrencyDollarIcon,
      title: 'Earn Real Money',
      description: 'Win matches and earn real money rewards instantly'
    },
    {
      icon: UsersIcon,
      title: 'Referral System',
      description: 'Invite friends and earn bonuses when they join and play'
    },
    {
      icon: BoltIcon,
      title: 'Quick Matches',
      description: 'Fast-paced gaming with instant matchmaking'
    }
  ]

  const gameTypes = [
    { name: 'PUBG Mobile', players: '1200+', image: '/games/pubg.jpg' },
    { name: 'Free Fire', players: '850+', image: '/games/freefire.jpg' },
    { name: 'Call of Duty', players: '650+', image: '/games/cod.jpg' },
    { name: 'FIFA Mobile', players: '420+', image: '/games/fifa.jpg' },
  ]

  useEffect(() => {
    setIsVisible(true)
  }, [])

  return (
    <div className="bg-black overflow-hidden">
      {/* Hero Section */}
      <div 
        className="relative min-h-screen flex items-center justify-center"
        style={{
          backgroundImage: 'url(/esports.avif)',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat'
        }}
      >
        {/* Animated gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-br from-black/80 via-black/60 to-black/80"></div>
        
        
        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-24">
          <div className="text-center">
            {/* Live Player Badge */}
            <div className={`inline-flex items-center bg-gray-800/80 border border-gray-700 rounded-full px-3 sm:px-4 py-2 mb-6 transition-all duration-1000 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
              <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
              <span className="text-gray-300 text-xs sm:text-sm font-medium">
                {liveStats.activePlayers.toLocaleString()} Players Online Now
              </span>
            </div>

            <h1 className={`text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-4 sm:mb-6 leading-tight transition-all duration-1000 delay-200 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
              Turn Your Gaming Skills Into{' '}
              <span className="text-[var(--color-brand)]">Real Money</span>
            </h1>
            
            <p className={`text-lg sm:text-xl md:text-2xl text-orange-100 mb-6 sm:mb-8 max-w-3xl mx-auto leading-relaxed transition-all duration-1000 delay-400 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
              Compete in tournaments. Every kill pays. Withdraw instantly to your bank account.
            </p>

            {/* Live Stats Row - Mobile Optimized */}
            <div className={`grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-6 mb-6 sm:mb-8 max-w-4xl mx-auto transition-all duration-1000 delay-600 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
              <div className="bg-gray-900/50 backdrop-blur-sm rounded-xl p-4 sm:p-6 border border-gray-700/50 hover:border-gray-600 transition-all duration-300">
                <div className="text-xl sm:text-2xl font-bold text-white mb-1">₦0</div>
                <div className="text-gray-500 text-xs sm:text-sm">Total Paid Out</div>
              </div>
              <div className="bg-gray-900/50 backdrop-blur-sm rounded-xl p-4 sm:p-6 border border-gray-700/50 hover:border-gray-600 transition-all duration-300">
                <div className="text-xl sm:text-2xl font-bold text-white mb-1">0</div>
                <div className="text-gray-500 text-xs sm:text-sm">Active Players</div>
              </div>
              <div className="bg-gray-900/50 backdrop-blur-sm rounded-xl p-4 sm:p-6 border border-gray-700/50 hover:border-gray-600 transition-all duration-300">
                <div className="text-xl sm:text-2xl font-bold text-white mb-1">0</div>
                <div className="text-gray-500 text-xs sm:text-sm">Daily Tournaments</div>
              </div>
            </div>
            
            {/* CTA Buttons - Mobile Optimized */}
            <div className={`flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center mb-8 sm:mb-12 transition-all duration-1000 delay-800 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
              {isAuthenticated ? (
                <>
                  <Link
                    href="/matches"
                    className="group inline-flex items-center justify-center px-6 sm:px-8 py-3 sm:py-4 text-gray-900 font-bold rounded-xl transition-all duration-300 hover:scale-105 hover:shadow-lg hover:shadow-orange-500/25"
                    style={{ background: 'linear-gradient(90deg, var(--color-brand), #C48612)' }}
                  >
                    <PlayIcon className="w-4 h-4 sm:w-5 sm:h-5 mr-2 group-hover:animate-bounce" />
                    Start Playing
                  </Link>
                  <Link
                    href="/dashboard"
                    className="group inline-flex items-center justify-center px-6 sm:px-8 py-3 sm:py-4 border-2 border-white text-white font-bold rounded-xl hover:bg-white hover:text-gray-900 transition-all duration-300 hover:scale-105"
                  >
                    Go to Dashboard
                    <ArrowRightIcon className="w-4 h-4 sm:w-5 sm:h-5 ml-2 group-hover:translate-x-1 transition-transform" />
                  </Link>
                </>
              ) : (
                <>
                  <Link
                    href="/register"
                    className="group inline-flex items-center justify-center px-6 sm:px-8 py-3 sm:py-4 text-gray-900 font-bold rounded-xl transition-all duration-300 hover:scale-105 hover:shadow-lg hover:shadow-orange-500/25"
                    style={{ background: 'linear-gradient(90deg, var(--color-brand), #C48612)' }}
                  >
                    Get Started
                    <ArrowRightIcon className="w-4 h-4 sm:w-5 sm:h-5 ml-2 group-hover:translate-x-1 transition-transform" />
                  </Link>
                  <Link
                    href="/login"
                    className="group inline-flex items-center justify-center px-6 sm:px-8 py-3 sm:py-4 border-2 border-white text-white font-bold rounded-xl hover:bg-white hover:text-gray-900 transition-all duration-300 hover:scale-105"
                  >
                    Login
                  </Link>
                </>
              )}
            </div>

            {/* Trust Indicators - Mobile Optimized */}
            <div className={`flex flex-col items-center space-y-4 sm:space-y-6 transition-all duration-1000 delay-1000 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
              <p className="text-gray-400 text-xs sm:text-sm">Trusted by thousands of players</p>
              
              {/* Payment Partners - Mobile Scrollable */}
              <div className="flex items-center space-x-4 sm:space-x-6 opacity-60 overflow-x-auto pb-2 w-full max-w-md sm:max-w-none justify-center">
                <div className="flex items-center space-x-2 bg-gray-800/50 border border-gray-700 rounded-lg px-3 sm:px-4 py-2 min-w-fit">
                  <span className="text-gray-300 font-medium text-xs sm:text-sm">Paystack</span>
                </div>
                <div className="flex items-center space-x-2 bg-gray-800/50 border border-gray-700 rounded-lg px-3 sm:px-4 py-2 min-w-fit">
                  <span className="text-gray-300 font-medium text-xs sm:text-sm">Flutterwave</span>
                </div>
                <div className="flex items-center space-x-2 bg-gray-800/50 border border-gray-700 rounded-lg px-3 sm:px-4 py-2 min-w-fit">
                  <span className="text-gray-300 font-medium text-xs sm:text-sm">SSL Secured</span>
                </div>
              </div>
              
              {/* Security Badges - Mobile Stacked */}
              <div className="flex flex-col sm:flex-row items-center space-y-2 sm:space-y-0 sm:space-x-6 text-xs text-gray-500">
                  <span>Instant Withdrawals</span>
                <span className="hidden sm:inline">•</span>
                  <span>Licensed & Regulated</span>
                <span className="hidden sm:inline">•</span>
                  <span>PCI Compliant</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="py-16 sm:py-20 bg-black relative overflow-hidden">
        
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12 sm:mb-16">
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-white mb-4 leading-tight">
              Why Choose <span className="text-[var(--color-brand)]">ClashArena</span>?
            </h2>
            <p className="text-lg sm:text-xl text-gray-300 max-w-2xl mx-auto leading-relaxed">
              Experience the future of competitive gaming with our innovative platform
            </p>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-8">
            {features.map((feature, index) => (
              <div 
                key={index} 
                className={`group text-center p-6 sm:p-8 rounded-2xl bg-gray-900/50 backdrop-blur-sm border border-gray-800 hover:border-gray-600 transition-all duration-500 hover:bg-gray-800/50 transform ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}
                style={{ transitionDelay: `${index * 200}ms` }}
              >
                <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-xl flex items-center justify-center mx-auto mb-4 sm:mb-6 bg-gray-800 border border-gray-700 group-hover:border-gray-600 transition-colors">
                  <feature.icon className="w-6 h-6 sm:w-7 sm:h-7 text-gray-400 group-hover:text-white transition-colors" />
                </div>
                <h3 className="text-lg sm:text-xl font-semibold text-white mb-3">
                  {feature.title}
                </h3>
                <p className="text-sm sm:text-base text-gray-400 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Live Tournaments Section */}
      <div className="py-16 sm:py-20 bg-gray-900 relative overflow-hidden">
        
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12 sm:mb-16">
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-white mb-4 leading-tight">
              Live <span className="text-[var(--color-brand)]">Tournaments</span>
            </h2>
            <p className="text-lg sm:text-xl text-gray-300 leading-relaxed">
              Join active tournaments and compete for real prizes
            </p>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
            {/* CODM Tournament */}
            <div className="group bg-gray-800/50 backdrop-blur-sm rounded-2xl shadow-lg overflow-hidden hover:shadow-2xl transition-all duration-500 hover:-translate-y-2 border border-gray-700/50 hover:border-gray-600">
              <div className="relative h-40 sm:h-48 flex items-center justify-center overflow-hidden" style={{ backgroundImage: 'url(/codm-wallpaper.jpg)', backgroundSize: 'cover', backgroundPosition: 'center' }}>
                <div className="absolute inset-0 bg-black/70"></div>
                <div className="absolute top-3 left-3">
                  <span className="bg-gray-600 text-white text-xs font-bold px-2 py-1 rounded-full">
                    COMING SOON
                  </span>
                </div>
                <div className="text-center text-white relative z-10">
                  <div className="text-base sm:text-lg font-bold">Call of Duty Mobile</div>
                </div>
              </div>
              <div className="p-4 sm:p-6">
                <h3 className="text-lg sm:text-xl font-semibold text-white mb-3">Tournaments Coming Soon</h3>
                <div className="space-y-2 mb-4">
                  <div className="flex justify-between text-xs sm:text-sm">
                    <span className="text-gray-400">Status:</span>
                    <span className="text-gray-300 font-medium">Preparing</span>
                  </div>
                  <div className="flex justify-between text-xs sm:text-sm">
                    <span className="text-gray-400">Entry Fee:</span>
                    <span className="text-gray-300 font-medium">TBD</span>
                  </div>
                  <div className="flex justify-between text-xs sm:text-sm">
                    <span className="text-gray-400">Prize Pool:</span>
                    <span className="text-gray-300 font-medium">TBD</span>
                  </div>
                  <div className="flex justify-between text-xs sm:text-sm">
                    <span className="text-gray-400">Players:</span>
                    <span className="text-gray-300 font-medium">0/0</span>
                  </div>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2 mb-2">
                  <div className="bg-gray-600 h-2 rounded-full transition-all duration-1000" style={{ width: '0%' }}></div>
                </div>
                <p className="text-gray-400 text-xs mb-4">Tournaments launching soon</p>
                <Link
                  href="/matches"
                  className="w-full bg-gray-600 text-white font-bold py-3 px-4 rounded-xl text-center block hover:bg-gray-700 transition-all duration-300 cursor-not-allowed opacity-50"
                >
                  Coming Soon
                </Link>
                <div className="mt-3 text-center text-xs sm:text-sm text-gray-400">
                  Tournament details will be announced soon
                </div>
              </div>
            </div>

            {/* PUBG Tournament */}
            <div className="group bg-gray-800/50 backdrop-blur-sm rounded-2xl shadow-lg overflow-hidden hover:shadow-2xl transition-all duration-500 hover:-translate-y-2 border border-gray-700/50 hover:border-gray-600">
              <div className="relative h-40 sm:h-48 flex items-center justify-center overflow-hidden" style={{ backgroundImage: 'url(/pubg-wallpaper.jpg)', backgroundSize: 'cover', backgroundPosition: 'center' }}>
                <div className="absolute inset-0 bg-black/70"></div>
                <div className="absolute top-3 left-3">
                  <span className="bg-gray-600 text-white text-xs font-bold px-2 py-1 rounded-full">
                    COMING SOON
                  </span>
                </div>
                <div className="text-center text-white relative z-10">
                  <div className="text-base sm:text-lg font-bold">PUBG Mobile</div>
                </div>
              </div>
              <div className="p-4 sm:p-6">
                <h3 className="text-lg sm:text-xl font-semibold text-white mb-3">Tournaments Coming Soon</h3>
                <div className="space-y-2 mb-4">
                  <div className="flex justify-between text-xs sm:text-sm">
                    <span className="text-gray-400">Status:</span>
                    <span className="text-gray-300 font-medium">Preparing</span>
                  </div>
                  <div className="flex justify-between text-xs sm:text-sm">
                    <span className="text-gray-400">Entry Fee:</span>
                    <span className="text-gray-300 font-medium">TBD</span>
                  </div>
                  <div className="flex justify-between text-xs sm:text-sm">
                    <span className="text-gray-400">Prize Pool:</span>
                    <span className="text-gray-300 font-medium">TBD</span>
                  </div>
                  <div className="flex justify-between text-xs sm:text-sm">
                    <span className="text-gray-400">Players:</span>
                    <span className="text-gray-300 font-medium">0/0</span>
                  </div>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2 mb-2">
                  <div className="bg-gray-600 h-2 rounded-full transition-all duration-1000" style={{ width: '0%' }}></div>
                </div>
                <p className="text-gray-400 text-xs mb-4">Tournaments launching soon</p>
                <Link
                  href="/matches"
                  className="w-full bg-gray-600 text-white font-bold py-3 px-4 rounded-xl text-center block hover:bg-gray-700 transition-all duration-300 cursor-not-allowed opacity-50"
                >
                  Coming Soon
                </Link>
                <div className="mt-3 text-center text-xs sm:text-sm text-gray-400">
                  Tournament details will be announced soon
                </div>
              </div>
            </div>

            {/* Free Fire Tournament */}
            <div className="group bg-gray-800/50 backdrop-blur-sm rounded-2xl shadow-lg overflow-hidden hover:shadow-2xl transition-all duration-500 hover:-translate-y-2 border border-gray-700/50 hover:border-gray-600">
              <div className="relative h-40 sm:h-48 flex items-center justify-center overflow-hidden" style={{ backgroundImage: 'url(/free-fire-wallpaper.jpg)', backgroundSize: 'cover', backgroundPosition: 'center' }}>
                <div className="absolute inset-0 bg-black/70"></div>
                <div className="absolute top-3 left-3">
                  <span className="bg-gray-600 text-white text-xs font-bold px-2 py-1 rounded-full">
                    COMING SOON
                  </span>
                </div>
                <div className="text-center text-white relative z-10">
                  <div className="text-base sm:text-lg font-bold">Free Fire</div>
                </div>
              </div>
              <div className="p-4 sm:p-6">
                <h3 className="text-lg sm:text-xl font-semibold text-white mb-3">Tournaments Coming Soon</h3>
                <div className="space-y-2 mb-4">
                  <div className="flex justify-between text-xs sm:text-sm">
                    <span className="text-gray-400">Status:</span>
                    <span className="text-gray-300 font-medium">Preparing</span>
                  </div>
                  <div className="flex justify-between text-xs sm:text-sm">
                    <span className="text-gray-400">Entry Fee:</span>
                    <span className="text-gray-300 font-medium">TBD</span>
                  </div>
                  <div className="flex justify-between text-xs sm:text-sm">
                    <span className="text-gray-400">Prize Pool:</span>
                    <span className="text-gray-300 font-medium">TBD</span>
                  </div>
                  <div className="flex justify-between text-xs sm:text-sm">
                    <span className="text-gray-400">Players:</span>
                    <span className="text-gray-300 font-medium">0/0</span>
                  </div>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2 mb-2">
                  <div className="bg-gray-600 h-2 rounded-full transition-all duration-1000" style={{ width: '0%' }}></div>
                </div>
                <p className="text-gray-400 text-xs mb-4">Tournaments launching soon</p>
                <Link
                  href="/matches"
                  className="w-full bg-gray-600 text-white font-bold py-3 px-4 rounded-xl text-center block hover:bg-gray-700 transition-all duration-300 cursor-not-allowed opacity-50"
                >
                  Coming Soon
                </Link>
                <div className="mt-3 text-center text-xs sm:text-sm text-gray-400">
                  Tournament details will be announced soon
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Winners Ticker */}
      <div className="py-6 sm:py-8 bg-black border-t border-gray-800 overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row items-center justify-center space-y-4 sm:space-y-0 sm:space-x-8">
            <div className="flex items-center space-x-2 text-gray-400">
              <TrophyIcon className="w-4 h-4 sm:w-5 sm:h-5" />
              <span className="text-xs sm:text-sm font-medium">Recent Winners:</span>
            </div>
            <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-8">
              {liveStats.recentWinners.length > 0 ? (
                liveStats.recentWinners.map((winner, index) => (
                  <div key={index} className="flex items-center space-x-2 text-white text-xs sm:text-sm animate-pulse">
                    <span className="text-orange-400 font-bold">{winner.name}</span>
                    <span className="text-gray-400">won</span>
                    <span className="text-green-400 font-bold">{winner.amount}</span>
                    <span className="text-gray-400">in {winner.game}</span>
                  </div>
                ))
              ) : (
                <div className="flex items-center space-x-2 text-gray-500 text-xs sm:text-sm">
                  <span>No recent winners yet</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="py-16 sm:py-20 bg-black relative overflow-hidden">
        
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-white mb-4 leading-tight">
            Ready to Start <span className="text-[var(--color-brand)]">Earning</span>?
          </h2>
          <p className="text-lg sm:text-xl text-orange-100 mb-8 max-w-2xl mx-auto leading-relaxed">
            Join ClashArena today and turn your gaming skills into real rewards
          </p>
          {!isAuthenticated && (
            <Link
              href="/register"
              className="group inline-flex items-center px-6 sm:px-8 py-3 sm:py-4 text-gray-900 font-bold rounded-xl transition-all duration-300 hover:scale-105 hover:shadow-lg hover:shadow-orange-500/25"
              style={{ background: 'linear-gradient(90deg, var(--color-brand), #C48612)' }}
            >
              Sign Up Now - It's Free!
              <ArrowRightIcon className="w-4 h-4 sm:w-5 sm:h-5 ml-2 group-hover:translate-x-1 transition-transform" />
            </Link>
          )}
        </div>
      </div>
    </div>
  )
}

export default HomePage