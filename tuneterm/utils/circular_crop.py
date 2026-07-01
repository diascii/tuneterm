from PIL import Image, ImageDraw

def create_vinyl_crop(image: Image.Image, size: int) -> Image.Image:
    # Resize and crop to square
    w, h = image.size
    min_dim = min(w, h)
    left = (w - min_dim) / 2
    top = (h - min_dim) / 2
    right = (w + min_dim) / 2
    bottom = (h + min_dim) / 2
    img = image.crop((left, top, right, bottom))
    img = img.resize((size, size), Image.Resampling.LANCZOS)
    
    # Create mask for circular crop and center hole
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    
    # Outer circle
    draw.ellipse((0, 0, size, size), fill=255)
    
    # Inner hole (about 15% of the size)
    hole_size = int(size * 0.15)
    hole_offset = (size - hole_size) // 2
    draw.ellipse((hole_offset, hole_offset, hole_offset + hole_size, hole_offset + hole_size), fill=0)
    
    # Apply mask
    result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    result.paste(img, (0, 0), mask)
    
    return result
