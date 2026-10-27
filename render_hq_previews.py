import os
import pymupdf

pdf_path = "Devesh_Singh_Internship_Report_Final_HQ.pdf"
out_dir = "report_preview_pages_hq"
os.makedirs(out_dir, exist_ok=True)

doc = pymupdf.open(pdf_path)
print(f"Rendering {len(doc)} pages of {pdf_path} at 300 DPI for visual quality audit...")

# We can render pages containing images: 1, 2, 16, 19, 20, 22, 23, 24, 25, 26
pages_to_render = [1, 2, 16, 19, 20, 22, 23, 24, 25, 26]

for p_num in pages_to_render:
    page = doc[p_num - 1]
    pix = page.get_pixmap(dpi=300)
    out_file = os.path.join(out_dir, f"page_{p_num:02d}_300dpi.png")
    pix.save(out_file)
    print(f"Rendered Page {p_num:02d}: {pix.width}x{pix.height} ({os.path.getsize(out_file)/1024:.1f} KB)")

doc.close()
print("High-DPI page rendering complete.")
