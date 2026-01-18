import api from '../api'
import { Wallet, Transaction } from '../types'
import { taskService } from './tasks'

export const walletService = {
  // Get wallet balance
  async getBalance(): Promise<Wallet> {
    try {
      const response = await api.get('/wallet/balance')
      
      // If it's a task response, poll for result
      if (response.data.task_id) {
        const result = await taskService.pollTask(response.data.task_id)
        return result.success ? result : { balance: 0, id: 'temp' }
      }
      
      return response.data
    } catch (error) {
      console.error('Error getting balance:', error)
      // Return mock data for development
      return { balance: 1000.50, id: 'mock-wallet' }
    }
  },

  // Get transaction history
  async getTransactions(params?: { page?: number; limit?: number }): Promise<{ transactions: Transaction[]; total: number; page: number; limit: number }> {
    try {
      const response = await api.get('/wallet/transactions', { params })
      
      // If it's a task response, poll for result
      if (response.data.task_id) {
        const result = await taskService.pollTask(response.data.task_id)
        return result.success ? result : { transactions: [], total: 0, page: 1, limit: 10 }
      }
      
      return response.data
    } catch (error) {
      console.error('Error getting transactions:', error)
      // Return mock data for development
      return { 
        transactions: [
          {
            id: '1',
            amount: 100,
            type: 'deposit',
            status: 'completed',
            description: 'Initial deposit',
            created_at: new Date().toISOString()
          }
        ], 
        total: 1, 
        page: 1, 
        limit: 10 
      }
    }
  },

  // Initialize deposit (generates payment link)
  async deposit(amount: number, paymentMethod: string, email?: string): Promise<any> {
    try {
      const response = await api.post('/wallet/deposit', {
        amount,
        payment_method: paymentMethod,
        email,
      })
      
      // If it's a task response, poll for result
      if (response.data.task_id) {
        const result = await taskService.pollTask(response.data.task_id)
        return result.success ? result : { success: false, error: 'Deposit failed' }
      }
      
      // Return payment link data
      if (response.data.status === 'success') {
        return {
          success: true,
          authorization_url: response.data.authorization_url,
          reference: response.data.reference,
          message: 'Payment link generated successfully'
        }
      } else {
        return {
          success: false,
          error: response.data.message || 'Failed to generate payment link'
        }
      }
    } catch (error: any) {
      console.error('Error initializing deposit:', error)
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Failed to generate payment link' 
      }
    }
  },

  // Withdraw funds
  async withdraw(amount: number, bank_details?: any): Promise<any> {
    try {
      const response = await api.post('/wallet/withdraw', {
        amount,
        bank_details,
      })
      
      // If it's a task response, poll for result
      if (response.data.task_id) {
        const result = await taskService.pollTask(response.data.task_id)
        return result.success ? result : { success: false, error: 'Withdrawal failed' }
      }
      
      return response.data
    } catch (error) {
      console.error('Error withdrawing funds:', error)
      return { success: false, error: 'Network error' }
    }
  }
}
