import os
import sys
import re
from datetime import datetime

# Set up backend path and utf-8 output
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.stdout.reconfigure(encoding='utf-8')

from app.services.ai_analyzer import analyze_resume, _TEMPORAL_HALLUCINATION_REGEX

TEST_RESUMES = [
    {
        "id": "01_Fresher_Tier3_2026",
        "archetype": "Tier-3 College Fresher (2026 Batch)",
        "text": """
HARSHIT KUMAR
B.Tech in Computer Science & Engineering (2022 – 2026) | CGPA: 7.8
ABES Engineering College, Ghaziabad | Email: harshit.dev@gmail.com | GitHub: github.com/harshitk

TECHNICAL SKILLS:
Languages: Java, JavaScript, Python, SQL
Frontend: React.js, HTML5, CSS3, Tailwind CSS
Backend: Node.js, Express.js, REST APIs
Databases: MongoDB, MySQL
Tools: Git, GitHub, Postman, VS Code

PROJECTS:
Campus Connect — Student Collaboration Platform (Jan 2026 – Apr 2026)
- Built full-stack social portal connecting 800+ college students for peer-to-peer study groups.
- Implemented real-time chat with Socket.io and secure JWT authentication.
- Deployed frontend on Vercel and backend on Render with 99.5% uptime.

AlgoVisualizer — Interactive Algorithm Visualizer (Nov 2025 – Dec 2025)
- Created interactive visualization tool for sorting and graph algorithms in React.
- Used by 350+ batchmates during semester exam prep with positive feedback.

ACHIEVEMENTS:
- Solved 450+ Data Structures & Algorithms problems on LeetCode (Knight badge, Rating 1820).
- 2nd Runner Up at Smart India Hackathon internal college round among 40 teams.
"""
    },
    {
        "id": "02_Prospective_Grad_2027",
        "archetype": "3rd Year Student (Graduating 2027)",
        "text": """
PRIYA NAIR
B.Tech Electronics & Communication Engineering (2023 – 2027, Expected) | CGPA: 8.6
IIT Roorkee | Email: priya.nair@iitr.ac.in | LinkedIn: linkedin.com/in/priyanair

EXPERIENCE:
Summer Open Source Fellow — Layer5 (May 2026 – July 2026)
- Contributed to Meshery cloud native management plane in Go and React.
- Fixed 14 open GitHub issues and merged 6 PRs related to Kubernetes service mesh visualizer.
- Reduced UI bundle size by 12% by pruning unneeded dependencies.

PROJECTS:
DroneSense — Autonomous Drone Simulation (Aug 2025 – Nov 2025)
- Implemented computer vision obstacle detection pipeline in Python using OpenCV and YOLOv8.
- Processed real-time video stream at 38 FPS with 91% object classification accuracy.

SKILLS:
C++, Go, Python, Linux, Docker, Kubernetes, Git, OpenCV, ROS2
"""
    },
    {
        "id": "03_Lateral_Switch_Mech_to_IT",
        "archetype": "Mechanical Engineer to Software Switcher",
        "text": """
RAHUL DESHMUKH
Transitioning Mechanical Engineer to Backend Developer
Email: rahul.deshmukh@gmail.com | Phone: +91 9823456781 | Pune, Maharashtra

PROFESSIONAL EXPERIENCE:
Tata Motors — Mechanical Quality Engineer (Aug 2022 – Sep 2024)
- Inspected chassis welding quality and reduced assembly defect rate by 14% on passenger EV line.
- Automated daily defect tracking sheet using Python scripts, saving 4 hours of manual data entry weekly.

SELF-DIRECTED SOFTWARE PROJECTS:
Inventory Hub — SaaS Inventory Management API (Jan 2025 – May 2026)
- Designed and deployed robust REST API using Django REST Framework and PostgreSQL.
- Implemented Redis caching for product search queries, cutting response latency from 320ms to 45ms.
- Wrote 80+ unit tests with PyTest achieving 88% code test coverage.

EDUCATION:
B.E. Mechanical Engineering, Pune University (2018 – 2022) | First Class with Distinction

SKILLS:
Python, Django, FastAPI, PostgreSQL, Redis, Docker, Git, Linux, PyTest
"""
    },
    {
        "id": "04_Data_Science_ML",
        "archetype": "Data Scientist / ML Engineer",
        "text": """
AAYUSH VERMA
Data Scientist | 2 Years Experience
Email: aayush.ml@gmail.com | Bengaluru, Karnataka

WORK EXPERIENCE:
Fractal Analytics — Junior Data Scientist (July 2024 – Present)
- Developed customer churn prediction model using LightGBM and XGBoost across 450,000 retail accounts.
- Improved churn prediction recall by 23% compared to legacy baseline, preventing an estimated $120k ARR loss.
- Built automated feature store pipeline using Apache Spark and Databricks processing 5GB daily data.

PROJECTS:
RAG Document Chatbot (Nov 2025 – Feb 2026)
- Implemented Retrieval-Augmented Generation system using LangChain, ChromaDB, and Claude 3.5 Sonnet.
- Processed 1,000+ technical PDF documents with sub-2s query retrieval response time.

EDUCATION:
B.Tech Data Science, Manipal Institute of Technology (2020 – 2024) | CGPA: 8.7

SKILLS:
Python, PyTorch, Scikit-Learn, LightGBM, SQL, Spark, Databricks, LangChain, Docker, AWS
"""
    },
    {
        "id": "05_DevOps_Cloud",
        "archetype": "DevOps & Cloud Engineer",
        "text": """
KARTHIK SUNDARAM
DevOps / Platform Engineer | AWS Certified Solutions Architect
Email: karthik.s@gmail.com | Chennai, India

EXPERIENCE:
Freshworks — Cloud Operations Engineer (Jan 2024 – Present)
- Managed production Kubernetes clusters (EKS) hosting 60+ microservices with 99.98% service uptime.
- Optimized AWS cloud spend by auditing unused EBS volumes and reserved instances, saving $16,500 monthly.
- Built reusable Terraform modules reducing developer cloud environment spin-up time from 3 hours to 12 minutes.
- Configured Datadog dashboards and PagerDuty alert policies, decreasing MTTR by 35%.

SKILLS:
Kubernetes, Docker, Terraform, Helm, AWS (EKS, EC2, S3, RDS), GitHub Actions, Datadog, Python, Bash
"""
    },
    {
        "id": "06_Frontend_React_Next",
        "archetype": "Frontend Specialist (React / Next.js)",
        "text": """
SHREYA AGRAWAL
Frontend Engineer | 3 Years Experience
Email: shreya.frontend@gmail.com | Gurugram, India

EXPERIENCE:
Urban Company — Frontend Engineer (Oct 2023 – Present)
- Rebuilt customer booking funnel in Next.js 14 App Router, improving Google Lighthouse score from 44 to 94.
- Reduced Largest Contentful Paint (LCP) from 3.8s to 1.1s, boosting checkout conversion rate by 9.4%.
- Maintained internal design system library with 40+ accessible React components used across 5 web apps.

PROJECTS:
TypeCraft — Online Collaborative Markdown Editor (2025)
- Created browser-based real-time Markdown editor using Zustand, Tailwind, and WebSockets.
- Gained 2,400 monthly active users on ProductHunt launch.

SKILLS:
React.js, Next.js, TypeScript, JavaScript (ES6+), Tailwind CSS, Zustand, GraphQL, Webpack, Jest
"""
    },
    {
        "id": "07_Mobile_Flutter_Android",
        "archetype": "Mobile App Developer (Flutter / Kotlin)",
        "text": """
NIKHIL JOSHI
Mobile App Developer
Email: nikhil.apps@gmail.com | Noida, UP

EXPERIENCE:
Groww — Associate Mobile Developer (Aug 2024 – Present)
- Contributed to flagship investment app on Android using Kotlin, Jetpack Compose, and Coroutines.
- Decreased app crash-free user rate to 99.85% by refactoring background network sync logic.
- Implemented biometrics authentication and QR code payment flow supporting UPI transactions.

PROJECTS:
HabitFlow — Minimal Habit Tracker (Google Play Store)
- Published solo Flutter app with over 45,000 organic downloads and 4.6 star rating across 850 reviews.
- Integrated RevenueCat in-app subscriptions generating $400/month recurring side income.

SKILLS:
Kotlin, Java, Flutter, Dart, Jetpack Compose, Coroutines, MVVM, SQLite, Firebase, REST APIs
"""
    },
    {
        "id": "08_Student_With_Gap_Year",
        "archetype": "Student with Preparation Gap Year",
        "text": """
SACHIN PATEL
B.Tech Information Technology (2021 – 2026) | CGPA: 7.2
Email: sachin.p@gmail.com | Ahmedabad, Gujarat

EDUCATION:
- B.Tech IT, Nirma University (2021 – 2026)
- Note: Took a 1-year academic gap (2022-2023) due to personal family health emergency. Resumed and completed coursework with 8.1 SGPA in final year.

EXPERIENCE:
CodeCraft Technologies — Web Development Intern (May 2025 – July 2025)
- Assisted backend team in writing unit tests for payment integration using Node.js and Jest.
- Fixed 18 reported UI responsiveness bugs across mobile viewports.

PROJECTS:
BookMyRoom — Hostel Booking Portal (2025 – 2026)
- Built student room booking portal using PHP, MySQL, and Bootstrap.
- Used by 250 students during college semester room allocation.

SKILLS:
C++, PHP, MySQL, JavaScript, HTML, CSS, Git
"""
    },
    {
        "id": "09_Cybersecurity_Pentester",
        "archetype": "Cybersecurity / Security Analyst",
        "text": """
ADITYA RAO
Information Security Analyst | CEH Certified
Email: aditya.sec@gmail.com | Hyderabad, Telangana

EXPERIENCE:
KPMG India — Cyber Security Analyst (Sept 2024 – Present)
- Conducted Web Application Penetration Testing (WAPT) for 15+ banking and fintech client applications.
- Identified 42 high and critical vulnerabilities including IDOR, SQL Injection, and Broken Object Level Auth.
- Formatted executive audit reports and remediation guidelines enabling 100% resolution before RBI audits.

INDEPENDENT SECURITY RESEARCH:
- Acknowledged in responsible disclosure Hall of Fame by Sony and Dutch Government for reporting sub-domain takeovers.
- Active HackerOne researcher with 600+ reputation points.

SKILLS:
Burp Suite, OWASP Top 10, Nmap, Wireshark, Metasploit, Python scripting, Linux, Bash
"""
    },
    {
        "id": "10_Academic_High_CGPA",
        "archetype": "Academic High CGPA Researcher",
        "text": """
POOJA KRISHNAN
B.Tech + M.Tech Dual Degree in Computer Science (2021 – 2026) | CGPA: 9.82 / 10.0
Institute Gold Medalist | Email: poojak@iitb.ac.in | Mumbai

RESEARCH PUBLICATIONS:
- "Optimizing Graph Neural Networks for Large-Scale Molecular Property Prediction" — Accepted at IEEE Transactions on Neural Networks 2026.
- "Comparative Analysis of Attention Mechanisms in Low-Resource Indic NLP" — Co-authored paper presented at ICON 2025.

ACADEMIC PROJECTS:
Parallel Graph Algorithms on GPU (2025):
- Implemented CUDA C++ parallel Breadth-First Search achieving 6.5x speedup over single-threaded OpenMP baseline.

TEACHING ASSISTANTSHIP:
- Teaching Assistant for CS210 Data Structures & Algorithms, mentoring batch of 120 undergraduate students.

SKILLS:
C, C++, CUDA, Python, PyTorch, LaTeX, MATLAB, Algorithms, Discrete Mathematics
"""
    },
    {
        "id": "11_Worst_Buzzword_Heavy",
        "archetype": "Pure Buzzword Overload (No Metrics)",
        "text": """
VIKAS SHUKLA
Dynamic, self-motivated software professional with proven track record of excellence.
Email: vikas@example.com | Phone: +91 9999999999

CAREER OBJECTIVE:
To obtain a challenging and rewarding position in a prestigious organization where I can utilize my extensive knowledge, unparalleled dedication, and synergistic abilities to contribute towards the organizational mission and vision.

EXPERIENCE:
Global Tech Innovations — Software Engineer (2023 – 2025)
- Responsible for full software development lifecycle from conceptualization to deployment.
- Actively participated in daily agile standups and sprint planning sessions with cross-functional leadership.
- Successfully implemented cutting-edge features to enhance client satisfaction and user delight.
- Worked hard and went above and beyond to ensure zero defects in production releases.
- Fostered teamwork and seamless collaboration among multidisciplinary stakeholders.

SKILLS:
Java, Python, C++, Excellent Communication, Fast Learner, Leadership, Multitasking, Hardworking
"""
    },
    {
        "id": "12_Staff_Architect_10Yrs",
        "archetype": "Staff Engineer / Architect (10+ Yrs Exp)",
        "text": """
SUMIT BANERJEE
Staff Software Engineer / Distributed Systems Architect
Email: sumit.banerjee@gmail.com | Bengaluru, India

EXPERIENCE:
Walmart Global Tech — Staff Software Engineer (March 2021 – Present)
- Principal architect for global inventory replenishment engine processing $3.2B annual GMV.
- Migrated legacy Java monolith to event-driven Kafka and Cassandra architecture across 4 global regions.
- Reduced end-to-end order processing latency from 45 seconds to 1.8 seconds at peak Black Friday traffic (85,000 req/s).
- Filed 2 US patents on predictive stock-out prevention algorithms.
- Led technical design reviews for an engineering organization of 85+ developers.

Flipkart — Principal Engineer (July 2016 – Feb 2021)
- Designed flash-sale queue management system serving 180,000 concurrent checkouts during Big Billion Days.
- Spearheaded company-wide adoption of gRPC and Protocol Buffers, cutting internal network payload sizes by 40%.

SKILLS:
System Design, Distributed Systems, Java, Go, Apache Kafka, Cassandra, Kubernetes, GCP, Architecture
"""
    },
    {
        "id": "13_Freelancer_Contractor",
        "archetype": "Full-Time Freelancer & Contractor",
        "text": """
DEEPESH CHOPRA
Full Stack Freelance Developer | Upwork Top Rated Plus (100% Job Success Score)
Email: deepesh.freelance@gmail.com | Delhi, India

EXPERIENCE:
Independent Freelance Software Developer (Jan 2023 – Present)
- Completed 38 custom web development contracts for international clients in US, UK, and Australia with 5.0 star feedback.
- Generated over $55,000 in freelance revenue across 3 years on Upwork platform.
- Built custom Shopify and WooCommerce headless storefronts using Next.js and Stripe API.
- Migrated 12 legacy WordPress websites to modern headless stacks, improving average page load speed by 2.4x.

PROJECT HIGHLIGHTS:
FitPulse App — Fitness Coaching Web App (2025)
- Contract project built for UK fitness startup handling 3,200 paying monthly subscribers with Stripe billing.

SKILLS:
Next.js, React, Node.js, Express, PostgreSQL, Stripe API, Tailwind CSS, Shopify API, WordPress, Supabase
"""
    },
    {
        "id": "14_AI_Wrapper_Builder",
        "archetype": "Indie Hacker / AI Product Builder",
        "text": """
MANISH AGARWAL
Full Stack AI Product Engineer
Email: manish.ai@gmail.com | Bengaluru | X/Twitter: @manish_builds

PROJECTS & PRODUCTS:
DocuSummary AI — PDF AI Assistant (Built & Launched Nov 2025 – Present)
- Solo-developed SaaS tool that extracts structured summaries and answers questions from legal contracts using GPT-4o.
- Scaled to 8,500 registered users and $1,800 Monthly Recurring Revenue (MRR) within 4 months of launch.
- Implemented vector similarity search with pgvector and OpenAI text-embedding-3-small on Supabase.
- Built background document processing queue using Celery and Redis to handle 50-page PDF uploads seamlessly.

VoiceNotes AI — Speech to Text Action Items (June 2025 – Oct 2025)
- Built iOS/Web transcription utility using Whisper API and FastAPI with 1,200 active weekly users.

SKILLS:
Python, FastAPI, Next.js, TypeScript, OpenAI API, LangChain, Supabase, pgvector, Redis, Celery, Stripe
"""
    }
]

