import React, { useState } from 'react'
import { useProjects } from '../hooks/useProjects'
import { searchService } from '../services/searchService'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'
import Loader from '../components/ui/Loader'
import SearchResultCard from '../components/search/SearchResultCard'
import SimilarityBadge from '../components/search/SimilarityBadge'
import toast from 'react-hot-toast'

const SearchContext = () => {
  const { projects, currentProject, setCurrentProject } = useProjects()
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [searchType, setSearchType] = useState('semantic')

  const handleSearch = async () => {
    if (!currentProject) {
      toast.error('Please select a project first')
      return
    }

    if (!query.trim()) {
      toast.error('Please enter a search query')
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
      if (data.length === 0) {
        toast.info('No results found')
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
          <h1 className="text-2xl font-bold text-gray-900">Context Search</h1>
          <p className="text-gray-600 mt-1">
            Search across your codebase using semantic or code-based queries
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

      <Card>
        <div className="space-y-4">
          <div className="flex space-x-4">
            <label className="inline-flex items-center">
              <input
                type="radio"
                value="semantic"
                checked={searchType === 'semantic'}
                onChange={(e) => setSearchType(e.target.value)}
                className="mr-2"
              />
              Semantic Search
            </label>
            <label className="inline-flex items-center">
              <input
                type="radio"
                value="code"
                checked={searchType === 'code'}
                onChange={(e) => setSearchType(e.target.value)}
                className="mr-2"
              />
              Code Search
            </label>
          </div>

          <div className="flex space-x-3">
            <Input
              placeholder={searchType === 'semantic' 
                ? "Describe what you're looking for (e.g., 'authentication logic')..." 
                : "Paste code snippet to find similar patterns..."}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              className="flex-1"
            />
            <Button onClick={handleSearch} loading={loading}>
              Search
            </Button>
          </div>
        </div>
      </Card>

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
              {result.similarity_score && (
                <SimilarityBadge score={result.similarity_score} />
              )}
            </SearchResultCard>
          ))}
        </div>
      )}

      {results.length === 0 && query && !loading && (
        <Card>
          <div className="text-center py-8">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No results found</h3>
            <p className="mt-1 text-sm text-gray-500">
              Try a different search query or check if the project has been parsed.
            </p>
          </div>
        </Card>
      )}
    </div>
  )
}

export default SearchContext