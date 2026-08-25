import { BrowserRouter } from 'react-router-dom'

import { AuthProvider } from '@/context/AuthContext'
import { SchoolProvider } from '@/context/SchoolContext'
import { ToastProvider } from '@/context/ToastContext'
import ErrorBoundary from '@/components/common/ErrorBoundary'
import AppRoutes from '@/routes/AppRoutes'

export function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <ToastProvider>
          <AuthProvider>
            <SchoolProvider>
              <AppRoutes />
            </SchoolProvider>
          </AuthProvider>
        </ToastProvider>
      </BrowserRouter>
    </ErrorBoundary>
  )
}

export default App
