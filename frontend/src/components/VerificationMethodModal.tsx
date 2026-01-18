'use client'

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useAuth } from '@/contexts/AuthContext'
import { otpService } from '@/lib/services/otp'
import {
  XMarkIcon,
  EnvelopeIcon,
  DevicePhoneMobileIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'

interface VerificationMethodModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: (type: 'email' | 'sms', contact: string) => void
  userEmail?: string
  userPhone?: string
}

const VerificationMethodModal = ({ 
  isOpen, 
  onClose, 
  onSuccess, 
  userEmail, 
  userPhone 
}: VerificationMethodModalProps) => {
  const { user } = useAuth()
  const [selectedMethod, setSelectedMethod] = useState<'email' | 'sms' | null>(null)
  const [phoneNumber, setPhoneNumber] = useState(userPhone || '')
  const [error, setError] = useState('')

  const sendOTPMutation = useMutation({
    mutationFn: async ({ method, contact }: { method: 'email' | 'sms', contact: string }) => {
      if (method === 'email') {
        return otpService.sendAndWaitForOTP(contact, undefined, 'email_verification')
      } else {
        return otpService.sendAndWaitForOTP(undefined, contact, 'phone_verification')
      }
    },
    onSuccess: (result) => {
      if (result.success) {
        const contact = selectedMethod === 'email' ? userEmail! : phoneNumber
        onSuccess(selectedMethod!, contact)
      } else {
        setError(result.error || 'Failed to send verification code')
      }
    },
    onError: (error: any) => {
      setError(error.message || 'Network error')
    }
  })

  const handleEmailVerification = () => {
    if (userEmail) {
      setSelectedMethod('email')
      setError('')
      sendOTPMutation.mutate({ method: 'email', contact: userEmail })
    }
  }

  const handleSMSVerification = () => {
    if (phoneNumber.trim()) {
      setSelectedMethod('sms')
      setError('')
      sendOTPMutation.mutate({ method: 'sms', contact: phoneNumber })
    } else {
      setError('Please enter your phone number')
    }
  }

  const handleClose = () => {
    setSelectedMethod(null)
    setPhoneNumber(userPhone || '')
    setError('')
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 rounded-lg max-w-md w-full">
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <h2 className="text-xl font-bold text-white">Verify Your Account</h2>
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
              Choose Verification Method
            </h3>
            <p className="text-gray-300 text-sm">
              Select how you'd like to receive your verification code
            </p>
          </div>

          <div className="space-y-4">
            {/* Email Option */}
            {userEmail && (
              <button
                onClick={handleEmailVerification}
                disabled={sendOTPMutation.isPending}
                className="w-full p-4 bg-gray-800 border border-gray-700 rounded-lg hover:border-orange-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-orange-100 rounded-full flex items-center justify-center">
                    <EnvelopeIcon className="w-5 h-5 text-orange-600" />
                  </div>
                  <div className="text-left">
                    <p className="text-white font-medium">Email Verification</p>
                    <p className="text-gray-400 text-sm">{userEmail}</p>
                  </div>
                </div>
              </button>
            )}

            {/* SMS Option */}
            <div className="p-4 bg-gray-800 border border-gray-700 rounded-lg">
              <div className="flex items-center space-x-3 mb-3">
                <div className="w-10 h-10 bg-orange-100 rounded-full flex items-center justify-center">
                  <DevicePhoneMobileIcon className="w-5 h-5 text-orange-600" />
                </div>
                <div className="text-left">
                  <p className="text-white font-medium">SMS Verification</p>
                  <p className="text-gray-400 text-sm">Recommended for Nigeria</p>
                </div>
              </div>
              
              <div className="space-y-3">
                <input
                  type="tel"
                  value={phoneNumber}
                  onChange={(e) => {
                    setPhoneNumber(e.target.value)
                    setError('')
                  }}
                  placeholder="+234 812 345 6789"
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-orange-500 focus:outline-none"
                />
                
                <button
                  onClick={handleSMSVerification}
                  disabled={!phoneNumber.trim() || sendOTPMutation.isPending}
                  className="w-full bg-orange-600 text-white py-2 px-4 rounded-lg hover:bg-orange-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {sendOTPMutation.isPending ? 'Sending...' : 'Send SMS Code'}
                </button>
              </div>
            </div>
          </div>

          {error && (
            <div className="mt-4 flex items-center space-x-2 text-red-400 text-sm">
              <ExclamationTriangleIcon className="w-4 h-4" />
              <span>{error}</span>
            </div>
          )}

          <div className="mt-6 p-3 bg-gray-800 rounded-lg">
            <p className="text-xs text-gray-400 text-center">
              💡 <strong>SMS Recommended:</strong> Higher delivery rate in Nigeria<br/>
              📱 <strong>Development:</strong> Check backend console for codes
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default VerificationMethodModal
