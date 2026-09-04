"""
Standing Automated Regression Test Suite:
Guards against the "Everyone Gets the Same Roast" production incident.
Simulates concurrent and sequential uploads of 15+ genuinely diverse resumes across formats (PDF, DOCX) and industries.
Asserts:
1. Strict Grounding: 100% of quoted_text entries are genuine substrings of that specific request's resume text.
2. Uniqueness: No two different resumes produce identical (overall_score, one_line_verdict) pairs or identical issues arrays.
3. Score Diversity: Scores vary across the batch reflecting document content, not locked to static score 38.
4. Concurrency Isolation: High-concurrency burst traffic exhibits zero cross-request contamination or quote leakage.
"""
import concurrent.futures
import io
import json
import unittest
from docx import Document
from reportlab.pdfgen import canvas
from fastapi.testclient import TestClient

from app.main import app
from app.db import database


SAMPLE_RESUMES = [
    {
        "role": "Frontend Developer",
        "format": "pdf",
        "text": """Alex Johnson - Senior Frontend Engineer
alex.johnson@email.com | 555-0101 | San Francisco, CA

PROFESSIONAL SUMMARY
Frontend Engineer with 6 years of experience building modern web apps in React, TypeScript, Next.js.

EXPERIENCE
Senior Frontend Developer at TechCorp (2022 - Present)
- Responsible for building reusable UI components and collaborating across teams.
- Leveraged synergistic paradigms to accelerate core business outcomes.
- Implemented state management using Redux Toolkit and React Query.
- Built design system components in Storybook.

Frontend Developer at WebSolutions (2018 - 2022)
- Developed responsive web interfaces using React, CSS Modules, and webpack.
- Participated in daily standups and sprint planning meetings.
- Assisted backend team with REST API integrations.

EDUCATION
B.S. Computer Science, UC Berkeley, 2018

SKILLS
React, TypeScript, JavaScript, HTML5, CSS3, Tailwind, Redux, Storybook
"""
    },
    {
        "role": "Financial Analyst",
        "format": "docx",
        "text": """Sarah Miller - Financial Analyst
sarah.m@financehub.com | New York, NY

OBJECTIVE
Experienced financial analyst specializing in equity research, valuation, and forecasting.

WORK HISTORY
Investment Analyst at Alpha Capital (2020 - 2024)
- Conducted discounted cash flow (DCF) modeling for 45 tech and healthcare stocks.
- Analyzed quarterly 10-K and 10-Q SEC filings for portfolio managers.
- Prepared comprehensive financial models predicting earnings per share variance.
- Monitored macroeconomic indicators including inflation and interest rates.

Junior Financial Analyst at Metro Bank (2018 - 2020)
- Performed variance analysis on monthly departmental operational budgets.
- Automated financial reconciliation reports in Excel VBA.
- Reconciled ledger accounts and presented findings to senior audit teams.

EDUCATION & CERTIFICATIONS
CFA Charterholder (2021)
B.S. in Finance, NYU Stern School of Business (2018)

SKILLS
Financial Modeling, DCF Valuation, Bloomberg Terminal, Excel VBA, Capital IQ
"""
    },
    {
        "role": "Registered Nurse",
        "format": "pdf",
        "text": """Emily Davis, BSN, RN
emily.davis@medcare.org | Chicago, IL

CLINICAL EXPERIENCE
Emergency Room Staff Nurse at City Memorial Hospital (2019 - Present)
- Triage acute emergency department patients using the Emergency Severity Index.
- Administer IV medications, blood products, and emergency interventions.
- Collaborate with attending physicians and trauma surgeons during resuscitations.
- Maintain electronic health records via Epic system while complying with HIPAA.

Medical-Surgical Nurse at Mercy Health (2017 - 2019)
- Managed bedside clinical care for up to 6 postoperative patients per shift.
- Coordinated patient discharge planning and family medication education.
- Documented wound care staging and monitored central line dressings.

EDUCATION & LICENSES
Registered Nurse License #RN-992813
B.S. in Nursing, University of Illinois at Chicago (2017)
BLS, ACLS, and PALS Certified
"""
    },
    {
        "role": "Executive Chef",
        "format": "docx",
        "text": """Marcus Aurelio - Executive Chef
chef.marcus@bistro.com | New Orleans, LA

CULINARY LEADERSHIP
Executive Chef at Le Bistro Moderne (2021 - Present)
- Designed seasonal French-Creole tasting menus featuring farm-to-table ingredients.
- Supervised kitchen brigade of 14 cooks, dishwashers, and sous chefs.
- Controlled food and beverage cost percentage within strict seasonal margins.
- Sourced artisanal produce directly from regional Louisiana agricultural cooperatives.

Head Sous Chef at Grand Hotel Palace (2017 - 2021)
- Managed inventory ordering, butchery fabrication, and sauce production.
- Enforced HACCP food safety standards across banquet and à la carte kitchens.
- Trained culinary apprentices on classic knife techniques and brigade workflow.

CERTIFICATIONS & EDUCATION
Culinary Institute of America, Associate in Culinary Arts (2016)
ServSafe Food Protection Manager Certification
"""
    },
    {
        "role": "Corporate Attorney",
        "format": "pdf",
        "text": """David Vance, Esq. - Corporate Counsel
david.vance@legalpartners.com | Boston, MA

LEGAL PRACTICE
Corporate Associate at Sterling & Sterling LLP (2020 - Present)
- Drafted and negotiated commercial agreements including master service agreements, SaaS licensing, and vendor NDAs.
- Advised early-stage startup clients on Delaware corporate formation and governance.
- Conducted legal due diligence reviews for cross-border merger transactions.
- Assessed regulatory compliance under federal consumer protection statutes.

Judicial Law Clerk at Massachusetts Superior Court (2018 - 2020)
- Researched statutory interpretation and drafted judicial memoranda for presiding justice.
- Reviewed summary judgment motions in complex commercial disputes.

BAR ADMISSIONS & EDUCATION
Admitted to Massachusetts Bar (2018)
J.D., Harvard Law School, cum laude (2018)
B.A. in Political Science, Amherst College (2015)
"""
    },
    {
        "role": "Civil Engineer",
        "format": "docx",
        "text": """Carlos Rodriguez, PE - Senior Structural Engineer
carlos.r@structuretech.com | Austin, TX

PROFESSIONAL PROFILE
Licensed Professional Engineer specializing in reinforced concrete and steel building design.

WORK HISTORY
Project Structural Engineer at Apex Infrastructure (2019 - Present)
- Performed seismic and wind load analysis using ETABS and SAP2000 for mid-rise towers.
- Prepared comprehensive structural calculation packages submitted to municipal permit offices.
- Conducted on-site foundation concrete pour inspections and rebar placement verification.
- Coordinated BIM structural framing models with MEP consultants via Revit.

Structural EIT at Texas Bridge Consultants (2016 - 2019)
- Evaluated bridge deck load ratings and fatigue stresses under AASHTO specifications.
- Inspected substructure pier caps for shear cracking and spalling damage.

CREDENTIALS & EDUCATION
Professional Engineer (PE) License #TX-88371
M.S. in Civil Engineering, UT Austin (2016)
B.S. in Civil Engineering, Texas A&M University (2014)
"""
    },
    {
        "role": "Digital Marketing Strategist",
        "format": "pdf",
        "text": """Chloe Dupont - Digital Marketing Specialist
chloe@brandboost.io | Seattle, WA

SUMMARY
Results-oriented digital marketer with background in paid acquisition, SEO, and email lifecycle campaigns.

EXPERIENCE
Growth Marketing Manager at Nimbus SaaS (2022 - Present)
- Managed paid search and social campaigns across Google Ads, LinkedIn, and Meta Ads.
- Conducted multi-variant A/B testing on landing page headlines and signup funnels.
- Orchestrated automated email onboarding drip series in Klaviyo and HubSpot.
- Tracked campaign attribution and customer lifetime value using Google Analytics 4.

Content Marketing Coordinator at Peak Media (2019 - 2022)
- Authored technical blog articles optimizing target keyword rankings on SERPs.
- Produced quarterly industry benchmark PDF whitepapers to generate inbound MQLs.
- Managed editorial calendar and social media distribution.

SKILLS
Google Ads, Meta Business Suite, GA4, HubSpot, Klaviyo, Ahrefs, SEMrush, Copywriting
"""
    },
    {
        "role": "High School Physics Teacher",
        "format": "docx",
        "text": """Dr. Nathan Green - Physics Educator
nathan.green@oakridge.edu | Denver, CO

TEACHING PHILOSOPHY
Dedicated educator fostering scientific inquiry, problem-solving, and laboratory experimentation.

TEACHING EXPERIENCE
AP Physics Teacher at Oakridge High School (2019 - Present)
- Taught AP Physics 1 and C Mechanics curriculum to junior and senior cohorts.
- Designed hands-on inquiry laboratory experiments exploring rotational dynamics and optics.
- Differentiated lesson delivery for diverse learning accommodations and IEP guidelines.
- Mentored competitive robotics club team for FIRST Tech Challenge championships.

Science Teacher at West Pines Middle School (2016 - 2019)
- Introduced introductory physical science fundamentals through interactive STEM demonstrations.
- Organized annual regional middle school science fair exhibition.

EDUCATION & LICENSURE
Ph.D. in Applied Physics, University of Colorado Boulder (2016)
Colorado State Teaching License (Secondary Science 7-12)
"""
    },
    {
        "role": "DevOps / Site Reliability Engineer",
        "format": "pdf",
        "text": """Priya Sharma - Senior SRE / Cloud Platform Engineer
priya.cloud@infraeng.net | San Jose, CA

INFRASTRUCTURE EXPERTISE
Site Reliability Engineer focusing on Kubernetes multi-cluster orchestration, Terraform IaC, and observability.

PROFESSIONAL EXPERIENCE
Senior Infrastructure Engineer at CloudScale Systems (2021 - Present)
- Architected production EKS clusters spanning multiple AWS availability zones.
- Provisioned immutable infrastructure utilizing Terraform modules and GitOps pipelines in ArgoCD.
- Configured Prometheus alerting rules and Grafana dashboards for cluster health monitoring.
- Facilitated blameless post-mortem reviews following incident severity triages.

Cloud Operations Engineer at DataStream Inc (2018 - 2021)
- Maintained Docker container images and pushed artifacts to secure registry.
- Migrated legacy on-premise relational databases to AWS RDS PostgreSQL.
- Implemented automated secret rotation using HashiCorp Vault.

TECHNICAL ARSENAL
Kubernetes, Docker, Terraform, AWS, Prometheus, Grafana, ArgoCD, Linux, Python, Bash, Helm
"""
    },
    {
        "role": "UI/UX Product Designer",
        "format": "docx",
        "text": """Elena Rostova - Senior Product Designer
elena@designcraft.studio | Brooklyn, NY

DESIGN STATEMENT
Product designer passionate about intuitive design systems, typography hierarchy, and accessibility standards.

EXPERIENCE
Senior Product Designer at FinTech Studio (2021 - Present)
- Led end-to-end design lifecycle for iOS and Android mobile investment applications.
- Facilitated qualitative user interviews and usability testing sessions with active investors.
- Maintained comprehensive design token architecture within Figma components library.
- Partnered with mobile engineering team to inspect front-end UI fidelity against specs.

UI Designer at Creative Spark (2018 - 2021)
- Created responsive website wireframes, interactive prototypes, and iconography.
- Executed visual brand identity redesigns for commercial clients.

TOOLS & METHODOLOGIES
Figma, FigJam, Protopie, Adobe Creative Suite, Design Systems, User Research, Wireframing
"""
    },
    {
        "role": "Supply Chain & Logistics Specialist",
        "format": "pdf",
        "text": """Robert Chen - Logistics Operations Manager
robert.chen@freightflow.org | Long Beach, CA

LOGISTICS LEADERSHIP
Logistics professional with expertise in international container freight forwarding, customs clearance, and warehouse management.

CAREER BACKGROUND
Operations Manager at Pacific Freight Logistics (2020 - Present)
- Coordinated drayage trucking schedules and intermodal rail dispatching for ocean container cargo.
- Audited commercial invoices, packing lists, and bills of lading to ensure US Customs compliance.
- Monitored warehouse pallet racking turnover and pick-pack inventory accuracy.
- Negotiated contract freight rates with carrier steamship lines and terminal operators.

Logistics Coordinator at Global Forwarding Ltd (2017 - 2020)
- Tracked inbound ocean shipments and resolved customs clearance inspection delays.
- Generated warehouse receiving reports and shipping manifests in SAP WMS.

EDUCATION
B.S. in Supply Chain Management, California State University Long Beach (2017)
APICS CSCP Certification
"""
    },
    {
        "role": "Veterinarian",
        "format": "docx",
        "text": """Dr. Hannah Abbott, DVM - Small Animal Veterinarian
dr.abbott@companioncare.vet | Portland, OR

CLINICAL VETERINARY MEDICINE
Compassionate companion animal veterinarian dedicated to preventative health, soft tissue surgery, and emergency triage.

PROFESSIONAL EXPERIENCE
Associate Veterinarian at Companion Animal Hospital (2019 - Present)
- Performed routine wellness examinations, vaccinations, and diagnostic blood panels for canines and felines.
- Conducted soft tissue surgeries including ovariohysterectomies, dental extractions, and mass excisions.
- Interpreted digital dental radiography, thoracic X-rays, and in-house abdominal ultrasound imaging.
- Counseled pet owners regarding chronic disease management plans such as feline diabetes and renal failure.

Veterinary Intern at Metro Pet Emergency Clinic (2018 - 2019)
- Managed acute emergency admissions involving toxic ingestion, trauma, and foreign body obstructions.
- Monitored critically ill hospitalized patients in intensive care unit.

EDUCATION & LICENSING
Doctor of Veterinary Medicine (DVM), Oregon State University (2018)
USDA Accredited Veterinarian
"""
    },
    {
        "role": "High School Student (Short Resume)",
        "format": "pdf",
        "text": """Timmy Nelson
timmy.nelson@school.edu | Columbus, OH

EDUCATION
Oak Creek High School - Expected Graduation May 2026
GPA: 3.8 / 4.0

EXPERIENCE
Library Volunteer (2024 - Present)
- Assisted library staff with shelving returned books and organizing reading sections.
- Helped elementary students select reading materials during weekend book clubs.

Lawn Mowing & Yard Care (2023 - 2024)
- Provided neighborhood lawn mowing, weeding, and leaf raking services.

ACTIVITIES
- High School Chess Club Member
- Track and Field Team (100m sprint)
"""
    },
    {
        "role": "Seasoned Aerospace Systems Architect (Long Resume)",
        "format": "docx",
        "text": """Arthur Pendelton, PhD - Principal Aerospace Systems Engineer
arthur.pendelton@aerosys.com | Huntsville, AL

EXECUTIVE SUMMARY
Thirty years of systems engineering leadership across defense, satellite launch systems, and hypersonic aerodynamic vehicles.

PROFESSIONAL EXPERIENCE
Principal Systems Architect at Orbital Defense Dynamics (2015 - Present)
- Directed the end-to-end mission requirements architecture for next-generation orbital tracking satellites.
- Authored critical subsystem specifications governing thermal protection tiles, guidance telemetry, and avionics bus interfaces.
- Chaired formal preliminary design reviews (PDR) and critical design reviews (CDR) alongside DoD stakeholders.
- Modeled orbital debris collision mitigation protocols adhering to NASA and ESA standards.

Senior Propulsion Engineer at AeroTech Industries (2002 - 2015)
- Supervised cryogenic turbopump testing campaigns for liquid oxygen and rocket propellant stages.
- Evaluated combustion chamber acoustic resonance instabilities using computational fluid dynamics simulations.
- Managed technical milestones for multi-million dollar defense contract deliverables.

Propulsion Specialist at National Launch Laboratories (1994 - 2002)
- Analyzed solid rocket motor nozzle throat erosion rates during static hot-fire testing.
- Formulated propellant grain geometry variations to optimize boost thrust curves.

ACADEMIC CREDENTIALS
Ph.D. in Aerospace Engineering, Georgia Institute of Technology (1994)
M.S. in Mechanical Engineering, Purdue University (1990)
B.S. in Aeronautical Engineering, Purdue University (1988)
AIAA Associate Fellow
"""
    },
    {
        "role": "Cybersecurity Penetration Tester",
        "format": "pdf",
        "text": """Lucas Black, OSCP - Senior Security Consultant
lucas.black@redteamsec.io | Austin, TX

OFFENSIVE SECURITY PROFILE
Offensive security specialist focused on network penetration testing, Active Directory exploitation, and web application assessments.

ENGAGEMENT HISTORY
Senior Penetration Tester at RedTeam Consulting (2021 - Present)
- Executed black-box and grey-box network penetration assessments across Fortune 500 corporate infrastructures.
- Discovered critical vulnerabilities including remote code execution, SQL injection, and deserialization flaws.
- Compromised enterprise Active Directory environments through Kerberoasting, AS-REP roasting, and pass-the-hash attacks.
- Authored detailed remediation reports presenting risk ratings to executive CISOs and engineering leads.

Information Security Analyst at CyberGuard Defense (2018 - 2021)
- Triaged security events and suspicious endpoint activities within Splunk SIEM platform.
- Developed custom detection rules to identify unauthorized command execution via PowerShell.

CERTIFICATIONS
Offensive Security Certified Professional (OSCP)
Certified Information Systems Security Professional (CISSP)
eLearnSecurity Web application Penetration Tester (eWPT)
"""
    },
]


