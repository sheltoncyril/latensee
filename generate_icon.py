"""Generates icon.ico and icon.png for use with PyInstaller builds."""
from PIL import Image, ImageDraw


def draw_icon(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    r = max(4, size // 5)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=r, fill="#0f111a")

    bars = [
        ("#f6821f", 0.38),
        ("#7c3aed", 0.50),
        ("#4285f4", 0.62),
        ("#0097d9", 0.75),
        ("#5fb955", 0.88),
    ]

    pad   = size * 0.15
    n     = len(bars)
    bar_h = (size - 2 * pad) / (n * 1.75)
    gap   = bar_h * 0.75
    max_w = size - 2 * pad
    y     = pad

    for color, frac in bars:
        w    = max_w * frac
        br   = max(1, bar_h / 2)
        d.rounded_rectangle([pad, y, pad + w, y + bar_h], radius=br, fill=color)

        mx, my, dm = pad + w, y + bar_h / 2, max(1, bar_h * 0.42)
        d.polygon([(mx + dm, my), (mx, my - dm), (mx - dm, my), (mx, my + dm)], fill="white")

        y += bar_h + gap

    return img


if __name__ == "__main__":
    sizes  = [16, 24, 32, 48, 64, 128, 256]
    images = [draw_icon(s) for s in sizes]
    images[0].save("icon.ico", format="ICO", sizes=[(s, s) for s in sizes],
                   append_images=images[1:])
    images[-1].save("icon.png", format="PNG")
    print("Generated icon.ico and icon.png")
