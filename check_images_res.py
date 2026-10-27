import os
from PIL import Image
import pymupdf

images_to_check = [
    'extracted_template_media/img_1_hq.png',
    'extracted_template_media/img_1.png',
    'extracted_template_media/image1.png',
    'presentation_assets/thiranex_certificate.png',
    'generated_diagrams/figure_4_1_architecture.png',
    'generated_diagrams/figure_4_2_state_workflow.png',
    'generated_diagrams/figure_4_3_order_lifecycle.png',
    'generated_diagrams/figure_6_1_performance.png',
    'screen/product_catalog.png',
    'screen/cart_drawer.png',
    'screen/checkout_step1.png',
    'screen/order_tracking.png',
    'screen/admin_dashboard.png',
    'screen/admin_orders.png'
]

print("=== SOURCE IMAGES RESOLUTION ===")
for p in images_to_check:
    if os.path.exists(p):
        im = Image.open(p)
        print(f"{p}: size={im.size}, mode={im.mode}, dpi={im.info.get('dpi')}")
    else:
        print(f"{p}: NOT FOUND")

print("\n=== EXTRACTED IMAGES FROM CURRENT PDF ===")
pdf_doc = pymupdf.open('Devesh_Singh_Internship_Report_Final.pdf')
for i, page in enumerate(pdf_doc):
    img_list = page.get_images(full=True)
    if img_list:
        for img_info in img_list:
            xref = img_info[0]
            base_image = pdf_doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            w = base_image["width"]
            h = base_image["height"]
            bpc = base_image["bpc"]
            cs = base_image["colorspace"]
            print(f"Page {i+1:02d} (xref {xref}): {w}x{h} ({image_ext}, cs={cs}, bpc={bpc}, bytes={len(image_bytes)})")
