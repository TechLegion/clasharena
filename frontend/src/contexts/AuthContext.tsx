'use client'

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { User, AuthResponse, LoginRequest, RegisterRequest } from '@/lib/types'
import api from '@/lib/api'
import { taskService } from '@/lib/services/tasks'
import { isTokenExpired } from '@/lib/jwt'

interface AuthContextType {
  user: User | null
  isLoading: boolean
  login: (credentials: LoginRequest) => Promise<void>
  register: (userData: RegisterRequest) => Promise<void>
  logout: () => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (token && token !== 'mock-jwt-token-for-development') {
      // Check if token is expired before making API calls
      if (isTokenExpired(token)) {
        console.log('Token is expired, clearing authentication')
        localStorage.removeItem('token')
        setUser(null)
        setIsAuthenticated(false)
        setIsLoading(false)
        return
      }
      
      // Real token exists and is valid - set authenticated state
      setIsAuthenticated(true)
      // Restore user data from localStorage
      try {
        const storedUser = localStorage.getItem('user')
        if (storedUser) {
          setUser(JSON.parse(storedUser))
        }
      } catch (error) {
        console.error('Failed to restore user data:', error)
        localStorage.removeItem('user')
        setUser(null)
        setIsAuthenticated(false)
      } finally {
        setIsLoading(false)
      }
    } else {
      // No token or mock token - clear user
      localStorage.removeItem('token')
      setUser(null)
      setIsAuthenticated(false)
      setIsLoading(false)
    }
  }, [])

  const login = async (credentials: LoginRequest) => {
    try {
      console.log('🚀 AuthContext: Attempting login with:', credentials)
      console.log('🚀 AuthContext: API base URL:', api.defaults.baseURL)
      const response = await api.post('/auth/login-direct', credentials)
      console.log('✅ AuthContext: Login response:', response.data)
      
      // Handle direct response (synchronous login)
      const { access_token, user } = response.data
      localStorage.setItem('token', access_token)
      localStorage.setItem('user', JSON.stringify(user)) // Store user data
      setUser(user)
      setIsAuthenticated(true)
    } catch (error: any) {
      console.error('❌ AuthContext: Login error:', error)
      console.error('❌ AuthContext: Error response:', error.response)
      console.error('❌ AuthContext: Error status:', error.response?.status)
      console.error('❌ AuthContext: Error data:', error.response?.data)
      
      // Handle different error types
      let errorMessage = 'Login failed. Please try again.'
      
      if (error.response?.status === 401) {
        errorMessage = 'Invalid email or password. Please check your credentials.'
      } else if (error.response?.status === 403) {
        errorMessage = 'Account is inactive. Please contact support.'
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail
      } else if (error.message) {
        errorMessage = error.message
      }
      
      throw new Error(errorMessage)
    }
  }

  const register = async (userData: RegisterRequest) => {
    try {
      const response = await api.post('/auth/register', userData)
      
      // Handle direct response (synchronous registration)
      const { access_token, user } = response.data
      localStorage.setItem('token', access_token)
      localStorage.setItem('user', JSON.stringify(user)) // Store user data
      setUser(user)
      setIsAuthenticated(true)
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Registration failed. Please try again.'
      throw new Error(errorMessage)
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    setUser(null)
    setIsAuthenticated(false)
  }

  const value: AuthContextType = {
    user,
    isLoading,
    login,
    register,
    logout,
    isAuthenticated,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}
