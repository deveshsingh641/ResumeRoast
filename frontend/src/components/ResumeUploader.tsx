import React, { useCallback, useRef, useState } from 'react'
import axios from 'axios'
import { useNavigate } from 'react-router-dom'
import { useAppStore } from '@/store/useAppStore'
import ProcessingState from './ProcessingState'

const MAX_SIZE = 5 * 1024 * 1024 // 5MB
const ALLOWED_EXTENSIONS = ['.pdf', '.docx']

function validateFile(file: File): string | null {
  if (!file) {
    return 'Please select a file to upload.'
  }
  if (file.size === 0) {
    return 'That file is empty (0 bytes). Please upload a complete resume document.'
  }
  const ext = '.' + file.name.split('.').pop()?.toLowerCase()
  if (!ALLOWED_EXTENSIONS.includes(ext)) {
    return "Only PDF or DOCX, up to 5MB — that file's format isn't supported."
  }
  if (file.size > MAX_SIZE) {
    const sizeMb = (file.size / 1024 / 1024).toFixed(1)
    return `Only PDF or DOCX, up to 5MB — that file's a bit big (${sizeMb}MB).`
  }
  return null
}

export default function ResumeUploader() {
  const navigate = useNavigate()
  const { setUploadStatus, setUploadError, setResult, uploadStatus } = useAppStore()
  const [isDragOver, setIsDragOver] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const isProcessing = isSubmitting || uploadStatus === 'uploading' || uploadStatus === 'analyzing'

  const processFile = useCallback(
    async (file: File) => {
      if (isProcessing) return // Prevent double-submit

      const valError = validateFile(file)
      if (valError) {
        setErrorMessage(valError)
        return
      }

      setIsSubmitting(true)
      setErrorMessage(null)
      setUploadError(null)
      setUploadStatus('uploading')

      const formData = new FormData()
      formData.append('file', file)

      try {
        setUploadStatus('analyzing')
        const { data } = await axios.post('/api/roast', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          timeout: 65000,
        })
        setResult(data)
        setUploadStatus('done')
        navigate(`/roast/${data.id}`)
      } catch (err: any) {
        setUploadStatus('idle')
        setIsSubmitting(false)

        let msg: string
        const detail = err?.response?.data?.detail

        if (typeof detail === 'object' && detail?.error === 'daily_limit_reached') {
          msg = detail.message
        } else if (typeof detail === 'string') {
          msg = detail
        } else if (err?.code === 'ECONNABORTED' || err?.message?.includes('timeout')) {
          msg = "The grading process timed out. Try again — it usually finishes in ~15 seconds."
        } else if (!err?.response) {
          msg = 'Unable to reach the grading server. Please check your internet connection and try again.'
        } else {
          msg = 'Failed to analyze resume. Please try exporting fresh as a PDF or standard DOCX.'
        }

        setUploadError(msg)
        setErrorMessage(msg)
      } finally {
        setIsSubmitting(false)
      }
    },
    [isProcessing, navigate, setResult, setUploadError, setUploadStatus]
  )

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setIsDragOver(false)
      if (isProcessing) return
      const file = e.dataTransfer.files[0]
      if (file) {
        processFile(file)
      }
    },
    [isProcessing, processFile]
  )

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (isProcessing) return
    const file = e.target.files?.[0]
    if (file) {
      processFile(file)
    }
  }

  // Morph into slim horizontal state when processing
  if (isProcessing) {
    return <ProcessingState />
  }

  return (
    <div className="w-full">
      {/* Empty Document Slot Dropzone */}
      <div
        role="button"
        tabIndex={0}
        aria-label="Upload resume: drag and drop or press Enter to browse"
        onDragOver={(e) => {
          e.preventDefault()
          if (!isProcessing) setIsDragOver(true)
        }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        onClick={() => !isProcessing && fileInputRef.current?.click()}
        onKeyDown={(e) => {
          if ((e.key === 'Enter' || e.key === ' ') && !isProcessing) {
            e.preventDefault()
            fileInputRef.current?.click()
          }
        }}
        className={`w-full text-center px-6 py-12 sm:py-16 select-none cursor-pointer transition-all duration-120 ${
          isDragOver
            ? 'border border-dashed border-stamp bg-[#E8422D]/[0.08]'
            : 'border border-dashed border-tan-dim bg-[#F5EFE0]/[0.04] hover:border-tan hover:bg-[#F5EFE0]/[0.07]'
        } rounded-sm`}
      >
        {/* Document Icon */}
        <div className="flex justify-center mb-4 text-tan-dim">
          <svg
            width="36"
            height="36"
            viewBox="0 0 24 24"
            fill="none"
            stroke={isDragOver ? '#E8422D' : '#8A8168'}
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="12" y1="18" x2="12" y2="12" />
            <polyline points="9 15 12 12 15 15" />
          </svg>
        </div>

        <p className="font-mono text-sm text-paper mb-1">
          {isDragOver ? 'Release to drop onto desk' : 'Place your resume on the desk'}
        </p>
        <p className="font-mono text-xs text-tan-dim mb-6">
          PDF or DOCX format · Max 5MB
        </p>

        {/* Primary verb-first button */}
        <button
          type="button"
          tabIndex={-1}
          disabled={isProcessing}
          className="btn-primary"
          onClick={(e) => {
            e.stopPropagation()
            if (!isProcessing) fileInputRef.current?.click()
          }}
        >
          Browse files
        </button>

        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          className="sr-only"
          disabled={isProcessing}
          onChange={handleFileChange}
          aria-label="Resume file input"
        />
      </div>

      {/* Inline specific error message */}
      {errorMessage && (
        <div
          role="alert"
          className="mt-3 text-left font-mono text-[13px] text-stamp leading-relaxed flex items-start gap-2"
        >
          <span aria-hidden="true">⚠</span>
          <span>{errorMessage}</span>
        </div>
      )}
    </div>
  )
}
