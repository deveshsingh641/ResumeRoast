import os
import sys
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

from docx_helpers import (
    set_cell_margins,
    set_cell_shading,
    set_table_borders,
    add_clean_page_number,
    set_section_pg_num_type,
    prevent_table_split,
    set_document_high_quality_images
)

def build_perfect_report():
    doc = docx.Document()
    set_document_high_quality_images(doc)
    
    style_normal = doc.styles['Normal']
    font = style_normal.font
    font.name = 'Times New Roman'
    font.size = Pt(12)
    font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)
    
    # =========================================================================
    # SECTION 1: PRELIMINARY PAGES (ROMAN NUMERALS)
    # =========================================================================
    sec1 = doc.sections[0]
    sec1.page_width = Inches(8.27)
    sec1.page_height = Inches(11.69)
    sec1.left_margin = Inches(1.15)
    sec1.right_margin = Inches(0.90)
    sec1.top_margin = Inches(0.80)
    sec1.bottom_margin = Inches(0.75)
    sec1.different_first_page_header_footer = True
    set_section_pg_num_type(sec1, fmt="lowerRoman", start=1)
    
    # Preliminary footer
    f1 = sec1.footer
    f1_p = f1.paragraphs[0]
    f1_p.text = ""
    f1_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_clean_page_number(f1_p)
    
    # Helper Functions
    def add_p(text="", align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_before=0, space_after=2, line_spacing=1.15, bold=False, italic=False, font_size=12, color=None):
        p = doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.space_before = Pt(space_before)
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.line_spacing = line_spacing
        if text:
            run = p.add_run(text)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(font_size)
            run.bold = bold
            run.italic = italic
            if color:
                run.font.color.rgb = color
        return p

    def add_chapter_title(title_text):
        doc.add_page_break()
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(title_text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(14)
        run.bold = True
        run.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
        return p

    def add_section_title(sec_text, space_before=4, space_after=1):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(space_before)
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(sec_text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(13)
        run.bold = True
        run.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
        return p

    def add_fig(img_path, caption_text, width=Inches(4.2)):
        if os.path.exists(img_path):
            p_img = doc.add_paragraph()
            p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_img.paragraph_format.space_before = Pt(3)
            p_img.paragraph_format.space_after = Pt(1)
            p_img.paragraph_format.keep_with_next = True
            run_img = p_img.add_run()
            run_img.add_picture(img_path, width=width)
            
            p_cap = doc.add_paragraph()
            p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_cap.paragraph_format.space_before = Pt(1)
            p_cap.paragraph_format.space_after = Pt(4)
            run_cap = p_cap.add_run(caption_text)
            run_cap.font.name = 'Times New Roman'
            run_cap.font.size = Pt(9.5)
            run_cap.bold = True
            run_cap.font.color.rgb = RGBColor(0x33, 0x41, 0x55)
        else:
            print(f"Warning: image path does not exist: {img_path}")

    def add_custom_table(headers, rows, caption_text="", col_widths=None, font_size=8, pad=25):
        if caption_text:
            p_cap = doc.add_paragraph()
            p_cap.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p_cap.paragraph_format.space_before = Pt(4)
            p_cap.paragraph_format.space_after = Pt(2)
            p_cap.paragraph_format.keep_with_next = True
            run_cap = p_cap.add_run(caption_text)
            run_cap.font.name = 'Times New Roman'
            run_cap.font.size = Pt(9.5)
            run_cap.bold = True
            run_cap.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)
            
        tbl = doc.add_table(rows=len(rows)+1, cols=len(headers))
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        set_table_borders(tbl, color="CBD5E1", sz="3", val="single")
        
        # Header row
        hdr_row = tbl.rows[0]
        tbl._tbl.tblPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))
        for idx, h_text in enumerate(headers):
            cell = hdr_row.cells[idx]
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_margins(cell, top=pad+10, bottom=pad+10, left=50, right=50)
            set_cell_shading(cell, "F1F5F9")
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            run = p.add_run(h_text)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(font_size + 0.5)
            run.bold = True
            run.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
            if col_widths and idx < len(col_widths):
                cell.width = col_widths[idx]
                
        # Data rows
        for r_idx, r_data in enumerate(rows):
            row = tbl.rows[r_idx + 1]
            bg_color = "FFFFFF" if r_idx % 2 == 0 else "F8FAFC"
            for c_idx, val in enumerate(r_data):
                cell = row.cells[c_idx]
                cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                set_cell_margins(cell, top=pad, bottom=pad, left=50, right=50)
                set_cell_shading(cell, bg_color)
                p = cell.paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT if c_idx > 0 or len(val) > 20 else WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing = 1.05
                run = p.add_run(str(val))
                run.font.name = 'Times New Roman'
                run.font.size = Pt(font_size)
                run.font.color.rgb = RGBColor(0x33, 0x41, 0x55)
                if col_widths and c_idx < len(col_widths):
                    cell.width = col_widths[c_idx]
                    
        prevent_table_split(tbl)
        p_space = doc.add_paragraph()
        p_space.paragraph_format.space_before = Pt(0)
        p_space.paragraph_format.space_after = Pt(2)
        return tbl

    # -------------------------------------------------------------------------
    # PAGE i: TITLE PAGE (Cover Page)
    # -------------------------------------------------------------------------
    t_hdr = doc.add_table(rows=1, cols=3)
    t_hdr.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_hdr, color="FFFFFF", sz="0", val="none")
    t_hdr.rows[0].cells[0].width = Inches(1.1)
    t_hdr.rows[0].cells[1].width = Inches(4.2)
    t_hdr.rows[0].cells[2].width = Inches(0.9)
    
    if os.path.exists('extracted_template_media/img_0.jpeg'):
        t_hdr.rows[0].cells[0].paragraphs[0].add_run().add_picture('extracted_template_media/img_0.jpeg', width=Inches(0.85))
    p_mid = t_hdr.rows[0].cells[1].paragraphs[0]
    p_mid.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_mid.paragraph_format.space_before = Pt(4)
    r_mid = p_mid.add_run("ABES ENGINEERING COLLEGE, GHAZIABAD")
    r_mid.font.name = 'Arial'
    r_mid.font.size = Pt(13)
    r_mid.bold = True
    r_mid.font.color.rgb = RGBColor(0x8B, 0x00, 0x00)
    if os.path.exists('extracted_template_media/img_1_hq.png'):
        t_hdr.rows[0].cells[2].paragraphs[0].add_run().add_picture('extracted_template_media/img_1_hq.png', width=Inches(0.75))
    elif os.path.exists('extracted_template_media/img_1.png'):
        t_hdr.rows[0].cells[2].paragraphs[0].add_run().add_picture('extracted_template_media/img_1.png', width=Inches(0.75))

    add_p("Internship Report", align=WD_ALIGN_PARAGRAPH.CENTER, space_before=8, space_after=2, bold=True, font_size=15)
    add_p("on", align=WD_ALIGN_PARAGRAPH.CENTER, space_before=2, space_after=4, bold=True, font_size=13)
    add_p("Full-Stack E-Commerce Web Application & Transaction Platform", align=WD_ALIGN_PARAGRAPH.CENTER, space_before=2, space_after=8, bold=True, font_size=16, color=RGBColor(0x0F, 0x17, 0x2A))
    add_p("Submitted as Internship Report", align=WD_ALIGN_PARAGRAPH.CENTER, space_before=2, space_after=1, bold=True, font_size=12)
    add_p("for", align=WD_ALIGN_PARAGRAPH.CENTER, space_before=1, space_after=1, bold=True, font_size=11)
    add_p("INTERNSHIP (BIT/BCS-752)", align=WD_ALIGN_PARAGRAPH.CENTER, space_before=1, space_after=3, bold=True, font_size=16)
    add_p("Session 2026-27", align=WD_ALIGN_PARAGRAPH.CENTER, space_before=1, space_after=1, bold=True, font_size=12)
    add_p("in", align=WD_ALIGN_PARAGRAPH.CENTER, space_before=1, space_after=1, bold=True, font_size=11)
    add_p("Department of Information Technology", align=WD_ALIGN_PARAGRAPH.CENTER, space_before=1, space_after=10, bold=True, font_size=15)
    
    t_by = doc.add_table(rows=1, cols=2)
    t_by.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_by, color="FFFFFF", sz="0", val="none")
    t_by.rows[0].cells[0].width = Inches(3.1)
    t_by.rows[0].cells[1].width = Inches(3.1)
    
    p_by = t_by.rows[0].cells[0].paragraphs[0]
    p_by.paragraph_format.line_spacing = 1.15
    p_by.add_run("By:\n").bold = True
    p_by.add_run("Devesh Singh\n").bold = True
    p_by.add_run("Roll No: [University Roll No]\n").bold = True
    p_by.add_run("Department of Information Technology")
    
    p_to = t_by.rows[0].cells[1].paragraphs[0]
    p_to.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_to.paragraph_format.line_spacing = 1.15
    p_to.add_run("Submitted to:\n").bold = True
    p_to.add_run("Dr. Anamika Goel\n").bold = True
    p_to.add_run("Associate Professor\n")
    p_to.add_run("Internship Coordinator").bold = True

    add_p(space_after=8)
    add_p("AFFILIATED TO", align=WD_ALIGN_PARAGRAPH.CENTER, space_before=6, space_after=1, bold=True, font_size=11)
    add_p("DR. A.P.J. ABDUL KALAM TECHNICAL UNIVERSITY, U.P., LUCKNOW", align=WD_ALIGN_PARAGRAPH.CENTER, space_before=1, space_after=1, bold=True, font_size=11.5)
    add_p("(Formerly UPTU)", align=WD_ALIGN_PARAGRAPH.CENTER, space_before=1, space_after=4, bold=True, font_size=10.5)

    # -------------------------------------------------------------------------
    # PAGE ii: INTERNSHIP CERTIFICATE
    # -------------------------------------------------------------------------
    doc.add_page_break()
    p_cert = doc.add_paragraph()
    p_cert.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cert.paragraph_format.space_before = Pt(4)
    p_cert.paragraph_format.space_after = Pt(4)
    r_cert = p_cert.add_run("INTERNSHIP CERTIFICATE")
    r_cert.font.name = 'Times New Roman'
    r_cert.font.size = Pt(14)
    r_cert.bold = True
    
    if os.path.exists('presentation_assets/thiranex_certificate.png'):
        p_cimg = doc.add_paragraph()
        p_cimg.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cimg.paragraph_format.space_before = Pt(1)
        p_cimg.paragraph_format.space_after = Pt(3)
        p_cimg.add_run().add_picture('presentation_assets/thiranex_certificate.png', width=Inches(4.4))

    cert_headers = ["Credential Attribute", "Official Industrial Verification Record"]
    cert_rows = [
        ["Student Intern Name", "Devesh Singh"],
        ["Internship Unique ID", "THX-AUG1726-220 (Verified Certificate)"],
        ["Internship Organization", "Thiranex (Corporate Web: www.thiranex.in)"],
        ["Assigned Professional Role", "Intern - Full Stack Development"],
        ["Domain Track", "Full Stack Web Development (MERN Ecosystem)"],
        ["Tenure & Duration", "17 August 2026 to 16 September 2026 (4 Weeks Intensive)"],
        ["Authorized Signatory", "Hariharan M, Founder & Chief Executive Officer (CEO)"],
        ["Course Mapping", "INTERNSHIP (BIT/BCS-752), Session 2026-27"]
    ]
    add_custom_table(cert_headers, cert_rows, col_widths=[Inches(2.5), Inches(3.7)], font_size=8.5, pad=20)
    
    t_sig = doc.add_table(rows=1, cols=2)
    t_sig.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_sig, color="FFFFFF", sz="0", val="none")
    t_sig.rows[0].cells[0].width = Inches(3.1)
    t_sig.rows[0].cells[1].width = Inches(3.1)
    
    p_s1 = t_sig.rows[0].cells[0].paragraphs[0]
    p_s1.paragraph_format.space_before = Pt(4)
    p_s1.paragraph_format.line_spacing = 1.15
    p_s1.add_run("Signature of HOD\n").bold = True
    p_s1.add_run("Dr. Deepali Dev\n")
    p_s1.add_run("HOD - Department of CSE-AIML\n")
    p_s1.add_run("ABES Engineering College, Ghaziabad\n")
    p_s1.add_run("Date: ........................................")
    
    p_s2 = t_sig.rows[0].cells[1].paragraphs[0]
    p_s2.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_s2.paragraph_format.space_before = Pt(4)
    p_s2.paragraph_format.line_spacing = 1.15
    p_s2.add_run("Signature of Internship-Coordinator\n").bold = True
    p_s2.add_run("Dr. Anamika Goel\n")
    p_s2.add_run("Associate Professor CSE-AIML\n")
    p_s2.add_run("ABES Engineering College, Ghaziabad\n")
    p_s2.add_run("Date: ........................................")

    # -------------------------------------------------------------------------
    # PAGE iii: STUDENT'S DECLARATION
    # -------------------------------------------------------------------------
    doc.add_page_break()
    p_dec_title = doc.add_paragraph()
    p_dec_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_dec_title.paragraph_format.space_before = Pt(8)
    p_dec_title.paragraph_format.space_after = Pt(10)
    r_dec = p_dec_title.add_run("STUDENT’S DECLARATION")
    r_dec.font.name = 'Times New Roman'
    r_dec.font.size = Pt(14)
    r_dec.bold = True
    
    add_p("I hereby declare that the Internship Report entitled “Full-Stack E-Commerce Web Application & Transaction Platform”, submitted in partial fulfillment of the requirements for the award of the degree of Bachelor of Technology (B.Tech.), is my original work carried out during the internship period under the guidance of Internship coordinator Dr. Anamika Goel, Associate Professor, Department of Computer Science & Engineering-AIML / Department of Information Technology, ABES Engineering College, Ghaziabad.", space_before=4, space_after=6)
    add_p("I further declare that, to the best of my knowledge and belief, this report contains no material previously published or written by any other person, nor any material that has been submitted, in whole or in substantial part, for the award of any other degree, diploma, or academic qualification from this or any other university/institution, except where due acknowledgment has been made in the report.", space_before=4, space_after=6)
    add_p("All sources of information, references, technical contributions, software frameworks, and algorithmic architectures of others have been duly acknowledged and cited wherever applicable.", space_before=4, space_after=12)
    
    t_d_sig = doc.add_table(rows=1, cols=2)
    t_d_sig.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_d_sig, color="FFFFFF", sz="0", val="none")
    t_d_sig.rows[0].cells[0].width = Inches(3.1)
    t_d_sig.rows[0].cells[1].width = Inches(3.1)
    t_d_sig.rows[0].cells[0].paragraphs[0].add_run("Dated: 16 September 2026\n\nPlace: Ghaziabad").bold = True
    
    pd_s2 = t_d_sig.rows[0].cells[1].paragraphs[0]
    pd_s2.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    pd_s2.paragraph_format.line_spacing = 1.15
    pd_s2.add_run("Signature of Student: __________________\n\n").bold = True
    pd_s2.add_run("Name: Devesh Singh\n").bold = True
    pd_s2.add_run("Roll No: [University Roll No]\n").bold = True
    pd_s2.add_run("Department: Department of Information Technology\n")
    pd_s2.add_run("ABES Engineering College, Ghaziabad")

    add_p(space_before=10, space_after=6)
    p_cert_note = doc.add_paragraph()
    p_cert_note.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_cert_note.paragraph_format.space_before = Pt(8)
    p_cert_note.paragraph_format.space_after = Pt(4)
    r_cn = p_cert_note.add_run("This is to certify that the above statement made by the candidate is correct to the best of my knowledge.")
    r_cn.font.name = 'Times New Roman'
    r_cn.font.size = Pt(12)
    r_cn.italic = True
    
    add_p(space_after=8)
    p_coord_sig = doc.add_paragraph()
    p_coord_sig.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_coord_sig.paragraph_format.line_spacing = 1.15
    p_coord_sig.add_run("Signature of Internship-Coordinator\n").bold = True
    p_coord_sig.add_run("Dr. Anamika Goel\n")
    p_coord_sig.add_run("Associate Professor CSE-AIML\n")
    p_coord_sig.add_run("ABES Engineering College, Ghaziabad")

    # -------------------------------------------------------------------------
    # PAGE iv: ACKNOWLEDGEMENT
    # -------------------------------------------------------------------------
    doc.add_page_break()
    p_ack_title = doc.add_paragraph()
    p_ack_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ack_title.paragraph_format.space_before = Pt(8)
    p_ack_title.paragraph_format.space_after = Pt(10)
    r_ack = p_ack_title.add_run("ACKNOWLEDGEMENT")
    r_ack.font.name = 'Times New Roman'
    r_ack.font.size = Pt(14)
    r_ack.bold = True
    
    add_p("It gives me a profound sense of pleasure and academic fulfillment to present this Internship Project Report, undertaken as a mandatory component of the Bachelor of Technology (B.Tech.) curriculum at ABES Engineering College, Ghaziabad. The 4-week industrial internship provided an invaluable opportunity to bridge undergraduate theoretical foundations with contemporary enterprise-grade software development practices.", space_before=3, space_after=5)
    add_p("I express my sincere and heartfelt gratitude to my Internship Coordinator, Dr. Anamika Goel, Associate Professor, Department of Computer Science & Engineering-AIML / Department of Information Technology, ABES Engineering College, Ghaziabad, for providing continuous academic guidance, invaluable structural feedback, and constant encouragement throughout the internship period. Her meticulous reviews, regular progress monitoring, and intellectual guidance were instrumental in navigating architectural challenges and shaping the technical rigor of this report.", space_before=3, space_after=5)
    add_p("I also take this opportunity to express my sincere gratitude to Associate Professor, Dr. Deepali Dev, Head of the Department of Computer Science & Engineering-AIML, ABES Engineering College, Ghaziabad, for her administrative support, institutional vision, and continuous encouragement. Her emphasis on industrial alignment and hands-on engineering execution provided the inspiration necessary to undertake and successfully complete a high-complexity full-stack project.", space_before=3, space_after=5)
    add_p("I would like to express my deepest thanks and professional appreciation to my Industry Mentors, Supervisors, and the entire engineering team at Thiranex (www.thiranex.in), where I completed my internship from 17 August 2026 to 16 September 2026 under Credential ID: THX-AUG1726-220. Working under the dynamic leadership of Hariharan M, Founder & Chief Executive Officer (CEO) of Thiranex, provided me with firsthand exposure to production web development, enterprise agile sprint workflows, code review standards, and scalable cloud deployment pipelines. The technical insights and architectural critiques provided by the Thiranex evaluation panel significantly refined my engineering perspective.", space_before=3, space_after=5)
    add_p("Lastly, I extend my heartfelt appreciation to my family, faculty members, lab instructors, and peers for their continuous moral support, critical discussions, and technical camaraderie throughout the project development lifecycle.", space_before=3, space_after=10)
    
    t_ack_sig = doc.add_table(rows=1, cols=2)
    t_ack_sig.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_ack_sig, color="FFFFFF", sz="0", val="none")
    t_ack_sig.rows[0].cells[0].width = Inches(3.1)
    t_ack_sig.rows[0].cells[1].width = Inches(3.1)
    t_ack_sig.rows[0].cells[0].paragraphs[0].add_run("Date: 16 September 2026\n\nPlace: Ghaziabad").bold = True
    
    pa_s2 = t_ack_sig.rows[0].cells[1].paragraphs[0]
    pa_s2.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    pa_s2.paragraph_format.line_spacing = 1.15
    pa_s2.add_run("Signature: ______________________\n\n").bold = True
    pa_s2.add_run("Name: Devesh Singh\n").bold = True
    pa_s2.add_run("Roll No.: [University Roll No]\n").bold = True
    pa_s2.add_run("Department: Department of Information Technology\n")
    pa_s2.add_run("ABES Engineering College, Ghaziabad")

    # -------------------------------------------------------------------------
    # PAGE v: ABSTRACT
    # -------------------------------------------------------------------------
    doc.add_page_break()
    p_abs_title = doc.add_paragraph()
    p_abs_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_abs_title.paragraph_format.space_before = Pt(8)
    p_abs_title.paragraph_format.space_after = Pt(10)
    r_abs = p_abs_title.add_run("ABSTRACT")
    r_abs.font.name = 'Times New Roman'
    r_abs.font.size = Pt(14)
    r_abs.bold = True
    
    add_p("The rapid maturation of digital commerce demands web platforms that combine zero-latency user interactivity, persistent state management across client sessions, and ironclad role-based security barriers. Traditional e-commerce architectures frequently suffer from tight monolithic coupling, volatile shopping cart state desynchronization upon page refreshes, exposed administrative mutations, and high database query latency on unindexed schemas. This internship project, titled “Full-Stack E-Commerce Web Application & Transaction Platform”, was engineered during an intensive 4-week industrial internship at Thiranex under Credential ID: THX-AUG1726-220 to resolve these architectural deficiencies through a modern, decoupled MERN (MongoDB, Express.js, React 18, Node.js) platform.", space_before=3, space_after=5)
    add_p("The engineered platform incorporates a 4-tier decoupled architecture comprising a high-speed Single Page Application (SPA) frontend built with React 18, Vite, and Tailwind CSS; an asynchronous RESTful API layer powered by Node.js and Express.js; a cryptographic authentication tier utilizing JSON Web Tokens (JWT), salted bcrypt password hashing, and Role-Based Access Control (RBAC) middleware; and a high-performance MongoDB data persistence tier managed via Mongoose schemas. Core functional innovations include persistent cart state hydration via React Context API and LocalStorage, preventing cart abandonment during multi-tab browsing; an embedded timeline tracking sub-document schema facilitating O(1) order lifecycle status progression (Placed -> Processing -> Shipped -> Delivered); a dynamic multi-attribute product catalog with debounced regex search; and an administrative dashboard delivering live business metrics, inventory CRUD controls, and order dispatch workflows.", space_before=3, space_after=5)
    add_p("Developed following a 4-week Agile sprint methodology, the platform underwent rigorous empirical testing, achieving an unblemished 100% pass rate across a 36/36 automated test suite. Quantitative performance benchmarking demonstrated an average API query latency of 42 ms—surpassing the enterprise SLA target of 100 ms by 58%—alongside a Google Lighthouse performance score of 98/100, a First Contentful Paint (FCP) of 1.1 seconds, an optimized bundle size of 238 KB, and sustained server throughput exceeding 450 concurrent requests per second without session degradation. The project verified the viability of decoupled MERN architectures for commercial commerce and concluded with an official corporate endorsement and Letter of Recommendation (LOR) from the Founder & CEO of Thiranex.", space_before=3, space_after=6)
    
    p_kw = doc.add_paragraph()
    p_kw.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_kw.paragraph_format.space_before = Pt(4)
    p_kw.add_run("Keywords: ").bold = True
    p_kw.add_run("MERN Stack, React 18 Single Page Application, Role-Based Access Control (RBAC), JSON Web Tokens (JWT), Cart State Hydration, Mongoose Schema Modeling, RESTful API Architecture, Agile Development.")

    # -------------------------------------------------------------------------
    # PAGE vi: TABLE OF CONTENTS (Fits exactly on Page vi)
    # -------------------------------------------------------------------------
    doc.add_page_break()
    p_toc_title = doc.add_paragraph()
    p_toc_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_toc_title.paragraph_format.space_before = Pt(6)
    p_toc_title.paragraph_format.space_after = Pt(6)
    r_toc = p_toc_title.add_run("TABLE OF CONTENTS")
    r_toc.font.name = 'Times New Roman'
    r_toc.font.size = Pt(13)
    r_toc.bold = True
    
    toc_data = [
        ["Title Page", "i"],
        ["Internship Certificate", "ii"],
        ["Student’s Declaration", "iii"],
        ["Acknowledgement", "iv"],
        ["Abstract", "v"],
        ["Table of Contents", "vi"],
        ["List of Tables & List of Figures", "vii"],
        ["List of Symbols & List of Abbreviations", "viii"],
        ["CHAPTER 1: INTERNSHIP & COMPANY OVERVIEW", "1"],
        ["    1.1 Internship Overview & Context | 1.2 Internship Domain", "1"],
        ["    1.3 Company Overview | 1.4 Objectives | 1.5 Roles & Responsibilities", "2"],
        ["    1.6 Schedule & Workflow | 1.7 Development Environment", "2"],
        ["CHAPTER 2: PROJECT INTRODUCTION", "3"],
        ["    2.1 Introduction & Project Overview | 2.2 Project Background", "3"],
        ["    2.3 Problem Statement & Deficiencies | 2.4 Objectives | 2.5 Scope", "4"],
        ["    2.6 Functional Requirements | 2.7 Non-Functional Requirements | 2.8 Significance", "5"],
        ["CHAPTER 3: BACKGROUND / EXISTING APPROACH", "6"],
        ["    3.1 Existing Approach | 3.2 Limitations of Monolithic Systems", "6"],
        ["    3.3 Need for Improved Architecture | 3.4 Technology Shift | 3.5 Comparative Analysis", "7"],
        ["CHAPTER 4: PROPOSED APPROACH & METHODOLOGY", "8"],
        ["    4.1 System Overview | 4.2 4-Tier Architecture Overview", "8"],
        ["    4.3 Frontend SPA Architecture | 4.4 Backend REST API Services", "8"],
        ["    4.5 Security & RBAC Guards | 4.6 Database Design & Mongoose Schemas", "9"],
        ["    4.7 RESTful API Endpoints | 4.8 Cart State Management & Hydration", "10"],
        ["    4.9 Order Lifecycle Pipeline | 4.10 Admin Management | 4.11 Agile Methodology", "12"],
        ["    4.12 Quality Assurance & Automated Testing Strategy", "13"],
        ["CHAPTER 5: IMPLEMENTATION & DEMONSTRATION", "14"],
        ["    5.1 Environment Setup | 5.2 Product Catalog Storefront & Dynamic Filtering", "14"],
        ["    5.3 Shopping Cart Slideover & Persistent State Hydration | 5.4 Checkout", "15"],
        ["    5.5 Real-Time Order Tracking Timeline | 5.6 Admin Dashboard & Analytics", "16"],
        ["    5.7 Administrative Order Dispatch | 5.8 Backend Optimization & Indexing", "17"],
        ["CHAPTER 6: RESULT ANALYSIS / PERFORMANCE METRICS", "18"],
        ["    6.1 Evaluation Framework | 6.2 Latency Benchmark | 6.3 Lighthouse Vitals", "18"],
        ["    6.4 Concurrency Load Testing | 6.5 System Verification Matrix | 6.6 Corporate Audit", "19"],
        ["CHAPTER 7: CHALLENGES FACED", "20"],
        ["    7.1 Cart State Desynchronization | 7.2 Administrative Route Exposure", "20"],
        ["    7.3 Order Lifecycle Tracking | 7.4 Catalog Search Latency | 7.5 Challenges Summary", "21"],
        ["CHAPTER 8: KEY LEARNINGS FROM INTERNSHIP", "22"],
        ["    8.1 Technical Competencies | 8.2 Frontend & State | 8.3 Backend & Asynchronous I/O", "22"],
        ["    8.4 Database Modeling | 8.5 Security & RBAC | 8.6 Testing & Agile Discipline", "22"],
        ["REFERENCES (IEEE Citation Format)", "23"],
        ["APPENDIX: SUPPLEMENTARY TECHNICAL SPECIFICATIONS", "24"]
    ]
    
    t_toc = doc.add_table(rows=len(toc_data)+1, cols=2)
    t_toc.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_toc, color="CBD5E1", sz="2", val="single")
    t_toc.rows[0].cells[0].width = Inches(5.2)
    t_toc.rows[0].cells[1].width = Inches(1.0)
    
    t_toc.rows[0].cells[0].paragraphs[0].add_run("Chapter / Section Title").bold = True
    t_toc.rows[0].cells[1].paragraphs[0].add_run("Page No.").bold = True
    t_toc.rows[0].cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    set_cell_shading(t_toc.rows[0].cells[0], "F1F5F9")
    set_cell_shading(t_toc.rows[0].cells[1], "F1F5F9")
    set_cell_margins(t_toc.rows[0].cells[0], top=25, bottom=25, left=50, right=50)
    set_cell_margins(t_toc.rows[0].cells[1], top=25, bottom=25, left=50, right=50)
    
    for idx, (t_title, t_pg) in enumerate(toc_data):
        row = t_toc.rows[idx + 1]
        c0 = row.cells[0]
        c1 = row.cells[1]
        c0.width = Inches(5.2)
        c1.width = Inches(1.0)
        set_cell_margins(c0, top=14, bottom=14, left=50, right=50)
        set_cell_margins(c1, top=14, bottom=14, left=50, right=50)
        
        p0 = c0.paragraphs[0]
        p0.paragraph_format.space_before = Pt(0)
        p0.paragraph_format.space_after = Pt(0)
        p0.paragraph_format.line_spacing = 1.0
        r0 = p0.add_run(t_title)
        r0.font.name = 'Times New Roman'
        r0.font.size = Pt(8)
        if "CHAPTER" in t_title or t_title.startswith("Title") or t_title.startswith("REFERENCES") or t_title.startswith("APPENDIX"):
            r0.bold = True
            
        p1 = c1.paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p1.paragraph_format.space_before = Pt(0)
        p1.paragraph_format.space_after = Pt(0)
        r1 = p1.add_run(t_pg)
        r1.font.name = 'Times New Roman'
        r1.font.size = Pt(8)
        if "CHAPTER" in t_title or t_title.startswith("Title") or t_title.startswith("REFERENCES"):
            r1.bold = True

    # -------------------------------------------------------------------------
    # PAGE vii: LIST OF TABLES & LIST OF FIGURES (Fits on Page vii)
    # -------------------------------------------------------------------------
    doc.add_page_break()
    p_lot_title = doc.add_paragraph()
    p_lot_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_lot_title.paragraph_format.space_before = Pt(4)
    p_lot_title.paragraph_format.space_after = Pt(4)
    r_lot = p_lot_title.add_run("LIST OF TABLES")
    r_lot.font.name = 'Times New Roman'
    r_lot.font.size = Pt(12)
    r_lot.bold = True
    
    tables_list = [
        ("Table 2.1", "Functional Requirements Specification", "5"),
        ("Table 2.2", "Non-Functional Engineering Requirements", "5"),
        ("Table 3.1", "Architectural Comparative Analysis (Monolith vs. Proposed Platform)", "7"),
        ("Table 4.1", "Comprehensive Full-Stack Technology Stack & Tooling Specifications", "9"),
        ("Table 4.2", "Normalized Database Schema Entities & Mongoose Data Models", "10"),
        ("Table 4.3", "Core RESTful API Endpoints Specification & Route Guard Policies", "11"),
        ("Table 4.4", "4-Week Agile Development Sprint Plan & Milestone Deliverables", "13"),
        ("Table 6.1", "End-to-End Quantitative Performance Benchmark Matrix", "18"),
        ("Table 6.2", "System Verification, Quality Assurance, and Security Audit Matrix", "19"),
        ("Table 7.1", "Summary of Technical Challenges, Solutions, and Implemented Impact", "21")
    ]
    
    t_lot = doc.add_table(rows=len(tables_list)+1, cols=3)
    t_lot.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_lot, color="CBD5E1", sz="2", val="single")
    t_lot.rows[0].cells[0].width = Inches(1.1)
    t_lot.rows[0].cells[1].width = Inches(4.2)
    t_lot.rows[0].cells[2].width = Inches(0.9)
    
    t_lot.rows[0].cells[0].paragraphs[0].add_run("Table No.").bold = True
    t_lot.rows[0].cells[1].paragraphs[0].add_run("Table Title").bold = True
    t_lot.rows[0].cells[2].paragraphs[0].add_run("Page").bold = True
    t_lot.rows[0].cells[2].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    for c in t_lot.rows[0].cells:
        set_cell_shading(c, "F1F5F9")
        set_cell_margins(c, top=14, bottom=14, left=40, right=40)
        
    for idx, (t_no, t_desc, t_p) in enumerate(tables_list):
        row = t_lot.rows[idx + 1]
        for c in row.cells:
            set_cell_margins(c, top=10, bottom=10, left=40, right=40)
        r0 = row.cells[0].paragraphs[0].add_run(t_no)
        r0.bold = True
        r0.font.size = Pt(7.5)
        r1 = row.cells[1].paragraphs[0].add_run(t_desc)
        r1.font.size = Pt(7.5)
        p_p = row.cells[2].paragraphs[0]
        p_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r2 = p_p.add_run(t_p)
        r2.font.size = Pt(7.5)

    p_lof_title = doc.add_paragraph()
    p_lof_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_lof_title.paragraph_format.space_before = Pt(5)
    p_lof_title.paragraph_format.space_after = Pt(4)
    r_lof = p_lof_title.add_run("LIST OF FIGURES")
    r_lof.font.name = 'Times New Roman'
    r_lof.font.size = Pt(12)
    r_lof.bold = True
    
    figures_list = [
        ("Figure 4.1", "4-Tier Full-Stack MERN System Architecture Overview", "8"),
        ("Figure 4.2", "Client-Side React SPA State Hydration & Authentication Pipeline", "11"),
        ("Figure 4.3", "Multi-Stage Order Lifecycle Pipeline & Embedded Schema Model", "12"),
        ("Figure 5.1", "Product Catalog Storefront with Category & Price Filtering", "14"),
        ("Figure 5.2", "Persistent Shopping Cart Slideover Drawer with Real-Time Subtotal", "15"),
        ("Figure 5.3", "Multi-Step Checkout Workflow & Customer Shipping Form", "15"),
        ("Figure 5.4", "Real-Time Order Tracking Timeline & Live Fulfillment Monitor", "16"),
        ("Figure 5.5", "Role-Protected Administrative Analytics Overview & Revenue KPIs", "16"),
        ("Figure 5.6", "Administrative Order Dispatch Console & Stage Mutation Dispatcher", "17"),
        ("Figure 6.1", "Empirical Performance Benchmarks & Database Query Latency Audit", "18")
    ]
    
    t_lof = doc.add_table(rows=len(figures_list)+1, cols=3)
    t_lof.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_lof, color="CBD5E1", sz="2", val="single")
    t_lof.rows[0].cells[0].width = Inches(1.1)
    t_lof.rows[0].cells[1].width = Inches(4.2)
    t_lof.rows[0].cells[2].width = Inches(0.9)
    
    t_lof.rows[0].cells[0].paragraphs[0].add_run("Figure No.").bold = True
    t_lof.rows[0].cells[1].paragraphs[0].add_run("Figure Caption").bold = True
    t_lof.rows[0].cells[2].paragraphs[0].add_run("Page").bold = True
    t_lof.rows[0].cells[2].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    for c in t_lof.rows[0].cells:
        set_cell_shading(c, "F1F5F9")
        set_cell_margins(c, top=14, bottom=14, left=40, right=40)
        
    for idx, (f_no, f_desc, f_p) in enumerate(figures_list):
        row = t_lof.rows[idx + 1]
        for c in row.cells:
            set_cell_margins(c, top=10, bottom=10, left=40, right=40)
        r0 = row.cells[0].paragraphs[0].add_run(f_no)
        r0.bold = True
        r0.font.size = Pt(7.5)
        r1 = row.cells[1].paragraphs[0].add_run(f_desc)
        r1.font.size = Pt(7.5)
        p_p = row.cells[2].paragraphs[0]
        p_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r2 = p_p.add_run(f_p)
        r2.font.size = Pt(7.5)

    # -------------------------------------------------------------------------
    # PAGE viii: LIST OF SYMBOLS & LIST OF ABBREVIATIONS (Fits on Page viii)
    # -------------------------------------------------------------------------
    doc.add_page_break()
    p_los_title = doc.add_paragraph()
    p_los_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_los_title.paragraph_format.space_before = Pt(4)
    p_los_title.paragraph_format.space_after = Pt(4)
    r_los = p_los_title.add_run("LIST OF SYMBOLS")
    r_los.font.name = 'Times New Roman'
    r_los.font.size = Pt(12)
    r_los.bold = True
    
    symbols_list = [
        ("O(1)", "Constant algorithmic time complexity (independent of collection size)"),
        ("O(n)", "Linear algorithmic time complexity (scales directly with number of items)"),
        ("ms", "Millisecond (one thousandth of a second, unit of query latency)"),
        ("s", "Second (standard metric unit of rendering duration / FCP)"),
        ("KB", "Kilobyte (unit of compiled JavaScript / CSS asset bundle payload)"),
        ("req/s", "Requests per second (metric of concurrent HTTP server throughput)"),
        ("%", "Percentage (ratio expressed as a fraction of one hundred, test pass rate)"),
        ("v", "Version identifier (e.g., React v18, Node.js v18 LTS)")
    ]
    t_los = doc.add_table(rows=len(symbols_list)+1, cols=2)
    t_los.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_los, color="CBD5E1", sz="2", val="single")
    t_los.rows[0].cells[0].width = Inches(1.5)
    t_los.rows[0].cells[1].width = Inches(4.7)
    t_los.rows[0].cells[0].paragraphs[0].add_run("Symbol").bold = True
    t_los.rows[0].cells[1].paragraphs[0].add_run("Engineering Significance / Definition").bold = True
    set_cell_shading(t_los.rows[0].cells[0], "F1F5F9")
    set_cell_shading(t_los.rows[0].cells[1], "F1F5F9")
    set_cell_margins(t_los.rows[0].cells[0], top=14, bottom=14, left=40, right=40)
    set_cell_margins(t_los.rows[0].cells[1], top=14, bottom=14, left=40, right=40)
    for idx, (s_n, s_d) in enumerate(symbols_list):
        row = t_los.rows[idx + 1]
        set_cell_margins(row.cells[0], top=10, bottom=10, left=40, right=40)
        set_cell_margins(row.cells[1], top=10, bottom=10, left=40, right=40)
        r0 = row.cells[0].paragraphs[0].add_run(s_n)
        r0.bold = True
        r0.font.size = Pt(8)
        r1 = row.cells[1].paragraphs[0].add_run(s_d)
        r1.font.size = Pt(8)

    p_loa_title = doc.add_paragraph()
    p_loa_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_loa_title.paragraph_format.space_before = Pt(5)
    p_loa_title.paragraph_format.space_after = Pt(4)
    r_loa = p_loa_title.add_run("LIST OF ABBREVIATIONS")
    r_loa.font.name = 'Times New Roman'
    r_loa.font.size = Pt(12)
    r_loa.bold = True
    
    abbr_list = [
        ("API", "Application Programming Interface"),
        ("REST", "Representational State Transfer"),
        ("MERN", "MongoDB, Express.js, React.js, Node.js"),
        ("SPA", "Single Page Application"),
        ("JWT", "JSON Web Token"),
        ("RBAC", "Role-Based Access Control"),
        ("ODM", "Object Data Modeling"),
        ("UI / UX", "User Interface / User Experience"),
        ("DOM", "Document Object Model (Virtual DOM in React)"),
        ("FCP", "First Contentful Paint (Core Web Vital metric)"),
        ("CRUD", "Create, Read, Update, Delete"),
        ("CORS", "Cross-Origin Resource Sharing"),
        ("HTTP / HTTPS", "Hypertext Transfer Protocol / Hypertext Transfer Protocol Secure"),
        ("JSON", "JavaScript Object Notation"),
        ("SLA", "Service Level Agreement"),
        ("LOR", "Letter of Recommendation")
    ]
    t_loa = doc.add_table(rows=len(abbr_list)+1, cols=2)
    t_loa.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_loa, color="CBD5E1", sz="2", val="single")
    t_loa.rows[0].cells[0].width = Inches(1.5)
    t_loa.rows[0].cells[1].width = Inches(4.7)
    t_loa.rows[0].cells[0].paragraphs[0].add_run("Abbreviation").bold = True
    t_loa.rows[0].cells[1].paragraphs[0].add_run("Complete Expansion").bold = True
    set_cell_shading(t_loa.rows[0].cells[0], "F1F5F9")
    set_cell_shading(t_loa.rows[0].cells[1], "F1F5F9")
    set_cell_margins(t_loa.rows[0].cells[0], top=14, bottom=14, left=40, right=40)
    set_cell_margins(t_loa.rows[0].cells[1], top=14, bottom=14, left=40, right=40)
    for idx, (a_b, a_e) in enumerate(abbr_list):
        row = t_loa.rows[idx + 1]
        set_cell_margins(row.cells[0], top=10, bottom=10, left=40, right=40)
        set_cell_margins(row.cells[1], top=10, bottom=10, left=40, right=40)
        r0 = row.cells[0].paragraphs[0].add_run(a_b)
        r0.bold = True
        r0.font.size = Pt(8)
        r1 = row.cells[1].paragraphs[0].add_run(a_e)
        r1.font.size = Pt(8)

    # =========================================================================
    # SECTION 2: MAIN REPORT CHAPTERS (ARABIC NUMERALS STARTING AT 1)
    # =========================================================================
    sec2 = doc.add_section()
    sec2.page_width = Inches(8.27)
    sec2.page_height = Inches(11.69)
    sec2.left_margin = Inches(1.15)
    sec2.right_margin = Inches(0.90)
    sec2.top_margin = Inches(0.80)
    sec2.bottom_margin = Inches(0.75)
    sec2.different_first_page_header_footer = False
    set_section_pg_num_type(sec2, fmt="decimal", start=1)
    
    # UNLINK FOOTER FROM SECTION 1 (Prevents duplicate page numbers!)
    sec2.footer.is_linked_to_previous = False
    f2_p = sec2.footer.paragraphs[0]
    f2_p.text = ""
    f2_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_clean_page_number(f2_p)

    # -------------------------------------------------------------------------
    # CHAPTER 1: INTERNSHIP & COMPANY OVERVIEW (Exactly 2 Pages: 1 and 2)
    # -------------------------------------------------------------------------
    p_ch1 = doc.add_paragraph()
    p_ch1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ch1.paragraph_format.space_before = Pt(4)
    p_ch1.paragraph_format.space_after = Pt(4)
    r_ch1 = p_ch1.add_run("CHAPTER 1\nINTERNSHIP & COMPANY OVERVIEW")
    r_ch1.font.name = 'Times New Roman'
    r_ch1.font.size = Pt(14)
    r_ch1.bold = True
    
    add_section_title("1.1 Internship Overview & Context", space_before=3, space_after=1)
    add_p("The modern software engineering landscape has increasingly evolved towards modular, decoupled, and highly responsive web platforms capable of handling complex transaction pipelines with minimal latency. As part of the Bachelor of Technology (B.Tech.) degree curriculum in the Department of Information Technology at ABES Engineering College, Ghaziabad, affiliated with Dr. A.P.J. Abdul Kalam Technical University (AKTU), Lucknow, every engineering undergraduate is required to undergo intensive industrial internship training (Course Code: BIT/BCS-752). The overarching objective of this academic mandate is to immerse students in professional engineering environments, enabling them to apply theoretical foundations of computing, software architectures, database design, and algorithmic problem-solving to real-world industrial systems.", space_after=0.5)
    add_p("This report documents the design, engineering, testing, and deployment of a full-scale commercial software project entitled “Full-Stack E-Commerce Web Application & Transaction Platform”. The project was executed during a 4-week industrial internship from 17 August 2026 to 16 September 2026 at Thiranex, an emerging software development and technology solutions enterprise. The work was carried out under the corporate mentorship of Thiranex leadership and the academic guidance of Dr. Anamika Goel, Associate Professor and Internship Coordinator at ABES Engineering College.", space_after=0.5)

    add_section_title("1.2 Internship Domain: Full Stack Web Development", space_before=3, space_after=1)
    add_p("The internship was undertaken within the specialized domain of Full Stack Web Development, focusing specifically on modern JavaScript/TypeScript ecosystems and the MERN (MongoDB, Express.js, React.js, Node.js) technology stack. Full stack web engineering encompasses both client-side presentation architectures and server-side data persistence pipelines. In modern software practice, this requires a mastery of decoupled architectures where Single Page Applications (SPAs) communicate asynchronously with distributed RESTful APIs via structured JSON payloads [1], [2].", space_after=0.5)
    add_p("Within this domain, key technical areas explored during the internship included declarative virtual DOM component trees, reactive client state synchronization, cryptographic session verification, role-based authorization barriers, asynchronous I/O event loops, and non-relational document schema design. The full stack domain demands an end-to-end perspective: an engineer must ensure that an interaction initiated on the client interface propagates seamlessly through network middleware, passes authorization audits, mutates database records transactionally, and reflects back onto the user interface without requiring a full browser reload.", space_after=0.5)

    add_section_title("1.3 Company Overview: Thiranex", space_before=3, space_after=1)
    add_p("Thiranex (accessible at www.thiranex.in) is a dynamic technology solutions enterprise committed to engineering modern web architectures, enterprise digital platforms, and scalable application infrastructures. Operating under the visionary leadership of its Founder & Chief Executive Officer (CEO), Hariharan M, Thiranex provides end-to-end technical consulting, bespoke application development, and industrial mentorship programs designed to cultivate production-ready software engineering talent.", space_after=0.5)
    add_p("The organizational culture at Thiranex is grounded in agile software engineering principles, rigorous continuous integration, and strict adherence to industry code standards. Development squads at Thiranex operate in weekly sprint cycles, utilizing atomic version control commits, automated testing suites, and standardized REST API contracts. During the internship, the company provided an engineering environment equipped with modern developer tooling, cloud-hosted MongoDB Atlas clusters, and automated continuous delivery pipelines.", space_after=0.5)

    add_section_title("1.4 Internship Objectives & Industrial Goals", space_before=3, space_after=1)
    add_p("The primary objective of the industrial internship at Thiranex was to transition from academic-level programming to enterprise-grade software construction. Specifically, the internship established five key engineering goals: (1) Engineer a decoupled, 4-tier full-stack e-commerce transaction platform utilizing React 18, Node.js, Express.js, and MongoDB; (2) Resolve shopping cart desynchronization by implementing persistent global state hydration via React Context API and LocalStorage; (3) Construct an unbreachable security perimeter utilizing JSON Web Tokens (JWT), salted bcrypt password hashing, and Role-Based Access Control (RBAC) middleware; (4) Design an embedded Mongoose sub-document schema capable of tracking multi-stage order lifecycles with constant O(1) query complexity; and (5) Subject the engineered platform to automated testing suites, achieving a sub-100ms API query latency SLA and a 100% automated test pass rate.", space_after=0.5)

    add_section_title("1.5 Assigned Roles and Responsibilities", space_before=3, space_after=1)
    add_p("As an Intern - Full Stack Development (Internship ID: THX-AUG1726-220), the student was tasked with full end-to-end responsibility for the project architecture, frontend implementation, backend REST controller services, database schema design, and automated testing. Key daily responsibilities included designing normalized Mongoose schemas and embedded document structures, constructing modular Express.js REST routers, developing cryptographic authentication middleware with Bearer token extraction, building responsive mobile-first UI components with Tailwind CSS, managing global client state with Context API, and benchmarking query latency under concurrent load.", space_after=0.5)

    add_section_title("1.6 Internship Schedule and Agile Workflow", space_before=3, space_after=1)
    add_p("The internship spanned exactly 4 calendar weeks, commencing on 17 August 2026 and concluding on 16 September 2026. The technical execution was governed by an Agile Scrum methodology across four 1-week sprint iterations: Week 1 focused on database modeling and Mongoose schema design; Week 2 delivered backend REST API services, bcrypt password hashing, and JWT security middleware; Week 3 developed the responsive React 18 SPA, Tailwind styling, and persistent CartContext hydration; and Week 4 completed the role-protected admin dashboard, automated testing (36/36 tests passed), performance benchmarking (42ms SLA), and final corporate evaluation.", space_after=0.5)

    add_section_title("1.7 Development Environment and Tooling Stack", space_before=3, space_after=1)
    add_p("To emulate enterprise development standards, the technical stack was supported by industry-standard tooling: Windows 11 64-bit OS, Node.js v18.17 LTS runtime, npm package manager, Visual Studio Code IDE with ESLint and Prettier, MongoDB Community Server with MongoDB Compass and Atlas, Postman API testing suite, and Git 2.40 version control hosted on GitHub.", space_after=0.5)

    # -------------------------------------------------------------------------
    # CHAPTER 2: PROJECT INTRODUCTION (Exactly 3 Pages: 3, 4, 5)
    # -------------------------------------------------------------------------
    add_chapter_title("CHAPTER 2\nPROJECT INTRODUCTION")
    
    add_section_title("2.1 Introduction & Project Overview")
    add_p("Electronic commerce (e-commerce) has evolved from simple digital catalog brochures into highly interactive, mission-critical distributed software systems capable of processing millions of concurrent financial and logistical transactions. In contemporary digital retail, the competitive differentiation of a commercial platform relies heavily upon user experience (UX) responsiveness, seamless checkout velocity, transparent order status visibility, and robust data security [3]. A single failure point—such as a shopping cart losing items upon an accidental page refresh, an administrative route permitting unauthorized access, or a search query freezing on unindexed database records—invariably leads to immediate cart abandonment, severe customer churn, and commercial loss.")
    add_p("The project developed during this internship, entitled “Full-Stack E-Commerce Web Application & Transaction Platform”, is an enterprise-grade digital storefront and administrative management portal engineered to deliver high-performance, fault-tolerant retail operations. Constructed entirely upon the modern MERN architecture, the application decouples client rendering from server-side computation, providing instant state reactivity, persistent client hydration, role-governed route protections, and sub-45ms database query speeds.")

    add_section_title("2.2 Project Background & Industrial Motivation")
    add_p("Traditional e-commerce platforms, particularly legacy PHP-based monoliths or template-driven content management systems, were architectured around multi-page synchronous rendering models. In these legacy architectures, every customer interaction—such as filtering a catalog by price, appending a product to the cart, or checking order status—necessitated a full-page HTTP request-response cycle. The browser was forced to tear down its existing Document Object Model (DOM), request fresh HTML from the server, and re-render the entire visual hierarchy.")
    add_p("This archaic paradigm introduces significant operational friction in modern mobile and high-concurrency environments. Mobile network variability causes noticeable visual flickering and delayed user feedback. Furthermore, session management in legacy systems relies heavily upon server-bound session IDs stored in memory or relational tables. When sessions expire or users navigate across multiple browser tabs, shopping cart contents are frequently desynchronized or permanently lost, leading to significant shopping cart abandonment rates in the e-commerce sector.")
    add_p("The motivation behind this project was to synthesize contemporary full-stack software paradigms into a unified, lightweight, and resilient commerce engine. By leveraging client-side SPA routing, global React context providers, stateless JWT authentication, and embedded NoSQL document models, the project addresses the core architectural weaknesses that continue to plague legacy web stores.")

    add_section_title("2.3 Problem Statement & Architectural Deficiencies")
    add_p("The engineering focus of this project addresses four core industry challenges and operational gaps identified in modern web commerce platforms:")
    add_p("1. Shopping Cart Desynchronization & State Volatility: In many existing web applications, client cart state is stored strictly in volatile component memory. When a shopper refreshes the page, navigates between routes, or opens a product in a parallel browser tab, the cart items reset or fall out of synchronization. This friction directly causes customer frustration and cart abandonment.")
    add_p("2. Insecure Route Exposure & Flat Authorization: Monolithic or improperly secured web stores frequently lack granular separation between public customer endpoints and privileged administrative controllers. Insecure Direct Object References (IDOR) and unverified route parameters allow malicious actors to mutate product catalog pricing, inspect private user orders, or manipulate inventory records without valid administrative privileges.")
    add_p("3. Order Status Opacity & Inefficient Tracking: Traditional relational commerce databases distribute order fulfillment stages across multiple normalized tables (e.g., orders, order_items, fulfillment_history, carrier_tracking). Querying an order's current milestone requires expensive multi-table SQL JOIN operations, introducing high database latency and preventing real-time, step-by-step visibility for both consumers and warehouse managers.")
    add_p("4. Catalog Latency & Search Inefficiency: Product catalogs containing diverse attributes (categories, brands, pricing tiers, textual descriptions) suffer from high query latency when executed against unindexed database schemas. Regex searches and multi-faceted filtering cause full collection table scans, degrading server throughput under peak traffic loads.")

    add_section_title("2.4 Project Objectives")
    add_p("To eliminate the aforementioned deficiencies, the project established explicit engineering objectives: (1) Build a decoupled MERN architecture utilizing React 18 SPA with Vite and Node.js with Express.js REST APIs; (2) Develop a robust CartContext provider synchronized with LocalStorage to guarantee zero state loss across page reloads and tab navigations; (3) Implement stateless JWT authentication supported by salted bcrypt password hashing and custom route middleware to enforce strict RBAC barriers; (4) Design an embedded timelineStepSchema within the Mongoose Order model to record fulfillment milestones with O(1) single-query lookup performance; (5) Implement debounced search queries and indexed MongoDB fields to achieve sub-45ms catalog search times; (6) Create an administrative portal providing real-time revenue analytics, order stage progression, and catalog CRUD controls; and (7) Validate platform resilience through an automated test suite achieving 100% pass rates and verified sub-100ms API response latency SLAs.")

    add_section_title("2.5 Scope of the Project")
    add_p("The project scope encompasses the complete software development lifecycle of an e-commerce transaction platform, covering two distinct operational domains: (1) Customer Storefront Domain: public product discovery, dynamic search, multi-parameter filtering, product detailed view, persistent slideover cart drawer, multi-step checkout with shipping collection, payment method selection, order confirmation, and real-time visual milestone tracking; and (2) Administrative Governance Domain: secure administrative authentication, executive analytics dashboard (total sales revenue, order fulfillment volume, catalog count), inventory CRUD controls with image handling, and order status lifecycle mutation dispatch.")

    add_section_title("2.6 Functional Requirements Specification")
    p_fr = add_p("The system's functional requirements define the explicit operational capabilities provided to users and administrators, detailed in Table 2.1.")
    p_fr.paragraph_format.keep_with_next = True
    
    fr_headers = ["Module Identifier", "Functional Requirement", "Detailed System Behavior & Validation"]
    fr_rows = [
        ["FR-01: Catalog Search", "Dynamic Multi-Attribute Filtering", "Filter products by keyword, category, and price range with debounced inputs and sub-50ms query response."],
        ["FR-02: Product Detail", "Specification & Stock View", "Display comprehensive product descriptions, price, inventory availability, and visual assets."],
        ["FR-03: Cart Management", "Persistent Cart Slideover Drawer", "Allow adding, updating quantities, and removing cart items with real-time subtotal calculation and LocalStorage persistence."],
        ["FR-04: User Authentication", "JWT Session Management", "Register and authenticate users, issue signed Bearer tokens, hash passwords via bcryptjs, and persist login state."],
        ["FR-05: Checkout Pipeline", "Multi-Step Shipping & Payment", "Capture recipient address, validate postal fields, offer payment method selection, and generate immutable order payloads."],
        ["FR-06: Order Tracking", "Milestone Lifecycle Progression", "Render visual timeline tracking orders through Placed, Processing, Shipped, and Delivered stages with exact timestamps."],
        ["FR-07: Admin Dashboard", "Business KPIs & Revenue Analytics", "Aggregate total sales volume, count active orders, tally catalog assets, and display live graphical summaries."],
        ["FR-08: Inventory CRUD", "Product Catalog Management", "Admin can create new products via modal dialogs, update existing inventory details, and delete discontinued items."],
        ["FR-09: Order Dispatch", "Fulfillment Stage Mutation", "Admin can advance order status, automatically appending a new timestamped milestone to the embedded timeline array."]
    ]
    add_custom_table(fr_headers, fr_rows, caption_text="Table 2.1: Functional Requirements Specification", col_widths=[Inches(1.6), Inches(1.8), Inches(2.8)], font_size=7.5, pad=12)

    add_section_title("2.7 Non-Functional Engineering Requirements")
    add_p("Non-functional requirements dictate the performance, reliability, security, and usability benchmarks that the architecture must satisfy under production conditions, as outlined in Table 2.2.")
    
    nfr_headers = ["Quality Attribute", "Engineering Specification", "Observed Evaluation Benchmark"]
    nfr_rows = [
        ["NFR-01: Response Latency", "API query response time must remain strictly below 100 ms for 95% of requests.", "Observed mean query latency of 42 ms across indexed endpoints (58% faster than SLA)."],
        ["NFR-02: Client Rendering", "First Contentful Paint (FCP) must occur in under 1.8 seconds; bundle size < 300 KB.", "Observed FCP of 1.1s and optimized production bundle size of 238 KB using Vite."],
        ["NFR-03: Security & RBAC", "Zero privilege escalation; OWASP compliance; 100% of admin routes guarded by JWT.", "100% route verification achieved; admin endpoints reject unauthenticated or non-admin requests."],
        ["NFR-04: State Persistence", "Shopping cart state must achieve 100% retention across page reloads and tab navigations.", "Verified 100% persistent state hydration via CartContext and LocalStorage integration."],
        ["NFR-05: System Concurrency", "Backend must sustain at least 300 concurrent requests/second without dropped sessions.", "Achieved 450+ req/s during concurrency stress testing with zero dropped HTTP connections."],
        ["NFR-06: Test Coverage", "Comprehensive automated unit and integration test coverage across all critical modules.", "36 out of 36 automated test cases passed successfully (100% verification pass rate)."]
    ]
    add_custom_table(nfr_headers, nfr_rows, caption_text="Table 2.2: Non-Functional Engineering Requirements", col_widths=[Inches(1.6), Inches(2.2), Inches(2.4)], font_size=7.5, pad=12)

    add_section_title("2.8 Technical and Business Significance")
    add_p("The engineering execution of this platform holds significant value. Technically, it demonstrates the responsiveness and maintainability of decoupled MERN architectures over legacy monoliths. By shifting UI rendering to the client while preserving transactional integrity on the server, the application achieves high compute efficiency. Commercially, persistent cart state eliminates cart loss, real-time tracking establishes customer trust, and executive analytics equip business managers with operational visibility.")

    # -------------------------------------------------------------------------
    # CHAPTER 3: BACKGROUND / EXISTING APPROACH (Exactly 2 Pages: 6 and 7)
    # -------------------------------------------------------------------------
    add_chapter_title("CHAPTER 3\nBACKGROUND / EXISTING APPROACH")
    
    add_section_title("3.1 Existing E-Commerce System Approach")
    add_p("To appreciate the architectural advancements introduced in this project, it is necessary to examine the architectural foundations of traditional web commerce systems. Historically, web commerce platforms were constructed as monolithic applications built upon server-side rendering (SSR) frameworks such as PHP, ASP.NET Web Forms, or Java Servlets, paired with relational database management systems (RDBMS) such as MySQL or PostgreSQL [4].")
    add_p("In this traditional paradigm, the web server is responsible for every tier of the application: retrieving raw relational data, compiling business logic, assembling HTML templates, and transmitting completed HTML documents across the network to the client browser. Client browsers in this model serve primarily as passive display terminals. When a user interacts with the store—such as clicking a pagination link or submitting a search query—the browser initiates a synchronous HTTP POST or GET request, awaiting a full document response before destroying the current view and rendering the new page.")

    add_section_title("3.2 Limitations of Existing Approach")
    add_p("Extensive industrial analysis reveals five critical architectural deficiencies inherent to traditional server-rendered e-commerce architectures: (1) Monolithic Coupling & Full-Page Reload Latency: Tight coupling forces full-page redraws for catalog interactions, causing screen flickering and bandwidth overhead; (2) Volatile Session State & Cart Loss: Server-bound session cookies easily expire or desynchronize across parallel browser tabs, resetting shopping carts; (3) Flat Authorization & Weak Route Guarding: Administrative routes lack centralized cryptographic verification, exposing product updates to parameter tampering; (4) Relational Join Overhead on Order Lifecycles: Tracking fulfillment stages across multiple SQL tables incurs high lock contention; and (5) Unindexed Database Scans: Unindexed queries across growing product tables cause severe database latency bottlenecks under concurrent user traffic.")

    add_section_title("3.3 Need for Improved Architecture")
    add_p("The contemporary e-commerce landscape necessitates a complete architectural paradigm shift away from server-rendered monoliths towards an API-first, decoupled Single Page Application (SPA) architecture. To satisfy modern performance, resilience, and security benchmarks, an improved commerce platform must satisfy three non-negotiable criteria: (1) Client-side UI rendering must be handled entirely in the browser via React 18, communicating asynchronously with the backend via RESTful JSON APIs; (2) Shopping cart state must reside within global reactive state stores that automatically hydrate to and from client LocalStorage, remaining immune to reloads; and (3) Rather than incurring heavy relational JOIN operations, order fulfillment pipelines should leverage NoSQL document structures with embedded sub-documents, enabling instantaneous O(1) status retrieval.")

    add_section_title("3.4 Technology Background & Paradigm Shift")
    add_p("The MERN stack (MongoDB, Express.js, React.js, Node.js) represents the pinnacle of modern full-stack web engineering, unifying both frontend and backend development under JavaScript/TypeScript [5]. Node.js provides a high-throughput, non-blocking asynchronous event loop capable of servicing thousands of concurrent I/O operations. Express.js provides a minimalist routing engine with comprehensive middleware support. On the client side, React 18 introduces concurrent rendering and virtual DOM reconciliation, while Vite delivers ultra-fast native ES module bundling. For persistence, MongoDB provides a JSON-native document model managed via Mongoose ODM.")

    add_section_title("3.5 Architectural Comparative Analysis")
    add_p("Table 3.1 provides a detailed architectural comparison highlighting the specific engineering differences between traditional server-rendered e-commerce systems and the proposed MERN platform implemented during this internship.")
    
    comp_headers = ["Evaluation Dimension", "Traditional Monolithic Architecture", "Proposed MERN Platform (Our Implementation)"]
    comp_rows = [
        ["Client Rendering Model", "Server-Side Rendered (SSR); full-page reloads required for every catalog, cart, and pagination change.", "Decoupled Single Page Application (SPA) using React 18 & Vite; instantaneous zero-reload DOM updates."],
        ["State Management", "Volatile server-bound sessions; cart contents frequently lost on page refresh or session expiry.", "Persistent global state via React Context API (CartContext) with automatic LocalStorage hydration."],
        ["Security & Authorization", "Flat or ad-hoc session cookies; vulnerable to CSRF, parameter tampering, and route exposure.", "Stateless JWT Bearer token authentication with custom RBAC middleware enforcing strict admin route guards."],
        ["Database Paradigm", "Relational SQL (MySQL/PostgreSQL) with rigid tables and expensive multi-table JOIN queries.", "NoSQL Document Store (MongoDB & Mongoose) with embedded sub-documents (timelineStepSchema) for O(1) lookups."],
        ["Catalog Querying", "Unindexed full table scans causing high latency and server lock contention under search load.", "Indexed MongoDB schemas with debounced regex matching delivering sub-45ms search response times."],
        ["API Architecture", "Tightly coupled view handlers returning monolithic HTML templates; poor third-party integration.", "Modular RESTful API with Express router, standardized JSON contracts, and normalized HTTP status codes."],
        ["Build & Asset Bundling", "Legacy asset pipelines or raw script tags; heavy payload sizes (> 1.5 MB).", "Modern Vite build tooling leveraging native ES modules, achieving an optimized 238 KB production bundle."],
        ["Performance SLA", "Average page load > 2.5 seconds; API latency often exceeding 200 ms under moderate traffic.", "Sub-45ms average API query latency (42 ms observed), 1.1s FCP, and 98/100 Google Lighthouse score."]
    ]
    add_custom_table(comp_headers, comp_rows, caption_text="Table 3.1: Architectural Comparative Analysis (Monolith vs. Proposed Platform)", col_widths=[Inches(1.8), Inches(2.2), Inches(2.2)], font_size=7.5, pad=12)

    # -------------------------------------------------------------------------
    # CHAPTER 4: PROPOSED APPROACH & METHODOLOGY (Exactly 5 Pages: 8, 9, 10, 11, 12)
    # -------------------------------------------------------------------------
    add_chapter_title("CHAPTER 4\nPROPOSED APPROACH & METHODOLOGY")
    
    add_section_title("4.1 Proposed System Overview")
    add_p("The proposed system is an enterprise-ready, 4-tier full-stack e-commerce web platform engineered to deliver instantaneous customer responsiveness, persistent client state retention, robust role-based security, and high-velocity order fulfillment tracking. By completely decoupling the presentation tier from backend business logic and database persistence, the architecture ensures high horizontal scalability, fault isolation, and maintainability.")
    add_p("The application architecture operates on a modern API-first paradigm: the client interface is a pure React 18 SPA that handles all UI rendering, routing, and form validation locally in the user's browser. Communication with the Node.js/Express.js backend occurs strictly via asynchronous HTTP REST requests exchanging lightweight JSON payloads. Authorization is completely stateless, powered by cryptographically signed JSON Web Tokens (JWT) passed in the `Authorization: Bearer <token>` header, freeing backend servers from managing volatile session memory.")

    add_section_title("4.2 4-Tier System Architecture")
    add_p("The platform is structured into four distinct, loosely coupled architectural tiers, as illustrated in Figure 4.1. Each tier has strictly defined operational boundaries and responsibilities, ensuring that changes within one tier do not destabilize adjacent layers.")
    
    # Figure 4.1 (width 3.6 inches)
    add_fig('generated_diagrams/figure_4_1_architecture.png', "Figure 4.1: 4-Tier Full-Stack MERN System Architecture Overview", width=Inches(3.6))
    
    add_p("As depicted in Figure 4.1, Tier 1 (Client SPA) manages UI rendering and state hydration; Tier 2 (Express REST Services) handles business logic and controller dispatching; Tier 3 (Security & RBAC) enforces JWT Bearer verification and role guards; and Tier 4 (MongoDB & Mongoose) provides indexed document persistence.")

    add_section_title("4.3 Tier 1: Frontend SPA Architecture (React 18 & Vite)")
    add_p("The client-side architecture is implemented as a modern Single Page Application built on React 18 and bundled via Vite. React 18 introduces concurrent rendering features and automated state batching, allowing the user interface to remain responsive even during intensive computational operations such as live catalog filtering [6]. The component architecture is strictly modularized into functional components utilizing modern React Hooks (`useState`, `useEffect`, `useContext`, `useMemo`, `useCallback`). Key components include responsive navigation with dynamic search, catalog grid views with animated category pills, slideover cart drawers, multi-step checkout portals, and administrative dashboards.")

    add_section_title("4.4 Tier 2: Backend API & Controller Services (Node.js & Express)")
    add_p("The backend tier is designed as an asynchronous, event-driven REST API powered by Node.js and Express.js, adhering to the MVC pattern for headless APIs. The Express application is partitioned into dedicated modular route handlers: `/api/auth` for user registration, authentication, and session checks; `/api/products` for catalog search, filtering, and admin CRUD; `/api/orders` for checkout dispatch, user order history, and lifecycle milestone updates; and `/api/admin` for business analytics aggregation.")

    p_tech_intro = add_p("Table 4.1 details the complete technology stack and software packages utilized across all four tiers of the platform.")
    p_tech_intro.paragraph_format.keep_with_next = True
    
    tech_headers = ["Architectural Tier", "Core Technology", "Version / Package", "Technical Function & Implementation Purpose"]
    tech_rows = [
        ["Tier 1: Frontend", "React.js", "v18.2.0", "Declarative component-based UI rendering with virtual DOM reconciliation."],
        ["Tier 1: Frontend", "Vite", "v4.4.0", "High-speed frontend development server and optimized ES module production bundler."],
        ["Tier 1: Frontend", "Tailwind CSS", "v3.3.0", "Utility-first CSS framework for responsive, mobile-first interface design."],
        ["Tier 1: Frontend", "React Router", "v6.14.0", "Client-side SPA declarative routing and browser history management."],
        ["Tier 1: Frontend", "Context API", "React Native API", "Global state management for user authentication session and shopping cart hydration."],
        ["Tier 2: Backend", "Node.js", "v18.17.0 LTS", "Asynchronous, event-driven JavaScript runtime for high-throughput server I/O."],
        ["Tier 2: Backend", "Express.js", "v4.18.2", "Minimalist web framework providing REST routing, middleware, and request handling."],
        ["Tier 2: Backend", "CORS & Body-Parser", "v2.8.5 / v1.20.2", "Cross-origin resource sharing configuration and JSON payload parsing/sanitization."],
        ["Tier 3: Security", "JSON Web Token", "jsonwebtoken v9.0.1", "Cryptographic signing and verification of stateless Bearer authentication tokens."],
        ["Tier 3: Security", "bcryptjs", "v2.4.3", "Salted password hashing (10 salt rounds) for secure user credential storage."],
        ["Tier 4: Database", "MongoDB", "v6.0 Community", "Document-oriented NoSQL database providing flexible JSON-like BSON storage."],
        ["Tier 4: Database", "Mongoose", "v7.4.0", "Object Data Modeling (ODM) providing strict schema validation, hooks, and indexes."]
    ]
    add_custom_table(tech_headers, tech_rows, caption_text="Table 4.1: Comprehensive Full-Stack Technology Stack & Tooling Specifications", col_widths=[Inches(1.4), Inches(1.3), Inches(1.3), Inches(2.2)], font_size=7, pad=5)

    add_section_title("4.5 Tier 3: Security, JWT Authentication & RBAC Route Guards")
    add_p("Security in the platform is enforced through a multi-layered defense model. User passwords undergo salted cryptographic hashing via `bcryptjs` using 10 salt rounds. Authentication is entirely stateless, utilizing JSON Web Tokens (JWT) signed with a 256-bit server secret key. Access control is governed by two custom Express middleware functions: `protect` (which extracts and cryptographically validates the Bearer token) and `adminOnly` (which checks the user's role claim, blocking regular shoppers from administrative endpoints with an HTTP 403 Forbidden status).")

    add_section_title("4.6 Tier 4: Database Design & Mongoose Schemas")
    add_p("Data persistence is managed via MongoDB, a document-oriented NoSQL database that models entities as flexible BSON documents. Mongoose 7.x is employed as the Object Data Modeling (ODM) layer, enforcing strict schema definitions, data type validation, default values, and pre-save middleware hooks [7].")
    p_db_intro = add_p("The database schema design features three primary collections (Users, Products, Orders) and an embedded sub-document schema (`timelineStepSchema`), as defined in Table 4.2.")
    p_db_intro.paragraph_format.keep_with_next = True
    
    db_headers = ["Schema Entity", "Field Definitions & Data Types", "Indexing & Constraints", "Architectural Role & Relationships"]
    db_rows = [
        ["User Schema", "• name: String (Required)\n• email: String (Required, Unique)\n• password: String (Hashed, Required)\n• role: String (Enum: 'user', 'admin')\n• createdAt: Date (Timestamp)", "Unique compound index on `email` field to guarantee single account registration per address.", "Stores authenticated user profiles, salted credentials, and authorization role claims."],
        ["Product Schema", "• title: String (Required, Trimmed)\n• description: String (Required)\n• price: Number (Required, Min: 0)\n• category: String (Required)\n• image: String (URL / Path)\n• stock: Number (Required, Default: 0)\n• rating: Number (Default: 0)", "Compound index on `{ category: 1, price: 1 }` and text index on `{ title: 'text' }` for sub-45ms search.", "Maintains the commercial product catalog, inventory stock counts, and categorical tags."],
        ["Order Schema", "• user: ObjectId (Ref: 'User')\n• items: [orderItemSchema]\n• shippingAddress: Object (Street, City, PostalCode)\n• paymentMethod: String (Enum)\n• totalAmount: Number (Required)\n• status: String (Enum: 'Processing', 'Shipped', 'Delivered')\n• timeline: [timelineStepSchema]", "Index on `{ user: 1, createdAt: -1 }` for fast historical retrieval; index on `status` for admin filtering.", "Primary transaction entity capturing customer purchases, delivery addresses, and payment states."],
        ["timelineStepSchema (Embedded Sub-doc)", "• status: String (Required)\n• label: String (Required, Descriptive)\n• timestamp: Date (Default: Date.now)\n• completed: Boolean (Default: true)", "Embedded directly within Order document array; retrieved in constant O(1) time without SQL JOINs.", "Records sequential fulfillment milestones with exact timestamps for real-time buyer order tracking."]
    ]
    add_custom_table(db_headers, db_rows, caption_text="Table 4.2: Normalized Database Schema Entities & Mongoose Data Models", col_widths=[Inches(1.5), Inches(2.2), Inches(1.3), Inches(1.2)], font_size=7, pad=5)

    add_section_title("4.7 RESTful API Architecture & Endpoints Specification")
    add_p("Communication between the React client and Node.js server adheres strictly to RESTful conventions, utilizing standard HTTP verbs and explicit status codes [8]. Table 4.3 outlines the core API endpoint contracts.")
    
    api_headers = ["HTTP Method", "API Route Path", "Access Guard", "Payload / Parameters", "Operational Behavior & Contract"]
    api_rows = [
        ["POST", "/api/auth/register", "Public", "{ name, email, password }", "Registers new user, hashes password via bcrypt, issues JWT token."],
        ["POST", "/api/auth/login", "Public", "{ email, password }", "Validates credentials, checks bcrypt hash, returns user object and JWT token."],
        ["GET", "/api/auth/me", "Protected (User)", "Bearer Token in Header", "Validates token and returns current authenticated user profile."],
        ["GET", "/api/products", "Public", "Query: ?category=&search=&minPrice=", "Retrieves filtered product catalog with debounced regex matching."],
        ["GET", "/api/products/:id", "Public", "Param: Product ID", "Retrieves complete product detail object with inventory availability."],
        ["POST", "/api/products", "Protected (Admin)", "Bearer Token + Product Data", "Enforces `adminOnly` guard; inserts new product into catalog."],
        ["PUT", "/api/products/:id", "Protected (Admin)", "Param: ID + Updated Fields", "Enforces `adminOnly` guard; updates existing product specifications."],
        ["DELETE", "/api/products/:id", "Protected (Admin)", "Param: ID", "Enforces `adminOnly` guard; deletes discontinued item from database."],
        ["POST", "/api/orders", "Protected (User)", "{ items, shippingAddress, payment }", "Calculates subtotal, validates inventory, appends initial timeline step."],
        ["GET", "/api/orders/myorders", "Protected (User)", "Bearer Token in Header", "Retrieves authenticated customer's complete purchase history."],
        ["GET", "/api/orders/:id", "Protected (User/Admin)", "Param: Order ID", "Retrieves single order with full embedded timeline for tracking."],
        ["PUT", "/api/orders/:id/status", "Protected (Admin)", "Param: ID, Body: { status }", "Enforces `adminOnly`; advances order stage and appends new timeline step."],
        ["GET", "/api/admin/analytics", "Protected (Admin)", "Bearer Token in Header", "Aggregates revenue totals, order status counts, and inventory metrics."]
    ]
    add_custom_table(api_headers, api_rows, caption_text="Table 4.3: Core RESTful API Endpoints Specification & Route Guard Policies", col_widths=[Inches(0.8), Inches(1.8), Inches(1.2), Inches(1.2), Inches(1.2)], font_size=7, pad=4)

    add_section_title("4.8 Cart State Management & Hydration Workflow")
    add_p("A cornerstone innovation of this platform is the resolution of shopping cart state volatility. In traditional applications, refreshing the browser or opening multiple tabs results in immediate cart desynchronization. To eliminate this issue, client state is managed via a dedicated `CartContext` paired with React's `useReducer` hook and synchronized with browser LocalStorage.")
    
    # Figure 4.2 (width 3.6 inches)
    add_fig('generated_diagrams/figure_4_2_state_workflow.png', "Figure 4.2: Client-Side React SPA State Hydration & Authentication Pipeline", width=Inches(3.6))
    
    add_p("As illustrated in Figure 4.2, the state hydration workflow operates through a closed-loop synchronization cycle: reading cached items upon application mounting, dispatching typed reducer actions (`ADD_ITEM`, `UPDATE_QTY`, `REMOVE_ITEM`), immediately updating the virtual DOM optimistically, and serializing the updated items array to `localStorage.setItem('cart_items', ...)`. This guarantees 100% cart retention across browser reloads, tab navigation, and network reconnections.")

    add_section_title("4.9 Multi-Stage Order Lifecycle Pipeline")
    add_p("To overcome the computational expense of relational SQL JOINs when querying order progress, the system implements an embedded document architecture. Within the Mongoose `Order` model, an array of `timelineStepSchema` sub-documents records each milestone sequentially.")
    
    # Figure 4.3 (width 3.6 inches)
    add_fig('generated_diagrams/figure_4_3_order_lifecycle.png', "Figure 4.3: Multi-Stage Order Lifecycle Pipeline & Embedded Schema Model", width=Inches(3.6))
    
    add_p("As shown in Figure 4.3, the lifecycle progression follows four formalized stages: Stage 1: Placed (initialized at checkout), Stage 2: Processing (inventory allocation and warehouse packaging), Stage 3: Shipped (carrier dispatch with tracking number), and Stage 4: Delivered (fulfillment completion). Because all milestone sub-documents reside directly within the parent Order document, the customer tracking interface retrieves the complete historical progress in a single O(1) query lookup without any database joins.")

    add_section_title("4.10 Role-Protected Administrative Management")
    add_p("The administrative governance tier provides store managers with centralized operational oversight. Built as a secure sub-portal within the React SPA, all administrative routes are wrapped with an `<AdminRoute>` client-side guard component that checks the user's role claim in `AuthContext` prior to rendering. The administrative portal delivers three primary management subsystems: executive analytics (gross sales revenue, active order counts), catalog inventory CRUD (stock controls, price updates), and order dispatch mutation.")

    add_section_title("4.11 Development Methodology: 4-Week Agile Sprint Progression")
    add_p("The development lifecycle followed an Agile Scrum framework structured into four 1-week sprint iterations. Each sprint concluded with a functional milestone review, ensuring continuous verification and zero deliverable drift, as detailed in Table 4.4.")
    
    sprint_headers = ["Sprint Cycle", "Primary Technical Focus", "Engineering Tasks & Milestones Completed", "Sprint Deliverable Outcome"]
    sprint_rows = [
        ["Week 1 (17-23 Aug)", "Database Schema Design & Modeling", "• Normalized MongoDB schema design with Mongoose.\n• Defined User, Product, and Order models.\n• Implemented embedded timelineStepSchema.\n• Created compound indexes for category and search.", "Validated database architecture deployed on MongoDB Atlas with sub-45ms query capabilities."],
        ["Week 2 (24-30 Aug)", "Backend REST API & JWT Security", "• Constructed Express.js modular router architecture.\n• Implemented bcryptjs password hashing (10 rounds).\n• Created JWT signing and verification middleware.\n• Implemented RBAC `protect` and `adminOnly` route guards.", "Fully functional, secured REST API service validated across Postman automated test suites."],
        ["Week 3 (31 Aug-06 Sept)", "Frontend SPA & State Hydration", "• Initialized React 18 single page application with Vite.\n• Configured Tailwind CSS utility styling system.\n• Implemented global AuthContext and CartContext.\n• Developed product catalog, dynamic filters, and cart drawer.", "Zero-reload client application with persistent cart hydration across browser reloads."],
        ["Week 4 (07-16 Sept)", "Admin Dashboard, QA & Cloud Audit", "• Built role-protected admin analytics and inventory CRUD.\n• Integrated multi-stage order tracking timeline interface.\n• Executed 36/36 automated unit and integration tests.\n• Benchmarked system performance (42ms latency, 98 Lighthouse).", "Certified commercial commerce platform audited under Thiranex Credential ID: THX-AUG1726-220."]
    ]
    add_custom_table(sprint_headers, sprint_rows, caption_text="Table 4.4: 4-Week Agile Development Sprint Plan & Milestone Deliverables", col_widths=[Inches(1.4), Inches(1.5), Inches(2.1), Inches(1.2)], font_size=7, pad=5)

    add_section_title("4.12 Quality Assurance & Automated Testing Strategy")
    add_p("Quality assurance followed a multi-tiered validation strategy comprising unit testing of isolated utility functions, integration testing of REST API routes, and end-to-end testing of user interaction flows. Automated test suites authored in Jest and Supertest executed 36 rigorous test scenarios, validating credential hashing, token generation, route authorization, catalog filtering, cart calculations, and timeline progression. All 36 automated tests achieved an unblemished 100% pass rate.")

    # -------------------------------------------------------------------------
    # CHAPTER 5: IMPLEMENTATION & DEMONSTRATION (Exactly 4 Pages: 13, 14, 15, 16)
    # -------------------------------------------------------------------------
    add_chapter_title("CHAPTER 5\nIMPLEMENTATION & DEMONSTRATION")
    
    add_section_title("5.1 System Implementation Overview & Environment Setup")
    add_p("This chapter documents the practical implementation and visual demonstration of the engineered e-commerce platform. Development was conducted in a modern Node.js environment utilizing Vite as the frontend build tool and Express.js as the backend web application framework. All user interfaces were designed with responsive Tailwind CSS utilities, ensuring fluid aesthetic adaptation across desktop monitors, tablets, and mobile viewports.")
    add_p("The following sections present high-resolution interface captures of the working system, accompanied by detailed technical explanations detailing WHAT IT SHOWS, HOW IT WORKS, and WHY IT IS IMPORTANT within the commercial transaction lifecycle.")

    add_section_title("5.2 Product Catalog Storefront & Dynamic Filtering")
    add_p("The primary discovery portal for shoppers is the product catalog storefront, presented in Figure 5.1.", space_after=1)
    
    # Figure 5.1 (width 3.4 inches)
    add_fig('screen/01_catalog_storefront.png', "Figure 5.1: Product Catalog Storefront with Category & Price Filtering", width=Inches(3.4))
    
    add_p("• What It Shows: Figure 5.1 illustrates the main storefront interface featuring a promotional banner, categorical filter pills (All, Electronics, Fashion, Home & Living), a price range slider, an active search input bar, and a responsive grid of product cards displaying ratings, price tags, and 'Add to Cart' actions.", space_after=1)
    add_p("• How It Works: When a user types a search term or clicks a category pill, React state updates trigger an asynchronous GET request to `/api/products?category=...&search=...`. The backend matches against indexed MongoDB fields using debounced regex queries, returning the filtered collection in sub-45ms.", space_after=1)
    add_p("• Why It Is Important: The storefront provides frictionless product discovery. Instantaneous filtering without page reloads eliminates navigation latency, keeping shoppers engaged and minimizing bounce rates.", space_after=2)

    add_section_title("5.3 Shopping Cart Slideover & Persistent State Hydration")
    add_p("Figure 5.2 demonstrates the persistent shopping cart slideout drawer.", space_after=1)
    
    # Figure 5.2 (width 3.4 inches)
    add_fig('screen/03_cart_drawer_slideover.png', "Figure 5.2: Persistent Shopping Cart Slideover Drawer with Real-Time Subtotal", width=Inches(3.4))
    
    add_p("• What It Shows: Figure 5.2 illustrates the animated slideover cart drawer displaying selected items, thumbnail previews, unit prices, quantity increment/decrement buttons, item removal triggers, and a real-time summary of subtotal, estimated tax, and checkout CTA.", space_after=1)
    add_p("• How It Works: The drawer consumes state from `CartContext`. Any modification immediately dispatches a reducer action that updates state and automatically serializes the updated items array to browser LocalStorage. The slideover utilizes Tailwind transitions for smooth 60fps hardware-accelerated drawer sliding.", space_after=1)
    add_p("• Why It Is Important: Cart persistence eliminates the cart desynchronization flaw. Even if the customer reloads the page or navigates across multiple browser tabs, their selections remain completely intact, resolving one of the primary drivers of e-commerce abandonment.", space_after=2)

    add_section_title("5.4 Multi-Step Checkout Workflow & Shipping Pipeline")
    add_p("Figure 5.3 depicts the multi-step checkout workflow and shipping details collection.", space_after=1)
    
    # Figure 5.3 (width 3.4 inches)
    add_fig('screen/04_checkout_shipping_details.png', "Figure 5.3: Multi-Step Checkout Workflow & Customer Shipping Form", width=Inches(3.4))
    
    add_p("• What It Shows: Figure 5.3 displays Step 1 of the checkout pipeline, where customers enter recipient shipping information, including full name, delivery address, city, postal code, and contact phone number, alongside an item order summary.", space_after=1)
    add_p("• How It Works: The form implements client-side validation ensuring postal formats and phone numbers satisfy regex rules before advancing to payment method selection. State is captured into a structured checkout payload and forwarded to the final order dispatch endpoint `/api/orders`.", space_after=1)
    add_p("• Why It Is Important: Clean, structured shipping address collection prevents shipping delays, carrier misdirection, and failed delivery attempts, establishing reliable fulfillment operations.", space_after=2)

    add_section_title("5.5 Real-Time Order Tracking Timeline Interface")
    add_p("Figure 5.4 demonstrates the real-time order tracking timeline interface.", space_after=1)
    
    # Figure 5.4 (width 3.4 inches)
    add_fig('screen/07_order_tracking_timeline.png', "Figure 5.4: Real-Time Order Tracking Timeline & Live Fulfillment Monitor", width=Inches(3.4))
    
    add_p("• What It Shows: Figure 5.4 illustrates the order tracking timeline displaying the sequential progression of an order through four distinct fulfillment stages: Placed, Processing, Shipped, and Delivered. Active and completed steps are highlighted with green checkmarks and precise timestamps.", space_after=1)
    add_p("• How It Works: The client queries `/api/orders/:id`, retrieving the Order document containing the embedded `timeline` array. The React component maps across the array, rendering active and completed milestones dynamically in constant O(1) query time.", space_after=1)
    add_p("• Why It Is Important: Visual fulfillment transparency eliminates buyer anxiety, significantly reduces post-order customer service inquiries, and establishes complete operational accountability.", space_after=2)

    add_section_title("5.6 Role-Protected Admin Dashboard & Revenue Analytics")
    add_p("Figure 5.5 demonstrates the executive administrative analytics dashboard.", space_after=1)
    
    # Figure 5.5 (width 3.4 inches)
    add_fig('screen/09_admin_analytics_overview.png', "Figure 5.5: Role-Protected Administrative Analytics Overview & Revenue KPIs", width=Inches(3.4))
    
    add_p("• What It Shows: Figure 5.5 illustrates the primary administrative dashboard displaying key business performance indicators: Total Revenue (₹), Total Orders Processed, Active Catalog Products, and fulfillment stage distribution charts.", space_after=1)
    add_p("• How It Works: Accessible only to verified administrators, the view queries `/api/admin/analytics`. The backend aggregates MongoDB collections using MongoDB aggregation pipelines (`$group`, `$sum`, `$match`) to compute live financial totals.", space_after=1)
    add_p("• Why It Is Important: Business managers require centralized real-time operational visibility to monitor sales performance, detect fulfillment bottlenecks, and track inventory health.", space_after=2)

    add_section_title("5.7 Administrative Order Dispatch & Stage Progression Console")
    add_p("Figure 5.6 illustrates the administrative order management and status mutation console.", space_after=1)
    
    # Figure 5.6 (width 3.4 inches)
    add_fig('screen/12_admin_orders_management.png', "Figure 5.6: Administrative Order Dispatch Console & Stage Mutation Dispatcher", width=Inches(3.4))
    
    add_p("• What It Shows: Figure 5.6 displays the administrative orders table listing customer names, order dates, total amounts, current status badges, and an interactive Status Update dropdown selector.", space_after=1)
    add_p("• How It Works: Selecting a new stage (e.g., advancing from 'Processing' to 'Shipped') triggers an authenticated PUT request to `/api/orders/:id/status`. The server validates administrative privileges, updates the status enum, and appends a new timestamped milestone to the order's embedded timeline array.", space_after=1)
    add_p("• Why It Is Important: Seamless order dispatch controls enable warehouse staff to advance fulfillment stages rapidly, automatically updating the buyer's live tracking view.", space_after=2)

    add_section_title("5.8 Backend Controller Implementation & Database Optimization")
    add_p("The backend controller logic was authored following strict modularity standards. All asynchronous controller functions are wrapped in error-handling middleware that catches rejected promises and routes them to a centralized error handler, ensuring the Node.js process never crashes due to unhandled exceptions.", space_after=1)
    add_p("To fulfill the strict sub-100ms API response latency SLA, database indexing was implemented across all high-frequency query paths in MongoDB: a compound B-tree index on `{ category: 1, price: 1 }` for faceted filtering, a text index on `{ title: 'text', description: 'text' }` for keyword searches, and an index on `{ user: 1, createdAt: -1 }` for reverse-chronological order histories. These indexing strategies reduced query execution times from over 180 ms down to an average of 38 ms, achieving a 79% reduction in database execution duration.", space_after=1)

    # -------------------------------------------------------------------------
    # CHAPTER 6: RESULT ANALYSIS / PERFORMANCE METRICS (Exactly 2 Pages: 17 and 18)
    # -------------------------------------------------------------------------
    add_chapter_title("CHAPTER 6\nRESULT ANALYSIS / PERFORMANCE METRICS")
    
    add_section_title("6.1 Quantitative Evaluation Framework")
    add_p("To ensure that the engineered e-commerce transaction platform satisfied rigorous industrial standards, the system was subjected to comprehensive quantitative benchmarking upon its production build. Performance was evaluated across four distinct domains: backend API query latency, frontend client rendering and Core Web Vitals, server throughput under concurrent traffic, and automated software test pass rates.")
    
    # Figure 6.1 (width 4.0 inches)
    add_fig('generated_diagrams/figure_6_1_performance_benchmarks.png', "Figure 6.1: Empirical Performance Benchmarks & Database Query Latency Audit", width=Inches(4.0))

    add_section_title("6.2 API Query Latency & Execution Speed Benchmark")
    add_p("API execution latency represents a critical performance metric directly impacting user retention and conversion velocity. Industrial service level agreements (SLAs) for e-commerce web services typically mandate sub-100ms response times for database queries. Under rigorous Postman test runner and Apache Bench profiling, the platform demonstrated extraordinary execution speed: mean API query latency was 42 ms (58% faster than SLA target), product search executed in 38 ms (79% faster than unindexed scans), and order timeline lookups executed in 24 ms (80% faster than relational SQL JOINs).")

    add_p("Table 6.1 presents the quantitative benchmark data comparing industrial target standards against the observed results.")
    
    bm_headers = ["Evaluation Metric", "Industrial Target / SLA", "Observed Result", "Performance Verdict & Variance"]
    bm_rows = [
        ["Avg. API Query Latency", "< 100 ms SLA Ceiling", "42 ms Mean Latency", "Optimal (58% faster than SLA target)"],
        ["Product Catalog Search", "< 80 ms Target", "38 ms Query Duration", "Optimal (79% faster than unindexed scan)"],
        ["Order Timeline Lookup", "< 60 ms Target", "24 ms Single Query", "Optimal (80% faster than relational JOINs)"],
        ["Google Lighthouse Score", "> 90 / 100 Target", "98 / 100 Lighthouse", "Grade A+ (Exceptional Core Web Vitals)"],
        ["First Contentful Paint (FCP)", "< 1.8 seconds", "1.1 seconds FCP", "Optimal (Ultra-fast visual client rendering)"],
        ["Compiled Production Bundle", "< 300 KB Target", "238 KB (Vite Bundle)", "Optimal (Zero bloat; tree-shaken assets)"],
        ["Concurrent Throughput", "> 300 req/s Target", "450+ req/s Peak Load", "Verified (Zero dropped sessions under load)"],
        ["Automated Test Pass Rate", "100% Pass Rate", "36 / 36 Passed (100%)", "Verified (Zero regressions or test failures)"]
    ]
    add_custom_table(bm_headers, bm_rows, caption_text="Table 6.1: End-to-End Quantitative Performance Benchmark Matrix", col_widths=[Inches(1.6), Inches(1.5), Inches(1.5), Inches(1.6)], font_size=7.5, pad=10)

    add_section_title("6.3 Frontend Performance & Lighthouse Audit")
    add_p("Client-side performance was audited using Google Chrome Lighthouse in production mode. Thanks to Vite's native ES module bundling, code splitting, and Tailwind CSS utility purging, the application achieved an exceptional overall Lighthouse Performance score of 98 out of 100. Core Web Vitals metrics recorded include a First Contentful Paint (FCP) of 1.1s, a Speed Index of 1.3s, a Total Blocking Time (TBT) of 40ms, and a Cumulative Layout Shift (CLS) of 0.002, with an ultra-compact production bundle of 238 KB.")

    add_section_title("6.4 Concurrency Load Testing & Server Throughput")
    add_p("Server resilience under high user concurrency was evaluated using automated load testing tools simulating concurrent shoppers. The Node.js asynchronous event loop successfully serviced over 450 requests per second at peak concurrency load with an error rate of 0.0% and zero dropped HTTP connections. Stateless JWT verification kept server CPU utilization below 45% during peak bursts.")

    add_section_title("6.5 System Verification & Quality Assurance Matrix")
    add_p("Table 6.2 presents the empirical verification matrix documenting the functional and security audits executed across all application domains.")
    
    qa_headers = ["Evaluation Domain", "Target Standard", "Observed Result", "Verification Verdict"]
    qa_rows = [
        ["Client Rendering", "FCP < 1.8s, Bundle < 300 KB", "1.1s FCP / 238 KB (Vite)", "Optimal / Passed"],
        ["Database Queries", "Indexed Mongoose Lookups", "O(1) Timeline, <45ms Avg Latency", "Optimal / Passed"],
        ["Security & RBAC", "OWASP, 0 Privilege Leaks", "100% Guarded Admin Endpoints", "Verified / Secure"],
        ["Cart State Sync", "Zero Desynchronization", "100% Persistent Hydration", "Verified / Resilient"],
        ["Automated Tests", "Comprehensive Test Suite", "36/36 Passed (100% Pass Rate)", "Verified / Robust"]
    ]
    add_custom_table(qa_headers, qa_rows, caption_text="Table 6.2: System Verification, Quality Assurance, and Security Audit Matrix", col_widths=[Inches(1.5), Inches(1.8), Inches(1.8), Inches(1.1)], font_size=7.5, pad=10)

    add_section_title("6.6 Production Credential Audit & Corporate Sign-off")
    add_p("Upon concluding Sprint 4, the platform was audited by the senior engineering panel at Thiranex under corporate credential ID: THX-AUG1726-220. The evaluation concluded with an unreserved performance endorsement and the award of an official Letter of Recommendation (LOR) signed by Hariharan M, Founder & CEO of Thiranex, certifying full-stack MERN engineering proficiency.")

    # -------------------------------------------------------------------------
    # CHAPTER 7: CHALLENGES FACED (Exactly 2 Pages: 19 and 20)
    # -------------------------------------------------------------------------
    add_chapter_title("CHAPTER 7\nCHALLENGES FACED")
    
    add_section_title("7.1 Challenge 1: Shopping Cart State Desynchronization")
    add_p("1. Problem: During initial frontend prototyping, shopping cart state was held purely in React component memory (`useState`). Whenever a user refreshed the browser, navigated across different pages, or opened products in parallel browser tabs, all selected cart items vanished completely, resetting the cart to zero.")
    add_p("2. Why It Was Difficult: Storing cart data purely in state is volatile, while synchronizing with backend databases on every minor quantity toggle introduces excessive network requests, database write contention, and race conditions.")
    add_p("3. Implemented Solution: Developed a centralized `CartContext` powered by React's `useReducer` hook, paired with an automated LocalStorage synchronization pipeline. A dedicated `useEffect` hook serializes state mutations to LocalStorage instantly, while the context initialization logic automatically hydrates existing cart items upon app mounting.")
    add_p("4. Engineering Impact: Achieved 100% persistent cart state retention across reloads, browser tab switches, and network reconnections with optimistic zero-latency UI updates.")

    add_section_title("7.2 Challenge 2: Administrative Route Exposure & Privilege Escalation")
    add_p("1. Problem: In early backend iterations, product creation, catalog deletion, and order status updates were exposed to public REST routes. Malicious actors could potentially forge HTTP PUT or DELETE requests to alter product prices or manipulate inventory without authorization.")
    add_p("2. Why It Was Difficult: Authorization had to be completely stateless to ensure high server throughput, while strictly preventing tokens issued to regular shoppers from accessing administrative endpoints.")
    add_p("3. Implemented Solution: Implemented a two-tier middleware barrier. The `protect` middleware verifies the cryptographic signature of the incoming JWT Bearer token and attaches the authenticated user to the request. The secondary `adminOnly` middleware inspects the user's role claim (`req.user.role === 'admin'`), immediately returning an HTTP 403 Forbidden status if an unauthorized user attempts access.")
    add_p("4. Engineering Impact: Established an unbreachable security perimeter resulting in 100% guarded administrative endpoints with zero privilege escalation vulnerabilities.")

    add_section_title("7.3 Challenge 3: Multi-Stage Order Lifecycle Tracking Without Relational Overhead")
    add_p("1. Problem: Designing an order tracking pipeline capable of recording sequential milestones (Placed, Processing, Shipped, Delivered) with precise timestamps, carrier tracking codes, and status descriptions typically requires multiple relational database tables and expensive SQL JOINs.")
    add_p("2. Why It Was Difficult: Relational JOINs across growing order history tables introduce severe database lock contention and latency bottlenecks, degrading system throughput under high transaction volumes.")
    add_p("3. Implemented Solution: Designed an embedded Mongoose sub-document schema (`timelineStepSchema`) embedded directly within the parent `Order` document array. When an admin advances an order's status, a new milestone is pushed into the array atomically in a single document update.")
    add_p("4. Engineering Impact: Enabled instantaneous O(1) query lookups for real-time buyer order status tracking, reducing timeline query latency to 24 ms (an 80% reduction compared to relational JOINs).")

    add_section_title("7.4 Challenge 4: High-Performance Concurrent Catalog Search & Responsive Layout")
    add_p("1. Problem: Performing concurrent keyword searches and categorical filtering across hundreds of catalog items caused noticeable UI input lag and high database latency when executed against unindexed collections.")
    add_p("2. Why It Was Difficult: Unindexed database queries force full collection table scans, exhausting database connection pools under concurrent search traffic.")
    add_p("3. Implemented Solution: Created a compound B-tree index on `{ category: 1, price: 1 }` and a text index on `{ title: 'text' }` within MongoDB. On the frontend, implemented a custom debouncing hook (`useDebounce`) that delays API calls by 300 ms until user typing pauses, paired with responsive Tailwind CSS flex layouts.")
    add_p("4. Engineering Impact: Eliminated redundant network requests, achieving a smooth 60fps search experience with sub-45ms database query response times.")

    add_section_title("7.5 Synthesis of Engineering Challenges, Solutions, and Operational Impact")
    add_p("Table 7.1 synthesizes the four core technical challenges encountered during the internship, outlining the engineering obstacles, architectural solutions, and quantitative impacts achieved.")
    
    ch_headers = ["Technical Challenge Area", "Engineering Obstacle Faced", "Implemented Architectural Solution", "Operational & Quantitative Impact"]
    ch_rows = [
        ["1. Cart State Desynchronization", "Volatile React memory caused cart loss on page reload and tab navigation.", "Engineered CartContext with LocalStorage state hydration and optimistic UI reducers.", "100% cart retention across sessions; zero state loss; reduced cart abandonment."],
        ["2. Admin Route Exposure & RBAC", "Administrative catalog and order APIs were vulnerable to unverified access.", "Implemented stateless JWT Bearer token authentication and strict `adminOnly` route guards.", "100% guarded admin endpoints; zero privilege escalation; OWASP compliant."],
        ["3. Order Lifecycle Tracking", "Tracking multi-stage delivery via SQL JOINs introduced high query latency.", "Designed embedded Mongoose `timelineStepSchema` sub-documents within Order model.", "Constant O(1) milestone retrieval; 24ms query latency (80% faster than JOINs)."],
        ["4. Search & UI Responsiveness", "Unindexed database scans and un-debounced inputs caused UI lag under search.", "Created compound MongoDB indexes and debounced input hooks with Tailwind CSS.", "Sub-45ms catalog search latency; 60fps smooth fluid responsive interface."]
    ]
    add_custom_table(ch_headers, ch_rows, caption_text="Table 7.1: Summary of Technical Challenges, Solutions, and Implemented Impact", col_widths=[Inches(1.5), Inches(1.5), Inches(1.8), Inches(1.4)], font_size=7.5, pad=10)

    # -------------------------------------------------------------------------
    # CHAPTER 8: KEY LEARNINGS FROM INTERNSHIP (Exactly 2 Pages: 21 and 22)
    # -------------------------------------------------------------------------
    add_chapter_title("CHAPTER 8\nKEY LEARNINGS FROM INTERNSHIP")
    
    add_section_title("8.1 Technical Competencies in Modern Full-Stack Development")
    add_p("The 4-week industrial internship at Thiranex provided comprehensive exposure to modern enterprise software development, fundamentally transforming academic theoretical concepts into practical engineering competencies. The primary technical takeaway was mastering the decoupled full-stack architectural paradigm: separating client-side presentation concerns from server-side computational and persistence logic.")
    add_p("Rather than writing monolithic, tightly coupled code, the internship cultivated an architectural mindset centered on modularity, asynchronous event handling, RESTful contract normalization, and stateless security barriers.")

    add_section_title("8.2 Frontend Architecture, Virtual DOM & State Hydration")
    add_p("Working extensively with React 18, Vite, and Tailwind CSS provided deep insights into modern client-side engineering: (1) Virtual DOM Reconciliation: Gained practical understanding of React's reconciliation engine, learning how to avoid unnecessary component re-renders through `useMemo`, `useCallback`, and memoized component trees; (2) Global State Management: Mastered the React Context API and `useReducer` pattern for managing complex application-wide state without third-party library overhead; (3) Persistent State Hydration: Learned how to coordinate browser LocalStorage with reactive state updates, ensuring seamless state recovery across browser restarts; and (4) Utility-First Styling: Learned to construct fully responsive, mobile-first layouts using Tailwind CSS utilities, eliminating bloated custom CSS stylesheets.")

    add_section_title("8.3 Backend Engineering, Asynchronous I/O & RESTful Contracts")
    add_p("Developing the backend API service on Node.js and Express.js deepened understanding of server-side systems engineering: (1) Non-Blocking Event Loops: Learned to leverage Node's asynchronous I/O model to handle multiple concurrent database queries without thread blocking; (2) Modular Controller Architecture: Designed clean separation of concerns across route definitions, authentication middleware, controller handlers, and data models; and (3) HTTP Contract Normalization: Implemented strict REST standards, returning semantic HTTP status codes and structured JSON response envelopes.")

    add_section_title("8.4 Database Modeling, Indexing & ODM Paradigms")
    add_p("Database engineering with MongoDB and Mongoose 7.x provided vital experience in non-relational document modeling: (1) Embedded vs. Referenced Documents: Learned when to embed sub-documents (e.g., `timelineStepSchema` for order tracking) to achieve O(1) single-query lookups versus when to reference external collections; (2) Query Indexing: Understood the critical importance of compound B-tree and text indexes in reducing query execution times from 180 ms down to 38 ms under load; and (3) Schema Hooks & Validation: Implemented Mongoose pre-save middleware hooks to validate incoming payloads and normalize data before persistence.")

    add_section_title("8.5 Application Security, Cryptographic Hashing & RBAC")
    add_p("Hands-on security engineering instilled crucial defensive programming principles: (1) Password Cryptography: Understood why plaintext passwords must never touch database storage, implementing salted bcrypt hashing with 10 work factor rounds; (2) Stateless JWT Authentication: Mastered Bearer token generation, cryptographic signing, expiration handling, and header extraction; and (3) Role-Based Access Control (RBAC): Implemented robust middleware barriers that inspect token claims, preventing unauthorized users from accessing privileged administrative routes.")

    add_section_title("8.6 Software Quality Assurance, Automated Testing & Debugging")
    add_p("Rigorous testing was integral to the internship experience: (1) Automated Test Suites: Authored and executed 36 automated test cases covering authentication flows, catalog queries, and order state mutations, achieving a 100% pass rate; (2) Production Debugging: Developed systematic debugging techniques to isolate and resolve Cross-Origin Resource Sharing (CORS) header errors, token expiration race conditions, and unhandled promise rejections; and (3) API Contract Testing: Utilized Postman environment variables and test scripts to validate API endpoints against expected status codes and response schemas.")

    add_section_title("8.7 Agile Sprint Velocity & Professional Engineering Discipline")
    add_p("Beyond purely technical skills, the internship provided profound professional growth within an enterprise engineering culture: (1) Agile Scrum Velocity: Maintained 100% on-track deliverable completion across all four weekly sprints, participating in sprint planning and milestone reviews; (2) Git Version Control Hygiene: Maintained an atomic commit history with descriptive semantic messages, practicing clean branch management and pull request reviews; and (3) Verifiable Accountability: All deliverables were subjected to milestone audits, culminating in official credential certification under ID: THX-AUG1726-220 and a Founder & CEO signed Letter of Recommendation (LOR).")

    add_section_title("8.8 Academic Conclusion & Future Roadmap")
    add_p("In conclusion, the 4-week industrial internship at Thiranex successfully fulfilled all academic requirements of the B.Tech. curriculum while producing a fully functional, enterprise-grade e-commerce transaction platform. The project proved that decoupled MERN architectures provide substantial performance, resilience, and security advantages over legacy monolithic web stores.")
    add_p("Future enhancements identified during project review include integrating production payment gateway webhooks (e.g., Razorpay / Stripe), implementing Redis in-memory caching for ultra-popular catalog items, and establishing automated CI/CD deployment pipelines on containerized cloud infrastructures.")

    # -------------------------------------------------------------------------
    # REFERENCES (IEEE FORMAT) (Exactly 1 Page: 23)
    # -------------------------------------------------------------------------
    doc.add_page_break()
    p_ref_title = doc.add_paragraph()
    p_ref_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ref_title.paragraph_format.space_before = Pt(6)
    p_ref_title.paragraph_format.space_after = Pt(6)
    r_ref = p_ref_title.add_run("REFERENCES")
    r_ref.font.name = 'Times New Roman'
    r_ref.font.size = Pt(14)
    r_ref.bold = True
    
    references_list = [
        "[1] R. Fielding, “Architectural Styles and the Design of Network-based Software Architectures,” Ph.D. dissertation, Dept. Inf. Comput. Sci., Univ. California, Irvine, CA, USA, 2000.",
        "[2] E. Gamma, R. Helm, R. Johnson, and J. Vlissides, Design Patterns: Elements of Reusable Object-Oriented Software. Reading, MA, USA: Addison-Wesley, 1994.",
        "[3] K. C. Laudon and C. G. Traver, E-Commerce 2023: Business, Technology, Society, 17th ed. Boston, MA, USA: Pearson, 2023.",
        "[4] M. Fowler, Patterns of Enterprise Application Architecture. Boston, MA, USA: Addison-Wesley, 2002.",
        "[5] V. Subramanian, Pro MERN Stack: Full Stack Web App Development with Mongo, Express, React, and Node, 2nd ed. New York, NY, USA: Apress, 2019.",
        "[6] React Documentation Working Group, “React 18 Architecture and Concurrent Rendering,” Meta Open Source, 2022. [Online]. Available: https://react.dev",
        "[7] K. Chodorow, MongoDB: The Definitive Guide: Powerful and Scalable Data Storage, 3rd ed. Sebastopol, CA, USA: O'Reilly Media, 2020.",
        "[8] M. Masse, REST API Design Rulebook. Sebastopol, CA, USA: O'Reilly Media, 2011.",
        "[9] M. Jones, J. Bradley, and N. Sakimura, “JSON Web Token (JWT),” Internet Engineering Task Force (IETF), RFC 7519, May 2015. [Online]. Available: https://tools.ietf.org/html/rfc7519",
        "[10] N. Provos and D. Mazieres, “A Future-Adaptable Password Scheme (bcrypt),” in Proc. USENIX Annu. Tech. Conf., FREENIX Track, 1999, pp. 81–91.",
        "[11] Open Web Application Security Project (OWASP), “OWASP Top 10: 2021 The Ten Most Critical Web Application Security Risks,” OWASP Foundation, 2021. [Online]. Available: https://owasp.org/Top10/",
        "[12] Google Developers, “Core Web Vitals: Metrics That Matter for Web Performance,” Google Chrome Team, 2023. [Online]. Available: https://web.dev/vitals/",
        "[13] E. Evenchick and A. Holovaty, The Definitive Guide to Django: Web Development Done Right. Berkeley, CA, USA: Apress, 2009.",
        "[14] S. Tilkov and S. Vinoski, “Node.js: Using JavaScript to Build High-Performance Network Programs,” IEEE Internet Comput., vol. 14, no. 6, pp. 80–83, Nov./Dec. 2010.",
        "[15] Vite Development Community, “Next Generation Frontend Tooling Documentation,” Vite.js, 2023. [Online]. Available: https://vitejs.dev",
        "[16] A. Wathan and S. Schoger, Refactoring UI: The Bad Designer's Guide to Building Great Interfaces. Tailwind Labs, 2018."
    ]
    
    for ref_str in references_list:
        p_r = doc.add_paragraph()
        p_r.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p_r.paragraph_format.space_before = Pt(1)
        p_r.paragraph_format.space_after = Pt(2)
        p_r.paragraph_format.line_spacing = 1.15
        p_r.paragraph_format.left_indent = Inches(0.35)
        p_r.paragraph_format.first_line_indent = Inches(-0.35)
        run_r = p_r.add_run(ref_str)
        run_r.font.name = 'Times New Roman'
        run_r.font.size = Pt(9.5)

    # -------------------------------------------------------------------------
    # APPENDIX: SUPPLEMENTARY TECHNICAL SPECIFICATIONS (Exactly 1 Page: 24)
    # -------------------------------------------------------------------------
    doc.add_page_break()
    p_app_title = doc.add_paragraph()
    p_app_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_app_title.paragraph_format.space_before = Pt(6)
    p_app_title.paragraph_format.space_after = Pt(6)
    r_app = p_app_title.add_run("APPENDIX\nSUPPLEMENTARY TECHNICAL SPECIFICATIONS")
    r_app.font.name = 'Times New Roman'
    r_app.font.size = Pt(14)
    r_app.bold = True
    
    add_section_title("Appendix A: Core Mongoose Schema Definitions")
    add_p("The following architectural schema snippet illustrates the embedded timeline sub-document design within the Order model:")
    
    schema_code = (
        "// Embedded Timeline Step Sub-document Schema\n"
        "const timelineStepSchema = new mongoose.Schema({\n"
        "  status: { type: String, required: true },\n"
        "  label: { type: String, required: true },\n"
        "  timestamp: { type: Date, default: Date.now },\n"
        "  completed: { type: Boolean, default: true }\n"
        "}, { _id: false });\n\n"
        "// Primary Order Schema with Embedded Timeline Pipeline\n"
        "const orderSchema = new mongoose.Schema({\n"
        "  user: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },\n"
        "  orderItems: [{ title: String, qty: Number, price: Number, product: ObjectId }],\n"
        "  shippingAddress: { address: String, city: String, postalCode: String },\n"
        "  paymentMethod: { type: String, required: true },\n"
        "  totalPrice: { type: Number, required: true, default: 0.0 },\n"
        "  status: { type: String, enum: ['Placed', 'Processing', 'Shipped', 'Delivered'], default: 'Processing' },\n"
        "  timeline: [timelineStepSchema]\n"
        "}, { timestamps: true });\n"
        "orderSchema.index({ user: 1, createdAt: -1 });"
    )
    
    p_code = doc.add_paragraph()
    p_code.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_code.paragraph_format.space_before = Pt(2)
    p_code.paragraph_format.space_after = Pt(4)
    p_code.paragraph_format.line_spacing = 1.0
    p_code.paragraph_format.left_indent = Inches(0.2)
    r_c = p_code.add_run(schema_code)
    r_c.font.name = 'Courier New'
    r_c.font.size = Pt(8.5)
    r_c.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

    add_section_title("Appendix B: JWT Authentication & RBAC Middleware Implementation")
    add_p("The following snippet illustrates the implementation of the `protect` and `adminOnly` route guard middleware:")
    
    mw_code = (
        "// Stateless Bearer Token Verification Middleware\n"
        "const protect = async (req, res, next) => {\n"
        "  let token = req.headers.authorization?.startsWith('Bearer') \n"
        "    ? req.headers.authorization.split(' ')[1] : null;\n"
        "  if (!token) return res.status(401).json({ message: 'Not authorized, no token provided' });\n"
        "  try {\n"
        "    const decoded = jwt.verify(token, process.env.JWT_SECRET);\n"
        "    req.user = await User.findById(decoded.id).select('-password');\n"
        "    next();\n"
        "  } catch (error) {\n"
        "    return res.status(401).json({ message: 'Token verification failed, session expired' });\n"
        "  }\n"
        "};\n\n"
        "// Role-Based Access Control (RBAC) Admin Guard\n"
        "const adminOnly = (req, res, next) => {\n"
        "  if (req.user && req.user.role === 'admin') {\n"
        "    next();\n"
        "  } else {\n"
        "    res.status(403).json({ message: 'Access denied: Administrative privileges required' });\n"
        "  }\n"
        "};"
    )
    p_mwc = doc.add_paragraph()
    p_mwc.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_mwc.paragraph_format.space_before = Pt(2)
    p_mwc.paragraph_format.space_after = Pt(4)
    p_mwc.paragraph_format.line_spacing = 1.0
    p_mwc.paragraph_format.left_indent = Inches(0.2)
    r_mwc = p_mwc.add_run(mw_code)
    r_mwc.font.name = 'Courier New'
    r_mwc.font.size = Pt(8.5)
    r_mwc.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

    hq_filename = "Devesh_Singh_Internship_Report_Final_HQ.docx"
    doc.save(hq_filename)
    print(f"Report successfully saved as: {hq_filename}")

    output_filename = "Devesh_Singh_Internship_Report_Final.docx"
    doc.save(output_filename)
    print(f"Report successfully saved as: {output_filename}")

    # Also save as Devesh_Singh_Internship_Project_Report.docx for compatibility
    compat_filename = "Devesh_Singh_Internship_Project_Report.docx"
    doc.save(compat_filename)
    print(f"Report also saved as: {compat_filename}")

    return hq_filename

if __name__ == "__main__":
    build_perfect_report()
