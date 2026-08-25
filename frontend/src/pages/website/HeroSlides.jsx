import { ExternalLink, ImageOff } from 'lucide-react'

import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import CrudPage from '@/components/common/CrudPage'
import { heroSlideService } from '@/services'

const COLUMNS = [
  {
    key: 'image',
    header: 'Image',
    headerClassName: 'w-28',
    render: (row) =>
      row.image_url ? (
        <img
          src={row.image_url}
          alt={row.alt_text || row.title || 'Hero slide'}
          className="h-12 w-20 rounded-md object-cover ring-1 ring-slate-200"
        />
      ) : (
        <span className="grid h-12 w-20 place-items-center rounded-md bg-slate-100 text-slate-400">
          <ImageOff className="h-4 w-4" aria-hidden="true" />
        </span>
      ),
  },
  {
    key: 'title',
    header: 'Slide',
    render: (row) => (
      <div className="min-w-0">
        <p className="truncate font-medium text-slate-900">{row.title || 'Untitled slide'}</p>
        {row.subtitle ? <p className="truncate text-xs text-slate-500">{row.subtitle}</p> : null}
      </div>
    ),
  },
  { key: 'caption', header: 'Caption', render: (row) => row.caption || '—' },
  {
    key: 'link',
    header: 'Button',
    render: (row) =>
      row.link_url ? (
        <span className="inline-flex items-center gap-1.5 text-xs text-brand-600">
          <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
          {row.link_label || 'Link'}
        </span>
      ) : (
        '—'
      ),
  },
  { key: 'order', header: 'Order', headerClassName: 'w-20' },
  {
    key: 'is_active',
    header: 'Status',
    render: (row) => (
      <Badge tone={row.is_active ? 'success' : 'neutral'}>{row.is_active ? 'Showing' : 'Hidden'}</Badge>
    ),
  },
]

const FIELDS = [
  {
    name: 'image',
    type: 'image',
    label: 'Slide image',
    required: true,
    hint: 'Wide, landscape images work best — roughly 1920×900. PNG or JPG.',
  },
  { name: 'title', label: 'Headline', placeholder: 'Admissions open for 2027', fullWidth: true },
  { name: 'subtitle', label: 'Supporting line', type: 'textarea', rows: 2 },
  { name: 'caption', label: 'Small label above the headline', placeholder: 'Admissions' },
  { name: 'order', label: 'Order', type: 'number', min: 0, defaultValue: 0, hint: 'Lower numbers show first.' },
  { name: 'link_label', label: 'Button text', placeholder: 'Read more' },
  { name: 'link_url', label: 'Button link', placeholder: '#about' },
  {
    name: 'alt_text',
    label: 'Image description',
    placeholder: 'Students at the annual sports day',
    hint: 'Read aloud by screen readers. Falls back to the headline.',
    fullWidth: true,
  },
  { name: 'is_active', label: 'Show this slide on the website', type: 'checkbox', defaultValue: true },
]

/**
 * The hero slider's images.
 *
 * Order and visibility are ordinary fields rather than drag handles: a school
 * adds a slide a few times a year, and a number in a form is easier to get
 * right than a drag target on a phone.
 */
export function HeroSlides() {
  return (
    <CrudPage
      title="Hero slider"
      description="The rotating banner at the top of the school's public home page."
      service={heroSlideService}
      module="content"
      singular="slide"
      columns={COLUMNS}
      fields={FIELDS}
      searchPlaceholder="Search slides…"
      emptyTitle="No slides yet"
      emptyDescription="Add an image and it will start rotating on the home page."
      extraActions={
        <a href="/" target="_blank" rel="noreferrer">
          <Button variant="secondary" leftIcon={<ExternalLink className="h-4 w-4" />}>
            View the site
          </Button>
        </a>
      }
    />
  )
}

export default HeroSlides
