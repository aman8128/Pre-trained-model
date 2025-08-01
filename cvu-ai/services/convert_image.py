import os
import cv2
import sys
import subprocess
from PIL import Image,ImageEnhance
from reportlab.graphics import renderPM
from svglib.svglib import svg2rlg
import svgwrite
from skimage.measure import find_contours
from pdf2image import convert_from_path
import numpy as np
from skimage.transform import resize
from skimage import measure
import vtracer
from scour.scour import scourString, parse_args

def convert_image_to_svg(input_path, output_path):
    output_directory = os.path.dirname(output_path)
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    original = Image.open(input_path).convert("RGBA")
    np_image = np.array(original)

    rgb = np_image[:, :, :3]
    alpha = np_image[:, :, 3]

    # 🧠 Apply edge-preserving smooth sharpening
    edge_preserved = cv2.edgePreservingFilter(rgb, flags=1, sigma_s=50, sigma_r=0.2)
    blurred = cv2.GaussianBlur(edge_preserved, (0, 0), sigmaX=1.0, sigmaY=1.0)
    sharpened = cv2.addWeighted(edge_preserved, 1.5, blurred, -0.5, 0)

    final = np.dstack([sharpened, alpha])

    enhanced_image_path = "enhanced_temp_image.png"
    Image.fromarray(final).save(enhanced_image_path)

    vtracer.convert_image_to_svg_py(
        enhanced_image_path,
        output_path,
        mode="spline",
        filter_speckle=10,
    )
    
    os.remove(enhanced_image_path)

    print(f"✅ Final polished SVG saved at: {output_path}")

def convert_image(input_path, output_path):
    ext_out = output_path.lower().split('.')[-1]
    ext_in = input_path.lower().split('.')[-1]

    try:
        # SVG to Raster
        if ext_in == "svg" and ext_out in ["png", "jpg", "jpeg", "webp"]:
            drawing = svg2rlg(input_path)
            temp_png = "temp_svg_rendered.png"
            renderPM.drawToFile(drawing, temp_png, fmt="PNG")
            img = Image.open(temp_png)
            if ext_out in ["jpg", "jpeg"]:
                img = img.convert("RGB")
            img.save(output_path, quality=95)
            os.remove(temp_png)
            print(f"🖼️ Converted SVG → {ext_out.upper()}")


        # Raster to SVG (Inkscape)
        elif ext_out == "svg" and ext_in in ["png", "jpg", "jpeg", "webp", "bmp", "tiff"]:
            convert_image_to_svg(input_path, output_path)

        # PDF to SVG (via Inkscape)
        elif ext_in == "pdf" and ext_out == "svg":
            convert_image_to_svg(input_path, output_path)

        # Image to PDF
        elif ext_out == "pdf" and ext_in in ["jpg", "jpeg", "png", "webp", "bmp", "tiff"]:
            img = Image.open(input_path).convert("RGB")
            img.save(output_path, "PDF", resolution=100.0)
            print(f"📄 Converted Image → PDF")

        # PDF to Image(s)
        elif ext_in == "pdf" and ext_out in ["jpg", "jpeg", "png", "webp"]:
            doc = fitz.open(input_path)
            for i, page in enumerate(doc):
                pix = page.get_pixmap()
                page_path = output_path.replace(f".{ext_out}", f"_page{i+1}.{ext_out}")
                pix.save(page_path)
                print(f"📸 Saved Page {i+1} → {page_path}")
            doc.close()

        # Raster Image to Raster Image
        elif ext_in in ["jpg", "jpeg", "png", "webp", "bmp", "tiff"] and ext_out in ["jpg", "jpeg", "png", "webp", "bmp", "tiff"]:
            img = Image.open(input_path)
            if ext_out in ["jpg", "jpeg"]:
                img = img.convert("RGB")
            img.save(output_path, quality=95)
            print(f"🔁 Converted {input_path} → {output_path}")

        # SVG to PDF
        elif ext_in == "svg" and ext_out == "pdf":
            drawing = svg2rlg(input_path)
            renderPM.drawToFile(drawing, output_path, fmt="PDF")
            print(f"🔁 Converted SVG → PDF")

        else:
            print("❌ Unsupported format combination:", ext_in, "→", ext_out)

    except Exception as e:
        print("❌ Error:", e)


# CLI Usage
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("\n📦 Usage: python convert_image.py input_file output_file\n")
    else:
        convert_image(sys.argv[1], sys.argv[2])
