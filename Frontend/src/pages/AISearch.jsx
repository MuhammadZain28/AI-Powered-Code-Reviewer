import React, { useState } from 'react'
import { useProjects } from '../hooks/useProjects'
import SearchBox from '../components/search/SearchBox'
import SearchResultCard from '../components/search/SearchResultCard'
import SimilarityBadge from '../components/search/SimilarityBadge'
import Card from '../components/ui/Card'
import Loader from '../components/ui/Loader'
import { searchService } from '../services/searchService'
import toast from 'react-hot-toast'

const AISearch = () => {
  const { projects, currentProject, setCurrentProject } = useProjects()
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [searchType, setSearchType] = useState('semantic')
  const [searchHistory, setSearchHistory] = useState([])

  const handleSearch = async (query) => {
    if (!currentProject) {
      toast.error('Please select a project first')
      return
    }

    setLoading(true)
    try {
      let data
      if (searchType === 'semantic') {
        data = await searchService.semanticSearch(currentProject.id, query)
      } else {
        data = await searchService.codeSearch(currentProject.id, query)
      }
      setResults(data)
      
      // Add to search history
      setSearchHistory(prev => [{
        id: Date.now(),
        query,
        type: searchType,
        timestamp: new Date(),
        resultCount: data.length
      }, ...prev].slice(0, 10))
      
      if (data.length === 0) {
        toast.info('No results found')
      } else {
        toast.success(`Found ${data.length} results`)
      }
    } catch (error) {
      toast.error(error.message || 'Search failed')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AI-Powered Search</h1>
          <p className="text-gray-600 mt-1">
            Use semantic search to find relevant code across your projects
          </p>
        </div>
        <select
          className="input w-64"
          value={currentProject?.id || ''}
          onChange={(e) => {
            const project = projects.find(p => p.id === parseInt(e.target.value))
            setCurrentProject(project)
            setResults([])
          }}
        >
          <option value="">Select a project</option>
          {projects.map(project => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>
      </div>

      <SearchBox
        onSearch={handleSearch}
        loading={loading}
        searchType={searchType}
        onSearchTypeChange={setSearchType}
      />

      {loading && <Loader />}

      {results.length > 0 && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold text-gray-900">
              Found {results.length} result{results.length !== 1 ? 's' : ''}
            </h2>
          </div>
          {results.map((result, index) => (
            <SearchResultCard key={result.id || index} result={result}>
              {result.score && (
                <SimilarityBadge score={result.score} />
              )}
            </SearchResultCard>
          ))}
        </div>
      )}

      {searchHistory.length > 0 && results.length === 0 && !loading && (
        <Card title="Recent Searches">
          <div className="space-y-2">
            {searchHistory.map(item => (
              <div key={item.id} className="flex justify-between items-center p-2 hover:bg-gray-50 rounded">
                <div>
                  <p className="font-medium text-gray-900">{item.query}</p>
                  <p className="text-sm text-gray-500">
                    {item.type} search • {item.resultCount} results
                  </p>
                </div>
                <span className="text-xs text-gray-400">
                  {new Date(item.timestamp).toLocaleTimeString()}
                </span>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}

export default AISearch