import api from '../api'
import { taskService } from './tasks'

export interface Bank {
  id: number
  name: string
  code: string
  longcode: string
  gateway: string | null
  pay_with_bank: boolean
  active: boolean
  is_deleted: boolean
  country: string
  currency: string
  type: string
}

export interface DepositRequest {
  amount: number
  email: string
}

export interface WithdrawalRequest {
  amount: number
  account_number: string
  bank_code: string
  account_name: string
}

export interface AccountValidation {
  account_name: string
  account_number: string
  bank_code: string
}

export interface Transaction {
  id: string
  type: 'deposit' | 'withdrawal'
  amount: number
  status: 'pending' | 'completed' | 'failed'
  description: string
  reference: string
  created_at: string
  completed_at?: string
}

export const paymentService = {
  // Initialize deposit
  async initializeDeposit(depositData: DepositRequest): Promise<{ task_id: string }> {
    try {
      const response = await api.post('/payments/deposit/initialize', depositData)
      return response.data
    } catch (error: any) {
      console.error('Error initializing deposit:', error)
      throw new Error(error.response?.data?.detail || 'Failed to initialize deposit')
    }
  },

  // Verify deposit
  async verifyDeposit(reference: string): Promise<any> {
    try {
      const response = await api.post('/payments/deposit/verify', { reference })
      return response.data
    } catch (error: any) {
      console.error('Error verifying deposit:', error)
      throw new Error(error.response?.data?.detail || 'Failed to verify deposit')
    }
  },

  // Request withdrawal
  async requestWithdrawal(withdrawalData: WithdrawalRequest): Promise<{ task_id: string }> {
    try {
      const response = await api.post('/payments/withdrawal/request', withdrawalData)
      return response.data
    } catch (error: any) {
      console.error('Error requesting withdrawal:', error)
      throw new Error(error.response?.data?.detail || 'Failed to request withdrawal')
    }
  },

  // Get banks list
  async getBanks(): Promise<{ banks: Bank[] }> {
    try {
      const response = await api.get('/payments/banks')
      return response.data
    } catch (error: any) {
      console.error('Error fetching banks:', error)
      throw new Error('Failed to fetch banks')
    }
  },

  // Validate account number
  async validateAccount(accountNumber: string, bankCode: string): Promise<AccountValidation> {
    try {
      const response = await api.post('/payments/validate-account', {
        account_number: accountNumber,
        bank_code: bankCode
      })
      return response.data
    } catch (error: any) {
      console.error('Error validating account:', error)
      throw new Error(error.response?.data?.detail || 'Failed to validate account')
    }
  },

  // Get transaction history
  async getTransactionHistory(page: number = 1, limit: number = 20): Promise<{ task_id: string }> {
    try {
      const response = await api.get('/payments/transactions', {
        params: { page, limit }
      })
      return response.data
    } catch (error: any) {
      console.error('Error fetching transactions:', error)
      throw new Error('Failed to fetch transaction history')
    }
  },

  // Initialize deposit and return payment URL (NO PAYMENT PROCESSING)
  async completeDeposit(depositData: DepositRequest): Promise<{
    success: boolean
    authorization_url?: string
    access_code?: string
    reference?: string
    transaction_id?: string
    error?: string
  }> {
    try {
      console.log('🚀 Starting deposit initialization with:', depositData)
      
      // Initialize deposit - this ONLY creates a payment link, no money is processed
      console.log('📞 Calling initializeDeposit...')
      const initResponse = await paymentService.initializeDeposit(depositData)
      console.log('✅ initializeDeposit response:', initResponse)
      
      // Return payment URL - user must complete payment on Paystack
      if (initResponse.status === 'success') {
        return {
          success: true,
          authorization_url: initResponse.authorization_url,
          access_code: initResponse.access_code,
          reference: initResponse.reference
        }
      } else {
        return {
          success: false,
          error: initResponse.message || 'Payment link generation failed'
        }
      }
    } catch (error: any) {
      console.error('❌ completeDeposit error:', error)
      return {
        success: false,
        error: error.message || 'Failed to generate payment link'
      }
    }
  },

  // Complete withdrawal flow with polling
  async completeWithdrawal(withdrawalData: WithdrawalRequest): Promise<{
    success: boolean
    transaction_id?: string
    reference?: string
    amount?: number
    new_balance?: number
    error?: string
  }> {
    try {
      // Request withdrawal
      const withdrawalResponse = await paymentService.requestWithdrawal(withdrawalData)
      
      // Poll for result
      const result = await taskService.pollTask(withdrawalResponse.task_id)
      
      if (result.success) {
        return {
          success: true,
          transaction_id: result.transaction_id,
          reference: result.reference,
          amount: result.amount,
          new_balance: result.new_balance
        }
      } else {
        return {
          success: false,
          error: result.error || 'Withdrawal request failed'
        }
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Withdrawal failed'
      }
    }
  }
}

