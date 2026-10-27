import zipfile
from PIL import Image
import io

with zipfile.ZipFile('Devesh_Singh_Internship_Report_Final.docx') as z:
    for name in sorted(z.namelist()):
        if name.startswith('word/media/'):
            data = z.read(name)
            im = Image.open(io.BytesIO(data))
            print(f"{name}: {im.size} ({im.format}), bytes={len(data)}")
