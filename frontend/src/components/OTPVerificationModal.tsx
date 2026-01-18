'use client'

import { useState, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useQueryClient } from '@tanstack/react-query'
import { useAuth } from '@/contexts/AuthContext'
import { taskService } from '@/lib/services/tasks'
import {
  XMarkIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline'

interface OTPVerificationModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
  email?: string
  phoneNumber?: string
  verificationType: 'email' | 'sms'
}

const OTPVerificationModal = ({ isOpen, onClose, onSuccess, email, phoneNumber, verificationType }: OTPVerificationModalProps) => {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [otpCode, setOtpCode] = useState('')
  const [isResending, setIsResending] = useState(false)
  const [resendCooldown, setResendCooldown] = useState(0)
  const [error, setError] = useState('')

  // Countdown timer for resend button
  useEffect(() => {
    if (resendCooldown > 0) {
      const timer = setTimeout(() => setResendCooldown(resendCooldown - 1), 1000)
      return () => clearTimeout(timer)
    }
  }, [resendCooldown])

  const verifyOTPMutation = useMutation({
    mutationFn: async (code: string) => {
      const response = await fetch('/api/v1/otp/verify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ 
          otp_code: code,
          purpose: verificationType === 'email' ? 'email_verification' : 'phone_verification'
        })
      })
      
      if (!response.ok) {
        throw new Error('Failed to verify OTP')
      }
      
      const data = await response.json()
      return taskService.pollTask(data.task_id)
    },
    onSuccess: (result) => {
      if (result.success) {
        queryClient.invalidateQueries({ queryKey: ['user'] })
        onSuccess()
      } else {
        setError(result.error || 'OTP verification failed')
      }
    },
    onError: (error: any) => {
      setError(error.message || 'Network error')
    }
  })

  const resendOTPMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch('/api/v1/otp/resend', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ 
          purpose: verificationType === 'email' ? 'email_verification' : 'phone_verification'
        })
      })
      
      if (!response.ok) {
        throw new Error('Failed to resend OTP')
      }
      
      const data = await response.json()
      return taskService.pollTask(data.task_id)
    },
    onSuccess: (result) => {
      if (result.success) {
        setResendCooldown(60) // 60 second cooldown
        setError('')
      } else {
        setError(result.error || 'Failed to resend OTP')
      }
      setIsResending(false)
    },
    onError: (error: any) => {
      setError(error.message || 'Network error')
      setIsResending(false)
    }
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (otpCode.length === 6) {
      setError('')
      verifyOTPMutation.mutate(otpCode)
    }
  }

  const handleResend = () => {
    if (resendCooldown === 0) {
      setIsResending(true)
      resendOTPMutation.mutate()
    }
  }

  const handleClose = () => {
    setOtpCode('')
    setError('')
    setResendCooldown(0)
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 rounded-lg max-w-md w-full">
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <h2 className="text-xl font-bold text-white">
            Verify Your {verificationType === 'email' ? 'Email' : 'Phone'}
          </h2>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6">
          <div className="text-center mb-6">
            <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircleIcon className="w-8 h-8 text-orange-600" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">
              Check Your {verificationType === 'email' ? 'Email' : 'Phone'}
            </h3>
            <p className="text-gray-300 text-sm">
              We've sent a 6-digit verification code to:
            </p>
            <p className="text-orange-400 font-medium">
              {verificationType === 'email' ? email : phoneNumber}
            </p>
            <p className="text-xs text-gray-400 mt-1">
              via {verificationType === 'email' ? 'email' : 'SMS'}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Enter Verification Code
              </label>
              <input
                type="text"
                value={otpCode}
                onChange={(e) => {
                  const value = e.target.value.replace(/\D/g, '').slice(0, 6)
                  setOtpCode(value)
                  setError('')
                }}
                placeholder="000000"
                className="w-full px-4 py-3 text-center text-2xl font-mono bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:border-orange-500 focus:outline-none"
                maxLength={6}
                required
              />
            </div>

            {error && (
              <div className="flex items-center space-x-2 text-red-400 text-sm">
                <ExclamationTriangleIcon className="w-4 h-4" />
                <span>{error}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={otpCode.length !== 6 || verifyOTPMutation.isPending}
              className="w-full bg-gradient-to-r from-orange-500 to-orange-600 text-white font-bold py-3 px-4 rounded-lg transition-all hover:from-orange-600 hover:to-orange-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
            >
              {verifyOTPMutation.isPending ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                  Verifying...
                </>
              ) : (
                `Verify ${verificationType === 'email' ? 'Email' : 'Phone'}`
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-gray-400 text-sm mb-3">
              Didn't receive the code?
            </p>
            <button
              onClick={handleResend}
              disabled={resendCooldown > 0 || isResending}
              className="text-orange-400 hover:text-orange-300 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center mx-auto"
            >
              {isResending ? (
                <>
                  <ArrowPathIcon className="w-4 h-4 mr-1 animate-spin" />
                  Sending...
                </>
              ) : resendCooldown > 0 ? (
                `Resend in ${resendCooldown}s`
              ) : (
                'Resend Code'
              )}
            </button>
          </div>

          <div className="mt-4 p-3 bg-gray-800 rounded-lg">
            <p className="text-xs text-gray-400 text-center">
              💡 <strong>Development Mode:</strong> Check your backend console for the OTP code
              {verificationType === 'sms' && (
                <><br/>📱 <strong>SMS Mode:</strong> SMS will be sent via Twilio in production</>
              )}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default OTPVerificationModal
