import { useEffect, useState } from 'react'

import AboutSchool from '@/components/landing/AboutSchool'
import Administration from '@/components/landing/Administration'
import Footer from '@/components/landing/Footer'
import HeroSlider from '@/components/landing/HeroSlider'
import Navbar from '@/components/landing/Navbar'
import SuccessfulStudents from '@/components/landing/SuccessfulStudents'
import TeachersSection from '@/components/landing/TeachersSection'
import useDocumentTitle from '@/hooks/useDocumentTitle'
import { publicSiteService, schoolService } from '@/services'

const EMPTY = {
  school: null,
  slides: [],
  about: null,
  teachers: [],
  administration: { principal: null, vice_principal: null },
  students: [],
  years: [],
}

/**
 * The school's public home page.
 *
 * Everything here is anonymous — no token is sent, and no section requires a
 * session. Signing in changes exactly one thing on this page: the header's
 * *Admin* button becomes *Dashboard*. Creating, editing and deleting any of
 * this content lives behind the permission-gated screens in `/app`.
 *
 * Each section loads independently and fails quietly. A visitor should never
 * see an error page because one endpoint was slow — they should see the rest
 * of the school's website.
 */
export function Landing() {
  useDocumentTitle(null)

  const [data, setData] = useState(EMPTY)

  useEffect(() => {
    let cancelled = false
    const set = (key) => (value) => {
      if (!cancelled) setData((current) => ({ ...current, [key]: value }))
    }
    const ignore = () => {}

    schoolService.info().then(set('school')).catch(ignore)
    publicSiteService.heroSlides().then(set('slides')).catch(ignore)
    publicSiteService.about().then(set('about')).catch(ignore)
    publicSiteService.teachers().then(set('teachers')).catch(ignore)
    publicSiteService.administration().then(set('administration')).catch(ignore)
    publicSiteService.successfulStudents().then(set('students')).catch(ignore)
    publicSiteService.achievementYears().then(set('years')).catch(ignore)

    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="min-h-screen bg-white">
      <Navbar />
      <main>
        <HeroSlider slides={data.slides} stats={data.school?.stats} />
        <AboutSchool about={data.about} />
        <Administration administration={data.administration} />
        <TeachersSection teachers={data.teachers} />
        <SuccessfulStudents years={data.years} initialStudents={data.students} />
      </main>
      <Footer />
    </div>
  )
}

export default Landing
