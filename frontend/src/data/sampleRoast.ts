import type { RoastResult, Issue } from '@/store/useAppStore'

export interface ExtendedRoastResult extends RoastResult {
  was_document_truncated?: boolean
}

export const SAMPLE_ROAST_DATA: ExtendedRoastResult = {
  id: 'demo-roast',
  overall_score: 22,
  band: 'weak',
  one_line_verdict: 'Bhai ye resume hai ya birthday card ka message? 🎂',
  total_issues: 6,
  is_truncated: true,
  was_document_truncated: false,
  issues: [
    {
      quoted_text:
        'To work in a dynamic environment where I can utilize my skills and contribute to organizational growth.',
      category: 'buzzword',
      roast:
        'Ye objective line har second resume mein copy-paste milegi bhai 💀 tu already 50,000 logo jaisa dikh raha hai, alag kaise banega?',
      fix: 'Seedha likho tu kya chahta hai: "Looking for a business development role where I can close deals and grow key accounts — like I did at Zenith."',
      start_offset: 45,
      end_offset: 145,
      severity_rank: 1,
    },
    {
      quoted_text: 'Responsible for handling client relationships',
      category: 'no-metrics',
      roast:
        '"Handling client relationships" — matlab chai pilate the ya deals bhi close karte the? 😩 kuch toh number do yaar.',
      fix: '"Managed relationships with 15+ enterprise clients, retaining 90% of accounts year-over-year."',
      start_offset: 210,
      end_offset: 255,
      severity_rank: 2,
    },
    {
      quoted_text: 'Team player with strong communication skills',
      category: 'buzzword',
      roast:
        'Sabko pata hai tu team player hai bhai, WhatsApp group mein bhi sabse zyada \'good morning\' sticker tu hi bhejta hai na 😂',
      fix: 'Proof do: "Coordinated a 6-member cross-functional team to launch 3 client campaigns on time."',
      start_offset: 260,
      end_offset: 304,
      severity_rank: 3,
    },
    {
      quoted_text: 'Hardworking and dedicated professional',
      category: 'buzzword',
      roast:
        "Koi khud ko resume mein 'lazy and unmotivated' thodi likhega bhai 🙃 ye line har resume ka default setting hai, kuch bata nahi rahi.",
      fix: 'Delete this line entirely — replace the space with a real achievement instead.',
      start_offset: 308,
      end_offset: 346,
      severity_rank: 4,
    },
    {
      quoted_text: 'Assisted in achieving sales targets',
      category: 'no-metrics',
      roast:
        '"Assisted in" ka matlab kya hota hai bhai — tune target achieve kiya ya sirf paas khada tha jab dusro ne kiya? 👀',
      fix: '"Contributed to exceeding quarterly sales targets by 24%, personally closing 8 new accounts."',
      start_offset: 350,
      end_offset: 385,
      severity_rank: 5,
    },
    {
      quoted_text:
        'Proficient in MS Office, hardworking, fast learner, good communication',
      category: 'buzzword',
      roast:
        "2024 mein 'MS Office proficient' likhna waise hi hai jaise likhna 'insaan hoon, saans leta hoon' 🫠 ye skill nahi hai bhai, ye basic survival hai.",
      fix: 'List actual relevant tools: "CRM: Salesforce, HubSpot · Excel: pivot tables, VLOOKUP · Canva for pitch decks".',
      start_offset: 400,
      end_offset: 470,
      severity_rank: 6,
    },
  ],
  strengths: [
    'Formatting clean hai aur ATS padh sakta hai, chalo ek cheez toh sahi hai 👍',
    'Company aur role clearly mentioned hai, confusion nahi hai kaam kya tha',
  ],
}

export const SAMPLE_RESUME_INFO = {
  candidateName: 'ROHAN MEHTA',
  candidateTitle: 'BUSINESS DEVELOPMENT ASSOCIATE',
  experienceHeader: 'EXPERIENCE',
  companyLine: 'Zenith Solutions Pvt Ltd — Business Development Associate',
  bullet1Text:
    'To work in a dynamic environment where I can utilize my skills and contribute to organizational growth.',
  bullet1Annotated:
    'utilize my skills and contribute to organizational growth',
  bullet1Tag: 'GHISA-PITA OBJECTIVE',
  bullet2Text:
    'Responsible for handling client relationships and achieving sales targets.',
  bullet2Annotated: 'handling client relationships',
  bullet2Tag: 'NUMBER GHAYAB HAI',
  bullet3Text:
    'Team player with strong communication skills, hardworking, dedicated professional, proficient in MS Office.',
  bullet3Annotated: 'proficient in MS Office',
  bullet3Tag: 'BUZZWORD KA OVERDOSE',
}
