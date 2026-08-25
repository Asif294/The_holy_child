import { useEffect } from 'react'

import { SCHOOL } from '@/utils/constants'
import useSchool from '@/hooks/useSchool'

export function useDocumentTitle(title) {
  const { school } = useSchool()
  const brand = school.brand_name || SCHOOL.brand
  const name = school.name_en || SCHOOL.nameEn

  useEffect(() => {
    document.title = title ? `${title} · ${brand}` : `${brand} — ${name}`
  }, [title, brand, name])
}

export default useDocumentTitle
