import { createContext, useCallback, useEffect, useMemo, useState } from 'react'

import { SCHOOL as SCHOOL_FALLBACK } from '@/utils/constants'
import { schoolService } from '@/services'

export const SchoolContext = createContext(null)

/**
 * The school's identity, loaded once from `GET /school/info/`.
 *
 * Everything that renders the school's name, contact details or crest reads it
 * from here, so an edit on the Settings screen reaches the sidebar, the login
 * page and the public site without a reload. The constants in `utils/constants`
 * remain as the first-paint fallback, used until the request lands and whenever
 * the API is unreachable.
 */
const FALLBACK = {
  name_en: SCHOOL_FALLBACK.nameEn,
  name_bn: SCHOOL_FALLBACK.nameBn,
  short_name: SCHOOL_FALLBACK.shortName,
  brand_name: SCHOOL_FALLBACK.brand,
  address: SCHOOL_FALLBACK.address,
  established: SCHOOL_FALLBACK.established,
  grade_range: SCHOOL_FALLBACK.gradeRange,
  grade_range_bn: SCHOOL_FALLBACK.gradeRangeBn,
  email: SCHOOL_FALLBACK.email,
  phone: SCHOOL_FALLBACK.phone,
  website: '',
  logo_url: null,
}

export function SchoolProvider({ children }) {
  const [school, setSchool] = useState(FALLBACK)
  const [isLoading, setIsLoading] = useState(true)

  const refresh = useCallback(async () => {
    try {
      const data = await schoolService.info()
      // Merge so a field the API omits keeps its fallback rather than blanking.
      setSchool((current) => ({ ...current, ...data }))
      return data
    } catch {
      // A branding fetch is not worth blocking the app for; keep the fallback.
      return null
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  const value = useMemo(
    () => ({ school, isLoading, refresh, setSchool }),
    [school, isLoading, refresh],
  )

  return <SchoolContext.Provider value={value}>{children}</SchoolContext.Provider>
}

export default SchoolProvider
