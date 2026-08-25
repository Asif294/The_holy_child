/**
 * The permission codes the UI references.
 *
 * Nothing here grants anything — Django is the only authority. These constants
 * exist so a typo in a navigation entry fails loudly in one place instead of
 * silently hiding a menu item.
 */
export const P = {
  dashboard: { view: 'dashboard.view' },
  student: { view: 'student.view', create: 'student.create', update: 'student.update', delete: 'student.delete' },
  teacher: { view: 'teacher.view', create: 'teacher.create', update: 'teacher.update', delete: 'teacher.delete' },
  class: { view: 'class.view', create: 'class.create', update: 'class.update', delete: 'class.delete' },
  subject: { view: 'subject.view', create: 'subject.create', update: 'subject.update', delete: 'subject.delete' },
  attendance: {
    view: 'attendance.view',
    create: 'attendance.create',
    update: 'attendance.update',
    delete: 'attendance.delete',
  },
  exam: { view: 'exam.view', create: 'exam.create', update: 'exam.update', delete: 'exam.delete' },
  result: { view: 'result.view', create: 'result.create', update: 'result.update', publish: 'result.publish' },
  fee: { view: 'fee.view', create: 'fee.create', update: 'fee.update', delete: 'fee.delete' },
  payment: { view: 'payment.view', create: 'payment.create', update: 'payment.update', delete: 'payment.delete' },
  admission: { view: 'admission.view', create: 'admission.create' },
  notice: { view: 'notice.view', create: 'notice.create', update: 'notice.update', delete: 'notice.delete' },
  principal: { view: 'principal.view', update: 'principal.update', approve: 'principal.approve' },
  content: { view: 'content.view', create: 'content.create', update: 'content.update', delete: 'content.delete' },
  achiever: {
    view: 'achiever.view',
    create: 'achiever.create',
    update: 'achiever.update',
    delete: 'achiever.delete',
  },
  report: { view: 'report.view', export: 'report.export' },
  user: { view: 'user.view', create: 'user.create', update: 'user.update', delete: 'user.delete' },
  role: { view: 'role.view', create: 'role.create', update: 'role.update', delete: 'role.delete' },
  permission: { view: 'permission.view' },
  setting: { view: 'setting.view', update: 'setting.update' },
}

/** Human labels for the permission action verbs, used by the role editor. */
export const ACTION_LABELS = {
  view: 'View',
  create: 'Create',
  update: 'Update',
  delete: 'Delete',
  export: 'Export',
  publish: 'Publish',
  approve: 'Approve',
}
