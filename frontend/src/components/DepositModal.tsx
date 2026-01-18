'use client'

import { useState, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useQueryClient } from '@tanstack/react-query'
import { useAuth } from '@/contexts/AuthContext'
import { paymentService } from '@/lib/services/payments'
import { formatCurrency } from '@/lib/utils'
import {
  XMarkIcon,
  CurrencyDollarIcon,
  CreditCardIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline'

interface DepositModalProps {
  isOpen: boolean
  onClose: () => void
}

const DepositModal = ({ isOpen, onClose }: DepositModalProps) => {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [amount, setAmount] = useState('')
  const [email, setEmail] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [depositResult, setDepositResult] = useState<any>(null)

  // Predefined amounts for quick selection
  const quickAmounts = [500, 1000, 2000, 5000, 10000, 20000]

  useEffect(() => {
    if (user?.email) {
      setEmail(user.email)
    }
  }, [user])

  const depositMutation = useMutation({
    mutationFn: paymentService.completeDeposit,
    onSuccess: (result) => {
      console.log('Payment link generation success:', result)
      if (result.success) {
        setDepositResult(result)
        // DO NOT refresh wallet balance here - no payment has been made yet
        // Balance will be updated only after successful payment via webhook
      } else {
        console.error('Payment link generation failed:', result.error)
        alert(`Payment link generation failed: ${result.error}`)
      }
    },
    onError: (error) => {
      console.error('Payment link generation error:', error)
      alert(`Payment link generation error: ${error.message}`)
    },
    onSettled: () => {
      console.log('Payment link generation settled')
      setIsProcessing(false)
    }
  })

  const handleDeposit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    console.log('Form submitted! Amount:', amount, 'Email:', email)
    console.log('Button disabled condition:', isProcessing || !amount || !email)
    
    if (!amount || !email) {
      console.log('Form validation failed - missing amount or email')
      return
    }

    const depositAmount = parseFloat(amount)
    if (depositAmount < 100) {
      alert('Minimum deposit amount is ₦100')
      return
    }

    if (depositAmount > 1000000) {
      alert('Maximum deposit amount is ₦1,000,000')
      return
    }

    setIsProcessing(true)
    depositMutation.mutate({
      amount: depositAmount,
      email
    })
  }

  const handleQuickAmount = (quickAmount: number) => {
    setAmount(quickAmount.toString())
  }

  const redirectToPayment = () => {
    if (depositResult?.authorization_url) {
      window.open(depositResult.authorization_url, '_blank')
    }
  }

  const resetModal = () => {
    setAmount('')
    setEmail('')
    setDepositResult(null)
    setIsProcessing(false)
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
          <h2 className="text-xl font-bold text-white">Deposit Funds</h2>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6">
          {!depositResult ? (
            <form onSubmit={handleDeposit} className="space-y-6">
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
                      className="p-2 text-sm bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition-colors border border-gray-700"
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
                    onChange={(e) => setAmount(e.target.value)}
                    placeholder="Enter amount"
                    min="100"
                    max="1000000"
                    step="100"
                    className="w-full pl-10 pr-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:border-orange-500 focus:outline-none"
                    required
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Minimum: ₦100 • Maximum: ₦1,000,000
                </p>
              </div>

              {/* Email Input */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Email Address
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your email"
                  className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:border-orange-500 focus:outline-none"
                  required
                />
              </div>

              {/* Payment Method Info */}
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <CreditCardIcon className="w-5 h-5 text-orange-400" />
                  <span className="text-sm font-medium text-gray-300">Payment Method</span>
                </div>
                <p className="text-xs text-gray-400">
                  You'll be redirected to Paystack for secure payment processing. 
                  We support cards, bank transfers, and mobile money.
                </p>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={(() => {
                  const isDisabled = isProcessing || !amount || !email
                  console.log('🔍 Button disabled check:', {
                    isProcessing,
                    amount,
                    email,
                    isDisabled,
                    amountTruthy: !!amount,
                    emailTruthy: !!email
                  })
                  return isDisabled
                })()}
                className={`w-full text-white font-bold py-3 px-4 rounded-lg transition-all flex items-center justify-center ${
                  isProcessing || !amount || !email 
                    ? 'bg-gray-600 cursor-not-allowed opacity-50' 
                    : 'bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 cursor-pointer'
                }`}
                onClick={() => {
                  console.log('Button clicked! Amount:', amount, 'Email:', email, 'IsProcessing:', isProcessing)
                  console.log('parseFloat(amount):', parseFloat(amount))
                }}
              >
                {isProcessing ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                    Processing...
                  </>
                ) : (
                  <>
                    <CreditCardIcon className="w-5 h-5 mr-2" />
                    Generate Payment Link
                  </>
                )}
              </button>
            </form>
          ) : (
            /* Payment Success State */
            <div className="text-center space-y-6">
              <div className="flex justify-center">
                <CheckCircleIcon className="w-16 h-16 text-green-500" />
              </div>
              
              <div>
                <h3 className="text-xl font-bold text-white mb-2">Payment Link Generated!</h3>
                <p className="text-gray-300">
                  Your payment link has been created. Click below to complete your deposit of{' '}
                  <span className="text-orange-400 font-bold">{formatCurrency(parseFloat(amount))}</span>
                </p>
                <p className="text-yellow-400 text-sm mt-2">
                  ⚠️ No payment has been processed yet. You will be redirected to Paystack to complete the payment.
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
                    <span className="text-white font-mono text-xs">{depositResult.reference}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Email:</span>
                    <span className="text-white">{email}</span>
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                <button
                  onClick={redirectToPayment}
                  className="w-full bg-gradient-to-r from-orange-500 to-orange-600 text-white font-bold py-3 px-4 rounded-lg transition-all hover:from-orange-600 hover:to-orange-700"
                >
                  Complete Payment →
                </button>
                
                <button
                  onClick={handleClose}
                  className="w-full bg-gray-700 text-white py-2 px-4 rounded-lg hover:bg-gray-600 transition-colors"
                >
                  Close
                </button>
              </div>

              <p className="text-xs text-gray-500">
                After payment, your balance will be updated automatically.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default DepositModal

