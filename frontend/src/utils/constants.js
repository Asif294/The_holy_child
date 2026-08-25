export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export const STORAGE_KEYS = {
  access: 'thc.access',
  refresh: 'thc.refresh',
  user: 'thc.user',
  sidebarCollapsed: 'thc.sidebar',
}

export const SCHOOL = {
  brand: 'SmartSchool',
  nameEn: 'The Holy Child Pre-Cadet & High School',
  nameBn: 'দি হলি চাইল্ড প্রি-ক্যাডেট এন্ড হাই স্কুল',
  shortName: 'Holy Child',
  address: 'Longorpara, Sribordi, Sherpur',
  established: '2006',
  gradeRange: 'Play Group to Class 10',
  gradeRangeBn: 'প্লে-গ্রুপ থেকে ১০ম শ্রেণি পর্যন্ত',
  email: 'info@holychildschool.edu.bd',
  phone: '+880 1700-000000',
}

/** Error codes the API returns in its `code` field. */
export const ERROR_CODES = {
  BAD_REQUEST: 'BAD_REQUEST',
  AUTHENTICATION_FAILED: 'AUTHENTICATION_FAILED',
  PERMISSION_DENIED: 'PERMISSION_DENIED',
  NOT_FOUND: 'NOT_FOUND',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  INTERNAL_SERVER_ERROR: 'INTERNAL_SERVER_ERROR',
  NETWORK_ERROR: 'NETWORK_ERROR',
}

export const DEFAULT_PAGE_SIZE = 20
