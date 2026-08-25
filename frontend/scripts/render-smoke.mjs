/**
 * Renders every top-level screen through Vite's SSR pipeline to catch runtime
 * render errors that a type-free build cannot.
 * Run with `npm run smoke`. Zero extra dependencies — it reuses the Vite
 * server and react-dom that the app already ships with.
 */
import { createServer } from 'vite'
import React from 'react'
import { renderToString } from 'react-dom/server'

// Minimal browser globals the app touches during a first render.
const store = new Map()
globalThis.localStorage = {
  getItem: (k) => (store.has(k) ? store.get(k) : null),
  setItem: (k, v) => store.set(k, String(v)),
  removeItem: (k) => store.delete(k),
  clear: () => store.clear(),
}
globalThis.matchMedia = () => ({ matches: false, addEventListener() {}, removeEventListener() {} })

const vite = await createServer({ server: { middlewareMode: true }, appType: 'custom', logLevel: 'error' })

// Node resolves react-router-dom natively; Vite externalises it for SSR too,
// so the app modules below share this exact instance and context flows normally.
const { MemoryRouter } = await import('react-router-dom')
const { AuthProvider } = await vite.ssrLoadModule('/src/context/AuthContext.jsx')
const { ToastProvider } = await vite.ssrLoadModule('/src/context/ToastContext.jsx')

const SCREENS = [
  ['Landing', '/src/pages/Landing.jsx'],
  ['Login', '/src/pages/auth/Login.jsx'],
  ['Register', '/src/pages/auth/Register.jsx'],
  ['Dashboard', '/src/pages/dashboard/Dashboard.jsx'],
  ['Students', '/src/pages/academics/Students.jsx'],
  ['Teachers', '/src/pages/academics/Teachers.jsx'],
  ['Classes', '/src/pages/academics/Classes.jsx'],
  ['Subjects', '/src/pages/academics/Subjects.jsx'],
  ['Attendance', '/src/pages/academics/Attendance.jsx'],
  ['Exams', '/src/pages/academics/Exams.jsx'],
  ['Results', '/src/pages/academics/Results.jsx'],
  ['PrincipalOffice', '/src/pages/principal/PrincipalOffice.jsx'],
  ['Notices', '/src/pages/principal/Notices.jsx'],
  ['Approvals', '/src/pages/principal/Approvals.jsx'],
  ['Fees', '/src/pages/finance/Fees.jsx'],
  ['Invoices', '/src/pages/finance/Invoices.jsx'],
  ['Payments', '/src/pages/finance/Payments.jsx'],
  ['Reports', '/src/pages/Reports.jsx'],
  ['Users', '/src/pages/system/Users.jsx'],
  ['Roles', '/src/pages/system/Roles.jsx'],
  ['Permissions', '/src/pages/system/Permissions.jsx'],
  ['Settings', '/src/pages/system/Settings.jsx'],
  ['Profile', '/src/pages/Profile.jsx'],
  ['Forbidden', '/src/pages/Forbidden.jsx'],
  ['NotFound', '/src/pages/NotFound.jsx'],
  ['Sidebar', '/src/layouts/Sidebar.jsx'],
  ['Topbar', '/src/layouts/Topbar.jsx'],
]

let failures = 0
for (const [name, path] of SCREENS) {
  try {
    const mod = await vite.ssrLoadModule(path)
    const Component = mod.default ?? Object.values(mod).find((v) => typeof v === 'function')
    const html = renderToString(
      React.createElement(
        MemoryRouter,
        null,
        React.createElement(
          ToastProvider,
          null,
          React.createElement(AuthProvider, null, React.createElement(Component)),
        ),
      ),
    )
    if (!html || html.length < 20) throw new Error(`rendered only ${html.length} chars`)
    console.log(`  ok   ${name.padEnd(18)} ${String(html.length).padStart(7)} chars`)
  } catch (error) {
    failures += 1
    console.log(`  FAIL ${name.padEnd(18)} ${error.message.split('\n')[0]}`)
  }
}

await vite.close()
console.log(failures ? `\n${failures} screen(s) failed to render.` : `\nAll ${SCREENS.length} screens rendered.`)
process.exit(failures ? 1 : 0)
