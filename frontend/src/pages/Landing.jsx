import { useEffect, useState } from 'react'

import CTA from '@/components/landing/CTA'
import DashboardPreview from '@/components/landing/DashboardPreview'
import Features from '@/components/landing/Features'
import Footer from '@/components/landing/Footer'
import Hero from '@/components/landing/Hero'
import Navbar from '@/components/landing/Navbar'
import PrincipalMessage from '@/components/landing/PrincipalMessage'
import WhyChooseUs from '@/components/landing/WhyChooseUs'
import useDocumentTitle from '@/hooks/useDocumentTitle'
import { principalService, schoolService } from '@/services'

export function Landing() {
  useDocumentTitle(null)

  const [school, setSchool] = useState(null)
  const [principal, setPrincipal] = useState(null)

  // Both endpoints are public; a failure just means the page falls back to its
  // built-in copy rather than showing an error to a visitor.
  useEffect(() => {
    schoolService.info().then(setSchool).catch(() => {})
    principalService.publicProfile().then(setPrincipal).catch(() => {})
  }, [])

  return (
    <div className="min-h-screen bg-white">
      <Navbar />
      <main>
        <Hero stats={school?.stats} />
        <Features />
        <DashboardPreview stats={school?.stats} />
        <PrincipalMessage principal={principal} />
        <WhyChooseUs />
        <CTA />
      </main>
      <Footer />
    </div>
  )
}

export default Landing
