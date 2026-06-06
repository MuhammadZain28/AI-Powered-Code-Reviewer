import React, { useState } from 'react'
import ProjectCard from './ProjectCard'
import Input from '../ui/Input'
import Button from '../ui/Button'

const ProjectList = ({ projects, onDeleteProject, onSelectProject }) => {
  const [searchTerm, setSearchTerm] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')

  const filteredProjects = projects.filter(project => {
    const matchesSearch = project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          (project.description && project.description.toLowerCase().includes(searchTerm.toLowerCase()))
    const matchesStatus = filterStatus === 'all' || project.status === filterStatus
    return matchesSearch && matchesStatus
  })

  return (
    <div className="space-y-4">
      <div className="flex space-x-4">
        <Input
          placeholder="Search projects..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="flex-1"
        />
        <select
          className="input w-48"
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
        >
          <option value="all">All Status</option>
          <option value="active">Active</option>
          <option value="processing">Processing</option>
          <option value="archived">Archived</option>
        </select>
      </div>

      {filteredProjects.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="text-gray-500">No projects found</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {filteredProjects.map((project) => (
            <div key={project.id} onClick={() => onSelectProject?.(project)} className="cursor-pointer">
              <ProjectCard
                project={project}
                onDelete={onDeleteProject}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default ProjectList