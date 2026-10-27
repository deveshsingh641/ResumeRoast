import os
import win32com.client
import pymupdf
from PIL import Image

def export_word_to_pdf(docx_path, pdf_path):
    print(f"Opening Word to export: {docx_path} -> {pdf_path}")
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    try:
        doc = word.Documents.Open(os.path.abspath(docx_path))
        # Update all fields
        for field in doc.Fields:
            field.Update()
        for section in doc.Sections:
            for footer in section.Footers:
                for field in footer.Range.Fields:
                    field.Update()
                    
        page_count = doc.ComputeStatistics(2) # wdStatisticPages
        print(f"Word document page count: {page_count}")
        
        # Export to PDF (17 = wdExportFormatPDF, 0 = wdExportOptimizeForPrint)
        doc.ExportAsFixedFormat(
            os.path.abspath(pdf_path),
            17,     # ExportFormat = PDF
            False,  # OpenAfterExport = False
            0,      # OptimizeFor = wdExportOptimizeForPrint
            0,      # Range = wdExportAllDocument
            1,      # From
            page_count, # To
            0,      # Item = wdExportDocumentContent
            True,   # IncludeDocProps
            True,   # KeepIRM
            1,      # CreateBookmarks = wdExportCreateHeadingBookmarks
            True,   # DocStructureTags
            True,   # BitmapMissingFonts
            False   # UseISO19005_1
        )
        doc.Close(False)
    finally:
        word.Quit()
    print("Word PDF export completed.")

def inject_lossless_high_res_images(pdf_in, pdf_out):
    print(f"\nInjecting master high-resolution images into: {pdf_out}")
    doc = pymupdf.open(pdf_in)
    
    # Define exact page image replacement mapping:
    # Page index (0-indexed) -> list of replacement image paths in order of appearance
    # If multiple images on a page, order by vertical/horizontal position
    replacements = {
        0: [ # Page 1: ABES logo (left), AKTU logo (right)
            ('extracted_template_media/img_0.jpeg', 'ABES College Logo'),
            ('extracted_template_media/img_1_hq.png', 'AKTU University Logo (HQ 800x800)')
        ],
        1: [ # Page 2: Thiranex Certificate
            ('presentation_assets/thiranex_certificate.png', 'Thiranex Official Certificate (3508x2481)')
        ],
        15: [ # Page 16: Figure 4.1 Architecture
            ('generated_diagrams/figure_4_1_architecture.png', 'Figure 4.1: Architecture Overview (3600x2200 Ultra-HD)')
        ],
        18: [ # Page 19: Figure 4.2 State Workflow
            ('generated_diagrams/figure_4_2_state_workflow.png', 'Figure 4.2: State Hydration Workflow (3600x1500 Ultra-HD)')
        ],
        19: [ # Page 20: Figure 4.3 Order Lifecycle
            ('generated_diagrams/figure_4_3_order_lifecycle.png', 'Figure 4.3: Order Lifecycle Pipeline (3600x1500 Ultra-HD)')
        ],
        21: [ # Page 22: Figure 5.1 Catalog Storefront
            ('screen/01_catalog_storefront.png', 'Figure 5.1: Product Catalog Storefront (2880x1800 Retina)')
        ],
        22: [ # Page 23: Figure 5.2 Cart Drawer (top), Figure 5.3 Checkout (bottom)
            ('screen/03_cart_drawer_slideover.png', 'Figure 5.2: Cart Slideover Drawer (2880x1800 Retina)'),
            ('screen/04_checkout_shipping_details.png', 'Figure 5.3: Checkout Shipping Form (2880x1800 Retina)')
        ],
        23: [ # Page 24: Figure 5.4 Order Tracking (top), Figure 5.5 Admin Dashboard (bottom)
            ('screen/07_order_tracking_timeline.png', 'Figure 5.4: Order Tracking Timeline (2880x1800 Retina)'),
            ('screen/09_admin_analytics_overview.png', 'Figure 5.5: Admin Analytics Dashboard (2880x1800 Retina)')
        ],
        24: [ # Page 25: Figure 5.6 Admin Orders
            ('screen/12_admin_orders_management.png', 'Figure 5.6: Admin Orders Console (2880x1800 Retina)')
        ],
        25: [ # Page 26: Figure 6.1 Performance Benchmarks
            ('generated_diagrams/figure_6_1_performance_benchmarks.png', 'Figure 6.1: Performance Benchmarks (3600x1800 Ultra-HD)')
        ]
    }
    
    total_replaced = 0
    for page_idx, rep_list in replacements.items():
        page = doc[page_idx]
        imgs = page.get_images(full=True)
        # Sort images by y0, then x0 coordinate
        img_info_list = []
        for img in imgs:
            xref = img[0]
            rects = page.get_image_rects(xref)
            bbox = rects[0] if rects else pymupdf.Rect(0, 0, 0, 0)
            img_info_list.append((bbox.y0, bbox.x0, xref, img))
            
        img_info_list.sort(key=lambda item: (item[0], item[1]))
        
        print(f"\nProcessing Page {page_idx + 1} ({len(img_info_list)} images found in PDF):")
        for idx, (img_path, desc) in enumerate(rep_list):
            if idx < len(img_info_list):
                xref = img_info_list[idx][2]
                if os.path.exists(img_path):
                    orig_size = Image.open(img_path).size
                    print(f"  Replacing xref {xref} with: {img_path} ({orig_size[0]}x{orig_size[1]}) [{desc}]")
                    page.replace_image(xref, filename=img_path)
                    total_replaced += 1
                else:
                    print(f"  WARNING: File not found: {img_path}")
            else:
                print(f"  WARNING: No matching image on page {page_idx+1} for index {idx}")
                
    doc.save(pdf_out, garbage=3, deflate=True)
    doc.close()
    print(f"\nSuccessfully replaced {total_replaced} images with pristine high-resolution versions!")
    return total_replaced

