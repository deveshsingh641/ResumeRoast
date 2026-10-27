import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def fix_table_in_doc(docx_path, output_path):
    doc = docx.Document(docx_path)
    
    # 1. Remove paragraph borders (w:pBdr) from all cover page paragraphs before the table
    # This removes the ugly box with dangling lines above the table!
    for p in doc.paragraphs[:35]:
        pBdr_list = p._p.xpath('.//w:pBdr')
        for bdr in pBdr_list:
            bdr.getparent().remove(bdr)

    # 2. Find Table 0 (the college header table)
    t = doc.tables[0]
    
    # Check if logos exist
    abes_logo_path = 'extracted_template_media/img_0.jpeg'
    aktu_logo_path = 'extracted_template_media/img_1_hq.png'
    if not os.path.exists(aktu_logo_path):
        aktu_logo_path = 'extracted_template_media/img_1.png'
        
    print(f"ABES logo exists: {os.path.exists(abes_logo_path)}")
    print(f"AKTU logo exists: {os.path.exists(aktu_logo_path)}")
    
    # Clear existing rows or reconstruct cleanly
    # Let's check how many rows exist
    print(f"Current Table 0 rows: {len(t.rows)}, cols: {len(t.columns)}")
    
    # If Table 0 has 1 row, add row 1
    if len(t.rows) == 1:
        row2 = t.add_row()
    else:
        row2 = t.rows[1]
        
    # Set table alignment to center
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    # Column widths
    total_w = Inches(6.5)
    w_col0 = Inches(1.3)
    w_col1 = Inches(3.9)
    w_col2 = Inches(1.3)
    
    # Row 0 cells
    cell_abes = t.rows[0].cells[0]
    cell_mid = t.rows[0].cells[1]
    cell_aktu = t.rows[0].cells[2]
    
    cell_abes.width = w_col0
    cell_mid.width = w_col1
    cell_aktu.width = w_col2
    
    cell_abes.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    cell_mid.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    cell_aktu.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    
    set_cell_margins(cell_abes, top=80, bottom=80, left=80, right=80)
    set_cell_margins(cell_mid, top=80, bottom=80, left=100, right=100)
    set_cell_margins(cell_aktu, top=80, bottom=80, left=80, right=80)
    
    # Format Cell 0 (ABES Logo)
    p_abes = cell_abes.paragraphs[0]
    p_abes.text = ""
    p_abes.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_abes.paragraph_format.space_before = Pt(0)
    p_abes.paragraph_format.space_after = Pt(0)
    if os.path.exists(abes_logo_path):
        r_abes = p_abes.add_run()
        r_abes.add_picture(abes_logo_path, width=Inches(0.95))
        
    # Format Cell 1 (ABES ENGINEERING COLLEGE, GHAZIABAD)
    p_mid = cell_mid.paragraphs[0]
    p_mid.text = ""
    p_mid.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_mid.paragraph_format.space_before = Pt(0)
    p_mid.paragraph_format.space_after = Pt(0)
    p_mid.paragraph_format.line_spacing = 1.15
    
    r_mid1 = p_mid.add_run("ABES ENGINEERING COLLEGE,\n")
    r_mid1.font.name = 'Arial'
    r_mid1.font.size = Pt(13)
    r_mid1.bold = True
    r_mid1.font.color.rgb = RGBColor(0x00, 0x00, 0x00)
    
    r_mid2 = p_mid.add_run("GHAZIABAD")
    r_mid2.font.name = 'Arial'
    r_mid2.font.size = Pt(13)
    r_mid2.bold = True
    r_mid2.font.color.rgb = RGBColor(0x00, 0x00, 0x00)
    
    # Format Cell 2 (AKTU Logo)
    p_aktu = cell_aktu.paragraphs[0]
    p_aktu.text = ""
    p_aktu.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_aktu.paragraph_format.space_before = Pt(0)
    p_aktu.paragraph_format.space_after = Pt(0)
    if os.path.exists(aktu_logo_path):
        r_aktu = p_aktu.add_run()
        r_aktu.add_picture(aktu_logo_path, width=Inches(0.90))

    # Row 1 (Affiliation row)
    # Merge cells across Row 1: cell 0, 1, 2
    cell_affil = row2.cells[0]
    for c in row2.cells[1:]:
        cell_affil.merge(c)
        
    cell_affil.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    set_cell_margins(cell_affil, top=100, bottom=100, left=120, right=120)
    
    # Format Row 1 paragraphs
    # Remove any extra paragraphs in cell_affil
    p_affil = cell_affil.paragraphs[0]
    p_affil.text = ""
    p_affil.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_affil.paragraph_format.space_before = Pt(2)
    p_affil.paragraph_format.space_after = Pt(2)
    p_affil.paragraph_format.line_spacing = 1.15
    
    r_af1 = p_affil.add_run("AFFILIATED TO\n")
    r_af1.font.name = 'Arial'
    r_af1.font.size = Pt(11)
    r_af1.bold = True
    r_af1.font.color.rgb = RGBColor(0x00, 0x20, 0x60) # Formal AKTU Navy Blue
    
    r_af2 = p_affil.add_run("DR. A.P.J. ABDUL KALAM TECHNICAL UNIVERSITY, U.P., LUCKNOW\n")
    r_af2.font.name = 'Arial'
    r_af2.font.size = Pt(11.5)
    r_af2.bold = True
    r_af2.font.color.rgb = RGBColor(0x00, 0x20, 0x60)
    
    r_af3 = p_affil.add_run("(Formerly UPTU)")
    r_af3.font.name = 'Arial'
    r_af3.font.size = Pt(10.5)
    r_af3.bold = True
    r_af3.font.color.rgb = RGBColor(0x00, 0x20, 0x60)
    
    # 3. Set clean, professional unified table borders (single black border, 0.75pt = sz 6)
    tblPr = t._tbl.tblPr
    existing_tblBorders = tblPr.xpath('w:tblBorders')
    for b in existing_tblBorders:
        tblPr.remove(b)
        
    tblBorders = parse_xml(f'''
    <w:tblBorders {nsdecls("w")}>
        <w:top w:val="single" w:sz="6" w:space="0" w:color="000000"/>
        <w:left w:val="single" w:sz="6" w:space="0" w:color="000000"/>
        <w:bottom w:val="single" w:sz="6" w:space="0" w:color="000000"/>
        <w:right w:val="single" w:sz="6" w:space="0" w:color="000000"/>
        <w:insideH w:val="single" w:sz="6" w:space="0" w:color="000000"/>
        <w:insideV w:val="single" w:sz="6" w:space="0" w:color="000000"/>
    </w:tblBorders>
    ''')
    tblPr.append(tblBorders)
    
    # 4. Remove the external redundant paragraphs P30, P31, P32 if they exist right after the table
    # Let's find any paragraphs immediately following the table that contain AFFILIATED TO / UPTU
    elements_to_remove = []
    found_table = False
    for el in doc.element.body:
        tag = el.tag.split('}')[-1]
        if tag == 'tbl' and el == t._tbl:
            found_table = True
            continue
        if found_table:
            if tag == 'p':
                txt = el.text.strip()
                if any(k in txt for k in ["AFFILIATED TO", "ABDUL KALAM", "UPTU"]):
                    elements_to_remove.append(el)
                elif "INTERNSHIP CERTIFICATE" in txt:
                    break
                    
    print(f"Removing {len(elements_to_remove)} redundant external affiliation paragraphs...")
    for el in elements_to_remove:
        el.getparent().remove(el)
        
    doc.save(output_path)
    print(f"Fixed document saved to: {output_path}")

if __name__ == "__main__":
    src = "Devesh_Singh_Internship_Report_Final_HQ.docx"
    out = "Devesh_Singh_Internship_Report_Final_HQ.docx"
    fix_table_in_doc(src, out)
