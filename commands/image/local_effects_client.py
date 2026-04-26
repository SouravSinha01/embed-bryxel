import io
import math
import random

from PIL import Image, ImageFilter, ImageSequence


class LocalEffectsClient:
    """Handles image effects that aren't available on Popcat."""

    SUPPORTED = {"pixel", "mirror", "shake", "burn", "mosaic", "shatter"}

    async def generate(self, effect: str, image_bytes: bytes) -> io.BytesIO:
        if effect not in self.SUPPORTED:
            raise ValueError(f"Unknown local effect: {effect}")

        img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")

        handler = getattr(self, f"_effect_{effect}")
        result = handler(img)

        buf = io.BytesIO()
        if isinstance(result, list):
            # Animated GIF (shake)
            result[0].save(
                buf,
                format="GIF",
                save_all=True,
                append_images=result[1:],
                loop=0,
                duration=60,
                disposal=2,
            )
        else:
            result.save(buf, format="PNG")

        buf.seek(0)
        return buf

    # ── Effects ────────────────────────────────────────────────────────────

    def _effect_pixel(self, img: Image.Image, block: int = 16) -> Image.Image:
        """Pixelate by downscaling then upscaling."""
        w, h = img.size
        small = img.resize((max(1, w // block), max(1, h // block)), Image.NEAREST)
        return small.resize((w, h), Image.NEAREST)

    def _effect_mirror(self, img: Image.Image) -> Image.Image:
        """Flip horizontally (mirror along y-axis)."""
        return img.transpose(Image.FLIP_LEFT_RIGHT)

    def _effect_shake(self, img: Image.Image, frames: int = 8, intensity: int = 12) -> list:
        """Animated shake: each frame is randomly offset."""
        w, h = img.size
        result = []
        for i in range(frames):
            dx = random.randint(-intensity, intensity)
            dy = random.randint(-intensity, intensity)
            canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            canvas.paste(img, (dx, dy))
            result.append(canvas.convert("P", palette=Image.ADAPTIVE, colors=256))
        return result

    def _effect_burn(self, img: Image.Image) -> Image.Image:
        """Overlay a fire/burn vignette using a radial gradient."""
        w, h = img.size
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        px = overlay.load()

        cx, cy = w / 2, h / 2
        max_dist = math.hypot(cx, cy)

        for y in range(h):
            for x in range(w):
                dist = math.hypot(x - cx, y - cy) / max_dist
                # Edge glow: orange-red that fades toward center
                alpha = int(max(0, (dist - 0.3) / 0.7) * 220)
                r = 255
                g = int(max(0, 120 - dist * 120))
                b = 0
                px[x, y] = (r, g, b, alpha)

        return Image.alpha_composite(img, overlay)

    def _effect_mosaic(self, img: Image.Image, tile: int = 20) -> Image.Image:
        """Tile the image into square mosaic blocks."""
        w, h = img.size
        out = img.copy()
        px = out.load()

        for ty in range(0, h, tile):
            for tx in range(0, w, tile):
                # Average color of this tile
                total_r = total_g = total_b = total_a = count = 0
                for dy in range(min(tile, h - ty)):
                    for dx in range(min(tile, w - tx)):
                        r, g, b, a = img.getpixel((tx + dx, ty + dy))
                        total_r += r; total_g += g; total_b += b; total_a += a
                        count += 1
                avg = (total_r // count, total_g // count, total_b // count, total_a // count)
                for dy in range(min(tile, h - ty)):
                    for dx in range(min(tile, w - tx)):
                        px[tx + dx, ty + dy] = avg

        return out

    def _effect_shatter(self, img: Image.Image) -> Image.Image:
        """Draw randomized polygon crack lines over the image."""
        import random
        w, h = img.size
        out = img.copy()

        # Draw crack lines using a simple overlay with PIL drawing
        from PIL import ImageDraw
        crack = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(crack)

        # Generate a few crack paths from random center points
        for _ in range(random.randint(4, 7)):
            x0 = random.randint(w // 4, 3 * w // 4)
            y0 = random.randint(h // 4, 3 * h // 4)
            branches = random.randint(4, 8)
            for _ in range(branches):
                angle = random.uniform(0, 2 * math.pi)
                length = random.randint(w // 6, w // 2)
                x1 = int(x0 + math.cos(angle) * length)
                y1 = int(y0 + math.sin(angle) * length)
                # Main crack line (white with slight alpha)
                draw.line([(x0, y0), (x1, y1)], fill=(255, 255, 255, 180), width=2)
                # Sub-crack
                mid_x = (x0 + x1) // 2 + random.randint(-20, 20)
                mid_y = (y0 + y1) // 2 + random.randint(-20, 20)
                draw.line([(mid_x, mid_y), (x1 + random.randint(-30, 30), y1 + random.randint(-30, 30))],
                          fill=(255, 255, 255, 120), width=1)

        return Image.alpha_composite(out, crack)