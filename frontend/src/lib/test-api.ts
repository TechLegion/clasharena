import api from './api'

export const testAPI = async () => {
  try {
    console.log('Testing ClashArena API...')
    
    // Test health endpoint
    const healthResponse = await fetch('http://localhost:8001/health')
    const healthData = await healthResponse.json()
    console.log('✅ Health check:', healthData)
    
    // Test API root
    const apiResponse = await fetch('http://localhost:8001/api/v1')
    const apiData = await apiResponse.json()
    console.log('✅ API root:', apiData)
    
    return true
  } catch (error) {
    console.error('❌ API test failed:', error)
    return false
  }
}

// Test registration
export const testRegistration = async (userData: {
  email: string
  username: string
  full_name: string
  password: string
}) => {
  try {
    const response = await api.post('/auth/register', userData)
    console.log('✅ Registration successful:', response.data)
    return response.data
  } catch (error: any) {
    console.error('❌ Registration failed:', error.response?.data || error.message)
    throw error
  }
}

// Test login
export const testLogin = async (credentials: {
  email: string
  password: string
}) => {
  try {
    const response = await api.post('/auth/login', credentials)
    console.log('✅ Login successful:', response.data)
    return response.data
  } catch (error: any) {
    console.error('❌ Login failed:', error.response?.data || error.message)
    throw error
  }
}
