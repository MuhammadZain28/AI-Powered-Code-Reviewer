import React from 'react'
import { Link } from 'react-router-dom'
import Card from '../ui/Card'
import Badge from '../ui/Badge'
import { formatDate } from '../../utils/helpers'
import { getProjectStatusColor } from '../../utils/statusColors'

const RecentProjects = ({ projects }) => {
  // Ensure projects is an array
  const projectsArray = Array.isArray(projects) ? projects : []
  
  if (projectsArray.length === 0) {
    return (
      <Card 
        title="Recent Projects"
        actions={
          <Link to="/projects" className="text-primary-600 hover:text-primary-700 text-sm">
            View all →
          </Link>
        }
      >
        <div className="text-center py-8">
          <p className="text-gray-500">No projects yet. Create your first project!</p>
        </div>
      </Card>
    )
  }

  return (
    <Card 
      title="Recent Projects"
      actions={
        <Link to="/projects" className="text-primary-600 hover:text-primary-700 text-sm">
          View all →
        </Link>
      }
    >
      <div className="space-y-4">
        {projectsArray.slice(0, 5).map((project) => (
          <Link 
            key={project.id} 
            to={`/projects/${project.id}`}
            className="block hover:bg-gray-50 -mx-2 px-2 py-3 rounded-lg transition-colors"
          >
            <div className="flex justify-between items-center">
              <div>
                <h4 className="font-medium">{project.name}</h4>
                <p className="text-sm text-gray-500 mt-1">
                  Updated {formatDate(project.updated_at || project.created_at)}
                </p>
              </div>
              <Badge variant={getProjectStatusColor(project.status || 'active')}>
                {project.status || 'active'}
              </Badge>
            </div>
          </Link>
        ))}
      </div>
    </Card>
  )
}

export default RecentProjects