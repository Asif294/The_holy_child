import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'

import { LoadingState } from '@/components/ui/Spinner'
import AuthLayout from '@/layouts/AuthLayout'
import DashboardLayout from '@/layouts/DashboardLayout'
import { P } from '@/utils/permissions'
import PermissionRoute from './PermissionRoute'
import ProtectedRoute from './ProtectedRoute'
import PublicOnlyRoute from './PublicOnlyRoute'

// Route-level code splitting: the landing page and the dashboard shell have
// almost nothing in common, so there is no reason to ship both to every visitor.
const Landing = lazy(() => import('@/pages/Landing'))
const Login = lazy(() => import('@/pages/auth/Login'))
const Dashboard = lazy(() => import('@/pages/dashboard/Dashboard'))
const Students = lazy(() => import('@/pages/academics/Students'))
const Teachers = lazy(() => import('@/pages/academics/Teachers'))
const Classes = lazy(() => import('@/pages/academics/Classes'))
const Subjects = lazy(() => import('@/pages/academics/Subjects'))
const Attendance = lazy(() => import('@/pages/academics/Attendance'))
const Exams = lazy(() => import('@/pages/academics/Exams'))
const Results = lazy(() => import('@/pages/academics/Results'))
const PrincipalOffice = lazy(() => import('@/pages/principal/PrincipalOffice'))
const Notices = lazy(() => import('@/pages/principal/Notices'))
const Approvals = lazy(() => import('@/pages/principal/Approvals'))
const Fees = lazy(() => import('@/pages/finance/Fees'))
const Invoices = lazy(() => import('@/pages/finance/Invoices'))
const Payments = lazy(() => import('@/pages/finance/Payments'))
const Reports = lazy(() => import('@/pages/Reports'))
const Users = lazy(() => import('@/pages/system/Users'))
const Roles = lazy(() => import('@/pages/system/Roles'))
const Permissions = lazy(() => import('@/pages/system/Permissions'))
const Settings = lazy(() => import('@/pages/system/Settings'))
const HeroSlides = lazy(() => import('@/pages/website/HeroSlides'))
const AboutPage = lazy(() => import('@/pages/website/AboutPage'))
const Achievements = lazy(() => import('@/pages/website/Achievements'))
const SuccessfulStudentsAdmin = lazy(() => import('@/pages/website/SuccessfulStudentsAdmin'))
const Profile = lazy(() => import('@/pages/Profile'))
const Forbidden = lazy(() => import('@/pages/Forbidden'))
const NotFound = lazy(() => import('@/pages/NotFound'))

function Fallback() {
  return (
    <div className="grid min-h-[60vh] place-items-center">
      <LoadingState />
    </div>
  )
}

/**
 * Every protected screen is wrapped twice: `ProtectedRoute` for authentication
 * and `PermissionRoute` for the specific code the screen needs. Neither is a
 * security boundary — Django re-checks the same code on every request — but
 * together they keep users off screens that would only show them a 403.
 *
 * `/` is deliberately outside both. The school's website — hero, about,
 * teachers, administration and results — is public, and signing in adds the
 * management surface rather than unlocking the site.
 */
export function AppRoutes() {
  return (
    <Suspense fallback={<Fallback />}>
      <Routes>
        {/* Public */}
        <Route path="/" element={<Landing />} />

        {/* Auth — sign-in only; accounts are issued by an administrator. */}
        <Route element={<PublicOnlyRoute />}>
          <Route element={<AuthLayout />}>
            <Route path="/login" element={<Login />} />
          </Route>
        </Route>
        <Route path="/register" element={<Navigate to="/login" replace />} />

        {/* Application shell */}
        <Route element={<ProtectedRoute />}>
          <Route path="/app" element={<DashboardLayout />}>
            <Route index element={<PermissionRoute permission={P.dashboard.view}><Dashboard /></PermissionRoute>} />

            {/* Academics */}
            <Route path="students" element={<PermissionRoute permission={P.student.view}><Students /></PermissionRoute>} />
            <Route path="teachers" element={<PermissionRoute permission={P.teacher.view}><Teachers /></PermissionRoute>} />
            <Route path="classes" element={<PermissionRoute permission={P.class.view}><Classes /></PermissionRoute>} />
            <Route path="subjects" element={<PermissionRoute permission={P.subject.view}><Subjects /></PermissionRoute>} />
            <Route path="attendance" element={<PermissionRoute permission={P.attendance.view}><Attendance /></PermissionRoute>} />
            <Route path="exams" element={<PermissionRoute permission={P.exam.view}><Exams /></PermissionRoute>} />
            <Route path="results" element={<PermissionRoute permission={P.result.view}><Results /></PermissionRoute>} />

            {/* Public website */}
            <Route path="hero-slides" element={<PermissionRoute permission={P.content.view}><HeroSlides /></PermissionRoute>} />
            <Route path="about" element={<PermissionRoute permission={P.content.view}><AboutPage /></PermissionRoute>} />
            <Route path="achievements" element={<PermissionRoute permission={P.content.view}><Achievements /></PermissionRoute>} />
            <Route
              path="successful-students"
              element={<PermissionRoute permission={P.achiever.view}><SuccessfulStudentsAdmin /></PermissionRoute>}
            />

            {/* Principal's office */}
            <Route path="principal" element={<PermissionRoute permission={P.principal.view}><PrincipalOffice /></PermissionRoute>} />
            <Route path="notices" element={<PermissionRoute permission={P.notice.view}><Notices /></PermissionRoute>} />
            <Route
              path="approvals"
              element={
                <PermissionRoute anyOf={[P.principal.view, P.principal.approve]}>
                  <Approvals />
                </PermissionRoute>
              }
            />

            {/* Finance */}
            <Route path="fees" element={<PermissionRoute permission={P.fee.view}><Fees /></PermissionRoute>} />
            <Route path="invoices" element={<PermissionRoute permission={P.fee.view}><Invoices /></PermissionRoute>} />
            <Route path="payments" element={<PermissionRoute permission={P.payment.view}><Payments /></PermissionRoute>} />

            {/* Reports */}
            <Route path="reports" element={<PermissionRoute permission={P.report.view}><Reports /></PermissionRoute>} />

            {/* System */}
            <Route path="users" element={<PermissionRoute permission={P.user.view}><Users /></PermissionRoute>} />
            <Route path="roles" element={<PermissionRoute permission={P.role.view}><Roles /></PermissionRoute>} />
            <Route path="permissions" element={<PermissionRoute permission={P.permission.view}><Permissions /></PermissionRoute>} />
            <Route path="settings" element={<PermissionRoute permission={P.setting.view}><Settings /></PermissionRoute>} />

            {/* Always available to a signed-in user */}
            <Route path="profile" element={<Profile />} />
            <Route path="403" element={<Forbidden />} />
          </Route>
        </Route>

        {/* Standalone 403 for guards that fire outside the shell */}
        <Route path="/403" element={<ProtectedRoute><Forbidden /></ProtectedRoute>} />

        <Route path="/dashboard" element={<Navigate to="/app" replace />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  )
}

export default AppRoutes
