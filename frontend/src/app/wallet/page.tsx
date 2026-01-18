'use client'

import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { walletService } from '@/lib/services/wallet'
import { formatCurrency } from '@/lib/utils'

export default function WalletPage() {
  const { isAuthenticated, isLoading, user } = useAuth()
  const router = useRouter()
  const queryClient = useQueryClient()

  const { data: wallet, isLoading: loadingBalance } = useQuery({
    queryKey: ['wallet','balance'],
    queryFn: () => walletService.getBalance(),
    enabled: isAuthenticated,
  })

  const { data: txPage, isLoading: loadingTx } = useQuery({
    queryKey: ['wallet','transactions'],
    queryFn: () => walletService.getTransactions({ page: 1, limit: 10 }),
    enabled: isAuthenticated,
  })

  const depositMutation = useMutation({
    mutationFn: ({ amount, method }: { amount: number; method: string }) => walletService.deposit(amount, method, user?.email),
    onSuccess: (result) => {
      if (result.success && result.authorization_url) {
        // Open payment link in new tab
        window.open(result.authorization_url, '_blank')
        // Reset form
        setDeposit({ amount: 1000, method: 'paystack' })
      }
      // Note: Don't invalidate wallet queries here - balance will update via webhook after payment
    },
  })

  const withdrawMutation = useMutation({
    mutationFn: ({ amount }: { amount: number }) => walletService.withdraw(amount),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wallet'] })
      setWithdraw({ amount: 1000 })
    },
  })

  const [deposit, setDeposit] = useState({ amount: 1000, method: 'paystack' })
  const [withdraw, setWithdraw] = useState({ amount: 1000 })

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [isAuthenticated, isLoading, router])

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
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        <h1 className="text-3xl font-bold text-white">Wallet</h1>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="bg-gray-900 rounded-lg shadow p-6">
            <h2 className="text-xl font-bold text-white mb-4">Balance</h2>
            {loadingBalance ? (
              <p className="text-gray-400">Loading...</p>
            ) : (
              <div>
                <p className="text-3xl font-bold text-white">{formatCurrency(wallet?.balance || 0)}</p>
                <p className="text-gray-400">Currency: {wallet?.currency || 'NGN'}</p>
              </div>
            )}
          </div>

          <div className="bg-gray-900 rounded-lg shadow p-6">
            <h2 className="text-xl font-bold text-white mb-4">Deposit</h2>
            <form
              onSubmit={(e) => {
                e.preventDefault()
                depositMutation.mutate({ amount: deposit.amount, method: deposit.method })
              }}
              className="space-y-4"
            >
              <div>
                <label className="block text-sm text-gray-300 mb-1">Amount (NGN)</label>
                <input
                  type="number"
                  min={100}
                  className="w-full bg-gray-800 text-white border border-gray-700 rounded px-3 py-2"
                  value={deposit.amount}
                  onChange={(e) => setDeposit({ ...deposit, amount: Number(e.target.value) })}
                />
              </div>
              <div>
                <label className="block text-sm text-gray-300 mb-1">Method</label>
                <select
                  className="w-full bg-gray-800 text-white border border-gray-700 rounded px-3 py-2"
                  value={deposit.method}
                  onChange={(e) => setDeposit({ ...deposit, method: e.target.value })}
                >
                  <option value="paystack">Paystack</option>
                  <option value="flutterwave">Flutterwave</option>
                </select>
              </div>
              <button
                type="submit"
                disabled={depositMutation.isPending}
                className="w-full bg-gradient-to-r from-orange-500 to-orange-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:from-orange-600 hover:to-orange-700 transition-all disabled:opacity-50"
              >
                {depositMutation.isPending ? 'Processing...' : 'Deposit'}
              </button>
              {depositMutation.isError && <p className="text-red-400 text-sm">Failed to generate payment link.</p>}
              {depositMutation.isSuccess && <p className="text-green-400 text-sm">Payment link generated! Check the new tab to complete payment.</p>}
            </form>
          </div>

          <div className="bg-gray-900 rounded-lg shadow p-6">
            <h2 className="text-xl font-bold text-white mb-4">Withdraw</h2>
            <form
              onSubmit={(e) => {
                e.preventDefault()
                withdrawMutation.mutate({ amount: withdraw.amount })
              }}
              className="space-y-4"
            >
              <div>
                <label className="block text-sm text-gray-300 mb-1">Amount (NGN)</label>
                <input
                  type="number"
                  min={100}
                  className="w-full bg-gray-800 text-white border border-gray-700 rounded px-3 py-2"
                  value={withdraw.amount}
                  onChange={(e) => setWithdraw({ amount: Number(e.target.value) })}
                />
              </div>
              <button
                type="submit"
                disabled={withdrawMutation.isPending}
                className="w-full bg-gradient-to-r from-orange-500 to-orange-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:from-orange-600 hover:to-orange-700 transition-all disabled:opacity-50"
              >
                {withdrawMutation.isPending ? 'Processing...' : 'Withdraw'}
              </button>
              {withdrawMutation.isError && <p className="text-red-400 text-sm">Withdrawal failed.</p>}
              {withdrawMutation.isSuccess && <p className="text-green-400 text-sm">Withdrawal completed.</p>}
            </form>
          </div>
        </div>

        <div className="bg-gray-900 rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-white mb-4">Transactions</h2>
          {loadingTx ? (
            <p className="text-gray-400">Loading...</p>
          ) : txPage && txPage.transactions && txPage.transactions.length > 0 ? (
            <div className="space-y-3">
              {txPage.transactions.map((t: any) => (
                <div key={t.id} className="flex items-center justify-between p-4 bg-gray-800 rounded-lg">
                  <div>
                    <p className="text-white font-medium capitalize">{t.type || t.transaction_type}</p>
                    <p className="text-sm text-gray-400">Ref: {t.reference}</p>
                  </div>
                  <div className="text-right">
                    <p className={`font-semibold ${t.amount > 0 ? 'text-green-500' : 'text-red-500'}`}>
                      {formatCurrency(t.amount)}
                    </p>
                    <p className="text-sm text-gray-300">{t.status}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-400">No transactions yet.</p>
          )}
        </div>
      </div>
    </div>
  )
}