def verify_all_pdf_images(pdf_file):
    print(f"\n==========================================")
    print(f"VERIFYING ALL IMAGES IN FINAL PDF: {pdf_file}")
    print(f"==========================================")
    doc = pymupdf.open(pdf_file)
    print(f"Total Pages in PDF: {len(doc)}")
    
    all_ok = True
    image_count = 0
    
    for i, page in enumerate(doc):
        imgs = page.get_images(full=True)
        if imgs:
            for img in imgs:
                image_count += 1
                xref = img[0]
                base = doc.extract_image(xref)
                w = base["width"]
                h = base["height"]
                ext = base["ext"]
                byte_size = len(base["image"])
                rects = page.get_image_rects(xref)
                rect = rects[0] if rects else None
                
                # Calculate effective DPI on page
                if rect and rect.width > 0 and rect.height > 0:
                    dpi_x = (w / rect.width) * 72
                    dpi_y = (h / rect.height) * 72
                    eff_dpi = min(dpi_x, dpi_y)
                else:
                    eff_dpi = 0
                    
                status = "PASS (HIGH QUALITY)" if eff_dpi >= 250 or w >= 800 else "CHECK"
                print(f"Page {i+1:02d} | xref {xref:3d} | {w:4d}x{h:4d} | {ext.upper():4s} | {byte_size/1024:6.1f} KB | Eff. DPI: {eff_dpi:4.0f} | {status}")
                if eff_dpi < 200 and w < 400:
                    all_ok = False
                    
    doc.close()
    print(f"\nTotal embedded images verified: {image_count}")
    print(f"Overall Image Quality Status: {'PASSED (ALL HIGH-RES)' if all_ok else 'FAILED'}")
    return all_ok

if __name__ == "__main__":
    docx_file = "Devesh_Singh_Internship_Report_Final_HQ.docx"
    temp_pdf = "temp_exported.pdf"
    final_pdf_hq = "Devesh_Singh_Internship_Report_Final_HQ.pdf"
    final_pdf = "Devesh_Singh_Internship_Report_Final.pdf"
    
    # 1. Export DOCX to initial PDF
    export_word_to_pdf(docx_file, temp_pdf)
    
    # 2. Inject uncompressed master high-res images
    inject_lossless_high_res_images(temp_pdf, final_pdf_hq)
    
    # Copy to compatibility final PDF
    import shutil
    shutil.copy(final_pdf_hq, final_pdf)
    print(f"Copied to {final_pdf}")
    
    # 3. Verify all images in final PDF
    verify_all_pdf_images(final_pdf_hq)
    
    # Clean up temp
    if os.path.exists(temp_pdf):
        os.remove(temp_pdf)
