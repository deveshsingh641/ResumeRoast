import { useEffect, useState } from 'react'
import type { Issue } from '@/store/useAppStore'
import { getHinglishTag } from '@/utils/categoryTags'

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
  controlledPaperSettled?: boolean
  controlledMarkStep?: number
  xRayMode?: boolean
}

export default function PaperMockup({
  candidateName = 'ROHIT SHARMA',
  candidateTitle = 'SOFTWARE ENGINEER // 3 YOE',
  experienceHeader = 'EXPERIENCE (KAAM KA RECORD)',
  companyLine = 'TechCorp Labs — Software Engineer (2022–Present)',
  bullet1Text = 'Leveraged cross-functional synergies to drive high-impact outcomes across 12 product teams.',
  bullet1Annotated = 'Leveraged cross-functional synergies to drive high-impact outcomes',
  bullet1Tag = 'BUZZWORD KA OVERDOSE',
  bullet2Text = 'Responsible for backend system development and general database optimization.',
  bullet2Annotated = 'Responsible for backend system development',
  bullet2Tag = 'NUMBER GHAYAB HAI',
  bullet3Text = 'Assisted in regular agile ceremonies and references available upon request.',
  bullet3Annotated = 'references available upon request',
  bullet3Tag = 'YE KYUN LIKHA BHAI',
  issues,
  rotation = -2,
  animate = true,
  controlledPaperSettled,
  controlledMarkStep,
  xRayMode = false,
}: PaperMockupProps) {
  // If custom issues passed from real resume, populate bullets from issues
  let finalBullet1Text = bullet1Text
  let finalBullet1Annotated = bullet1Annotated
  let finalBullet1Tag = getHinglishTag(bullet1Tag)
  let cat1 = 'buzzword'

  let finalBullet2Text = bullet2Text
  let finalBullet2Annotated = bullet2Annotated
  let finalBullet2Tag = getHinglishTag(bullet2Tag)
  let cat2 = 'no-metrics'

  let finalBullet3Text = bullet3Text
  let finalBullet3Annotated = bullet3Annotated
  let finalBullet3Tag = getHinglishTag(bullet3Tag)
  let cat3 = 'formatting'

  if (issues && issues.length > 0) {
    if (issues[0]) {
      finalBullet1Text = issues[0].quoted_text
      finalBullet1Annotated = issues[0].quoted_text
      finalBullet1Tag = issues[0].badge_label?.trim() || getHinglishTag(issues[0].category)
      cat1 = issues[0].category
    }
    if (issues[1]) {
      finalBullet2Text = issues[1].quoted_text
      finalBullet2Annotated = issues[1].quoted_text
      finalBullet2Tag = issues[1].badge_label?.trim() || getHinglishTag(issues[1].category)
      cat2 = issues[1].category
    }
    if (issues[2]) {
      finalBullet3Text = issues[2].quoted_text
      finalBullet3Annotated = issues[2].quoted_text
      finalBullet3Tag = issues[2].badge_label?.trim() || getHinglishTag(issues[2].category)
      cat3 = issues[2].category
    }
  }

  // Animation sequence states
  const [paperSettled, setPaperSettled] = useState(
    controlledPaperSettled !== undefined ? controlledPaperSettled : !animate
  )
  const [markStep, setMarkStep] = useState(
    controlledMarkStep !== undefined ? controlledMarkStep : (animate ? 0 : 3)
  )

  // Scroll offset for dynamic drop shadow (Part 2.1)
  const [scrollShadowOffset, setScrollShadowOffset] = useState(0)

  useEffect(() => {
    const handleScroll = () => {
      setScrollShadowOffset(Math.min(window.scrollY * 0.035, 18))
    }
    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  useEffect(() => {
    if (controlledPaperSettled !== undefined) {
      setPaperSettled(controlledPaperSettled)
    }
  }, [controlledPaperSettled])

  useEffect(() => {
    if (controlledMarkStep !== undefined) {
      setMarkStep(controlledMarkStep)
    }
  }, [controlledMarkStep])

  useEffect(() => {
    // Only use internal timers if not controlled externally
    if (controlledMarkStep !== undefined || controlledPaperSettled !== undefined) {
      return
    }

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
  }, [animate, controlledMarkStep, controlledPaperSettled])

  const getHeatmapColor = (cat: string) => {
    switch (cat) {
      case 'buzzword':
      case 'no-metrics':
      case 'typo':
        return { color: '#E8422D', bg: 'rgba(232, 66, 45, 0.12)', label: 'CRITICAL [RECRUITER DROP-OFF]' }
      case 'formatting':
      case 'length':
        return { color: '#FFB93C', bg: 'rgba(255, 185, 60, 0.12)', label: 'MODERATE [WASTED REAL ESTATE]' }
      default:
        return { color: '#7FA65C', bg: 'rgba(127, 166, 92, 0.12)', label: 'OPTIMAL [CLEAR IMPACT]' }
    }
  }

  const items = [
    {
      id: 1,
      fullText: finalBullet1Text,
      annotatedPart: finalBullet1Annotated,
      tag: finalBullet1Tag,
      category: cat1,
      tagSide: 'right' as const,
      rotationAngle: 3,
    },
    {
      id: 2,
      fullText: finalBullet2Text,
      annotatedPart: finalBullet2Annotated,
      tag: finalBullet2Tag,
      category: cat2,
      tagSide: 'left' as const,
      rotationAngle: -2.5,
    },
    {
      id: 3,
      fullText: finalBullet3Text,
      annotatedPart: finalBullet3Annotated,
      tag: finalBullet3Tag,
      category: cat3,
      tagSide: 'right' as const,
      rotationAngle: 2,
    },
  ]

  return (
    <div className="relative w-full max-w-[620px] mx-auto select-none my-4 sm:my-6">
      {/* Paper Card */}
      <div
        className={`paper-mockup-card relative bg-paper text-ink rounded-sm px-4 py-6 sm:px-10 sm:py-10 transition-all duration-300 ${
          animate && paperSettled ? 'animate-paper-settle' : ''
        }`}
        style={{
          boxShadow: `0 ${30 + scrollShadowOffset}px ${60 + scrollShadowOffset * 1.5}px rgba(0,0,0,0.5)`,
          transform: `rotate(${rotation}deg)`,
          ['--paper-rotate' as string]: `${rotation}deg`,
          border: xRayMode ? '1px solid #FFB93C' : '1px solid rgba(0,0,0,0.1)',
        }}
      >
        {/* Paper subtle document lines or X-Ray scan grid */}
        {!xRayMode ? (
          <div
            className="absolute inset-0 pointer-events-none opacity-[0.03] rounded-sm"
            style={{
              backgroundImage:
                'repeating-linear-gradient(transparent, transparent 23px, #2B2620 23px, #2B2620 24px)',
              backgroundPositionY: '20px',
            }}
            aria-hidden="true"
          />
        ) : (
          <div
            className="absolute inset-0 pointer-events-none opacity-[0.08] rounded-sm"
            style={{
              backgroundImage:
                'repeating-linear-gradient(0deg, #17140F 0px, #17140F 1px, transparent 1px, transparent 14px), repeating-linear-gradient(90deg, #17140F 0px, #17140F 1px, transparent 1px, transparent 14px)',
            }}
            aria-hidden="true"
          />
        )}

        {/* 1.6 X-Ray Mode Diagnostic Header Banner */}
        {xRayMode && (
          <div className="mb-4 -mt-2 py-1.5 px-3 bg-[#17140F] border border-amber-500/40 rounded-sm flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm">🩻</span>
              <span className="font-mono text-[10px] text-amber-400 font-bold uppercase tracking-wider">
                X-RAY DIAGNOSTIC SCAN // HEATMAP OVERLAY
              </span>
            </div>
            <span className="font-mono text-[9px] text-emerald-400 font-semibold uppercase animate-pulse">
              LIVE SENSORS
            </span>
          </div>
        )}

        {/* Candidate Header — IBM Plex Mono */}
        <div
          className={`relative border-b border-black/10 pb-4 mb-6 text-left ${
            xRayMode ? 'p-2 rounded bg-emerald-500/10 border border-emerald-600/30' : ''
          }`}
        >
          <div className="flex items-center justify-between">
            <h2 className="font-mono text-base sm:text-lg font-semibold tracking-wider text-ink">
              {candidateName}
            </h2>
            {xRayMode && (
              <span className="font-mono text-[9px] uppercase px-1.5 py-0.5 rounded bg-emerald-600 text-white font-bold">
                SAFE ZONE
              </span>
            )}
          </div>
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

        {/* Bullet Points with Red Pen Annotations OR X-Ray Heatmap Strips */}
        <div className="relative space-y-4 text-left font-body text-xs sm:text-sm text-ink leading-relaxed">
          {items.map((item, idx) => {
            const isVisible = markStep > idx
            const heat = getHeatmapColor(item.category)

            if (xRayMode) {
              return (
                <div
                  key={item.id}
                  className="p-3 rounded-sm transition-all duration-200"
                  style={{
                    backgroundColor: heat.bg,
                    borderLeft: `4px solid ${heat.color}`,
                    borderTop: `1px solid ${heat.color}30`,
                    borderRight: `1px solid ${heat.color}20`,
                    borderBottom: `1px solid ${heat.color}20`,
                  }}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span
                      className="font-mono text-[10px] font-bold tracking-wider uppercase"
                      style={{ color: heat.color }}
                    >
                      {item.tag}
                    </span>
                    <span
                      className="font-mono text-[9px] font-semibold uppercase px-1.5 py-0.2 rounded"
                      style={{ backgroundColor: `${heat.color}25`, color: heat.color }}
                    >
                      {heat.label}
                    </span>
                  </div>
                  <p className="font-body text-xs sm:text-sm text-ink font-medium leading-relaxed">
                    "{item.fullText}"
                  </p>
                </div>
              )
            }

            // Standard Annotated View
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

        {/* X-Ray Mode Diagnostic Scale Legend */}
        {xRayMode && (
          <div className="mt-6 pt-4 border-t border-black/10 flex flex-wrap items-center justify-between gap-2 text-left">
            <span className="font-mono text-[10px] text-ink/70 font-semibold uppercase tracking-wider">
              Density Scale:
            </span>
            <div className="flex items-center gap-3 font-mono text-[10px]">
              <div className="flex items-center gap-1">
                <span className="w-2.5 h-2.5 rounded-xs bg-[#7FA65C] inline-block" />
                <span className="text-ink/80">Damdaar (Safe)</span>
              </div>
              <div className="flex items-center gap-1">
                <span className="w-2.5 h-2.5 rounded-xs bg-[#FFB93C] inline-block" />
                <span className="text-ink/80">Thik-Thak (Mid)</span>
              </div>
              <div className="flex items-center gap-1">
                <span className="w-2.5 h-2.5 rounded-xs bg-[#E8422D] inline-block" />
                <span className="text-ink/80">Kamzor (Flaw)</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Mobile Stacked List of Callout Tags (collapsed below paper on small screens in annotated mode) */}
      {!xRayMode && (
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
      )}
    </div>
  )
}
