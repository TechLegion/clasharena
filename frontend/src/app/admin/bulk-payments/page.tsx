'use client'

import { useState, useEffect } from 'react'
import {
  CurrencyDollarIcon,
  UsersIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  EyeIcon,
  PlusIcon,
  ArrowDownTrayIcon
} from '@heroicons/react/24/outline'

interface BulkPayment {
  id: string
  status: string
  total_amount: number
  total_recipients: number
  successful_count: number
  failed_count: number
  description: string
  created_at: string
  updated_at: string
}

interface BulkPaymentRecipient {
  id: string
  user_id: string
  username: string
  email: string
  amount: number
  reason: string
  account_number: string
  bank_code: string
  account_name: string
  status: string
  error_message?: string
  paystack_reference?: string
}

export default function AdminBulkPayments() {
  const [bulkPayments, setBulkPayments] = useState<BulkPayment[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedPayment, setSelectedPayment] = useState<string | null>(null)
  const [recipients, setRecipients] = useState<BulkPaymentRecipient[]>([])
  const [showModal, setShowModal] = useState(false)

  useEffect(() => {
    fetchBulkPayments()
  }, [])

  const fetchBulkPayments = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      const response = await fetch('http://localhost:8001/api/v1/payments/bulk/history', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        const data = await response.json()
        setBulkPayments(data.bulk_payments || [])
      } else {
        console.error('Failed to fetch bulk payments')
      }
    } catch (error) {
      console.error('Error fetching bulk payments:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchRecipients = async (bulkPaymentId: string) => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`http://localhost:8001/api/v1/payments/bulk/${bulkPaymentId}/recipients`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        const data = await response.json()
        setRecipients(data.recipients || [])
        setSelectedPayment(bulkPaymentId)
        setShowModal(true)
      } else {
        console.error('Failed to fetch recipients')
      }
    } catch (error) {
      console.error('Error fetching recipients:', error)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-900 text-green-300'
      case 'processing':
        return 'bg-blue-900 text-blue-300'
      case 'failed':
        return 'bg-red-900 text-red-300'
      case 'partially_completed':
        return 'bg-yellow-900 text-yellow-300'
      default:
        return 'bg-gray-700 text-gray-300'
    }
  }

  const getRecipientStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-900 text-green-300'
      case 'failed':
        return 'bg-red-900 text-red-300'
      case 'processing':
        return 'bg-blue-900 text-blue-300'
      default:
        return 'bg-gray-700 text-gray-300'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Bulk Payments</h1>
          <p className="mt-2 text-gray-300">Manage bulk payments to multiple users</p>
        </div>
        <button
          onClick={() => {/* TODO: Implement create bulk payment modal */}}
          className="bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-md font-medium flex items-center"
        >
          <PlusIcon className="h-5 w-5 mr-2" />
          Create Bulk Payment
        </button>
      </div>

      {/* Bulk Payments Table */}
      <div className="bg-gray-800 shadow rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-700">
            <thead className="bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Payment ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Description
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Amount
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Recipients
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-gray-800 divide-y divide-gray-700">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-4 text-center text-gray-400">
                    Loading bulk payments...
                  </td>
                </tr>
              ) : bulkPayments.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-4 text-center text-gray-400">
                    No bulk payments found
                  </td>
                </tr>
              ) : (
                bulkPayments.map((payment) => (
                  <tr key={payment.id} className="hover:bg-gray-700">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-white">
                        {payment.id.slice(0, 8)}...
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-white">
                        {payment.description}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-white font-medium">
                        ₦{payment.total_amount.toLocaleString()}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-white">
                        {payment.successful_count}/{payment.total_recipients}
                      </div>
                      {payment.failed_count > 0 && (
                        <div className="text-xs text-red-400">
                          {payment.failed_count} failed
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(payment.status)}`}>
                        {payment.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                      {new Date(payment.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => fetchRecipients(payment.id)}
                          className="text-blue-400 hover:text-blue-300"
                          title="View Recipients"
                        >
                          <EyeIcon className="h-5 w-5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recipients Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-6xl shadow-lg rounded-md bg-gray-800">
            <div className="mt-3">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-white">
                  Recipients - {selectedPayment?.slice(0, 8)}...
                </h3>
                <button
                  onClick={() => setShowModal(false)}
                  className="text-gray-400 hover:text-white"
                >
                  <XCircleIcon className="h-6 w-6" />
                </button>
              </div>
              
              <div className="overflow-x-auto max-h-96">
                <table className="min-w-full divide-y divide-gray-700">
                  <thead className="bg-gray-700 sticky top-0">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase">
                        User
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase">
                        Amount
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase">
                        Reason
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase">
                        Account
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase">
                        Status
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase">
                        Reference
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-gray-800 divide-y divide-gray-700">
                    {recipients.map((recipient) => (
                      <tr key={recipient.id}>
                        <td className="px-4 py-2 whitespace-nowrap">
                          <div className="text-sm text-white">
                            {recipient.username}
                          </div>
                          <div className="text-xs text-gray-400">
                            {recipient.email}
                          </div>
                        </td>
                        <td className="px-4 py-2 whitespace-nowrap">
                          <div className="text-sm text-white font-medium">
                            ₦{recipient.amount.toLocaleString()}
                          </div>
                        </td>
                        <td className="px-4 py-2 whitespace-nowrap">
                          <div className="text-sm text-white">
                            {recipient.reason}
                          </div>
                        </td>
                        <td className="px-4 py-2 whitespace-nowrap">
                          <div className="text-sm text-white">
                            {recipient.account_name}
                          </div>
                          <div className="text-xs text-gray-400">
                            {recipient.account_number} ({recipient.bank_code})
                          </div>
                        </td>
                        <td className="px-4 py-2 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getRecipientStatusColor(recipient.status)}`}>
                            {recipient.status}
                          </span>
                          {recipient.error_message && (
                            <div className="text-xs text-red-400 mt-1">
                              {recipient.error_message}
                            </div>
                          )}
                        </td>
                        <td className="px-4 py-2 whitespace-nowrap">
                          <div className="text-xs text-gray-400">
                            {recipient.paystack_reference || 'N/A'}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
