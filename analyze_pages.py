import pymupdf

doc = pymupdf.open('Devesh_Singh_Internship_Project_Report.pdf')
for i, page in enumerate(doc):
    text = page.get_text()
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    first_line = lines[0] if lines else '[EMPTY]'
    key_lines = [l for l in lines if any(k in l for k in ['CHAPTER', 'INTERNSHIP', 'DECLARATION', 'ACKNOWLEDGEMENT', 'ABSTRACT', 'TABLE OF CONTENT', 'LIST OF', 'REFERENCES', 'APPENDIX', 'Figure', 'Table', '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.'])]
    print(f"Page {i+1:02d}: first='{first_line[:45]}' | keys={key_lines[:3]}")
