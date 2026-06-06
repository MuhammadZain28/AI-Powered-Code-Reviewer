import { useState, useCallback } from 'react'
import toast from 'react-hot-toast'

export const useFetch = (apiFunction, options = {}) => {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [data, setData] = useState(null)

  const { showSuccessToast = true, showErrorToast = true } = options

  const execute = useCallback(async (...args) => {
    setLoading(true)
    setError(null)
    
    try {
      const result = await apiFunction(...args)
      setData(result)
      if (showSuccessToast) {
        toast.success('Operation completed successfully')
      }
      return result
    } catch (err) {
      setError(err)
      if (showErrorToast) {
        toast.error(err.message || 'Operation failed')
      }
      throw err
    } finally {
      setLoading(false)
    }
  }, [apiFunction, showSuccessToast, showErrorToast])

  return {
    execute,
    loading,
    error,
    data
  }
}