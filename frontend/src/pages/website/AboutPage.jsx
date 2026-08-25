import { useEffect, useState } from 'react'
import { ExternalLink, Save } from 'lucide-react'

import Alert from '@/components/ui/Alert'
import Button from '@/components/ui/Button'
import Card, { CardBody, CardHeader } from '@/components/ui/Card'
import Input, { Textarea } from '@/components/ui/Input'
import { LoadingState } from '@/components/ui/Spinner'
import Can from '@/components/common/Can'
import PageHeader from '@/components/common/PageHeader'
import { ImageField } from '@/components/common/ResourceForm'
import useApi from '@/hooks/useApi'
import useAuth from '@/hooks/useAuth'
import useDocumentTitle from '@/hooks/useDocumentTitle'
import useToast from '@/hooks/useToast'
import { aboutService } from '@/services'

const TEXT_FIELDS = [
  {
    name: 'summary',
    label: 'Summary',
    rows: 4,
    hint: 'The opening paragraph under the section heading.',
  },
  { name: 'history', label: 'Our history', rows: 6 },
  { name: 'mission', label: 'Our mission', rows: 5 },
  { name: 'vision', label: 'Our vision', rows: 5 },
]

const EMPTY = { headline: '', motto: '', summary: '', history: '', mission: '', vision: '' }

/**
 * The About-the-School copy behind the public site.
 *
 * A single record rather than a list, so this is a plain form instead of a
 * `CrudPage`. Fields left blank are simply not rendered on the public page —
 * a school can fill this in a paragraph at a time.
 */
export function AboutPage() {
  useDocumentTitle('About the school')

  const toast = useToast()
  const { hasPermission } = useAuth()
  const { data, error, isLoading, refetch } = useApi(() => aboutService.retrieve(), [])

  const [values, setValues] = useState(EMPTY)
  const [image, setImage] = useState(null)
  const [errors, setErrors] = useState({})
  const [isSaving, setSaving] = useState(false)

  const canEdit = hasPermission('content.update')

  useEffect(() => {
    if (!data) return
    setValues({
      headline: data.headline ?? '',
      motto: data.motto ?? '',
      summary: data.summary ?? '',
      history: data.history ?? '',
      mission: data.mission ?? '',
      vision: data.vision ?? '',
    })
  }, [data])

  function update(field, value) {
    setValues((current) => ({ ...current, [field]: value }))
    setErrors((current) => ({ ...current, [field]: undefined }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setSaving(true)
    setErrors({})
    try {
      await aboutService.update(values, image)
      setImage(null)
      // The save already succeeded; a failed re-read is not a failed save.
      await refetch().catch(() => {})
      toast.success('The About section has been updated.')
    } catch (caught) {
      setErrors(caught.errors ?? {})
      toast.error(caught.message)
    } finally {
      setSaving(false)
    }
  }

  function errorFor(field) {
    const value = errors[field]
    return Array.isArray(value) ? value[0] : value
  }

  if (isLoading) return <LoadingState label="Loading the About section…" />

  return (
    <div>
      <PageHeader
        title="About the school"
        description="The school's story, mission and vision, as they appear on the public home page."
        actions={
          <a href="/#about" target="_blank" rel="noreferrer">
            <Button variant="secondary" leftIcon={<ExternalLink className="h-4 w-4" />}>
              View the site
            </Button>
          </a>
        }
      />

      {error ? (
        <Alert type="error" title="Could not load this page" className="mb-6">
          {error.message}
        </Alert>
      ) : null}

      {!canEdit ? (
        <Alert type="info" className="mb-6">
          You can read this content but not change it. Editing needs the <code>content.update</code> permission.
        </Alert>
      ) : null}

      <form onSubmit={handleSubmit} noValidate>
        <fieldset disabled={!canEdit || isSaving} className="space-y-4">
          <Card>
            <CardHeader
              title="Heading"
              description="Shown at the top of the About section, above the copy."
            />
            <CardBody className="grid gap-4 sm:grid-cols-2">
              <Input
                label="Section headline"
                placeholder="A school built for the children of Longorpara"
                value={values.headline}
                onChange={(event) => update('headline', event.target.value)}
                error={errorFor('headline')}
              />
              <Input
                label="Motto"
                placeholder="Discipline · Knowledge · Character"
                value={values.motto}
                onChange={(event) => update('motto', event.target.value)}
                error={errorFor('motto')}
              />
              <div className="sm:col-span-2">
                <ImageField
                  label="Section image"
                  file={image}
                  existingUrl={data?.image_url}
                  onChange={setImage}
                  hint="Optional. A photograph of the school or its grounds."
                />
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardHeader
              title="The school's story"
              description="Anything you leave blank is left off the public page rather than shown empty."
            />
            <CardBody className="space-y-4">
              {TEXT_FIELDS.map((field) => (
                <Textarea
                  key={field.name}
                  label={field.label}
                  rows={field.rows}
                  hint={field.hint}
                  value={values[field.name]}
                  onChange={(event) => update(field.name, event.target.value)}
                  error={errorFor(field.name)}
                />
              ))}
            </CardBody>
          </Card>
        </fieldset>

        <Can permission="content.update">
          <div className="mt-4 flex justify-end">
            <Button type="submit" leftIcon={<Save className="h-4 w-4" />} isLoading={isSaving}>
              Save changes
            </Button>
          </div>
        </Can>
      </form>
    </div>
  )
}

export default AboutPage
