import {
  Award,
  BadgeCheck,
  BookOpen,
  CalendarCheck,
  ClipboardList,
  CreditCard,
  FileBarChart,
  GraduationCap,
  KeyRound,
  LayoutDashboard,
  Layers,
  Megaphone,
  Receipt,
  Settings,
  ShieldCheck,
  Stamp,
  UserCog,
  Users,
  Wallet,
} from 'lucide-react'

import { P } from './permissions'

/**
 * The sidebar, described as data.
 *
 * Every entry is keyed to a permission code — never to a role name. A new role
 * with `fee.view` gets the Fees menu automatically, without anyone editing
 * this file.
 */
export const NAVIGATION = [
  {
    id: 'overview',
    items: [{ label: 'Dashboard', to: '/app', icon: LayoutDashboard, permission: P.dashboard.view, end: true }],
  },
  {
    id: 'academics',
    title: 'Academics',
    items: [
      { label: 'Students', to: '/app/students', icon: GraduationCap, permission: P.student.view },
      { label: 'Teachers', to: '/app/teachers', icon: Users, permission: P.teacher.view },
      { label: 'Classes', to: '/app/classes', icon: Layers, permission: P.class.view },
      { label: 'Subjects', to: '/app/subjects', icon: BookOpen, permission: P.subject.view },
      { label: 'Attendance', to: '/app/attendance', icon: CalendarCheck, permission: P.attendance.view },
      { label: 'Exams', to: '/app/exams', icon: ClipboardList, permission: P.exam.view },
      { label: 'Results', to: '/app/results', icon: Award, permission: P.result.view },
    ],
  },
  {
    id: 'principal',
    title: "Principal's Office",
    items: [
      { label: 'Principal', to: '/app/principal', icon: BadgeCheck, permission: P.principal.view },
      { label: 'Notices', to: '/app/notices', icon: Megaphone, permission: P.notice.view },
      { label: 'Approvals', to: '/app/approvals', icon: Stamp, anyOf: [P.principal.view, P.principal.approve] },
    ],
  },
  {
    id: 'finance',
    title: 'Finance',
    items: [
      { label: 'Fees', to: '/app/fees', icon: Wallet, permission: P.fee.view },
      { label: 'Invoices', to: '/app/invoices', icon: Receipt, permission: P.fee.view },
      { label: 'Payments', to: '/app/payments', icon: CreditCard, permission: P.payment.view },
    ],
  },
  {
    id: 'reports',
    title: 'Reports',
    items: [{ label: 'Reports', to: '/app/reports', icon: FileBarChart, permission: P.report.view }],
  },
  {
    id: 'system',
    title: 'System',
    items: [
      { label: 'Users', to: '/app/users', icon: UserCog, permission: P.user.view },
      { label: 'Roles', to: '/app/roles', icon: ShieldCheck, permission: P.role.view },
      { label: 'Permissions', to: '/app/permissions', icon: KeyRound, permission: P.permission.view },
      { label: 'Settings', to: '/app/settings', icon: Settings, permission: P.setting.view },
    ],
  },
]

/** Drops entries the user cannot reach, then drops sections left empty. */
export function visibleNavigation({ hasPermission, hasAnyPermission }) {
  return NAVIGATION.map((section) => ({
    ...section,
    items: section.items.filter((item) =>
      item.anyOf ? hasAnyPermission(item.anyOf) : hasPermission(item.permission),
    ),
  })).filter((section) => section.items.length > 0)
}
