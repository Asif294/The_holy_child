import api from './api'
import { createCrudService } from './crudService'

/**
 * Builds a multipart body from plain values plus a set of files.
 *
 * DRF reads a file only from `multipart/form-data`, and a `null` file means
 * "leave whatever is already stored alone" — so an unset file is omitted from
 * the body rather than sent as an empty string, which would clear it.
 */
function toFormData(values, files = {}) {
  const form = new FormData()
  Object.entries(values ?? {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null) form.append(key, value)
  })
  Object.entries(files).forEach(([key, file]) => {
    if (file) form.append(key, file)
  })
  return form
}

/* --- Access control ------------------------------------------------------ */
export const userService = {
  ...createCrudService('users'),
  async assignRole(id, roleId) {
    const { data } = await api.post(`/users/${id}/assign-role/`, { role_id: roleId })
    return data
  },
}

export const roleService = {
  ...createCrudService('roles'),
  async setPermissions(id, permissions) {
    const { data } = await api.post(`/roles/${id}/permissions/`, { permissions })
    return data
  },
}

export const permissionService = {
  ...createCrudService('permissions'),
  async grouped() {
    const { data } = await api.get('/permissions/grouped/')
    return data
  },
}

/* --- Academics ----------------------------------------------------------- */
export const studentService = {
  ...createCrudService('students'),
  async statistics(params = {}) {
    const { data } = await api.get('/students/statistics/', { params })
    return data
  },
}

export const guardianService = createCrudService('guardians')

export const teacherService = {
  ...createCrudService('teachers'),
  async statistics() {
    const { data } = await api.get('/teachers/statistics/')
    return data
  },
  async myProfile() {
    const { data } = await api.get('/teachers/me/')
    return data
  },
}

export const designationService = createCrudService('designations')
export const departmentService = createCrudService('departments')

export const classService = createCrudService('classes')
export const sectionService = createCrudService('sections')
export const sessionService = createCrudService('academic-sessions')

export const subjectService = createCrudService('subjects')
export const classSubjectService = createCrudService('class-subjects')

export const attendanceService = {
  ...createCrudService('attendance'),
  async register(sectionId, date) {
    const { data } = await api.get('/attendance/register/', { params: { section: sectionId, date } })
    return data
  },
  async bulk(payload) {
    const { data } = await api.post('/attendance/bulk/', payload)
    return data
  },
  async summary(params = {}) {
    const { data } = await api.get('/attendance/summary/', { params })
    return data
  },
}

export const examService = {
  ...createCrudService('exams'),
  async upcoming(limit = 5) {
    const { data } = await api.get('/exams/upcoming/', { params: { limit } })
    return data
  },
}

export const examTypeService = createCrudService('exam-types')
export const examScheduleService = createCrudService('exam-schedules')

export const resultService = {
  ...createCrudService('results'),
  async publish(examId) {
    const { data } = await api.post('/results/publish/', { exam: examId })
    return data
  },
  async studentSummary(studentId, examId) {
    const { data } = await api.get('/results/student-summary/', { params: { student: studentId, exam: examId } })
    return data
  },
}

/* --- Finance ------------------------------------------------------------- */
export const feeCategoryService = createCrudService('fee-categories')
export const feeStructureService = createCrudService('fee-structures')

export const invoiceService = {
  ...createCrudService('invoices'),
  async statistics(params = {}) {
    const { data } = await api.get('/invoices/statistics/', { params })
    return data
  },
  async outstanding(params = {}) {
    const { data } = await api.get('/invoices/outstanding/', { params })
    return data
  },
}

export const paymentService = {
  ...createCrudService('payments'),
  async recent(limit = 10) {
    const { data } = await api.get('/payments/recent/', { params: { limit } })
    return data
  },
}

/* --- Principal's office --------------------------------------------------- */
export const principalService = {
  ...createCrudService('principals'),
  /** Omit `office` for `{ principal, vice_principal }`; pass one for a single record. */
  async current(office) {
    const { data } = await api.get('/principals/current/', { params: office ? { office } : {} })
    return data
  },
  async dashboard() {
    const { data } = await api.get('/principals/dashboard/')
    return data
  },
  async publicProfile() {
    const { data } = await api.get('/public/principal/', { skipAuth: true })
    return data?.data ?? null
  },
}

export const noticeService = {
  ...createCrudService('notices'),
  async publish(id) {
    const { data } = await api.post(`/notices/${id}/publish/`)
    return data
  },
}

