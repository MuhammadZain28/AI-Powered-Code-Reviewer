import React, { useState } from 'react'
import Modal from '../ui/Modal'
import Input from '../ui/Input'
import Button from '../ui/Button'
import { PlusIcon } from '@heroicons/react/outline'

const CreateProjectModal = ({ isOpen, onClose, onCreate }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    repo_url: ''
  })
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!formData.name.trim()) {
      return
    }
    setLoading(true)
    try {
      await onCreate(formData)
      setFormData({ name: '', description: '', repo_url: '' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Create New Project" size="md">
      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label className="input-label">
            Project Name <span className="text-red-500">*</span>
          </label>
          <Input
            placeholder="e.g., My Awesome Project"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
            autoFocus
          />
        </div>
        
        <div>
          <label className="input-label">Description</label>
          <textarea
            className="input min-h-[100px] resize-y"
            placeholder="What is this project about?"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          />
        </div>
        
        <div>
          <label className="input-label">Repository URL (Optional)</label>
          <Input
            placeholder="https://github.com/username/repo"
            value={formData.repo_url}
            onChange={(e) => setFormData({ ...formData, repo_url: e.target.value })}
          />
          <p className="text-xs text-dark-textSecondary mt-1">
            Provide a GitHub repository URL to automatically import code
          </p>
        </div>
        
        <div className="flex justify-end space-x-3 pt-4">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={loading}>
            <PlusIcon className="w-4 h-4 mr-2" />
            Create Project
          </Button>
        </div>
      </form>
    </Modal>
  )
}

export default CreateProjectModal