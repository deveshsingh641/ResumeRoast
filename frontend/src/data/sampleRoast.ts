import type { RoastResult } from '@/store/useAppStore'

export interface ExtendedRoastResult extends RoastResult {
  was_document_truncated?: boolean
}

export interface SampleResume {
  roastData: ExtendedRoastResult
  resumeInfo: {
    candidateName: string
    candidateTitle: string
    experienceHeader: string
    companyLine: string
    bullet1Text: string
    bullet1Annotated: string
    bullet1Tag: string
    bullet2Text: string
    bullet2Annotated: string
    bullet2Tag: string
    bullet3Text: string
    bullet3Annotated: string
    bullet3Tag: string
  }
}

const rohanMehta: SampleResume = {
  roastData: {
    id: 'demo-roast-rohan',
    overall_score: 22,
    band: 'weak',
    one_line_verdict: 'Bhai ye resume hai ya birthday card ka message? 🎂',
    total_issues: 6,
    is_truncated: true,
    was_document_truncated: false,
    issues: [
      {
        quoted_text: 'To work in a dynamic environment where I can utilize my skills and contribute to organizational growth.',
        category: 'buzzword',
        roast: 'Ye objective line har second resume mein copy-paste milegi bhai 💀 tu already 50,000 logo jaisa dikh raha hai, alag kaise banega?',
        fix: 'Seedha likho tu kya chahta hai: "Looking for a business development role where I can close deals and grow key accounts — like I did at Zenith."',
        start_offset: 45, end_offset: 145, severity_rank: 1,
      },
      {
        quoted_text: 'Responsible for handling client relationships',
        category: 'no-metrics',
        roast: '"Handling client relationships" — matlab chai pilate the ya deals bhi close karte the? 😩 kuch toh number do yaar.',
        fix: '"Managed relationships with 15+ enterprise clients, retaining 90% of accounts year-over-year."',
        start_offset: 210, end_offset: 255, severity_rank: 2,
      },
      {
        quoted_text: 'Team player with strong communication skills',
        category: 'buzzword',
        roast: "Sabko pata hai tu team player hai bhai, WhatsApp group mein bhi sabse zyada 'good morning' sticker tu hi bhejta hai na 😂",
        fix: 'Proof do: "Coordinated a 6-member cross-functional team to launch 3 client campaigns on time."',
        start_offset: 260, end_offset: 304, severity_rank: 3,
      },
      {
        quoted_text: 'Hardworking and dedicated professional',
        category: 'buzzword',
        roast: "Koi khud ko resume mein 'lazy and unmotivated' thodi likhega bhai 🙃 ye line har resume ka default setting hai, kuch bata nahi rahi.",
        fix: 'Delete this line entirely — replace the space with a real achievement instead.',
        start_offset: 308, end_offset: 346, severity_rank: 4,
      },
      {
        quoted_text: 'Assisted in achieving sales targets',
        category: 'no-metrics',
        roast: '"Assisted in" ka matlab kya hota hai bhai — tune target achieve kiya ya sirf paas khada tha jab dusro ne kiya? 👀',
        fix: '"Contributed to exceeding quarterly sales targets by 24%, personally closing 8 new accounts."',
        start_offset: 350, end_offset: 385, severity_rank: 5,
      },
      {
        quoted_text: 'Proficient in MS Office, hardworking, fast learner, good communication',
        category: 'buzzword',
        roast: "2024 mein 'MS Office proficient' likhna waise hi hai jaise likhna 'insaan hoon, saans leta hoon' 🫠 ye skill nahi hai bhai, ye basic survival hai.",
        fix: 'List actual relevant tools: "CRM: Salesforce, HubSpot · Excel: pivot tables, VLOOKUP · Canva for pitch decks".',
        start_offset: 400, end_offset: 470, severity_rank: 6,
      },
    ],
    strengths: [
      'Formatting clean hai aur ATS padh sakta hai, chalo ek cheez toh sahi hai 👍',
      'Company aur role clearly mentioned hai, confusion nahi hai kaam kya tha',
    ],
  },
  resumeInfo: {
    candidateName: 'ROHAN MEHTA',
    candidateTitle: 'BUSINESS DEVELOPMENT ASSOCIATE',
    experienceHeader: 'EXPERIENCE',
    companyLine: 'Zenith Solutions Pvt Ltd — Business Development Associate',
    bullet1Text: 'To work in a dynamic environment where I can utilize my skills and contribute to organizational growth.',
    bullet1Annotated: 'utilize my skills and contribute to organizational growth',
    bullet1Tag: 'GHISA-PITA OBJECTIVE',
    bullet2Text: 'Responsible for handling client relationships and achieving sales targets.',
    bullet2Annotated: 'handling client relationships',
    bullet2Tag: 'NUMBER GHAYAB HAI',
    bullet3Text: 'Team player with strong communication skills, hardworking, dedicated professional, proficient in MS Office.',
    bullet3Annotated: 'proficient in MS Office',
    bullet3Tag: 'BUZZWORD KA OVERDOSE',
  },
}