export const approvalService = {
  ...createCrudService('approval-requests'),
  async decide(id, decision, note = '') {
    const { data } = await api.post(`/approval-requests/${id}/decide/`, { decision, note })
    return data
  },
  async mine(params = {}) {
    const { data } = await api.get('/approval-requests/mine/', { params })
    return data
  },
}

/* --- Public website content ------------------------------------------------ */
export const heroSlideService = {
  ...createCrudService('hero-slides'),
  /** Slides carry an image file, so writes go out as multipart. */
  async createWithImage(values, imageFile) {
    const { data } = await api.post('/hero-slides/', toFormData(values, { image: imageFile }))
    return data
  },
  async updateWithImage(id, values, imageFile) {
    const { data } = await api.patch(`/hero-slides/${id}/`, toFormData(values, { image: imageFile }))
    return data
  },
}

export const achievementService = createCrudService('achievements')

export const successfulStudentService = {
  ...createCrudService('successful-students'),
  async createWithPhoto(values, photoFile) {
    const { data } = await api.post('/successful-students/', toFormData(values, { photo: photoFile }))
    return data
  },
  async updateWithPhoto(id, values, photoFile) {
    const { data } = await api.patch(`/successful-students/${id}/`, toFormData(values, { photo: photoFile }))
    return data
  },
}

export const aboutService = {
  async retrieve() {
    const { data } = await api.get('/website/about/')
    return data
  },
  async update(values, imageFile) {
    if (!imageFile) {
      const { data } = await api.patch('/website/about/', values)
      return data
    }
    const { data } = await api.patch('/website/about/', toFormData(values, { image: imageFile }))
    return data
  },
}

/**
 * Everything the landing page reads.
 *
 * These are the only calls in the app that skip the Authorization header: the
 * public site must render identically for a visitor with no session and for a
 * head teacher who is signed in.
 */
export const publicSiteService = {
  async heroSlides() {
    const { data } = await api.get('/public/hero-slides/', { skipAuth: true })
    return Array.isArray(data) ? data : []
  },
  async about() {
    const { data } = await api.get('/public/about/', { skipAuth: true })
    return data
  },
  async teachers(params = {}) {
    const { data } = await api.get('/public/teachers/', { params, skipAuth: true })
    return Array.isArray(data) ? data : []
  },
  async administration() {
    const { data } = await api.get('/public/administration/', { skipAuth: true })
    return data ?? { principal: null, vice_principal: null }
  },
  async successfulStudents(year) {
    const params = year && year !== 'all' ? { year } : {}
    const { data } = await api.get('/public/successful-students/', { params, skipAuth: true })
    return Array.isArray(data) ? data : []
  },
  async achievementYears() {
    const { data } = await api.get('/public/successful-students/years/', { skipAuth: true })
    return Array.isArray(data) ? data : []
  },
}

/* --- Dashboard ------------------------------------------------------------ */
export const dashboardService = {
  async overview() {
    const { data } = await api.get('/dashboard/overview/')
    return data
  },
  async summary() {
    const { data } = await api.get('/dashboard/summary/')
    return data
  },
  async attendanceTrend(days = 7) {
    const { data } = await api.get('/dashboard/attendance-trend/', { params: { days } })
    return data
  },
  async enrollment() {
    const { data } = await api.get('/dashboard/enrollment/')
    return data
  },
  async feeTrend(months = 6) {
    const { data } = await api.get('/dashboard/fee-trend/', { params: { months } })
    return data
  },
  async activities(limit = 10) {
    const { data } = await api.get('/dashboard/activities/', { params: { limit } })
    return data
  },
}

export const eventService = {
  ...createCrudService('events'),
  async upcoming() {
    const { data } = await api.get('/events/upcoming/')
    return data
  },
}

export const schoolService = {
  async info() {
    const { data } = await api.get('/school/info/', { skipAuth: true })
    return data
  },

  /** The editable profile behind Settings. Needs `setting.view`. */
  async profile() {
    const { data } = await api.get('/school/profile/')
    return data
  },

  /**
   * Saves the profile. Switches to multipart only when a new logo file is
   * attached, so ordinary text edits stay plain JSON.
   */
  async updateProfile(values, logoFile) {
    if (!logoFile) {
      const { data } = await api.patch('/school/profile/', values)
      return data
    }

    const form = new FormData()
    Object.entries(values).forEach(([key, value]) => {
      form.append(key, value ?? '')
    })
    form.append('logo', logoFile)
    const { data } = await api.patch('/school/profile/', form)
    return data
  },
}

export { default as authService } from './authService'
export { default as api } from './api'
