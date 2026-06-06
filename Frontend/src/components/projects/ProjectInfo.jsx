import React, { useState } from 'react'
import Card from '../ui/Card'
import Button from '../ui/Button'
import Input from '../ui/Input'
import Badge from '../ui/Badge'
import { getProjectStatusColor } from '../../utils/statusColors'
import { formatDate } from '../../utils/helpers'
import toast from 'react-hot-toast'

const ProjectInfo = ({ project, onUpdate }) => {
  const [isEditing, setIsEditing] = useState(false)
  const [formData, setFormData] = useState({
    name: project?.name || '',
    description: project?.description || '',
    repo_url: project?.repo_url || ''
  })
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      await onUpdate(project.id, formData)
      setIsEditing(false)
      toast.success('Project updated successfully')
    } catch (error) {
      toast.error(error.message || 'Failed to update project')
    } finally {
      setLoading(false)
    }
  }

  if (!project) {
    return (
      <Card title="Project Information">
        <p className="text-gray-500 text-center py-8">No project selected</p>
      </Card>
    )
  }

  return (
    <Card title="Project Information">
      {isEditing ? (
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Project Name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
          />
          <Input
            label="Description"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          />
          <Input
            label="Repository URL"
            value={formData.repo_url}
            onChange={(e) => setFormData({ ...formData, repo_url: e.target.value })}
          />
          <div className="flex space-x-3">
            <Button type="submit" loading={loading}>Save</Button>
            <Button type="button" variant="secondary" onClick={() => setIsEditing(false)}>
              Cancel
            </Button>
          </div>
        </form>
      ) : (
        <div className="space-y-3">
          <div>
            <label className="text-sm font-medium text-gray-500">Name</label>
            <p className="text-lg font-semibold text-gray-900">{project.name}</p>
          </div>
          {project.description && (
            <div>
              <label className="text-sm font-medium text-gray-500">Description</label>
              <p className="text-gray-700">{project.description}</p>
            </div>
          )}
          {project.repo_url && (
            <div>
              <label className="text-sm font-medium text-gray-500">Repository</label>
              <a href={project.repo_url} target="_blank" rel="noopener noreferrer" 
                 className="text-primary-600 hover:text-primary-700 block">
                {project.repo_url}
              </a>
            </div>
          )}
          <div>
            <label className="text-sm font-medium text-gray-500">Status</label>
            <div className="mt-1">
              <Badge variant={getProjectStatusColor(project.status)}>
                {project.status || 'active'}
              </Badge>
            </div>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-500">Created</label>
            <p className="text-gray-700">{formatDate(project.created_at)}</p>
          </div>
          <Button variant="outline" onClick={() => setIsEditing(true)} className="mt-4">
            Edit Project
          </Button>
        </div>
      )}
    </Card>
  )
}

export default ProjectInfo