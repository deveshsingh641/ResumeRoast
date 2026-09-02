import { useEffect, useState } from 'react'
import type { Issue } from '@/store/useAppStore'

interface PaperMockupProps {
  candidateName?: string
  candidateTitle?: string
  experienceHeader?: string
  companyLine?: string
  bullet1Text?: string
  bullet1Annotated?: string
  bullet1Tag?: string
  bullet2Text?: string
  bullet2Annotated?: string
  bullet2Tag?: string
  bullet3Text?: string
  bullet3Annotated?: string
  bullet3Tag?: string
  issues?: Issue[]
  rotation?: number
  animate?: boolean
}

export default function PaperMockup({
  candidateName = 'ALEX JOHNSON',
  candidateTitle = 'SENIOR FULL-STACK ENGINEER // 5 YOE',
  experienceHeader = 'EXPERIENCE',
  companyLine = 'TechCorp Inc. — Senior Software Engineer (2022–Present)',
  bullet1Text = 'Leveraged cross-functional synergies to drive high-impact outcomes across 12 product teams.',
  bullet1Annotated = 'Leveraged cross-functional synergies to drive high-impact outcomes',
  bullet1Tag = 'BUZZWORD DETECTED',
  bullet2Text = 'Responsible for backend system development and general database optimization.',
  bullet2Annotated = 'Responsible for backend system development',
  bullet2Tag = 'ZERO METRICS / VAGUE',
  bullet3Text = 'Assisted in regular agile ceremonies and references available upon request.',
  bullet3Annotated = 'references available upon request',
  bullet3Tag = 'OBSOLETE / CLUTTER',
  issues,
  rotation = -2,
  animate = true,
}: PaperMockupProps) {
  // If custom issues passed from real resume, populate bullets from issues
  let finalBullet1Text = bullet1Text
  let finalBullet1Annotated = bullet1Annotated
  let finalBullet1Tag = bullet1Tag

  let finalBullet2Text = bullet2Text
  let finalBullet2Annotated = bullet2Annotated
  let finalBullet2Tag = bullet2Tag

  let finalBullet3Text = bullet3Text
  let finalBullet3Annotated = bullet3Annotated
  let finalBullet3Tag = bullet3Tag

  if (issues && issues.length > 0) {
    if (issues[0]) {
      finalBullet1Text = issues[0].quoted_text
      finalBullet1Annotated = issues[0].quoted_text
      finalBullet1Tag = (issues[0].category || 'FLAGGED').toUpperCase()
    }
    if (issues[1]) {
      finalBullet2Text = issues[1].quoted_text
      finalBullet2Annotated = issues[1].quoted_text
      finalBullet2Tag = (issues[1].category || 'FLAGGED').toUpperCase()
    }
    if (issues[2]) {
      finalBullet3Text = issues[2].quoted_text
      finalBullet3Annotated = issues[2].quoted_text
      finalBullet3Tag = (issues[2].category || 'FLAGGED').toUpperCase()
    }
  }

  // Animation sequence states
  const [paperSettled, setPaperSettled] = useState(!animate)
  const [markStep, setMarkStep] = useState(animate ? 0 : 3)

  useEffect(() => {
    if (!animate) {
      setPaperSettled(true)
      setMarkStep(3)
      return
    }

    // Step 0: paper entrance
    const t0 = setTimeout(() => {
      setPaperSettled(true)
    }, 350)

    // Sequential annotations (staggered 180ms after paper settles)
    const t1 = setTimeout(() => setMarkStep(1), 530)
    const t2 = setTimeout(() => setMarkStep(2), 720)
    const t3 = setTimeout(() => setMarkStep(3), 910)

    return () => {
      clearTimeout(t0)
      clearTimeout(t1)
      clearTimeout(t2)
      clearTimeout(t3)
    }
  }, [animate])

  const items = [
    {
      id: 1,
      fullText: finalBullet1Text,
      annotatedPart: finalBullet1Annotated,
      tag: finalBullet1Tag,
      tagSide: 'right' as const,
      rotationAngle: 3,
    },
    {
      id: 2,
      fullText: finalBullet2Text,
      annotatedPart: finalBullet2Annotated,
      tag: finalBullet2Tag,
      tagSide: 'left' as const,
      rotationAngle: -2.5,
    },
    {
      id: 3,
      fullText: finalBullet3Text,
      annotatedPart: finalBullet3Annotated,
      tag: finalBullet3Tag,
      tagSide: 'right' as const,
      rotationAngle: 2,
    },
  ]

  return (
    <div className="relative w-full max-w-[620px] mx-auto select-none my-6">
      {/* Paper Card */}
      <div
        className={`relative bg-paper text-ink rounded-sm px-6 py-8 sm:px-10 sm:py-10 transition-transform duration-300 ${
          animate && paperSettled ? 'animate-paper-settle' : ''
        }`}
        style={{
          boxShadow: '0 30px 60px rgba(0,0,0,0.45)',
          transform: `rotate(${rotation}deg)`,
          ['--paper-rotate' as string]: `${rotation}deg`,
          border: '1px solid rgba(0,0,0,0.1)',
        }}
      >
        {/* Paper subtle document lines */}
        <div
          className="absolute inset-0 pointer-events-none opacity-[0.03] rounded-sm"
          style={{
            backgroundImage:
              'repeating-linear-gradient(transparent, transparent 23px, #2B2620 23px, #2B2620 24px)',
            backgroundPositionY: '20px',
          }}
          aria-hidden="true"
        />

        {/* Candidate Header — IBM Plex Mono */}
        <div className="relative border-b border-black/10 pb-4 mb-6 text-left">
          <h2 className="font-mono text-base sm:text-lg font-semibold tracking-wider text-ink">
            {candidateName}
          </h2>
          <p className="font-mono text-xs text-ink/70 mt-1 tracking-wide">
            {candidateTitle}
          </p>
        </div>

        {/* Section Heading */}
        <div className="relative mb-3 text-left">
          <p className="font-mono text-xs font-semibold uppercase tracking-widest text-ink/60">
            {experienceHeader}
          </p>
          <p className="font-body text-sm font-medium text-ink mt-1">
            {companyLine}
          </p>
        </div>

        {/* Bullet Points with Red Pen Annotations */}
        <div className="relative space-y-4 text-left font-body text-xs sm:text-sm text-ink leading-relaxed">
          {items.map((item, idx) => {
            const isVisible = markStep > idx
            const parts = item.fullText.split(item.annotatedPart)
            const hasMatch = parts.length > 1

            return (
              <div key={item.id} className="relative flex items-start gap-2">
                <span className="font-mono text-xs text-ink/50 select-none mt-0.5">•</span>
                <div className="flex-1 relative">
                  {hasMatch ? (
                    <>
                      <span>{parts[0]}</span>
                      <span className="relative inline-block px-1 mx-0.5">
                        {item.annotatedPart}
                        {/* Red pen annotation ellipse */}
                        <svg
                          className={`absolute -inset-x-1 -inset-y-1 w-[calc(100%+8px)] h-[calc(100%+8px)] pointer-events-none transition-opacity duration-200 ${
                            isVisible ? 'opacity-100' : 'opacity-0'
                          }`}
                          viewBox="0 0 100 40"
                          preserveAspectRatio="none"
                          aria-hidden="true"
                          style={{
                            transform: `rotate(${item.rotationAngle}deg)`,
                          }}
                        >
                          <ellipse
                            cx="50"
                            cy="20"
                            rx="48"
                            ry="17"
                            fill="none"
                            stroke="#E8422D"
                            strokeWidth="2.5"
                            strokeDasharray="250"
                            strokeDashoffset={isVisible ? '0' : '250'}
                            style={{
                              transition: isVisible
                                ? 'stroke-dashoffset 220ms ease-out'
                                : 'none',
                            }}
                          />
                        </svg>
                      </span>
                      <span>{parts[1]}</span>
                    </>
                  ) : (
                    <span className="relative inline-block px-1">
                      {item.fullText}
                      <svg
                        className={`absolute -inset-x-1 -inset-y-1 w-[calc(100%+8px)] h-[calc(100%+8px)] pointer-events-none transition-opacity duration-200 ${
                          isVisible ? 'opacity-100' : 'opacity-0'
                        }`}
                        viewBox="0 0 100 40"
                        preserveAspectRatio="none"
                        aria-hidden="true"
                        style={{
                          transform: `rotate(${item.rotationAngle}deg)`,
                        }}
                      >
                        <ellipse
                          cx="50"
                          cy="20"
                          rx="48"
                          ry="17"
                          fill="none"
                          stroke="#E8422D"
                          strokeWidth="2.5"
                          strokeDasharray="250"
                          strokeDashoffset={isVisible ? '0' : '250'}
                          style={{
                            transition: isVisible
                              ? 'stroke-dashoffset 220ms ease-out'
                              : 'none',
                          }}
                        />
                      </svg>
                    </span>
                  )}
                </div>

                {/* Floating tag callouts — Desktop only */}
                {item.tagSide === 'right' ? (
                  <div
                    className={`hidden lg:flex absolute -right-36 top-1 items-center gap-1.5 transition-all duration-200 pointer-events-none ${
                      isVisible
                        ? 'opacity-100 translate-x-0'
                        : 'opacity-0 -translate-x-2'
                    }`}
                  >
                    <span className="w-5 h-[1px] bg-stamp inline-block" />
                    <span className="bg-bg border border-stamp text-stamp font-mono text-[10px] tracking-wider uppercase px-2 py-0.5 rounded-sm shadow-md whitespace-nowrap">
                      {item.tag}
                    </span>
                  </div>
                ) : (
                  <div
                    className={`hidden lg:flex absolute -left-40 top-1 items-center gap-1.5 transition-all duration-200 pointer-events-none ${
                      isVisible
                        ? 'opacity-100 translate-x-0'
                        : 'opacity-0 translate-x-2'
                    }`}
                  >
                    <span className="bg-bg border border-stamp text-stamp font-mono text-[10px] tracking-wider uppercase px-2 py-0.5 rounded-sm shadow-md whitespace-nowrap">
                      {item.tag}
                    </span>
                    <span className="w-5 h-[1px] bg-stamp inline-block" />
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Mobile Stacked List of Callout Tags (collapsed below paper on small screens) */}
      <div className="flex flex-col gap-1.5 mt-4 lg:hidden px-2">
        {items.map((item, idx) => (
          <div
            key={item.id}
            className={`flex items-center gap-2 transition-opacity duration-200 ${
              markStep > idx ? 'opacity-100' : 'opacity-0'
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-stamp shrink-0" />
            <span className="font-mono text-xs text-stamp tracking-wider uppercase">
              {item.tag}:
            </span>
            <span className="font-mono text-xs text-tan-dim truncate">
              "{item.annotatedPart}"
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
