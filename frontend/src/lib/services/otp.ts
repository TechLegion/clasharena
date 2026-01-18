import { taskService } from './tasks'
import { API_BASE_URL } from '../utils'

interface SendOTPRequest {
  email?: string
  phone_number?: string
  purpose?: string
}

interface VerifyOTPRequest {
  otp_code: string
  purpose?: string
}

interface TaskResponse {
  task_id: string
  status: string
}

export const otpService = {
  // Send OTP via email
  async sendEmailOTP(email: string, purpose: string = 'email_verification'): Promise<TaskResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/otp/send/email`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({ email, purpose })
    })

    if (!response.ok) {
      throw new Error('Failed to send email OTP')
    }

    return response.json()
  },

  // Send OTP via SMS
  async sendSMSOTP(phoneNumber: string, purpose: string = 'phone_verification'): Promise<TaskResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/otp/send/sms`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({ phone_number: phoneNumber, purpose })
    })

    if (!response.ok) {
      throw new Error('Failed to send SMS OTP')
    }

    return response.json()
  },

  // Verify OTP
  async verifyOTP(otpCode: string, purpose: string = 'email_verification'): Promise<TaskResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/otp/verify`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({ otp_code: otpCode, purpose })
    })

    if (!response.ok) {
      throw new Error('Failed to verify OTP')
    }

    return response.json()
  },

  // Resend OTP
  async resendOTP(purpose: string = 'email_verification'): Promise<TaskResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/otp/resend`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({ purpose })
    })

    if (!response.ok) {
      throw new Error('Failed to resend OTP')
    }

    return response.json()
  },

  // Helper function to poll and get result
  async sendAndWaitForOTP(email?: string, phoneNumber?: string, purpose?: string) {
    let taskResponse: TaskResponse

    if (email) {
      taskResponse = await this.sendEmailOTP(email, purpose || 'email_verification')
    } else if (phoneNumber) {
      taskResponse = await this.sendSMSOTP(phoneNumber, purpose || 'phone_verification')
    } else {
      throw new Error('Either email or phone number must be provided')
    }

    return taskService.pollTask(taskResponse.task_id)
  },

  // Helper function to verify and wait for result
  async verifyAndWaitForOTP(otpCode: string, purpose: string = 'email_verification') {
    const taskResponse = await this.verifyOTP(otpCode, purpose)
    return taskService.pollTask(taskResponse.task_id)
  }
}
