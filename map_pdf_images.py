import pymupdf

doc = pymupdf.open('Devesh_Singh_Internship_Report_Final.pdf')
print(f"Total pages: {len(doc)}\n")

for i, page in enumerate(doc):
    imgs = page.get_images(full=True)
    if imgs:
        print(f"=== PAGE {i+1} ({len(imgs)} image(s)) ===")
        for img in imgs:
            xref = img[0]
            base = doc.extract_image(xref)
            rects = page.get_image_rects(xref)
            bbox = rects[0] if rects else "none"
            print(f"  xref {xref}: name={img[7]}, format={base['ext']}, size={base['width']}x{base['height']}, bbox={bbox}")
