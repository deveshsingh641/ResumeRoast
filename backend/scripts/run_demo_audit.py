import sys
import os
import json

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.stdout.reconfigure(encoding='utf-8')

from app.services.ai_analyzer import analyze_resume

DEMO_RESUMES = {
    "Devesh_Style_Fresher_2026": """
DEVESH SINGH
B.Tech Computer Science and Engineering (2022 – 2026) | CGPA: 8.4
Email: devesh@example.com | Phone: +91 9876543210 | GitHub: github.com/devesh | LinkedIn: linkedin.com/in/devesh

EXPERIENCE:
Thiranex — Full Stack Web Development Intern (Aug 2026 – Sep 2026)
- Developed responsive web interfaces using React.js, Tailwind CSS, and TypeScript for client projects.
- Optimized MongoDB aggregate queries, reducing query response times by 35% across 5 collections.
- Collaborated with senior engineering team to integrate RESTful API endpoints and fix frontend state bugs.

PROJECTS:
ResumeRoast — Savage AI Resume Roaster (July 2026)
- Built viral web application using FastAPI, React, and Google Gemini API that roasts resumes with Indian comedic persona.
- Implemented real-time streaming, Razorpay payment gateway integration, and PDF parody certificate generation.
- Achieved over 1,200 active users in the first week with zero downtime.

E-Commerce Microservices Platform (Jan 2026 – March 2026)
- Architected modular backend with Node.js, Express, and PostgreSQL with Docker containerization.
- Integrated Redis caching layer to handle product catalogue lookups with sub-50ms latency.

SKILLS:
Languages: Python, JavaScript, TypeScript, C++, SQL
Frameworks & Libraries: React, FastAPI, Node.js, Express, Tailwind CSS
Databases & Tools: PostgreSQL, MongoDB, Redis, Docker, Git, Linux
    """,

    "Experienced_Dev_Good_Metrics": """
ROHAN SHARMA
Senior Software Engineer | 4 Years Experience
Email: rohan@example.com | Phone: +91 9988776655

EXPERIENCE:
Zomato — SDE-2 (March 2024 – Present)
- Led migration of monolith checkout service to Go-based microservices handling 12,000 requests per second.
- Reduced p99 latency from 240ms to 45ms by introducing distributed Redis caching and query batching.
- Mentored 4 junior engineers on backend concurrency patterns and system design best practices.

Swiggy — SDE-1 (July 2022 – Feb 2024)
- Designed and shipped driver allocation algorithm improvement that cut idle driver wait times by 18%.
- Built automated fraud detection pipeline using Apache Kafka and PostgreSQL processing 2M events daily.

EDUCATION:
B.Tech Information Technology, NIT Trichy (2018 – 2022) | CGPA: 8.9

SKILLS:
Go, Java, Python, Kafka, Redis, PostgreSQL, Kubernetes, AWS, System Design
    """,

    "Weak_Buzzword_Heavy_Resume": """
ANIKET VERMA
Passionate, results-driven professional seeking challenging role in IT industry.
Email: aniket@example.com | Phone: +91 9123456789

OBJECTIVE:
Looking to leverage my synergistic skills and strong work ethic in a dynamic, fast-paced environment to maximize organizational value.

EXPERIENCE:
XYZ Tech Solutions — Software Engineer (2024 – 2025)
- Responsible for developing web applications and fixing various bugs as assigned by team lead.
- Worked closely with cross-functional teams to brainstorm innovative solutions and enhance user experience.
- Successfully delivered project milestones on time with utmost dedication.
- Utilized cutting-edge paradigms and best practices across the development lifecycle.

PROJECTS:
Portfolio Website:
- Created responsive personal website using HTML, CSS, and JavaScript.
Weather App:
- Developed weather application utilizing external weather API.

SKILLS:
C, C++, Java, Python, HTML, CSS, Problem Solving, Leadership, Team Player, Time Management
    """
}

def run():
    print("=" * 70)
    print("RUNNING DEMO RESUME AUDIT ON LIVE PIPELINE")
    print("=" * 70)

    for name, text in DEMO_RESUMES.items():
        print(f"\n---> Testing Profile: {name} (Length: {len(text)} chars)")
        try:
            result = analyze_resume(text, language="hi-IN")
            print(f"Overall Score: {result.get('overall_score')}/100 (Band: {result.get('band')})")
            print(f"One Line Verdict: {result.get('one_line_verdict')}")
            print(f"Issues Found ({len(result.get('issues', []))} total):")
            for i, iss in enumerate(result.get("issues", []), 1):
                print(f"  [{i}] Category: {iss.get('category')} | Badge: {iss.get('badge_label')}")
                print(f"      Quoted: \"{iss.get('quoted_text')}\"")
                print(f"      Roast:  \"{iss.get('roast')}\"")
                print(f"      Fix:    \"{iss.get('fix')}\"")
            print("Strengths:")
            for s in result.get("strengths", []):
                print(f"  - {s}")
        except Exception as e:
            print(f"ERROR analyzing {name}: {type(e).__name__}: {e}")

if __name__ == "__main__":
    run()
