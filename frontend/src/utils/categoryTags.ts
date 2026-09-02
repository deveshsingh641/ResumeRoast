/**
 * Category Tag & Label Mappings for ResumeRoast (Hinglish UI)
 * Maps internal category codes to savage, spoken-Hinglish stamp labels.
 */

export const HINGLISH_CATEGORY_TAGS: Record<string, string> = {
  // Direct specification mappings (A.3)
  'generic objective': 'GHISA-PITA OBJECTIVE',
  'zero metrics / vague': 'NUMBER GHAYAB HAI',
  'buzzword overload': 'BUZZWORD KA OVERDOSE',
  'no metrics': 'NUMBER KAHAN HAI',
  'formatting issue': 'FORMAT BIGDA HUA HAI',
  'too long': 'LAMBA BAHUT KAR DIYA',
  'typo': 'SPELLING MISS HAI',
  'irrelevant': 'YE KYUN LIKHA BHAI',

  // System category codes used by backend & model
  'buzzword': 'BUZZWORD KA OVERDOSE',
  'no-metrics': 'NUMBER KAHAN HAI',
  'formatting': 'FORMAT BIGDA HUA HAI',
  'length': 'LAMBA BAHUT KAR DIYA',
  'density': 'LAMBA BAHUT KAR DIYA',
  'clutter': 'YE KYUN LIKHA BHAI',
  'obsolete': 'YE KYUN LIKHA BHAI',
  'other': 'YE KYA HAI BHAI',
  'flagged': 'GAYAB CHEEZ',
}

/**
 * Returns formatted Hinglish badge text for any category or raw tag string.
 */
export function getHinglishTag(categoryOrTag?: string): string {
  if (!categoryOrTag) return 'RED PEN KI PAKAD'
  const normalized = categoryOrTag.trim().toLowerCase()
  return HINGLISH_CATEGORY_TAGS[normalized] || categoryOrTag.toUpperCase()
}
