/** Joins class names, dropping falsy values. Small on purpose — no dependency needed. */
export function cn(...classes) {
  return classes.flat().filter(Boolean).join(' ')
}

export default cn
