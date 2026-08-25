import { useEffect } from 'react'

import { SCHOOL } from '@/utils/constants'
import useSchool from '@/hooks/useSchool'

/**
 * Sets the browser tab title.
 *
 * Pass a title for a dashboard screen and it is suffixed with the product
 * wordmark. Pass nothing — which only the public landing page does — and the
 * tab carries the school's own name, because that is the page a visitor
 * bookmarked.
 */
export function useDocumentTitle(title) {
  const { school } = useSchool()
  const brand = school.brand_name || SCHOOL.brand
  const name = school.name_en || SCHOOL.nameEn

  useEffect(() => {
    document.title = title ? `${title} · ${brand}` : name
  }, [title, brand, name])
}

export default useDocumentTitle
