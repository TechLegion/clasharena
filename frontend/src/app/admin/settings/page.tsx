'use client'

import { useState, useEffect } from 'react'
import {
  CogIcon,
  ShieldCheckIcon,
  CurrencyDollarIcon,
  BellIcon,
  ServerIcon,
  KeyIcon,
  GlobeAltIcon
} from '@heroicons/react/24/outline'

export default function AdminSettings() {
  const [settings, setSettings] = useState({
    platform: {
      name: 'ClashArena',
      currency: 'NGN',
      timezone: 'Africa/Lagos',
      maintenance_mode: false
    },
    payments: {
      min_deposit: 100,
      max_deposit: 1000000,
      min_withdrawal: 500,
      max_withdrawal: 500000,
      withdrawal_fee: 0
    },
    matches: {
      min_bet: 100,
      max_bet: 100000,
      auto_approve_results: false,
      default_timeout: 300
    },
    notifications: {
      email_notifications: true,
      sms_notifications: false,
      push_notifications: true,
      admin_alerts: true
    },
    security: {
      two_factor_required: false,
      ip_whitelist: '',
      session_timeout: 30,
      password_policy: 'strong'
    }
  })

  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('platform')

  const tabs = [
    { id: 'platform', name: 'Platform', icon: GlobeAltIcon },
    { id: 'payments', name: 'Payments', icon: CurrencyDollarIcon },
    { id: 'matches', name: 'Matches', icon: ShieldCheckIcon },
    { id: 'notifications', name: 'Notifications', icon: BellIcon },
    { id: 'security', name: 'Security', icon: KeyIcon }
  ]

  const updateSetting = (category: string, key: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category as keyof typeof prev],
        [key]: value
      }
    }))
  }

  const saveSettings = async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch('http://localhost:8001/api/v1/admin/settings', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(settings)
      })

      if (response.ok) {
        alert('Settings saved successfully!')
      } else {
        alert('Failed to save settings')
      }
    } catch (error) {
      console.error('Error saving settings:', error)
      alert('Error saving settings')
    } finally {
      setLoading(false)
    }
  }

  const renderPlatformSettings = () => (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Platform Name
        </label>
        <input
          type="text"
          value={settings.platform.name}
          onChange={(e) => updateSetting('platform', 'name', e.target.value)}
          className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
        />
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Default Currency
        </label>
        <select
          value={settings.platform.currency}
          onChange={(e) => updateSetting('platform', 'currency', e.target.value)}
          className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
        >
          <option value="NGN">Nigerian Naira (NGN)</option>
          <option value="USD">US Dollar (USD)</option>
          <option value="EUR">Euro (EUR)</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Timezone
        </label>
        <select
          value={settings.platform.timezone}
          onChange={(e) => updateSetting('platform', 'timezone', e.target.value)}
          className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
        >
          <option value="Africa/Lagos">Africa/Lagos</option>
          <option value="UTC">UTC</option>
          <option value="America/New_York">America/New_York</option>
        </select>
      </div>

      <div className="flex items-center">
        <input
          type="checkbox"
          checked={settings.platform.maintenance_mode}
          onChange={(e) => updateSetting('platform', 'maintenance_mode', e.target.checked)}
          className="rounded border-gray-600 text-orange-500 focus:ring-orange-500"
        />
        <label className="ml-2 text-sm text-gray-300">
          Maintenance Mode
        </label>
      </div>
    </div>
  )

  const renderPaymentSettings = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Minimum Deposit (₦)
          </label>
          <input
            type="number"
            value={settings.payments.min_deposit}
            onChange={(e) => updateSetting('payments', 'min_deposit', parseInt(e.target.value))}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Maximum Deposit (₦)
          </label>
          <input
            type="number"
            value={settings.payments.max_deposit}
            onChange={(e) => updateSetting('payments', 'max_deposit', parseInt(e.target.value))}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Minimum Withdrawal (₦)
          </label>
          <input
            type="number"
            value={settings.payments.min_withdrawal}
            onChange={(e) => updateSetting('payments', 'min_withdrawal', parseInt(e.target.value))}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Maximum Withdrawal (₦)
          </label>
          <input
            type="number"
            value={settings.payments.max_withdrawal}
            onChange={(e) => updateSetting('payments', 'max_withdrawal', parseInt(e.target.value))}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Withdrawal Fee (₦)
        </label>
        <input
          type="number"
          value={settings.payments.withdrawal_fee}
          onChange={(e) => updateSetting('payments', 'withdrawal_fee', parseInt(e.target.value))}
          className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
        />
      </div>
    </div>
  )

  const renderMatchSettings = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Minimum Bet (₦)
          </label>
          <input
            type="number"
            value={settings.matches.min_bet}
            onChange={(e) => updateSetting('matches', 'min_bet', parseInt(e.target.value))}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Maximum Bet (₦)
          </label>
          <input
            type="number"
            value={settings.matches.max_bet}
            onChange={(e) => updateSetting('matches', 'max_bet', parseInt(e.target.value))}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Default Timeout (seconds)
        </label>
        <input
          type="number"
          value={settings.matches.default_timeout}
          onChange={(e) => updateSetting('matches', 'default_timeout', parseInt(e.target.value))}
          className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
        />
      </div>

      <div className="flex items-center">
        <input
          type="checkbox"
          checked={settings.matches.auto_approve_results}
          onChange={(e) => updateSetting('matches', 'auto_approve_results', e.target.checked)}
          className="rounded border-gray-600 text-orange-500 focus:ring-orange-500"
        />
        <label className="ml-2 text-sm text-gray-300">
          Auto-approve match results
        </label>
      </div>
    </div>
  )

  const renderNotificationSettings = () => (
    <div className="space-y-6">
      <div className="flex items-center">
        <input
          type="checkbox"
          checked={settings.notifications.email_notifications}
          onChange={(e) => updateSetting('notifications', 'email_notifications', e.target.checked)}
          className="rounded border-gray-600 text-orange-500 focus:ring-orange-500"
        />
        <label className="ml-2 text-sm text-gray-300">
          Email Notifications
        </label>
      </div>

      <div className="flex items-center">
        <input
          type="checkbox"
          checked={settings.notifications.sms_notifications}
          onChange={(e) => updateSetting('notifications', 'sms_notifications', e.target.checked)}
          className="rounded border-gray-600 text-orange-500 focus:ring-orange-500"
        />
        <label className="ml-2 text-sm text-gray-300">
          SMS Notifications
        </label>
      </div>

      <div className="flex items-center">
        <input
          type="checkbox"
          checked={settings.notifications.push_notifications}
          onChange={(e) => updateSetting('notifications', 'push_notifications', e.target.checked)}
          className="rounded border-gray-600 text-orange-500 focus:ring-orange-500"
        />
        <label className="ml-2 text-sm text-gray-300">
          Push Notifications
        </label>
      </div>

      <div className="flex items-center">
        <input
          type="checkbox"
          checked={settings.notifications.admin_alerts}
          onChange={(e) => updateSetting('notifications', 'admin_alerts', e.target.checked)}
          className="rounded border-gray-600 text-orange-500 focus:ring-orange-500"
        />
        <label className="ml-2 text-sm text-gray-300">
          Admin Alerts
        </label>
      </div>
    </div>
  )

  const renderSecuritySettings = () => (
    <div className="space-y-6">
      <div className="flex items-center">
        <input
          type="checkbox"
          checked={settings.security.two_factor_required}
          onChange={(e) => updateSetting('security', 'two_factor_required', e.target.checked)}
          className="rounded border-gray-600 text-orange-500 focus:ring-orange-500"
        />
        <label className="ml-2 text-sm text-gray-300">
          Require Two-Factor Authentication
        </label>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Session Timeout (minutes)
        </label>
        <input
          type="number"
          value={settings.security.session_timeout}
          onChange={(e) => updateSetting('security', 'session_timeout', parseInt(e.target.value))}
          className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Password Policy
        </label>
        <select
          value={settings.security.password_policy}
          onChange={(e) => updateSetting('security', 'password_policy', e.target.value)}
          className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
        >
          <option value="weak">Weak (6+ characters)</option>
          <option value="medium">Medium (8+ characters, mixed case)</option>
          <option value="strong">Strong (8+ characters, numbers, symbols)</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          IP Whitelist (comma-separated)
        </label>
        <textarea
          value={settings.security.ip_whitelist}
          onChange={(e) => updateSetting('security', 'ip_whitelist', e.target.value)}
          rows={3}
          placeholder="192.168.1.1, 10.0.0.1"
          className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
        />
      </div>
    </div>
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">System Settings</h1>
        <p className="mt-2 text-gray-300">Configure platform settings and preferences</p>
      </div>

      <div className="bg-gray-800 shadow rounded-lg">
        {/* Tabs */}
        <div className="border-b border-gray-700">
          <nav className="-mb-px flex space-x-8 px-6">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`${
                  activeTab === tab.id
                    ? 'border-orange-500 text-orange-400'
                    : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-300'
                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center`}
              >
                <tab.icon className="h-5 w-5 mr-2" />
                {tab.name}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {activeTab === 'platform' && renderPlatformSettings()}
          {activeTab === 'payments' && renderPaymentSettings()}
          {activeTab === 'matches' && renderMatchSettings()}
          {activeTab === 'notifications' && renderNotificationSettings()}
          {activeTab === 'security' && renderSecuritySettings()}
        </div>

        {/* Save Button */}
        <div className="bg-gray-700 px-6 py-4 flex justify-end">
          <button
            onClick={saveSettings}
            disabled={loading}
            className="bg-orange-600 hover:bg-orange-700 disabled:opacity-50 text-white px-6 py-2 rounded-md font-medium transition-colors"
          >
            {loading ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  )
}
