"""Generates icon.ico and icon.png for use with PyInstaller builds."""
from PIL import Image, ImageDraw

RENDER_SIZE = 512


def draw_icon_hires() -> Image.Image:
    S = RENDER_SIZE
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    r = S // 5
    d.rounded_rectangle([0, 0, S - 1, S - 1], radius=r, fill="#0f111a")

    colors = ["#f6821f", "#4285f4", "#7c3aed", "#5fb955"]
    fracs  = [0.26, 0.48, 0.69, 0.91]
    n      = len(colors)
    pad    = int(S * 0.15)
    inner_w = S - 2 * pad
    inner_h = S - 2 * pad
    bar_w  = int(inner_w / n) - int(S * 0.03)
    gap    = (inner_w - n * bar_w) // (n - 1)
    bottom = S - pad

    for i, (color, frac) in enumerate(zip(colors, fracs)):
        bh = int(inner_h * frac)
        x0 = pad + i * (bar_w + gap)
        y0 = bottom - bh
        x1 = x0 + bar_w
        br = bar_w // 4
        d.rounded_rectangle([x0, y0, x1, bottom], radius=br, fill=color)

    return img


def scale(img: Image.Image, size: int) -> Image.Image:
    return img.resize((size, size), Image.LANCZOS)


if __name__ == "__main__":
    hires = draw_icon_hires()
    sizes  = [16, 24, 32, 48, 64, 128, 256]
    images = [scale(hires, s) for s in sizes]
    images[0].save("icon.ico", format="ICO", sizes=[(s, s) for s in sizes],
                   append_images=images[1:])
    hires.save("icon.png", format="PNG")
    print("Generated icon.ico and icon.png")
