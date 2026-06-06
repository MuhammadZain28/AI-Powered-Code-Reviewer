import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import AppLayout from '../components/layout/AppLayout'
import { useAuth } from '../hooks/useAuth'
import Dashboard from '../pages/Dashboard'
import Projects from '../pages/Projects'
import ProjectDetails from '../pages/ProjectDetails'
import ParseProject from '../pages/ParseProject'
import SearchContext from '../pages/SearchContext'
import AISearch from '../pages/AISearch'
import Reviews from '../pages/Reviews'
import Settings from '../pages/Settings'
import Login from '../pages/Login'

const PrivateRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth()
  
  if (loading) return null
  return isAuthenticated ? children : <Navigate to="/login" />
}

export const AppRoutes = () => {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<Navigate to="/dashboard" />} />
      
      <Route element={<AppLayout />}>
        <Route path="/dashboard" element={
          <PrivateRoute><Dashboard /></PrivateRoute>
        } />
        <Route path="/projects" element={
          <PrivateRoute><Projects /></PrivateRoute>
        } />
        <Route path="/projects/:id" element={
          <PrivateRoute><ProjectDetails /></PrivateRoute>
        } />
        <Route path="/projects/:id/parse" element={
          <PrivateRoute><ParseProject /></PrivateRoute>
        } />
        <Route path="/search" element={
          <PrivateRoute><SearchContext /></PrivateRoute>
        } />
        <Route path="/ai-search" element={
          <PrivateRoute><AISearch /></PrivateRoute>
        } />
        <Route path="/reviews" element={
          <PrivateRoute><Reviews /></PrivateRoute>
        } />
        <Route path="/settings" element={
          <PrivateRoute><Settings /></PrivateRoute>
        } />
      </Route>
    </Routes>
  )
}