def _build_pdf(text: str) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    y = 800
    for line in text.strip().splitlines():
        if not line.strip():
            y -= 12
            continue
        c.drawString(40, y, line[:90])
        y -= 14
        if y < 40:
            c.showPage()
            y = 800
    c.save()
    return buf.getvalue()


def _build_docx(text: str) -> bytes:
    doc = Document()
    for line in text.strip().splitlines():
        doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


class TestAuditIdenticalRoastRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prepared = []
        for item in SAMPLE_RESUMES:
            fmt = item["format"]
            filename = f"{item['role'].lower().replace(' ', '_').replace('/', '_')}.{fmt}"
            file_bytes = _build_pdf(item["text"]) if fmt == "pdf" else _build_docx(item["text"])
            cls.prepared.append({
                "role": item["role"],
                "filename": filename,
                "bytes": file_bytes,
                "text": item["text"],
            })

    def setUp(self):
        self.client = TestClient(app)
        database._memory_store.clear()
        database._usage_memory.clear()
        database._dedup_cache.clear()

    def test_pairwise_uniqueness_and_grounding_across_15_resumes(self):
        """
        Submits 15 distinct resumes sequentially and verifies:
        1. Every quoted_text is a genuine substring of the uploaded resume.
        2. No two different resumes produce identical (overall_score, one_line_verdict).
        3. Scores are dynamically distributed across multiple values (not static 38).
        4. Verdicts are diverse.
        """
        results = []
        for i, p in enumerate(self.prepared):
            mime = "application/pdf" if p["filename"].endswith(".pdf") else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            resp = self.client.post(
                "/api/roast",
                files={"file": (p["filename"], p["bytes"], mime)},
                headers={"X-User-Email": f"audit_pro_{i}@pro.com", "X-Forwarded-For": f"10.20.30.{i+1}"},
            )
            self.assertEqual(resp.status_code, 200, f"Upload failed for {p['role']}: {resp.text}")
            data = resp.json()
            results.append({"role": p["role"], "text": p["text"], "response": data})

        # 1. Grounding check: every quote must be a substring of that specific resume
        for res in results:
            resume_lower = res["text"].lower()
            for iss in res["response"].get("issues", []):
                qt = iss.get("quoted_text", "").strip().lower()
                self.assertTrue(
                    qt in resume_lower or qt[:25] in resume_lower,
                    f"Ungrounded / contaminated quote '{qt}' in resume for {res['role']}"
                )

        # 2. Score diversity: scores must not all be 38
        distinct_scores = {r["response"]["overall_score"] for r in results}
        self.assertGreaterEqual(
            len(distinct_scores), 6,
            f"Scores lack diversity across 15 distinct resumes: {distinct_scores}"
        )
        self.assertNotIn(
            len(results),
            [list(r["response"]["overall_score"] for r in results).count(38)],
            "Score 38 should not be assigned to every resume!"
        )

        # 3. Pairwise uniqueness: no two resumes share identical score and verdict
        pairs_count = len(results) * (len(results) - 1) // 2
        identical_score_verdict_pairs = 0
        for i in range(len(results)):
            for j in range(i + 1, len(results)):
                r1 = results[i]["response"]
                r2 = results[j]["response"]
                if (r1["overall_score"] == r2["overall_score"] and
                    r1["one_line_verdict"] == r2["one_line_verdict"]):
                    identical_score_verdict_pairs += 1

        self.assertEqual(
            identical_score_verdict_pairs, 0,
            f"Found {identical_score_verdict_pairs} pairs with identical score and verdict out of {pairs_count}!"
        )

    def test_high_concurrency_burst_uploads_no_cross_contamination(self):
        """
        Simulates 10 simultaneous upload requests firing in parallel.
        Ensures:
        1. All 10 requests succeed.
        2. No resume text or quote leaks between concurrent requests.
        """
        concurrent_items = self.prepared[:10]
        results = []

        def _upload(idx, item):
            with TestClient(app) as tc:
                mime = "application/pdf" if item["filename"].endswith(".pdf") else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                resp = tc.post(
                    "/api/roast",
                    files={"file": (item["filename"], item["bytes"], mime)},
                    headers={"X-User-Email": f"burst_user_{idx}@pro.com", "X-Forwarded-For": f"172.16.0.{idx+1}"},
                )
                return idx, item, resp

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(_upload, i, item) for i, item in enumerate(concurrent_items)]
            for fut in concurrent.futures.as_completed(futures):
                idx, item, resp = fut.result()
                self.assertEqual(resp.status_code, 200, f"Concurrent request {idx} ({item['role']}) failed: {resp.text}")
                results.append({"role": item["role"], "text": item["text"], "response": resp.json()})

        self.assertEqual(len(results), 10)

        # Verify zero cross-contamination
        for res in results:
            resume_lower = res["text"].lower()
            for iss in res["response"].get("issues", []):
                qt = iss.get("quoted_text", "").strip().lower()
                self.assertTrue(
                    qt in resume_lower or qt[:25] in resume_lower,
                    f"Concurrency leakage: quote '{qt}' does not belong to {res['role']}"
                )


if __name__ == "__main__":
    unittest.main()
