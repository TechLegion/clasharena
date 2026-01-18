'use client'

import { useState, useEffect } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useQueryClient } from '@tanstack/react-query'
import { useAuth } from '@/contexts/AuthContext'
import { paymentService, Bank } from '@/lib/services/payments'
import { formatCurrency } from '@/lib/utils'
import {
  XMarkIcon,
  CurrencyDollarIcon,
  BuildingLibraryIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'

interface WithdrawalModalProps {
  isOpen: boolean
  onClose: () => void
  currentBalance: number
}

const WithdrawalModal = ({ isOpen, onClose, currentBalance }: WithdrawalModalProps) => {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [amount, setAmount] = useState('')
  const [selectedBank, setSelectedBank] = useState('')
  const [accountNumber, setAccountNumber] = useState('')
  const [accountName, setAccountName] = useState('')
  const [isValidating, setIsValidating] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [withdrawalResult, setWithdrawalResult] = useState<any>(null)
  const [validationError, setValidationError] = useState('')

  // Predefined amounts for quick selection
  const quickAmounts = [1000, 2500, 5000, 10000, 25000, 50000]

  // Fetch banks list
  const { data: banksData, isLoading: loadingBanks } = useQuery({
    queryKey: ['banks'],
    queryFn: paymentService.getBanks,
    enabled: isOpen
  })

  const banks: Bank[] = banksData?.banks || []

  const validateAccountMutation = useMutation({
    mutationFn: ({ accountNumber, bankCode }: { accountNumber: string; bankCode: string }) =>
      paymentService.validateAccount(accountNumber, bankCode),
    onSuccess: (data) => {
      setAccountName(data.account_name)
      setValidationError('')
      setIsValidating(false)
    },
    onError: (error: any) => {
      setValidationError(error.message || 'Invalid account details')
      setAccountName('')
      setIsValidating(false)
    }
  })

  const withdrawalMutation = useMutation({
    mutationFn: paymentService.completeWithdrawal,
    onSuccess: (result) => {
      if (result.success) {
        setWithdrawalResult(result)
        // Refresh wallet balance
        queryClient.invalidateQueries({ queryKey: ['wallet'] })
      }
    },
    onError: (error) => {
      console.error('Withdrawal error:', error)
    },
    onSettled: () => {
      setIsProcessing(false)
    }
  })

  const handleAmountChange = (value: string) => {
    const numValue = parseFloat(value)
    if (numValue > currentBalance) {
      setAmount(currentBalance.toString())
    } else {
      setAmount(value)
    }
  }

  const handleQuickAmount = (quickAmount: number) => {
    if (quickAmount <= currentBalance) {
      setAmount(quickAmount.toString())
    }
  }

  const handleAccountNumberChange = (value: string) => {
    setAccountNumber(value)
    setAccountName('')
    setValidationError('')
    
    // Auto-validate when we have both account number and bank
    if (value.length >= 10 && selectedBank) {
      const bank = banks.find(b => b.code === selectedBank)
      if (bank) {
        validateAccount(value, bank.code)
      }
    }
  }

  const validateAccount = async (accountNumber: string, bankCode: string) => {
    if (accountNumber.length < 10) return
    
    setIsValidating(true)
    validateAccountMutation.mutate({ accountNumber, bankCode })
  }

  const handleWithdrawal = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!amount || !selectedBank || !accountNumber || !accountName) {
      return
    }

    const withdrawalAmount = parseFloat(amount)
    if (withdrawalAmount < 500) {
      alert('Minimum withdrawal amount is ₦500')
      return
    }

    if (withdrawalAmount > currentBalance) {
      alert('Insufficient balance')
      return
    }

    if (!accountName) {
      alert('Please verify your account details first')
      return
    }

    setIsProcessing(true)
    withdrawalMutation.mutate({
      amount: withdrawalAmount,
      account_number: accountNumber,
      bank_code: selectedBank,
      account_name: accountName
    })
  }

  const resetModal = () => {
    setAmount('')
    setSelectedBank('')
    setAccountNumber('')
    setAccountName('')
    setValidationError('')
    setWithdrawalResult(null)
    setIsProcessing(false)
    setIsValidating(false)
  }

  const handleClose = () => {
    resetModal()
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 rounded-lg max-w-md w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <h2 className="text-xl font-bold text-white">Withdraw Funds</h2>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6">
          {/* Current Balance */}
          <div className="bg-gray-800 rounded-lg p-4 mb-6">
            <div className="flex items-center justify-between">
              <span className="text-gray-300">Available Balance</span>
              <span className="text-orange-400 font-bold text-lg">
                {formatCurrency(currentBalance)}
              </span>
            </div>
          </div>

          {!withdrawalResult ? (
            <form onSubmit={handleWithdrawal} className="space-y-6">
              {/* Quick Amount Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-3">
                  Quick Amount Selection
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {quickAmounts.map((quickAmount) => (
                    <button
                      key={quickAmount}
                      type="button"
                      onClick={() => handleQuickAmount(quickAmount)}
                      disabled={quickAmount > currentBalance}
                      className={`p-2 text-sm rounded-lg transition-colors border ${
                        quickAmount > currentBalance
                          ? 'bg-gray-700 text-gray-500 border-gray-600 cursor-not-allowed'
                          : 'bg-gray-800 hover:bg-gray-700 text-white border-gray-700'
                      }`}
                    >
                      {formatCurrency(quickAmount)}
                    </button>
                  ))}
                </div>
              </div>

              {/* Amount Input */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Amount (NGN)
                </label>
                <div className="relative">
                  <CurrencyDollarIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="number"
                    value={amount}
                    onChange={(e) => handleAmountChange(e.target.value)}
                    placeholder="Enter amount"
                    min="500"
                    max={currentBalance}
                    step="100"
                    className="w-full pl-10 pr-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:border-orange-500 focus:outline-none"
                    required
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Minimum: ₦500 • Maximum: {formatCurrency(currentBalance)}
                </p>
              </div>

              {/* Bank Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Select Bank
                </label>
                <div className="relative">
                  <BuildingLibraryIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <select
                    value={selectedBank}
                    onChange={(e) => setSelectedBank(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:border-orange-500 focus:outline-none"
                    required
                  >
                    <option value="">Select your bank</option>
                    {loadingBanks ? (
                      <option disabled>Loading banks...</option>
                    ) : (
                      banks.map((bank) => (
                        <option key={bank.code} value={bank.code}>
                          {bank.name}
                        </option>
                      ))
                    )}
                  </select>
                </div>
              </div>

              {/* Account Number */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Account Number
                </label>
                <input
                  type="text"
                  value={accountNumber}
                  onChange={(e) => handleAccountNumberChange(e.target.value)}
                  placeholder="Enter 10-digit account number"
                  maxLength={10}
                  className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:border-orange-500 focus:outline-none"
                  required
                />
                {isValidating && (
                  <p className="text-xs text-blue-400 mt-1">Validating account...</p>
                )}
                {validationError && (
                  <p className="text-xs text-red-400 mt-1">{validationError}</p>
                )}
              </div>

              {/* Account Name (Auto-filled after validation) */}
              {accountName && (
                <div className="bg-green-900/20 border border-green-500/30 rounded-lg p-3">
                  <div className="flex items-center space-x-2">
                    <CheckCircleIcon className="w-5 h-5 text-green-400" />
                    <span className="text-green-400 text-sm font-medium">
                      Account Name: {accountName}
                    </span>
                  </div>
                </div>
              )}

              {/* Withdrawal Info */}
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <ExclamationTriangleIcon className="w-5 h-5 text-orange-400" />
                  <span className="text-sm font-medium text-gray-300">Important</span>
                </div>
                <ul className="text-xs text-gray-400 space-y-1">
                  <li>• Withdrawals are processed within 24 hours</li>
                  <li>• Ensure account details are correct</li>
                  <li>• A 2.5% processing fee applies</li>
                  <li>• You'll receive ₦{(parseFloat(amount) * 0.975).toFixed(2)} after fees</li>
                </ul>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isProcessing || !amount || !selectedBank || !accountNumber || !accountName}
                className="w-full bg-gradient-to-r from-orange-500 to-orange-600 text-white font-bold py-3 px-4 rounded-lg transition-all hover:from-orange-600 hover:to-orange-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {isProcessing ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                    Processing...
                  </>
                ) : (
                  <>
                    <CurrencyDollarIcon className="w-5 h-5 mr-2" />
                    Request Withdrawal
                  </>
                )}
              </button>
            </form>
          ) : (
            /* Withdrawal Success State */
            <div className="text-center space-y-6">
              <div className="flex justify-center">
                <CheckCircleIcon className="w-16 h-16 text-green-500" />
              </div>
              
              <div>
                <h3 className="text-xl font-bold text-white mb-2">Withdrawal Requested!</h3>
                <p className="text-gray-300">
                  Your withdrawal request of{' '}
                  <span className="text-orange-400 font-bold">{formatCurrency(parseFloat(amount))}</span>{' '}
                  has been submitted successfully.
                </p>
              </div>

              <div className="bg-gray-800 rounded-lg p-4 text-left">
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Amount:</span>
                    <span className="text-white font-medium">{formatCurrency(parseFloat(amount))}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Reference:</span>
                    <span className="text-white font-mono text-xs">{withdrawalResult.reference}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Account:</span>
                    <span className="text-white">{accountName}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">New Balance:</span>
                    <span className="text-orange-400 font-bold">
                      {formatCurrency(withdrawalResult.new_balance)}
                    </span>
                  </div>
                </div>
              </div>

              <button
                onClick={handleClose}
                className="w-full bg-gradient-to-r from-orange-500 to-orange-600 text-white font-bold py-3 px-4 rounded-lg transition-all hover:from-orange-600 hover:to-orange-700"
              >
                Close
              </button>

              <p className="text-xs text-gray-500">
                Your withdrawal will be processed within 24 hours. You'll receive a confirmation email.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default WithdrawalModal

