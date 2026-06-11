import io
import os
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color
from reportlab.lib.utils import ImageReader
from pypdf import PdfReader, PdfWriter
from PIL import Image

# Configuración de color para el texto y ruta del logo
COLOR_RGB = (244 / 255, 132 / 255, 28 / 255)  # F4841C
LOGO_PATH = os.path.join(os.path.dirname(__file__), 'logo.png')


def _ajustar_transparencia_logo(logo_path, alpha):
    img = Image.open(logo_path).convert("RGBA")

    r, g, b, alpha_channel = img.split()

    nuevo_alpha = alpha_channel.point(lambda px: int(px * alpha))

    img_con_transparencia = Image.merge("RGBA", (r, g, b, nuevo_alpha))

    return img_con_transparencia


def _generar_overlay(width, height, texto, logo_img=None):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(width, height))

    color = Color(*COLOR_RGB, alpha=0.16)
    c.setFillColor(color)

    font_name = "Helvetica-Bold"
    font_size = 40
    c.setFont(font_name, font_size)

    c.saveState()
    c.translate(width / 2, height / 2)
    c.rotate(45)

    text_width = c.stringWidth(texto, font_name, font_size)
    step_x = text_width + 80
    step_y = font_size + 80

    diagonal = (width ** 2 + height ** 2) ** 0.5
    n_x = int(diagonal / step_x) + 2
    n_y = int(diagonal / step_y) + 2

    for i in range(-n_x, n_x):
        for j in range(-n_y, n_y):
            c.drawCentredString(i * step_x, j * step_y, texto)

    c.restoreState()

    # --- Logo en la esquina ---
    if logo_img is not None:
        img_width, img_height = logo_img.size
        aspect = img_height / img_width

        logo_width = width * 0.15
        logo_height = logo_width * aspect

        margin = 20
        x = width - logo_width - margin
        y = margin  # Esquina inferior derecha

        c.drawImage(
            ImageReader(logo_img),
            x, y,
            width=logo_width,
            height=logo_height
        )

    c.save()
    buffer.seek(0)
    return buffer


def aplicar_marca_agua(pdf_bytes, texto, alpha_logo=0.18):
    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()

    logo_img = None
    if os.path.exists(LOGO_PATH):
        logo_img = _ajustar_transparencia_logo(LOGO_PATH, alpha_logo)
    else:
        print(f"[DEBUG] No se encontró logo en {LOGO_PATH}")

    for page in reader.pages:
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)

        overlay_buffer = _generar_overlay(width, height, texto, logo_img)
        overlay_page = PdfReader(overlay_buffer).pages[0]

        page.merge_page(overlay_page)
        writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return output.read()
