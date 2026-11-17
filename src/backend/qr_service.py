import io
import base64
import qrcode
from qrcode.constants import ERROR_CORRECT_M

def generate_qr_png_bytes(content: str, box_size: int = 10, border: int = 3) -> bytes:
    """
    Generate high-resolution PNG image bytes for given text content.
    
    Parameters:
    - content: Payload string or URL to encode.
    - box_size: Dimension in pixels of each QR box/module (default: 10 px).
    - border: Thickness of border in boxes (default: 3).
    - error_correction: Error correction level ERROR_CORRECT_M (~15% recovery capability).
    """
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(content)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()

def generate_qr_base64(content: str) -> str:
    """
    Generate QR code and return it as a base64 Data URL string for instant client preview.
    Format: 'data:image/png;base64,...'
    """
    png_bytes = generate_qr_png_bytes(content)
    encoded = base64.b64encode(png_bytes).decode("utf-8")
    return f"data:image/png;base64,{encoded}"
