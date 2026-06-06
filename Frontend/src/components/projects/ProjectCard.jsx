import React from 'react'
import { Link } from 'react-router-dom'
import Card from '../ui/Card'
import Badge from '../ui/Badge'
import { getProjectStatusColor } from '../../utils/statusColors'
import { formatDate } from '../../utils/helpers'

// Heroicons v1 imports
import { FolderIcon, CodeIcon, ChatAltIcon, DotsVerticalIcon } from '@heroicons/react/outline'

const ProjectCard = ({ project, onDelete }) => {
  const [showMenu, setShowMenu] = React.useState(false)

  return (
    <Card className="hover:border-dark-border transition-all duration-200 group">
      <div className="relative">
        <div className="flex justify-between items-start">
          <Link to={`/projects/${project.id}`} className="flex-1">
            <div className="flex items-center space-x-3 mb-3">
              <div className="p-2 bg-primary-600/10 rounded-lg">
                <FolderIcon className="w-6 h-6 text-primary-500" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-dark-text group-hover:text-primary-500 transition-colors">
                  {project.name}
                </h3>
                <p className="text-sm text-dark-textSecondary mt-0.5">
                  Updated {formatDate(project.updated_at || project.created_at)}
                </p>
              </div>
            </div>
            {project.description && (
              <p className="text-dark-textSecondary text-sm line-clamp-2 mb-3">
                {project.description}
              </p>
            )}
            <div className="flex items-center space-x-4 text-sm text-dark-textSecondary">
              <div className="flex items-center space-x-1">
                <CodeIcon className="w-4 h-4" />
                <span>{project.file_count || 0} files</span>
              </div>
              <div className="flex items-center space-x-1">
                <ChatAltIcon className="w-4 h-4" />
                <span>{project.review_count || 0} reviews</span>
              </div>
            </div>
          </Link>
          
          <div className="flex items-center space-x-2">
            <Badge variant={getProjectStatusColor(project.status || 'active')}>
              {project.status || 'active'}
            </Badge>
            <div className="relative">
              <button
                onClick={() => setShowMenu(!showMenu)}
                className="p-1 rounded-lg hover:bg-dark-hover transition-colors"
              >
                <DotsVerticalIcon className="w-5 h-5 text-dark-textSecondary" />
              </button>
              {showMenu && (
                <>
                  <div className="fixed inset-0" onClick={() => setShowMenu(false)} />
                  <div className="absolute right-0 mt-2 w-48 bg-dark-card border border-dark-border rounded-lg shadow-lg z-10">
                    <Link
                      to={`/projects/${project.id}`}
                      className="block px-4 py-2 text-sm text-dark-text hover:bg-dark-hover transition-colors"
                      onClick={() => setShowMenu(false)}
                    >
                      View Details
                    </Link>
                    <Link
                      to={`/projects/${project.id}/parse`}
                      className="block px-4 py-2 text-sm text-dark-text hover:bg-dark-hover transition-colors"
                      onClick={() => setShowMenu(false)}
                    >
                      Parse Repository
                    </Link>
                    <button
                      onClick={() => {
                        setShowMenu(false)
                        onDelete?.(project.id)
                      }}
                      className="block w-full text-left px-4 py-2 text-sm text-red-500 hover:bg-dark-hover transition-colors"
                    >
                      Delete Project
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </Card>
  )
}

export default ProjectCard