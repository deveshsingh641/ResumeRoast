import pymupdf

doc = pymupdf.open('Devesh_Singh_Internship_Report_Final.pdf')
print(f"Total Pages: {len(doc)}\n")
for i, page in enumerate(doc):
    text = page.get_text()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    first_line = lines[0] if lines else 'EMPTY'
    last_line = lines[-1] if lines else 'EMPTY'
    
    # Check for tables/drawings/images on page
    images = page.get_images()
    tables = [line for line in lines if line.startswith("Table ")]
    figs = [line for line in lines if line.startswith("Figure ")]
    
    extra = []
    if images:
        extra.append(f"{len(images)} img(s)")
    if tables:
        extra.append(f"Tables: {', '.join(tables)}")
    if figs:
        extra.append(f"Figs: {', '.join(figs)}")
    extra_str = f" | {' | '.join(extra)}" if extra else ""

    print(f"Page {i+1:02d}: lines={len(lines):2d} | first=\"{first_line[:40]}\" | last=\"{last_line[:35]}\"{extra_str}")
