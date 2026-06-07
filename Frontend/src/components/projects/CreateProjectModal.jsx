import React, { useState } from 'react'
import Modal from '../ui/Modal'
import Input from '../ui/Input'
import Button from '../ui/Button'
import { PlusIcon } from '@heroicons/react/outline'

const CreateProjectModal = ({ isOpen, onClose, onCreate }) => {
  const [formData, setFormData] = useState({
    name: 'Distributed Academic Information System',
    description: 'Distributed Academic Information System (DAIS) is a comprehensive web application designed to manage and streamline academic processes for educational institutions. It provides a centralized platform for students, faculty, and administrators to access and manage academic information efficiently.',
    repo_path: 'D:\\Project\\Centralized-Academic-Management\\backend',
    frontend: 'React.js',
    backend: 'FastAPI',
    technologies: 'PostgreSQL, Distributed Systems',
    features: 'User Authentication, Fee Structure Comparison, Distributed Data Storage',
    modules: 'User Management, Fee Management, Data Analytics'
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
      setFormData({ name: '', description: '', repo_path: '', frontend: '', backend: '', technologies: '', features: '', modules: '' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Create New Project" size="xl">
      <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-4">
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
          <label className="input-label">Project Path</label>
          <Input
            placeholder="e.g., /path/to/project"
            value={formData.repo_path}
            onChange={(e) => setFormData({ ...formData, repo_path: e.target.value })}
          />
        </div>
        <div>
          <label className="input-label">Frontend Technologies</label>
          <Input
            placeholder="e.g., React, Vue.js"
            value={formData.frontend}
            onChange={(e) => setFormData({ ...formData, frontend: e.target.value })}
          />
        </div>
        <div>
          <label className="input-label">Backend Technologies</label>
          <Input
            placeholder="e.g., Node.js, Python"
            value={formData.backend}
            onChange={(e) => setFormData({ ...formData, backend: e.target.value })}
          />
        </div>
        <div className="col-span-2">
          <label className="input-label">Technologies</label>
          <Input
            placeholder="e.g., MongoDB, PostgreSQL"
            value={formData.technologies}
            onChange={(e) => setFormData({ ...formData, technologies: e.target.value })}
          />
        </div>
        <div>
          <label className="input-label">Key Features</label>
          <Input
            placeholder="e.g., Authentication, API Integration"
            value={formData.features}
            onChange={(e) => setFormData({ ...formData, features: e.target.value })}
          />
        </div>
        <div>
          <label className="input-label">Modules</label>
          <Input
            placeholder="e.g., User Management, Payment Processing"
            value={formData.modules}
            onChange={(e) => setFormData({ ...formData, modules: e.target.value })}
          />
        </div>
        <div className="col-span-2">
          <label className="input-label">Description</label>
          <textarea
            className="input min-h-[100px] resize-none"
            placeholder="What is this project about?"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          />
        </div>
          <p className="text-xs text-dark-textSecondary mt-1">
            Provide the local path to your project directory. This is used for file indexing and code analysis. Make sure the path is correct and accessible by the application.
          </p>
        
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