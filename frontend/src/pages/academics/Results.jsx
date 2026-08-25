import { useMemo, useState } from 'react'
import { Award, Search, Send } from 'lucide-react'

import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import Input, { Select } from '@/components/ui/Input'
import { ConfirmDialog } from '@/components/ui/Modal'
import Can from '@/components/common/Can'
import DataTable from '@/components/common/DataTable'
import PageHeader from '@/components/common/PageHeader'
import useApi from '@/hooks/useApi'
import useDocumentTitle from '@/hooks/useDocumentTitle'
import usePaginatedList from '@/hooks/usePaginatedList'
import useToast from '@/hooks/useToast'
import { examService, resultService, subjectService } from '@/services'
import { formatPercent } from '@/utils/formatters'

const GRADE_TONES = {
  'A+': 'success',
  A: 'success',
  'A-': 'brand',
  B: 'info',
  C: 'warning',
  D: 'warning',
  F: 'danger',
}

export function Results() {
  useDocumentTitle('Results')

  const toast = useToast()
  const list = usePaginatedList(resultService)
  const { data: exams } = useApi(() => examService.all(), [], { initialData: [] })
  const { data: subjects } = useApi(() => subjectService.all(), [], { initialData: [] })

  const [publishing, setPublishing] = useState(false)
  const [isPublishing, setIsPublishing] = useState(false)

  const examOptions = useMemo(() => (exams ?? []).map((exam) => ({ value: exam.id, label: exam.name })), [exams])
  const subjectOptions = useMemo(
    () => (subjects ?? []).map((subject) => ({ value: subject.id, label: subject.name })),
    [subjects],
  )
  const selectedExam = list.filters.exam

  async function handlePublish() {
    setIsPublishing(true)
    try {
      const result = await resultService.publish(selectedExam)
      toast.success(result.message ?? 'Results published.')
      setPublishing(false)
      list.reload()
    } catch (error) {
      toast.error(error.message)
    } finally {
      setIsPublishing(false)
    }
  }

  const columns = [
    {
      key: 'student_name',
      header: 'Student',
      render: (row) => (
        <div className="min-w-0">
          <p className="truncate font-medium text-slate-900">{row.student_name}</p>
          <p className="text-xs text-slate-500">Roll {row.student_roll ?? '—'}</p>
        </div>
      ),
    },
    { key: 'exam_name', header: 'Exam' },
    { key: 'subject_name', header: 'Subject' },
    {
      key: 'marks_obtained',
      header: 'Marks',
      render: (row) => (
        <span className="font-medium text-slate-900">
          {row.is_absent ? 'Absent' : `${row.marks_obtained} / ${row.full_marks}`}
        </span>
      ),
    },
    { key: 'percentage', header: 'Percentage', render: (row) => formatPercent(row.percentage) },
    {
      key: 'grade',
      header: 'Grade',
      render: (row) => (
        <Badge tone={GRADE_TONES[row.grade] ?? 'neutral'}>
          {row.grade || '—'} · {row.grade_point}
        </Badge>
      ),
    },
    {
      key: 'is_published',
      header: 'Published',
      render: (row) =>
        row.is_published ? <Badge tone="success">Published</Badge> : <Badge tone="warning">Withheld</Badge>,
    },
  ]

  return (
    <div>
      <PageHeader
        title="Results"
        description="Marks recorded against exam papers. Grades are derived on the server from the national scale."
        actions={
          <Can permission="result.publish">
            <Button
              leftIcon={<Send className="h-4 w-4" />}
              onClick={() => setPublishing(true)}
              disabled={!selectedExam}
              title={selectedExam ? undefined : 'Choose an exam first'}
            >
              Publish results
            </Button>
          </Can>
        }
      />

      <DataTable
        columns={columns}
        rows={list.items}
        isLoading={list.isLoading}
        error={list.error}
        emptyIcon={Award}
        emptyTitle="No results recorded"
        emptyDescription="Filter by an exam, or record marks against a paper."
        toolbar={
          <div className="flex flex-wrap items-center gap-3">
            <Input
              containerClassName="w-full sm:max-w-xs"
              placeholder="Search by student or subject…"
              leftIcon={<Search className="h-4 w-4" />}
              value={list.search}
              onChange={(event) => list.setSearch(event.target.value)}
              aria-label="Search results"
            />
            <Select
              className="w-auto min-w-[12rem]"
              placeholder="All exams"
              options={examOptions}
              value={list.filters.exam ?? ''}
              onChange={(event) => list.setFilter('exam', event.target.value)}
              aria-label="Filter by exam"
            />
            <Select
              className="w-auto min-w-[10rem]"
              placeholder="All subjects"
              options={subjectOptions}
              value={list.filters.subject ?? ''}
              onChange={(event) => list.setFilter('subject', event.target.value)}
              aria-label="Filter by subject"
            />
          </div>
        }
        pagination={{
          page: list.page,
          totalPages: list.totalPages,
          count: list.count,
          pageSize: list.pageSize,
          onChange: list.setPage,
        }}
      />

      <ConfirmDialog
        isOpen={publishing}
        onClose={() => setPublishing(false)}
        onConfirm={handlePublish}
        isLoading={isPublishing}
        variant="primary"
        title="Publish results for this exam?"
        description="Every result recorded against this exam becomes visible to students and parents. This is separate from recording marks, so nothing is released by accident."
        confirmLabel="Publish"
      />
    </div>
  )
}

export default Results