const priyaSharma: SampleResume = {
  roastData: {
    id: 'demo-roast-priya',
    overall_score: 26,
    band: 'weak',
    one_line_verdict: 'GitHub link bhi nahi aur React bhi likh di 😭',
    total_issues: 6,
    is_truncated: true,
    was_document_truncated: false,
    issues: [
      {
        quoted_text: 'Passionate software developer with excellent problem-solving skills',
        category: 'buzzword',
        roast: '"Passionate" aur "excellent" — ye toh LinkedIn bio se utha li lagti hai bhai 🤡 recruiter ko code dikha, feelings nahi.',
        fix: '"B.Tech CS, 3rd year. Built 4 full-stack projects with React + Node. 7.8 CGPA. Looking for backend-heavy SWE internship."',
        start_offset: 0, end_offset: 66, severity_rank: 1,
      },
      {
        quoted_text: 'Worked on a college project using React, Node.js, MongoDB, AWS, Docker, Redis',
        category: 'buzzword',
        roast: 'Itne saare tools ek "college project" mein? 👀 Har ek ka actual use batao — warna lagta hai ye tech stack Wikipedia se copy kiya hai.',
        fix: '"Built a hostel room-booking app (React frontend, Node.js REST API, MongoDB Atlas) — deployed on AWS EC2, live at priya.dev."',
        start_offset: 120, end_offset: 196, severity_rank: 2,
      },
      {
        quoted_text: 'Improved the performance of the application',
        category: 'no-metrics',
        roast: 'Improved kaise? Kitna? 5ms ya 500ms? Bina number ke ye line sirf poem hai bhai, achievement nahi 📝',
        fix: '"Reduced API response time from 1.2s to 340ms by adding Redis caching for frequently queried endpoints."',
        start_offset: 250, end_offset: 293, severity_rank: 3,
      },
      {
        quoted_text: 'Developed a machine learning model for sentiment analysis',
        category: 'no-metrics',
        roast: '"Developed a model" — accuracy kitni thi bhai? Recruiter ko result chahiye, method nahi 😬',
        fix: '"Fine-tuned BERT for Twitter sentiment classification — 87.4% F1 score on held-out test set."',
        start_offset: 310, end_offset: 365, severity_rank: 4,
      },
      {
        quoted_text: 'Participated in various hackathons and coding competitions',
        category: 'no-metrics',
        roast: '"Participated in various" — bhai participation trophy nahi chahiye, result batao 🏆 jeet kuch tha ya sirf gaye the?',
        fix: '"Top 15 of 380 teams, Smart India Hackathon 2023 (fintech track). 3× LeetCode contest top-500 finish."',
        start_offset: 420, end_offset: 477, severity_rank: 5,
      },
      {
        quoted_text: 'Hobbies: Cooking, Travelling, Listening to music',
        category: 'irrelevant',
        roast: 'Bhai biodata thodi hai 😅 cooking aur travelling se SWE internship nahi milti, ye space GitHub links mein use karo.',
        fix: 'Hobbies section hatao. Space ko live GitHub links ya open-source contributions se bharo.',
        start_offset: 540, end_offset: 589, severity_rank: 6,
      },
    ],
    strengths: [
      'Tech stack relevant hai aur modern tools explore kiye hain 🔥',
      'Education section clean hai aur CGPA clearly mentioned hai 🎓',
    ],
  },
  resumeInfo: {
    candidateName: 'PRIYA SHARMA',
    candidateTitle: 'B.TECH CS — SOFTWARE DEVELOPER',
    experienceHeader: 'PROJECTS',
    companyLine: 'Hostel Booking App — React · Node.js · MongoDB',
    bullet1Text: 'Passionate software developer with excellent problem-solving skills and strong communication.',
    bullet1Annotated: 'Passionate software developer with excellent problem-solving skills',
    bullet1Tag: 'LINKEDIN BIO COPY-PASTE',
    bullet2Text: 'Worked on a college project using React, Node.js, MongoDB, AWS, Docker, Redis, and GraphQL.',
    bullet2Annotated: 'React, Node.js, MongoDB, AWS, Docker, Redis',
    bullet2Tag: 'TECH STACK STUFFING',
    bullet3Text: 'Improved the performance of the application and participated in various hackathons.',
    bullet3Annotated: 'Improved the performance of the application',
    bullet3Tag: 'NUMBER BILKUL NAHI',
  },
}

