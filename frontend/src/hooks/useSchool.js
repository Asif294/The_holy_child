import { useContext } from 'react'

import { SchoolContext } from '@/context/SchoolContext'

export function useSchool() {
  const context = useContext(SchoolContext)
  if (!context) {
    throw new Error('useSchool must be used inside a <SchoolProvider>.')
  }
  return context
}

export default useSchool
