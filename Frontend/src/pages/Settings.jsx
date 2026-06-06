import React, { useState } from 'react'
import Card from '../components/ui/Card'
import Input from '../components/ui/Input'
import Button from '../components/ui/Button'
import { useAuth } from '../hooks/useAuth'
import toast from 'react-hot-toast'

const Settings = () => {
  const { user } = useAuth()
  const [profileForm, setProfileForm] = useState({
    name: user?.name || '',
    email: user?.email || '',
    company: user?.company || ''
  })
  const [passwordForm, setPasswordForm] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  })
  const [loading, setLoading] = useState(false)

  const handleProfileUpdate = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      // API call to update profile
      toast.success('Profile updated successfully')
    } catch (error) {
      toast.error(error.message || 'Failed to update profile')
    } finally {
      setLoading(false)
    }
  }

  const handlePasswordUpdate = async (e) => {
    e.preventDefault()
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      toast.error('New passwords do not match')
      return
    }
    
    setLoading(true)
    try {
      // API call to update password
      toast.success('Password updated successfully')
      setPasswordForm({
        current_password: '',
        new_password: '',
        confirm_password: ''
      })
    } catch (error) {
      toast.error(error.message || 'Failed to update password')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-1">Manage your account settings and preferences</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Profile Information">
          <form onSubmit={handleProfileUpdate} className="space-y-4">
            <Input
              label="Name"
              value={profileForm.name}
              onChange={(e) => setProfileForm({ ...profileForm, name: e.target.value })}
            />
            <Input
              label="Email"
              type="email"
              value={profileForm.email}
              onChange={(e) => setProfileForm({ ...profileForm, email: e.target.value })}
            />
            <Input
              label="Company"
              value={profileForm.company}
              onChange={(e) => setProfileForm({ ...profileForm, company: e.target.value })}
            />
            <Button type="submit" loading={loading}>
              Update Profile
            </Button>
          </form>
        </Card>

        <Card title="Change Password">
          <form onSubmit={handlePasswordUpdate} className="space-y-4">
            <Input
              label="Current Password"
              type="password"
              value={passwordForm.current_password}
              onChange={(e) => setPasswordForm({ ...passwordForm, current_password: e.target.value })}
              required
            />
            <Input
              label="New Password"
              type="password"
              value={passwordForm.new_password}
              onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
              required
            />
            <Input
              label="Confirm New Password"
              type="password"
              value={passwordForm.confirm_password}
              onChange={(e) => setPasswordForm({ ...passwordForm, confirm_password: e.target.value })}
              required
            />
            <Button type="submit" loading={loading}>
              Change Password
            </Button>
          </form>
        </Card>

        <Card title="API Settings" className="lg:col-span-2">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                API Key
              </label>
              <div className="flex space-x-2">
                <Input
                  value="••••••••••••••••"
                  disabled
                  className="flex-1 font-mono"
                />
                <Button variant="outline">
                  Regenerate
                </Button>
              </div>
              <p className="mt-1 text-sm text-gray-500">
                Use this API key to authenticate requests from external tools
              </p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}

export default Settings