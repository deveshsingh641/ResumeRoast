import docx

doc = docx.Document(r'D:\ResumeRoast\InternshipProjectReportFormat (1).docx')
for i, el in enumerate(doc.element.body[:35]):
    tag = el.tag.split('}')[-1]
    if tag == 'tbl':
        t = docx.table.Table(el, doc)
        print(f'Element {i}: Table ({len(t.rows)}x{len(t.columns)})')
        for r_i, r in enumerate(t.rows):
            print(f'   Row {r_i}: {[c.text.strip().replace("\n", " ") for c in r.cells]}')
    elif tag == 'p':
        p = docx.text.paragraph.Paragraph(el, doc)
        borders = el.xpath('.//w:pBdr')
        print(f'Element {i}: P - "{p.text}" (pBdr={len(borders)})')