const amanVerma: SampleResume = {
  roastData: {
    id: 'demo-roast-aman',
    overall_score: 19,
    band: 'weak',
    one_line_verdict: 'Bhai ye resume hai ya annual report ka summary? 📊',
    total_issues: 6,
    is_truncated: true,
    was_document_truncated: false,
    issues: [
      {
        quoted_text: 'Spearheaded synergistic cross-functional initiatives to drive holistic brand value',
        category: 'buzzword',
        roast: 'Itna bhari corporate jargon padh ke recruiter behosh ho jayega bhai 😵 "spearheaded synergistic" — real life mein koi aisa nahi bolta.',
        fix: '"Led GTM launch for 2 product lines across 4 cities — coordinated design, sales, and ops teams in a 6-week sprint."',
        start_offset: 80, end_offset: 160, severity_rank: 1,
      },
      {
        quoted_text: 'Managed end-to-end campaign lifecycle and stakeholder communications',
        category: 'no-metrics',
        roast: '"End-to-end" sun ke lagta hai kuch bada kiya, par bina data ke ye sirf English hai, achievement nahi 🗣️',
        fix: '"Managed 3 paid campaigns (Google + Meta) — tracked ROAS and CPA week-over-week, aligned with brand quarterly targets."',
        start_offset: 200, end_offset: 265, severity_rank: 2,
      },
      {
        quoted_text: 'Demonstrated exceptional leadership and strategic thinking',
        category: 'buzzword',
        roast: '"Exceptional leadership" — bhai ye award nahi tha, toh proof kahan hai? Recruiter aankh band kar ke nahi manega 🙃',
        fix: '"Led a team of 5 content creators; set weekly OKRs, ran retrospectives — reduced missed deadlines by 40%."',
        start_offset: 310, end_offset: 367, severity_rank: 3,
      },
      {
        quoted_text: 'Collaborated with internal and external stakeholders',
        category: 'buzzword',
        roast: 'Har resume mein "collaborated with stakeholders" aata hai bhai, tu bata kaun nahi karta yaar 😂 specific karo.',
        fix: '"Partnered with 3 agency vendors and 2 product managers to align campaign messaging — cut revision cycles from 5 to 2 rounds."',
        start_offset: 390, end_offset: 441, severity_rank: 4,
      },
      {
        quoted_text: 'Leveraged data-driven insights to optimize performance',
        category: 'no-metrics',
        roast: '"Data-driven insights" sun ke lagta hai kuch dekha, but koi number nahi — seedha bolo kya dekha aur kya change kiya 📉',
        fix: '"A/B tested 6 subject-line variants; winning variant lifted open rate from 18% to 31% across subscriber list."',
        start_offset: 460, end_offset: 514, severity_rank: 5,
      },
      {
        quoted_text: 'DECLARATION: I hereby declare that all information provided is true to the best of my knowledge.',
        category: 'irrelevant',
        roast: 'Bhai 2005 ka declaration kyu daal rakha hai? ✋ Ye line 15 saal pehle hi expire ho gayi, delete karo.',
        fix: 'Declaration section poora delete karo. Whitespace ko ek concrete campaign case study se bharo.',
        start_offset: 590, end_offset: 688, severity_rank: 6,
      },
    ],
    strengths: [
      'Career progression clear dikh rahi hai, promotions mentioned hain 📈',
      'Section headings standard hain, ATS ko parse karne mein dikkat nahi hogi 🎯',
    ],
  },
  resumeInfo: {
    candidateName: 'AMAN VERMA',
    candidateTitle: 'MARKETING MANAGER',
    experienceHeader: 'EXPERIENCE',
    companyLine: 'BrandEdge India Pvt Ltd — Marketing Manager',
    bullet1Text: 'Spearheaded synergistic cross-functional initiatives to drive holistic brand value.',
    bullet1Annotated: 'Spearheaded synergistic cross-functional initiatives',
    bullet1Tag: 'CORPORATE JARGON OVERDOSE',
    bullet2Text: 'Managed end-to-end campaign lifecycle and stakeholder communications.',
    bullet2Annotated: 'end-to-end campaign lifecycle',
    bullet2Tag: 'NUMBER GHAYAB HAI',
    bullet3Text: 'Demonstrated exceptional leadership and strategic thinking across all verticals.',
    bullet3Annotated: 'exceptional leadership and strategic thinking',
    bullet3Tag: 'PROOF KAHAN HAI BHAI',
  },
}

export const SAMPLE_RESUMES: SampleResume[] = [rohanMehta, priyaSharma, amanVerma]

export function getDailyRotationIndex(): number {
  const now = new Date()
  const start = new Date(now.getFullYear(), 0, 0)
  const diff = now.getTime() - start.getTime()
  const dayOfYear = Math.floor(diff / (1000 * 60 * 60 * 24))
  return dayOfYear % SAMPLE_RESUMES.length
}

export const SAMPLE_ROAST_DATA: ExtendedRoastResult = rohanMehta.roastData
export const SAMPLE_RESUME_INFO = rohanMehta.resumeInfo