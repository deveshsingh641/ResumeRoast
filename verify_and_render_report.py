import os
import win32com.client
import pymupdf # fitz

def verify_and_render():
    docx_path = os.path.abspath("Devesh_Singh_Internship_Report_Final.docx")
    pdf_path = os.path.abspath("Devesh_Singh_Internship_Report_Final.pdf")
    
    print(f"Opening Word to inspect and export: {docx_path}")
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    try:
        doc = word.Documents.Open(docx_path)
        # Update fields (e.g. page numbers)
        for field in doc.Fields:
            field.Update()
        for section in doc.Sections:
            for footer in section.Footers:
                for field in footer.Range.Fields:
                    field.Update()
                    
        # Compute page count
        page_count = doc.ComputeStatistics(2) # 2 = wdStatisticPages
        print(f"\n==========================================")
        print(f"TOTAL WORD DOCUMENT PAGE COUNT: {page_count} PAGES")
        print(f"==========================================\n")
        
        # Save updated docx
        doc.Save()
        
        # Export to PDF (17 = wdExportFormatPDF)
        print(f"Exporting to PDF: {pdf_path}")
        doc.ExportAsFixedFormat(pdf_path, 17, False, 0, 0, 1, page_count)
        doc.Close(False)
    finally:
        word.Quit()
        
    print(f"PDF exported successfully. Rendering pages to images...")
    os.makedirs("report_preview_pages", exist_ok=True)
    pdf_doc = pymupdf.open(pdf_path)
    total_rendered_pages = len(pdf_doc)
    print(f"Total pages in PDF: {total_rendered_pages}")
    
    for i, page in enumerate(pdf_doc):
        pix = page.get_pixmap(dpi=150)
        img_out = f"report_preview_pages/page_{i+1:02d}.png"
        pix.save(img_out)
        print(f"Saved {img_out} ({pix.width}x{pix.height})")
        
    print("\nPage rendering completed successfully.")
    return total_rendered_pages

if __name__ == "__main__":
    verify_and_render()