def run_stress_test():
    print("=" * 80)
    print(f"STRESS TESTING 14 DIVERSE REAL-WORLD RESUMES THROUGH AI ANALYZER PIPELINE")
    print(f"Current Date Context: {datetime.now().strftime('%B %Y')}")
    print("=" * 80)

    results = []
    hallucination_detected = False

    for idx, r in enumerate(TEST_RESUMES, 1):
        resume_id = r["id"]
        archetype = r["archetype"]
        text = r["text"].strip()
        print(f"\n[{idx}/14] Testing: {archetype} ({resume_id}) ...")

        try:
            res = analyze_resume(text, language="hi-IN")
            score = res.get("overall_score")
            band = res.get("band")
            verdict = res.get("one_line_verdict", "")
            issues = res.get("issues", [])
            strengths = res.get("strengths", [])

            # --- CHECKS ---
            errors = []
            
            # 1. Temporal Hallucination Check in Verdict
            if _TEMPORAL_HALLUCINATION_REGEX.search(verdict):
                errors.append(f"Verdict contains temporal hallucination: '{verdict}'")
                hallucination_detected = True

            # 2. Check each issue
            for i_idx, iss in enumerate(issues, 1):
                roast = iss.get("roast", "")
                badge = iss.get("badge_label", "")
                quoted = iss.get("quoted_text", "")
                category = iss.get("category", "")

                # Check temporal hallucination in roast
                if _TEMPORAL_HALLUCINATION_REGEX.search(roast) or _TEMPORAL_HALLUCINATION_REGEX.search(badge):
                    errors.append(f"Issue {i_idx} has temporal hallucination: '{badge}' - '{roast}'")
                    hallucination_detected = True

                # Check false no-metrics
                if category == "no-metrics":
                    if re.search(r"\d", quoted) or "%" in quoted:
                        errors.append(f"Issue {i_idx} false no-metrics on quoted text: '{quoted}'")

                # Check that quoted text actually exists in resume text
                if quoted and quoted not in text:
                    # check normalized whitespace
                    norm_quoted = " ".join(quoted.split())
                    norm_text = " ".join(text.split())
                    if norm_quoted not in norm_text:
                        errors.append(f"Issue {i_idx} quoted text not found in resume: '{quoted}'")

            # 3. Check score band calibration
            if band == "weak" and score > 45:
                errors.append(f"Score {score} flagged as weak (should be mid/strong)")
            elif band == "strong" and score < 65:
                errors.append(f"Score {score} flagged as strong (should be mid/weak)")

            status = "PASS" if not errors else "FAIL"
            print(f"      Score: {score}/100 ({band}) | Issues: {len(issues)} | Strengths: {len(strengths)}")
            print(f"      Verdict: \"{verdict}\"")
            if errors:
                for err in errors:
                    print(f"      [ERROR] {err}")
            else:
                print(f"      [OK] All checks passed cleanly.")

            results.append({
                "id": resume_id,
                "archetype": archetype,
                "score": score,
                "band": band,
                "verdict": verdict,
                "issues_count": len(issues),
                "status": status,
                "errors": errors
            })

        except Exception as e:
            print(f"      [FATAL ERROR] {type(e).__name__}: {e}")
            results.append({
                "id": resume_id,
                "archetype": archetype,
                "score": None,
                "band": None,
                "verdict": None,
                "issues_count": 0,
                "status": "CRASH",
                "errors": [str(e)]
            })

    # Summary Table
    print("\n" + "=" * 80)
    print("STRESS TEST SUMMARY REPORT")
    print("=" * 80)
    print(f"{'#':<3} | {'Archetype':<32} | {'Score':<6} | {'Band':<7} | {'Issues':<6} | {'Status'}")
    print("-" * 80)
    passed_count = sum(1 for r in results if r["status"] == "PASS")
    for idx, r in enumerate(results, 1):
        score_str = str(r["score"]) if r["score"] is not None else "N/A"
        band_str = str(r["band"]) if r["band"] is not None else "N/A"
        print(f"{idx:<3} | {r['archetype'][:32]:<32} | {score_str:<6} | {band_str:<7} | {r['issues_count']:<6} | {r['status']}")

    print("=" * 80)
    print(f"Final Result: {passed_count}/{len(results)} Profiles PASSED")
    if hallucination_detected:
        print("[CRITICAL WARNING] Temporal Hallucinations were detected in one or more outputs!")
    else:
        print("[SUCCESS] ZERO Temporal Hallucinations detected across all profiles!")
    print("=" * 80)

if __name__ == "__main__":
    run_stress_test()
