import logging

from PIL import Image
from typing import List
from tuneterm.utils.circular_crop import create_vinyl_crop
import io

_log = logging.getLogger("tuneterm")

def rgb_to_ansi(r: int, g: int, b: int, is_bg: bool = False) -> str:
    code = "48;2" if is_bg else "38;2"
    return f"\033[{code};{r};{g};{b}m"

def image_to_half_block_ascii(image: Image.Image, width: int, height: int) -> str:
    """Convert an image to a truecolor half-block ascii string."""
    if image.mode != "RGBA":
        image = image.convert("RGBA")
        
    img = image.resize((width, height * 2), Image.Resampling.LANCZOS)
    pixels = img.load()
    
    lines = []
    for y in range(0, img.height, 2):
        line = ""
        for x in range(img.width):
            r1, g1, b1, a1 = pixels[x, y]
            if y + 1 < img.height:
                r2, g2, b2, a2 = pixels[x, y + 1]
            else:
                r2, g2, b2, a2 = (0, 0, 0, 0)
                
            if a1 == 0 and a2 == 0:
                line += "\033[0m "
            elif a1 > 0 and a2 == 0:
                line += f"{rgb_to_ansi(r1, g1, b1, False)}\033[49m▀"
            elif a1 == 0 and a2 > 0:
                line += f"{rgb_to_ansi(r2, g2, b2, False)}\033[49m▄"
            else:
                line += f"{rgb_to_ansi(r1, g1, b1, False)}{rgb_to_ansi(r2, g2, b2, True)}▀"
        
        line += "\033[0m"
        lines.append(line)
        
    return "\n".join(lines)

def image_to_braille_ascii(image: Image.Image, width: int, height: int) -> str:
    """Convert an image to a truecolor braille ascii string."""
    if image.mode != "RGBA":
        image = image.convert("RGBA")
        
    img = image.resize((width * 2, height * 4), Image.Resampling.LANCZOS)
    pixels = img.load()
    
    braille_map = [
        [0x01, 0x08],
        [0x02, 0x10],
        [0x04, 0x20],
        [0x40, 0x80]
    ]
    
    lines = []
    for y in range(height):
        line = ""
        for x in range(width):
            char_val = 0
            r_sum, g_sum, b_sum, count = 0, 0, 0, 0
            
            for dy in range(4):
                for dx in range(2):
                    px = x * 2 + dx
                    py = y * 4 + dy
                    
                    if px < img.width and py < img.height:
                        r, g, b, a = pixels[px, py]
                        
                        if a > 127:  # Use alpha for shape sharpness
                            char_val |= braille_map[dy][dx]
                            r_sum += r
                            g_sum += g
                            b_sum += b
                            count += 1
            
            if count > 0 and char_val > 0:
                r_avg = r_sum // count
                g_avg = g_sum // count
                b_avg = b_sum // count
                char = chr(0x2800 + char_val)
                line += f"{rgb_to_ansi(r_avg, g_avg, b_avg)}{char}"
            else:
                line += "\033[0m "
                
        line += "\033[0m"
        lines.append(line)
        
    return "\n".join(lines)

def generate_vinyl_frames(image_bytes: bytes, width: int = 40, height: int = 20) -> List[str]:
    """Generates 36 frames of spinning vinyl."""
    try:
        if image_bytes:
            img = Image.open(io.BytesIO(image_bytes))
        else:
            img = Image.new("RGBA", (200, 200), (30, 30, 30, 255))
    except Exception as e:
        _log.debug("[ASCIIArt] Gagal load image, fallback ke blank: %s", e)
        img = Image.new("RGBA", (200, 200), (30, 30, 30, 255))
        
    high_res_size = max(width, height * 2) * 4
    cropped = create_vinyl_crop(img, high_res_size)
    
    frames = []
    for i in range(36):
        angle = i * -10
        rotated = cropped.rotate(angle, resample=Image.Resampling.BICUBIC, expand=False)
        ascii_frame = image_to_braille_ascii(rotated, width, height)
        frames.append(ascii_frame)
        
    return frames
