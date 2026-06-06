import React, { useState } from 'react'
import Card from '../ui/Card'
import Input from '../ui/Input'
import Button from '../ui/Button'

const SearchBox = ({ onSearch, loading, searchType, onSearchTypeChange }) => {
  const [query, setQuery] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (query.trim()) {
      onSearch(query)
    }
  }

  return (
    <Card>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="flex space-x-4">
          <label className="inline-flex items-center">
            <input
              type="radio"
              value="semantic"
              checked={searchType === 'semantic'}
              onChange={(e) => onSearchTypeChange(e.target.value)}
              className="mr-2"
            />
            Semantic Search
          </label>
          <label className="inline-flex items-center">
            <input
              type="radio"
              value="code"
              checked={searchType === 'code'}
              onChange={(e) => onSearchTypeChange(e.target.value)}
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
            className="flex-1"
            disabled={loading}
          />
          <Button type="submit" loading={loading}>
            Search
          </Button>
        </div>
      </form>
    </Card>
  )
}

export default SearchBox