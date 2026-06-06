export const API_BASE_URL = '/api/v1'

export const PROJECT_STATUS = {
  ACTIVE: 'active',
  ARCHIVED: 'archived',
  PROCESSING: 'processing'
}

export const REVIEW_SEVERITY = {
  CRITICAL: 'critical',
  HIGH: 'high',
  MEDIUM: 'medium',
  LOW: 'low'
}

export const REVIEW_TYPES = {
  BUG: 'bug',
  SECURITY: 'security',
  PERFORMANCE: 'performance',
  MAINTAINABILITY: 'maintainability',
  ARCHITECTURE: 'architecture'
}

export const LANGUAGE_EXTENSIONS = {
  python: ['.py'],
  javascript: ['.js', '.jsx'],
  typescript: ['.ts', '.tsx'],
  java: ['.java'],
  go: ['.go'],
  rust: ['.rs']
}